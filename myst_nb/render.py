"""Module for rendering notebook components to docutils nodes.

Note, this module purposely does not import any Sphinx modules at the top-level,
in order for docutils-only use.
"""
from binascii import a2b_base64
from contextlib import contextmanager
from functools import lru_cache
import hashlib
import json
import logging
from mimetypes import guess_extension
import os
from pathlib import Path
import re
from typing import TYPE_CHECKING, Any, Dict, Iterator, List, Optional, Union

import attr
from docutils import nodes
from docutils.parsers.rst import directives as options_spec
from importlib_metadata import entry_points
from myst_parser.main import MdParserConfig, create_md_parser
from nbformat import NotebookNode

from myst_nb.loggers import DEFAULT_LOG_TYPE

if TYPE_CHECKING:
    from myst_nb.docutils_ import DocutilsNbRenderer


WIDGET_STATE_MIMETYPE = "application/vnd.jupyter.widget-state+json"
WIDGET_VIEW_MIMETYPE = "application/vnd.jupyter.widget-view+json"
RENDER_ENTRY_GROUP = "myst_nb.renderers"
_ANSI_RE = re.compile("\x1b\\[(.*?)([@-~])")


@attr.s()
class MimeData:
    """Mime data from an execution output (display_data / execute_result)

    e.g. notebook.cells[0].outputs[0].data['text/plain'] = "Hello, world!"

    see: https://nbformat.readthedocs.io/en/5.1.3/format_description.html#display-data
    """

    mime_type: str = attr.ib()
    """Mime type key of the output.data"""
    content: Union[str, bytes] = attr.ib()
    """Data value of the output.data"""
    cell_metadata: Dict[str, Any] = attr.ib(factory=dict)
    """Cell level metadata of the output"""
    output_metadata: Dict[str, Any] = attr.ib(factory=dict)
    """Output level metadata of the output"""
    cell_index: Optional[int] = attr.ib(default=None)
    """Index of the cell in the notebook"""
    output_index: Optional[int] = attr.ib(default=None)
    """Index of the output in the cell"""
    line: Optional[int] = attr.ib(default=None)
    """Source line of the cell"""
    md_headings: bool = attr.ib(default=False)
    """Whether to render headings in text/markdown blocks."""
    # we can only do this if know the content will be rendered into the main body
    # of the document, e.g. not inside a container node
    # (otherwise it will break the structure of the AST)

    @property
    def string(self) -> str:
        """Get the content as a string."""
        try:
            return self.content.decode("utf-8")
        except AttributeError:
            return self.content


class NbElementRenderer:
    """A class for rendering notebook elements."""

    # TODO the type of renderer could be DocutilsNbRenderer or SphinxNbRenderer

    def __init__(self, renderer: "DocutilsNbRenderer", logger: logging.Logger) -> None:
        """Initialize the renderer.

        :params output_folder: the folder path for external outputs (like images)
        """
        self._renderer = renderer
        self._logger = logger

    @property
    def renderer(self) -> "DocutilsNbRenderer":
        """The renderer this output renderer is associated with."""
        return self._renderer

    @property
    def logger(self) -> logging.Logger:
        """The logger for this renderer.

        In extension to a standard logger,
        this logger also for `line` and `subtype` kwargs to the `log` methods.
        """
        # TODO the only problem with logging here, is that we cannot generate
        # nodes.system_message to append to the document.
        return self._logger

    @property
    def source(self):
        """The source of the notebook."""
        return self.renderer.document["source"]

    def get_resources(self) -> Dict[str, Any]:
        """Get the resources from the notebook pre-processing."""
        return self.renderer.md_options["nb_resources"]

    def write_file(
        self, path: List[str], content: bytes, overwrite=False, exists_ok=False
    ) -> str:
        """Write a file to the external output folder.

        :param path: the path to write the file to, relative to the output folder
        :param content: the content to write to the file
        :param overwrite: whether to overwrite an existing file
        :param exists_ok: whether to ignore an existing file if overwrite is False

        :returns: URI to use for referencing the file
        """
        output_folder = self.renderer.nb_config.output_folder
        filepath = Path(output_folder).joinpath(*path)
        if not output_folder:
            pass  # do not output anything if output_folder is not set (docutils only)
        elif filepath.exists():
            if overwrite:
                filepath.write_bytes(content)
            elif not exists_ok:
                # TODO raise or just report?
                raise FileExistsError(f"File already exists: {filepath}")
        else:
            filepath.parent.mkdir(parents=True, exist_ok=True)
            filepath.write_bytes(content)

        if self.renderer.sphinx_env:
            # sphinx expects paths in POSIX format, relative to the documents path,
            # or relative to the source folder if prepended with '/'
            filepath = filepath.resolve()
            if os.name == "nt":
                # Can't get relative path between drives on Windows
                return filepath.as_posix()
            # Path().relative_to() doesn't work when not a direct subpath
            return "/" + os.path.relpath(filepath, self.renderer.sphinx_env.app.srcdir)
        else:
            return str(filepath)

    def add_js_file(self, key: str, uri: Optional[str], kwargs: Dict[str, str]) -> None:
        """Register a JavaScript file to include in the HTML output of this document."""
        if "nb_js_files" not in self.renderer.document:
            self.renderer.document["nb_js_files"] = {}
        # TODO handle duplicate keys (whether to override/ignore)
        self.renderer.document["nb_js_files"][key] = (uri, kwargs)

    def render_nb_metadata(self, metadata: dict) -> dict:
        """Render the notebook metadata.

        :returns: unhandled metadata
        """
        # add ipywidgets state JavaScript,
        # The JSON inside the script tag is identified and parsed by:
        # https://github.com/jupyter-widgets/ipywidgets/blob/32f59acbc63c3ff0acf6afa86399cb563d3a9a86/packages/html-manager/src/libembed.ts#L36
        # see also: https://ipywidgets.readthedocs.io/en/7.6.5/embedding.html
        ipywidgets = metadata.pop("widgets", None)
        ipywidgets_mime = (ipywidgets or {}).get(WIDGET_STATE_MIMETYPE, {})
        if ipywidgets_mime.get("state", None):
            self.add_js_file(
                "ipywidgets_state",
                None,
                {
                    "type": "application/vnd.jupyter.widget-state+json",
                    "body": sanitize_script_content(json.dumps(ipywidgets_mime)),
                },
            )
            for i, (path, kwargs) in enumerate(
                self.renderer.nb_config.ipywidgets_js.items()
            ):
                self.add_js_file(f"ipywidgets_{i}", path, kwargs)

        return metadata

    def render_raw_cell(
        self, content: str, metadata: dict, cell_index: int, source_line: int
    ) -> List[nodes.Element]:
        """Render a raw cell.

        https://nbformat.readthedocs.io/en/5.1.3/format_description.html#raw-nbconvert-cells

        :param content: the raw cell content
        :param metadata: the cell level metadata
        :param cell_index: the index of the cell
        :param source_line: the line number of the cell in the source document
        """
        mime_type = metadata.get("format")
        if not mime_type:
            # skip without warning, since e.g. jupytext saves raw cells with no format
            return []
        return self.render_mime_type(
            MimeData(
                mime_type, content, metadata, cell_index=cell_index, line=source_line
            )
        )

    def render_stdout(
        self,
        output: NotebookNode,
        cell_metadata: Dict[str, Any],
        cell_index: int,
        source_line: int,
    ) -> List[nodes.Element]:
        """Render a notebook stdout output.

        https://nbformat.readthedocs.io/en/5.1.3/format_description.html#stream-output

        :param output: the output node
        :param metadata: the cell level metadata
        :param cell_index: the index of the cell containing the output
        :param source_line: the line number of the cell in the source document
        """
        if "remove-stdout" in cell_metadata.get("tags", []):
            return []
        lexer = self.renderer.get_cell_render_config(
            cell_metadata, "text_lexer", "render_text_lexer"
        )
        node = self.renderer.create_highlighted_code_block(
            output["text"], lexer, source=self.source, line=source_line
        )
        node["classes"] += ["output", "stream"]
        return [node]

    def render_stderr(
        self,
        output: NotebookNode,
        cell_metadata: Dict[str, Any],
        cell_index: int,
        source_line: int,
    ) -> List[nodes.Element]:
        """Render a notebook stderr output.

        https://nbformat.readthedocs.io/en/5.1.3/format_description.html#stream-output

        :param output: the output node
        :param metadata: the cell level metadata
        :param cell_index: the index of the cell containing the output
        :param source_line: the line number of the cell in the source document
        """
        if "remove-stderr" in cell_metadata.get("tags", []):
            return []
        output_stderr = self.renderer.get_cell_render_config(
            cell_metadata, "output_stderr"
        )
        msg = f"stderr was found in the cell outputs of cell {cell_index + 1}"
        outputs = []
        if output_stderr == "remove":
            return []
        elif output_stderr == "remove-warn":
            self.logger.warning(msg, subtype="stderr", line=source_line)
            return []
        elif output_stderr == "warn":
            self.logger.warning(msg, subtype="stderr", line=source_line)
        elif output_stderr == "error":
            self.logger.error(msg, subtype="stderr", line=source_line)
        elif output_stderr == "severe":
            self.logger.critical(msg, subtype="stderr", line=source_line)
        lexer = self.renderer.get_cell_render_config(
            cell_metadata, "text_lexer", "render_text_lexer"
        )
        node = self.renderer.create_highlighted_code_block(
            output["text"], lexer, source=self.source, line=source_line
        )
        node["classes"] += ["output", "stderr"]
        outputs.append(node)
        return outputs

    def render_error(
        self,
        output: NotebookNode,
        cell_metadata: Dict[str, Any],
        cell_index: int,
        source_line: int,
    ) -> List[nodes.Element]:
        """Render a notebook error output.

        https://nbformat.readthedocs.io/en/5.1.3/format_description.html#error

        :param output: the output node
        :param metadata: the cell level metadata
        :param cell_index: the index of the cell containing the output
        :param source_line: the line number of the cell in the source document
        """
        traceback = strip_ansi("\n".join(output["traceback"]))
        lexer = self.renderer.get_cell_render_config(
            cell_metadata, "error_lexer", "render_error_lexer"
        )
        node = self.renderer.create_highlighted_code_block(
            traceback, lexer, source=self.source, line=source_line
        )
        node["classes"] += ["output", "traceback"]
        return [node]

    def render_mime_type(self, data: MimeData) -> List[nodes.Element]:
        """Render a notebook mime output, as a block level element."""
        if data.mime_type == "text/plain":
            return self.render_text_plain(data)
        if data.mime_type in {
            "image/png",
            "image/jpeg",
            "application/pdf",
            "image/svg+xml",
            "image/gif",
        }:
            return self.render_image(data)
        if data.mime_type == "text/html":
            return self.render_text_html(data)
        if data.mime_type == "text/latex":
            return self.render_text_latex(data)
        if data.mime_type == "application/javascript":
            return self.render_javascript(data)
        if data.mime_type == WIDGET_VIEW_MIMETYPE:
            return self.render_widget_view(data)
        if data.mime_type == "text/markdown":
            return self.render_markdown(data)

        return self.render_unknown(data)

    def render_unknown(self, data: MimeData) -> List[nodes.Element]:
        """Render a notebook output of unknown mime type."""
        self.logger.warning(
            f"skipping unknown output mime type: {data.mime_type}",
            subtype="unknown_mime_type",
            line=data.line,
        )
        return []

    def render_markdown(self, data: MimeData) -> List[nodes.Element]:
        """Render a notebook text/markdown mime data output."""
        fmt = self.renderer.get_cell_render_config(
            data.cell_metadata, "markdown_format", "render_markdown_format"
        )
        return self._render_markdown_base(
            data, fmt=fmt, inline=False, allow_headings=data.md_headings
        )

    def render_text_plain(self, data: MimeData) -> List[nodes.Element]:
        """Render a notebook text/plain mime data output."""
        lexer = self.renderer.get_cell_render_config(
            data.cell_metadata, "text_lexer", "render_text_lexer"
        )
        node = self.renderer.create_highlighted_code_block(
            data.string, lexer, source=self.source, line=data.line
        )
        node["classes"] += ["output", "text_plain"]
        return [node]

    def render_text_html(self, data: MimeData) -> List[nodes.Element]:
        """Render a notebook text/html mime data output."""
        return [
            nodes.raw(text=data.string, format="html", classes=["output", "text_html"])
        ]

    def render_text_latex(self, data: MimeData) -> List[nodes.Element]:
        """Render a notebook text/latex mime data output."""
        # TODO should we always assume this is math?
        return [
            nodes.math_block(
                text=strip_latex_delimiters(data.string),
                nowrap=False,
                number=None,
                classes=["output", "text_latex"],
            )
        ]

    def render_image(self, data: MimeData) -> List[nodes.Element]:
        """Render a notebook image mime data output."""
        # Adapted from:
        # https://github.com/jupyter/nbconvert/blob/45df4b6089b3bbab4b9c504f9e6a892f5b8692e3/nbconvert/preprocessors/extractoutput.py#L43

        # ensure that the data is a bytestring
        if data.mime_type in {
            "image/png",
            "image/jpeg",
            "image/gif",
            "application/pdf",
        }:
            # data is b64-encoded as text
            data_bytes = a2b_base64(data.content)
        elif isinstance(data.content, str):
            # ensure corrent line separator
            data_bytes = os.linesep.join(data.splitlines()).encode("utf-8")
        # create filename
        extension = (
            guess_extension(data.mime_type) or "." + data.mime_type.rsplit("/")[-1]
        )
        # latex does not recognize the '.jpe' extension
        extension = ".jpeg" if extension == ".jpe" else extension
        # ensure de-duplication of outputs by using hash as filename
        # TODO note this is a change to the current implementation,
        # which names by {notbook_name}-{cell_index}-{output-index}.{extension}
        data_hash = hashlib.sha256(data_bytes).hexdigest()
        filename = f"{data_hash}{extension}"
        # TODO should we be trying to clear old files?
        uri = self.write_file([filename], data_bytes, overwrite=False, exists_ok=True)
        image_node = nodes.image(uri=uri)
        # apply attributes to the image node
        # TODO backwards-compatible re-naming to image_options?
        image_options = self.renderer.get_cell_render_config(
            data.cell_metadata, "image", "render_image_options"
        )
        for key, spec in [
            ("classes", options_spec.class_option),
            ("alt", options_spec.unchanged),
            ("height", options_spec.length_or_unitless),
            ("width", options_spec.length_or_percentage_or_unitless),
            ("scale", options_spec.percentage),
            ("align", lambda a: options_spec.choice(a, ("left", "center", "right"))),
        ]:
            if key not in image_options:
                continue
            try:
                image_node[key] = spec(image_options[key])
            except Exception as exc:
                msg = f"Invalid image option ({key!r}; {image_options[key]!r}): {exc}"
                self.logger.warning(msg, subtype="image", line=data.line)
        return [image_node]

    def render_javascript(self, data: MimeData) -> List[nodes.Element]:
        """Render a notebook application/javascript mime data output."""
        content = sanitize_script_content(data.string)
        mime_type = "application/javascript"
        return [
            nodes.raw(
                text=f'<script type="{mime_type}">{content}</script>',
                format="html",
            )
        ]

    def render_widget_view(self, data: MimeData) -> List[nodes.Element]:
        """Render a notebook application/vnd.jupyter.widget-view+json mime output."""
        # TODO note ipywidgets present?
        content = sanitize_script_content(json.dumps(data.string))
        return [
            nodes.raw(
                text=f'<script type="{WIDGET_VIEW_MIMETYPE}">{content}</script>',
                format="html",
            )
        ]

    def render_mime_type_inline(self, data: MimeData) -> List[nodes.Element]:
        """Render a notebook mime output, as an inline level element."""
        if data.mime_type == "text/plain":
            return self.render_text_plain_inline(data)
        if data.mime_type in {
            "image/png",
            "image/jpeg",
            "application/pdf",
            "image/svg+xml",
            "image/gif",
        }:
            return self.render_image_inline(data)
        if data.mime_type == "text/html":
            return self.render_text_html_inline(data)
        if data.mime_type == "text/latex":
            return self.render_text_latex_inline(data)
        if data.mime_type == "application/javascript":
            return self.render_javascript_inline(data)
        if data.mime_type == WIDGET_VIEW_MIMETYPE:
            return self.render_widget_view_inline(data)
        if data.mime_type == "text/markdown":
            return self.render_markdown_inline(data)

        return self.render_unknown_inline(data)

    def render_unknown_inline(self, data: MimeData) -> List[nodes.Element]:
        """Render a notebook output of unknown mime type."""
        self.logger.warning(
            f"skipping unknown output mime type: {data.mime_type}",
            subtype="unknown_mime_type",
            line=data.line,
        )
        return []

    def render_markdown_inline(self, data: MimeData) -> List[nodes.Element]:
        """Render a notebook text/markdown mime data output."""
        fmt = self.renderer.get_cell_render_config(
            data.cell_metadata, "markdown_format", "render_markdown_format"
        )
        return self._render_markdown_base(
            data, fmt=fmt, inline=True, allow_headings=data.md_headings
        )

    def render_text_plain_inline(self, data: MimeData) -> List[nodes.Element]:
        """Render a notebook text/plain mime data output."""
        # TODO previously this was not syntax highlighted?
        lexer = self.renderer.get_cell_render_config(
            data.cell_metadata, "text_lexer", "render_text_lexer"
        )
        node = self.renderer.create_highlighted_code_block(
            data.string,
            lexer,
            source=self.source,
            line=data.line,
            node_cls=nodes.literal,
        )
        node["classes"] += ["output", "text_plain"]
        return [node]

    def render_text_html_inline(self, data: MimeData) -> List[nodes.Element]:
        """Render a notebook text/html mime data output."""
        return self.render_text_html(data)

    def render_text_latex_inline(self, data: MimeData) -> List[nodes.Element]:
        """Render a notebook text/latex mime data output."""
        # TODO should we always assume this is math?
        return [
            nodes.math(
                text=strip_latex_delimiters(data.string),
                nowrap=False,
                number=None,
                classes=["output", "text_latex"],
            )
        ]

    def render_image_inline(self, data: MimeData) -> List[nodes.Element]:
        """Render a notebook image mime data output."""
        return self.render_image(data)

    def render_javascript_inline(self, data: MimeData) -> List[nodes.Element]:
        """Render a notebook application/javascript mime data output."""
        return self.render_javascript(data)

    def render_widget_view_inline(self, data: MimeData) -> List[nodes.Element]:
        """Render a notebook application/vnd.jupyter.widget-view+json mime output."""
        return self.render_widget_view(data)

    def _render_markdown_base(
        self, data: MimeData, *, fmt: str, inline: bool, allow_headings: bool
    ) -> List[nodes.Element]:
        """Base render for a notebook markdown mime output (block or inline)."""
        psuedo_element = nodes.Element()  # element to hold the parsed markdown
        current_parser = self.renderer.md
        current_md_config = self.renderer.md_config
        try:
            # potentially replace the parser temporarily
            if fmt == "myst":
                # use the current configuration to render the markdown
                pass
            elif fmt == "commonmark":
                # use an isolated, CommonMark only, parser
                self.renderer.md_config = MdParserConfig(commonmark_only=True)
                self.renderer.md = create_md_parser(
                    self.renderer.md_config, self.renderer.__class__
                )
            elif fmt == "gfm":
                # use an isolated, GitHub Flavoured Markdown only, parser
                self.renderer.md_config = MdParserConfig(gfm_only=True)
                self.renderer.md = create_md_parser(
                    self.renderer.md_config, self.renderer.__class__
                )
            else:
                self.logger.warning(
                    f"skipping unknown markdown format: {fmt}",
                    subtype="unknown_markdown_format",
                    line=data.line,
                )
                return []

            with self.renderer.current_node_context(psuedo_element):
                self.renderer.nested_render_text(
                    data.string,
                    data.line or 0,
                    inline=inline,
                    allow_headings=allow_headings,
                )
        finally:
            # restore the parser
            self.renderer.md = current_parser
            self.renderer.md_config = current_md_config

        return psuedo_element.children


class EntryPointError(Exception):
    """Exception raised when an entry point cannot be loaded."""


@lru_cache(maxsize=10)
def load_renderer(name: str) -> NbElementRenderer:
    """Load a renderer,
    given a name within the ``RENDER_ENTRY_GROUP`` entry point group
    """
    all_eps = entry_points()
    if hasattr(all_eps, "select"):
        # importlib_metadata >= 3.6 or importlib.metadata in python >=3.10
        eps = all_eps.select(group=RENDER_ENTRY_GROUP, name=name)
        found = name in eps.names
    else:
        eps = {ep.name: ep for ep in all_eps.get(RENDER_ENTRY_GROUP, [])}
        found = name in eps
    if found:
        klass = eps[name].load()
        if not issubclass(klass, NbElementRenderer):
            raise EntryPointError(
                f"Entry Point for {RENDER_ENTRY_GROUP}:{name} "
                f"is not a subclass of `NbElementRenderer`: {klass}"
            )
        return klass

    raise EntryPointError(f"No Entry Point found for {RENDER_ENTRY_GROUP}:{name}")


def strip_ansi(text: str) -> str:
    """Strip ANSI escape sequences from a string"""
    return _ANSI_RE.sub("", text)


def sanitize_script_content(content: str) -> str:
    """Sanitize the content of a ``<script>`` tag."""
    # note escaping addresses https://github.com/jupyter/jupyter-sphinx/issues/184
    return content.replace("</script>", r"<\/script>")


def strip_latex_delimiters(source):
    r"""Remove LaTeX math delimiters that would be rendered by the math block.

    These are: ``\(…\)``, ``\[…\]``, ``$…$``, and ``$$…$$``.
    This is necessary because sphinx does not have a dedicated role for
    generic LaTeX, while Jupyter only defines generic LaTeX output, see
    https://github.com/jupyter/jupyter-sphinx/issues/90 for discussion.
    """
    source = source.strip()
    delimiter_pairs = (pair.split() for pair in r"\( \),\[ \],$$ $$,$ $".split(","))
    for start, end in delimiter_pairs:
        if source.startswith(start) and source.endswith(end):
            return source[len(start) : -len(end)]

    return source


@contextmanager
def create_figure_context(
    self: "DocutilsNbRenderer", figure_options: Optional[Dict[str, Any]], line: int
) -> Iterator:
    """Create a context manager, which optionally wraps new nodes in a figure node.

    A caption may also be added before or after the nodes.
    """
    if not isinstance(figure_options, dict):
        yield
        return

    # note: most of this is copied directly from sphinx.Figure

    # create figure node
    figure_node = nodes.figure()
    figure_node.line = line
    figure_node.source = self.document["source"]

    # add attributes to figure node
    if figure_options.get("classes"):
        figure_node["classes"] += str(figure_options["classes"]).split()
    if figure_options.get("align") in ("center", "left", "right"):
        figure_node["align"] = figure_options["align"]

    # add target name
    if figure_options.get("name"):
        name = nodes.fully_normalize_name(str(figure_options.get("name")))
        figure_node["names"].append(name)
        self.document.note_explicit_target(figure_node, figure_node)

    # create caption node
    caption = None
    if figure_options.get("caption", ""):
        node = nodes.Element()  # anonymous container for parsing
        with self.current_node_context(node):
            self.nested_render_text(str(figure_options["caption"]), line)
        first_node = node.children[0]
        legend_nodes = node.children[1:]
        if isinstance(first_node, nodes.paragraph):
            caption = nodes.caption(first_node.rawsource, "", *first_node.children)
            caption.source = self.document["source"]
            caption.line = line
        elif not (isinstance(first_node, nodes.comment) and len(first_node) == 0):
            self.create_warning(
                "Figure caption must be a paragraph or empty comment.",
                line=line,
                wtype=DEFAULT_LOG_TYPE,
                subtype="fig_caption",
            )

    self.current_node.append(figure_node)
    old_current_node = self.current_node
    self.current_node = figure_node

    if caption and figure_options.get("caption_before", False):
        figure_node.append(caption)
        if legend_nodes:
            figure_node += nodes.legend("", *legend_nodes)

    yield

    if caption and not figure_options.get("caption_before", False):
        figure_node.append(caption)
        if legend_nodes:
            figure_node += nodes.legend("", *legend_nodes)

    self.current_node = old_current_node

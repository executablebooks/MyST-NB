"""Module for rendering notebook components to docutils nodes."""
import hashlib
import json
import logging
import os
import re
from binascii import a2b_base64
from functools import lru_cache
from mimetypes import guess_extension
from pathlib import Path
from typing import TYPE_CHECKING, List, Union

from docutils import nodes
from importlib_metadata import entry_points
from myst_parser.main import MdParserConfig, create_md_parser
from nbformat import NotebookNode

if TYPE_CHECKING:
    from myst_nb.docutils_ import DocutilsNbRenderer


WIDGET_STATE_MIMETYPE = "application/vnd.jupyter.widget-state+json"
WIDGET_VIEW_MIMETYPE = "application/vnd.jupyter.widget-view+json"
RENDER_ENTRY_GROUP = "myst_nb.renderers"
_ANSI_RE = re.compile("\x1b\\[(.*?)([@-~])")


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


_RGX_CARRIAGERETURN = re.compile(r".*\r(?=[^\n])")
_RGX_BACKSPACE = re.compile(r"[^\n]\b")


def coalesce_streams(outputs: List[NotebookNode]) -> List[NotebookNode]:
    """Merge all stream outputs with shared names into single streams.

    This ensure deterministic outputs.

    Adapted from:
    https://github.com/computationalmodelling/nbval/blob/master/nbval/plugin.py.
    """
    if not outputs:
        return []

    new_outputs = []
    streams = {}
    for output in outputs:
        if output["output_type"] == "stream":
            if output["name"] in streams:
                streams[output["name"]]["text"] += output["text"]
            else:
                new_outputs.append(output)
                streams[output["name"]] = output
        else:
            new_outputs.append(output)

    # process \r and \b characters
    for output in streams.values():
        old = output["text"]
        while len(output["text"]) < len(old):
            old = output["text"]
            # Cancel out anything-but-newline followed by backspace
            output["text"] = _RGX_BACKSPACE.sub("", output["text"])
        # Replace all carriage returns not followed by newline
        output["text"] = _RGX_CARRIAGERETURN.sub("", output["text"])

    # We also want to ensure stdout and stderr are always in the same consecutive order,
    # because they are asynchronous, so order isn't guaranteed.
    for i, output in enumerate(new_outputs):
        if output["output_type"] == "stream" and output["name"] == "stderr":
            if (
                len(new_outputs) >= i + 2
                and new_outputs[i + 1]["output_type"] == "stream"
                and new_outputs[i + 1]["name"] == "stdout"
            ):
                stdout = new_outputs.pop(i + 1)
                new_outputs.insert(i, stdout)

    return new_outputs


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
        """The logger for this renderer."""
        # TODO the only problem with logging here, is that we cannot generate
        # nodes.system_message to append to the document.
        return self._logger

    @property
    def source(self):
        """The source of the notebook."""
        return self.renderer.document["source"]

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
        output_folder = Path(self.renderer.get_nb_config("output_folder", None))
        filepath = output_folder.joinpath(*path)
        if filepath.exists():
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

    def get_cell_metadata(self, cell_index: int) -> NotebookNode:
        # TODO handle key/index error
        return self.renderer.config["notebook"]["cells"][cell_index]["metadata"]

    def render_stdout(
        self, output: NotebookNode, cell_index: int, source_line: int
    ) -> List[nodes.Element]:
        """Render a notebook stdout output.

        https://nbformat.readthedocs.io/en/5.1.3/format_description.html#stream-output

        :param output: the output node
        :param cell_index: the index of the cell containing the output
        :param source_line: the line number of the cell in the source document
        """
        metadata = self.get_cell_metadata(cell_index)
        if "remove-stdout" in metadata.get("tags", []):
            return []
        lexer = self.renderer.get_nb_config("render_text_lexer", cell_index)
        node = self.renderer.create_highlighted_code_block(
            output["text"], lexer, source=self.source, line=source_line
        )
        node["classes"] += ["output", "stream"]
        return [node]

    def render_stderr(
        self, output: NotebookNode, cell_index: int, source_line: int
    ) -> List[nodes.Element]:
        """Render a notebook stderr output.

        https://nbformat.readthedocs.io/en/5.1.3/format_description.html#stream-output

        :param output: the output node
        :param cell_index: the index of the cell containing the output
        :param source_line: the line number of the cell in the source document
        """
        metadata = self.get_cell_metadata(cell_index)
        if "remove-stdout" in metadata.get("tags", []):
            return []
        output_stderr = self.renderer.get_nb_config("output_stderr", cell_index)
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
        lexer = self.renderer.get_nb_config("render_text_lexer", cell_index)
        node = self.renderer.create_highlighted_code_block(
            output["text"], lexer, source=self.source, line=source_line
        )
        node["classes"] += ["output", "stderr"]
        outputs.append(node)
        return outputs

    def render_error(
        self, output: NotebookNode, cell_index: int, source_line: int
    ) -> List[nodes.Element]:
        """Render a notebook error output.

        https://nbformat.readthedocs.io/en/5.1.3/format_description.html#error

        :param output: the output node
        :param cell_index: the index of the cell containing the output
        :param source_line: the line number of the cell in the source document
        """
        traceback = strip_ansi("\n".join(output["traceback"]))
        lexer = self.renderer.get_nb_config("render_error_lexer", cell_index)
        node = self.renderer.create_highlighted_code_block(
            traceback, lexer, source=self.source, line=source_line
        )
        node["classes"] += ["output", "traceback"]
        return [node]

    def render_mime_type(
        self, mime_type: str, data: Union[str, bytes], cell_index: int, source_line: int
    ) -> List[nodes.Element]:
        """Render a notebook mime output.

        https://nbformat.readthedocs.io/en/5.1.3/format_description.html#display-data

        :param mime_type: the key from the "data" dict
        :param data: the value from the "data" dict
        :param cell_index: the index of the cell containing the output
        :param source_line: the line number of the cell in the source document
        """
        if mime_type == "text/plain":
            return self.render_text_plain(data, cell_index, source_line)
        if mime_type in {
            "image/png",
            "image/jpeg",
            "application/pdf",
            "image/svg+xml",
            "image/gif",
        }:
            return self.render_image(mime_type, data, cell_index, source_line)
        if mime_type == "text/html":
            return self.render_text_html(data, cell_index, source_line)
        if mime_type == "text/latex":
            return self.render_text_latex(data, cell_index, source_line)
        if mime_type == "application/javascript":
            return self.render_javascript(data, cell_index, source_line)
        if mime_type == WIDGET_VIEW_MIMETYPE:
            return self.render_widget_view(data, cell_index, source_line)
        if mime_type == "text/markdown":
            return self.render_markdown(data, cell_index, source_line)

        return self.render_unknown(mime_type, data, cell_index, source_line)

    def render_unknown(
        self, mime_type: str, data: Union[str, bytes], cell_index: int, source_line: int
    ) -> List[nodes.Element]:
        """Render a notebook output of unknown mime type.

        :param mime_type: the key from the "data" dict
        :param data: the value from the "data" dict
        :param cell_index: the index of the cell containing the output
        :param source_line: the line number of the cell in the source document
        """
        self.logger.warning(
            f"skipping unknown output mime type: {mime_type}",
            subtype="unknown_mime_type",
            line=source_line,
        )
        return []

    def render_markdown(
        self, data: str, cell_index: int, source_line: int
    ) -> List[nodes.Element]:
        """Render a notebook text/markdown mime data output.

        :param data: the value from the "data" dict
        :param cell_index: the index of the cell containing the output
        :param source_line: the line number of the cell in the source document
        """
        # create a container to parse the markdown into
        temp_container = nodes.container()

        # setup temporary renderer config
        md = self.renderer.md
        match_titles = self.renderer.md_env.get("match_titles", None)
        if self.renderer.get_nb_config("embed_markdown_outputs", cell_index):
            # this configuration is used in conjunction with a transform,
            # which move this content outside & below the output container
            # in this way the Markdown output can contain headings,
            # and not break the structure of the docutils AST
            # TODO create transform and for sphinx prioritise this output for all output formats
            self.renderer.md_env["match_titles"] = True
        else:
            # otherwise we render as simple Markdown and heading are not allowed
            self.renderer.md_env["match_titles"] = False
            self.renderer.md = create_md_parser(
                MdParserConfig(commonmark_only=True), self.renderer.__class__
            )

        # parse markdown
        with self.renderer.current_node_context(temp_container):
            self.renderer.nested_render_text(data, source_line)

        # restore renderer config
        self.renderer.md = md
        self.renderer.md_env["match_titles"] = match_titles

        return temp_container.children

    def render_text_plain(
        self, data: str, cell_index: int, source_line: int
    ) -> List[nodes.Element]:
        """Render a notebook text/plain mime data output.

        :param data: the value from the "data" dict
        :param cell_index: the index of the cell containing the output
        :param source_line: the line number of the cell in the source document
        """
        lexer = self.renderer.get_nb_config("render_text_lexer", cell_index)
        node = self.renderer.create_highlighted_code_block(
            data, lexer, source=self.source, line=source_line
        )
        node["classes"] += ["output", "text_plain"]
        return [node]

    def render_text_html(
        self, data: str, cell_index: int, source_line: int
    ) -> List[nodes.Element]:
        """Render a notebook text/html mime data output.

        :param data: the value from the "data" dict
        :param cell_index: the index of the cell containing the output
        :param source_line: the line number of the cell in the source document
        :param inline: create inline nodes instead of block nodes
        """
        return [nodes.raw(text=data, format="html", classes=["output", "text_html"])]

    def render_text_latex(
        self, data: str, cell_index: int, source_line: int
    ) -> List[nodes.Element]:
        """Render a notebook text/latex mime data output.

        :param data: the value from the "data" dict
        :param cell_index: the index of the cell containing the output
        :param source_line: the line number of the cell in the source document
        """
        # TODO should we always assume this is math?
        return [
            nodes.math_block(
                text=strip_latex_delimiters(data),
                nowrap=False,
                number=None,
                classes=["output", "text_latex"],
            )
        ]

    def render_image(
        self,
        mime_type: Union[str, bytes],
        data: bytes,
        cell_index: int,
        source_line: int,
    ) -> List[nodes.Element]:
        """Render a notebook image mime data output.

        :param mime_type: the key from the "data" dict
        :param data: the value from the "data" dict
        :param cell_index: the index of the cell containing the output
        :param source_line: the line number of the cell in the source document
        """
        # Adapted from:
        # https://github.com/jupyter/nbconvert/blob/45df4b6089b3bbab4b9c504f9e6a892f5b8692e3/nbconvert/preprocessors/extractoutput.py#L43

        # ensure that the data is a bytestring
        if mime_type in {"image/png", "image/jpeg", "image/gif", "application/pdf"}:
            # data is b64-encoded as text
            data_bytes = a2b_base64(data)
        elif isinstance(data, str):
            # ensure corrent line separator
            data_bytes = os.linesep.join(data.splitlines()).encode("utf-8")
        # create filename
        extension = guess_extension(mime_type) or "." + mime_type.rsplit("/")[-1]
        # latex does not recognize the '.jpe' extension
        extension = ".jpeg" if extension == ".jpe" else extension
        # ensure de-duplication of outputs by using hash as filename
        # TODO note this is a change to the current implementation,
        # which names by {notbook_name}-{cell_index}-{output-index}.{extension}
        data_hash = hashlib.sha256(data_bytes).hexdigest()
        filename = f"{data_hash}{extension}"
        uri = self.write_file([filename], data_bytes, overwrite=False, exists_ok=True)
        # TODO add additional attributes
        return [nodes.image(uri=uri)]

    def render_javascript(
        self, data: str, cell_index: int, source_line: int
    ) -> List[nodes.Element]:
        """Render a notebook application/javascript mime data output.

        :param data: the value from the "data" dict
        :param cell_index: the index of the cell containing the output
        :param source_line: the line number of the cell in the source document
        """
        content = sanitize_script_content(data)
        mime_type = "application/javascript"
        return [
            nodes.raw(
                text=f'<script type="{mime_type}">{content}</script>',
                format="html",
            )
        ]

    def render_widget_view(
        self, data: str, cell_index: int, source_line: int
    ) -> List[nodes.Element]:
        """Render a notebook application/vnd.jupyter.widget-view+json mime output.

        :param data: the value from the "data" dict
        :param cell_index: the index of the cell containing the output
        :param source_line: the line number of the cell in the source document
        """
        content = json.dumps(sanitize_script_content(data))
        return [
            nodes.raw(
                text=f'<script type="{WIDGET_VIEW_MIMETYPE}">{content}</script>',
                format="html",
            )
        ]

    def render_widget_state(self, mime_type: str, data: dict) -> nodes.Element:
        """Render a notebook application/vnd.jupyter.widget-state+json mime output.

        :param mime_type: the key from the "notebook.metdata.widgets" dict
        :param data: the value from the "notebook.metdata.widgets" dict
        """
        # The JSON inside the script tag is identified and parsed by:
        # https://github.com/jupyter-widgets/ipywidgets/blob/32f59acbc63c3ff0acf6afa86399cb563d3a9a86/packages/html-manager/src/libembed.ts#L36
        content = json.dumps(sanitize_script_content(data["state"]))
        return nodes.raw(
            text=f'<script type="{mime_type}">\n{content}\n</script>',
            format="html",
        )


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
            raise Exception(
                f"Entry Point for {RENDER_ENTRY_GROUP}:{name} "
                f"is not a subclass of `NbElementRenderer`: {klass}"
            )
        return klass

    raise Exception(f"No Entry Point found for {RENDER_ENTRY_GROUP}:{name}")

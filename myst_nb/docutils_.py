"""A parser for docutils."""
import hashlib
import json
import logging
import os
import re
from binascii import a2b_base64
from contextlib import nullcontext
from functools import lru_cache
from mimetypes import guess_extension
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Dict, List, Optional, Tuple, Union

from docutils import nodes
from docutils.core import default_description, publish_cmdline
from importlib_metadata import entry_points
from jupyter_cache import get_cache
from jupyter_cache.executors import load_executor
from jupyter_cache.executors.utils import single_nb_execution
from markdown_it.main import MarkdownIt
from markdown_it.rules_core import StateCore
from markdown_it.token import Token
from markdown_it.tree import SyntaxTreeNode
from myst_parser.docutils_ import DOCUTILS_EXCLUDED_ARGS as DOCUTILS_EXCLUDED_ARGS_MYST
from myst_parser.docutils_ import Parser as MystParser
from myst_parser.docutils_ import create_myst_config, create_myst_settings_spec
from myst_parser.docutils_renderer import DocutilsRenderer, token_line
from myst_parser.main import MdParserConfig, create_md_parser
from nbformat import NotebookNode
from nbformat import reads as read_nb
from typing_extensions import Literal

from myst_nb.configuration import NbParserConfig
from myst_nb.render_outputs import coalesce_streams

NOTEBOOK_VERSION = 4
WIDGET_STATE_MIMETYPE = "application/vnd.jupyter.widget-state+json"
WIDGET_VIEW_MIMETYPE = "application/vnd.jupyter.widget-view+json"
_ANSI_RE = re.compile("\x1b\\[(.*?)([@-~])")


DOCUTILS_EXCLUDED_ARGS = {
    # docutils.conf can't represent dicts
    # TODO can we make this work?
    "custom_formats",
}


# mapping of standard logger level names to their docutils equivalent
_LOGNAME_TO_DOCUTILS_LEVEL = {
    "DEBUG": 0,
    "INFO": 1,
    "WARN": 2,
    "WARNING": 2,
    "ERROR": 3,
    "CRITICAL": 4,
    "FATAL": 4,
}


class DocutilsFormatter(logging.Formatter):
    """A formatter that formats log messages for docutils."""

    def __init__(self, source: str):
        """Initialize a new formatter."""
        self._source = source
        super().__init__()

    def format(self, record: logging.LogRecord) -> str:
        """Format a log record for docutils."""
        levelname = record.levelname.upper()
        level = _LOGNAME_TO_DOCUTILS_LEVEL.get(levelname, 0)
        node = nodes.system_message(
            record.msg, source=self._source, type=levelname, level=level
        )
        return node.astext()


class DocutilsLogHandler(logging.Handler):
    """Bridge from a Python logger to a docutils reporter."""

    def __init__(self, document: nodes.document) -> None:
        """Initialize a new handler."""
        super().__init__()
        self._document = document
        reporter = self._document.reporter
        self._name_to_level = {
            "DEBUG": reporter.DEBUG_LEVEL,
            "INFO": reporter.INFO_LEVEL,
            "WARN": reporter.WARNING_LEVEL,
            "WARNING": reporter.WARNING_LEVEL,
            "ERROR": reporter.ERROR_LEVEL,
            "CRITICAL": reporter.SEVERE_LEVEL,
            "FATAL": reporter.SEVERE_LEVEL,
        }

    def emit(self, record: logging.LogRecord) -> None:
        """Handle a log record."""
        levelname = record.levelname.upper()
        level = self._name_to_level.get(levelname, self._document.reporter.DEBUG_LEVEL)
        self._document.reporter.system_message(level, record.msg)


class Parser(MystParser):
    """Docutils parser for Jupyter Notebooks, containing MyST Markdown."""

    supported: Tuple[str, ...] = ("mystnb", "ipynb")
    """Aliases this parser supports."""

    settings_spec = (
        "MyST-NB options",
        None,
        create_myst_settings_spec(DOCUTILS_EXCLUDED_ARGS, NbParserConfig, "nb_"),
        *MystParser.settings_spec,
    )
    """Runtime settings specification."""

    config_section = "myst-nb parser"

    @staticmethod
    def get_logger(document: nodes.document) -> logging.Logger:
        """Get or create a logger for a docutils document."""
        logger = logging.getLogger(document["source"])
        logger.setLevel(logging.DEBUG)
        if not logger.handlers:
            logger.addHandler(DocutilsLogHandler(document))
        return logger

    def parse(self, inputstring: str, document: nodes.document) -> None:
        """Parse source text.

        :param inputstring: The source string to parse
        :param document: The root docutils node to add AST elements to
        """
        # create a logger for this document
        logger = self.get_logger(document)

        # get markdown parsing configuration
        try:
            md_config = create_myst_config(
                document.settings, DOCUTILS_EXCLUDED_ARGS_MYST
            )
        except (TypeError, ValueError) as error:
            logger.error(f"myst configuration invalid: {error.args[0]}")
            md_config = MdParserConfig()

        # get notebook rendering configuration
        try:
            nb_config = create_myst_config(
                document.settings, DOCUTILS_EXCLUDED_ARGS, NbParserConfig, "nb_"
            )
        except (TypeError, ValueError) as error:
            logger.error(f"myst-nb configuration invalid: {error.args[0]}")
            nb_config = NbParserConfig()

        # convert inputstring to notebook
        # TODO handle converters
        notebook: NotebookNode = read_nb(inputstring, as_version=NOTEBOOK_VERSION)

        # execute notebook if necessary
        # TODO also look at notebook metadata
        if nb_config.execution_mode == "force":
            path = str(Path(document["source"]).parent)
            cwd_context = (
                TemporaryDirectory()
                if nb_config.execution_in_temp
                else nullcontext(path)
            )
            with cwd_context as cwd:
                cwd = os.path.abspath(cwd)
                logger.info(f"Executing notebook in {cwd}")
                result = single_nb_execution(
                    notebook,
                    cwd=cwd,
                    allow_errors=nb_config.execution_allow_errors,
                    timeout=nb_config.execution_timeout,
                )
                logger.info(f"Executed notebook in {result.time:.2f} seconds")
                # TODO save execution data on document (and environment if sphinx)
                # TODO handle errors
        elif nb_config.execution_mode == "cache":
            # TODO for sphinx, the default would be in the output directory
            cache = get_cache(nb_config.execution_cache_path or ".cache")
            stage_record = cache.stage_notebook_file(document["source"])
            # TODO handle converters
            if cache.get_cache_record_of_staged(stage_record.pk) is None:
                executor = load_executor("basic", cache, logger=logger)
                executor.run_and_cache(
                    filter_pks=[stage_record.pk],
                    allow_errors=nb_config.execution_allow_errors,
                    timeout=nb_config.execution_timeout,
                    run_in_temp=nb_config.execution_in_temp,
                )
            else:
                logger.info("Using cached notebook outputs")
            # TODO handle errors
            _, notebook = cache.merge_match_into_notebook(notebook)

        # TODO write executed notebook to output folder
        # always for sphinx, but maybe docutils option on whether to do this?
        # only on successful parse?

        # Setup parser
        mdit_parser = create_md_parser(md_config, DocutilsNbRenderer)
        mdit_parser.options["document"] = document
        mdit_parser.options["notebook"] = notebook
        mdit_parser.options["nb_config"] = nb_config.as_dict()
        mdit_env: Dict[str, Any] = {}
        # parse to tokens
        mdit_tokens = notebook_to_tokens(notebook, mdit_parser, mdit_env)
        # convert to docutils AST, which is added to the document
        mdit_parser.renderer.render(mdit_tokens, mdit_parser.options, mdit_env)


def notebook_to_tokens(
    notebook: NotebookNode, mdit_parser: MarkdownIt, mdit_env: Dict[str, Any]
) -> List[Token]:
    # disable front-matter, since this is taken from the notebook
    mdit_parser.disable("front_matter", ignoreInvalid=True)
    # this stores global state, such as reference definitions

    # Parse block tokens only first, leaving inline parsing to a second phase
    # (required to collect all reference definitions, before assessing references).
    metadata = dict(notebook.metadata.items())
    # save these keys on the document, rather than as docinfo
    spec_data = {
        key: metadata.pop(key, None) for key in ("kernelspec", "language_info")
    }

    # get language lexer name
    langinfo = spec_data.get("language_info", {})
    lexer = langinfo.get("pygments_lexer", langinfo.get("name", None))
    if lexer is None:
        lexer = spec_data.get("kernelspec", {}).get("language", None)
    # TODO warning if no lexer

    # extract widgets
    widgets = metadata.pop("widgets", None)
    block_tokens = [
        Token("nb_spec_data", "", 0, meta=spec_data),
        Token(
            "front_matter",
            "",
            0,
            map=[0, 0],
            content=metadata,  # type: ignore[arg-type]
        ),
    ]
    for cell_index, nb_cell in enumerate(notebook.cells):

        # skip empty cells
        if len(nb_cell["source"].strip()) == 0:
            continue

        # skip cells tagged for removal
        # TODO make configurable
        tags = nb_cell.metadata.get("tags", [])
        if ("remove_cell" in tags) or ("remove-cell" in tags):
            continue

        # generate tokens
        tokens: List[Token]
        if nb_cell["cell_type"] == "markdown":
            # TODO if cell has tag output-caption, then use as caption for next/preceding cell?
            tokens = [
                Token(
                    "nb_cell_markdown_open",
                    "",
                    1,
                    hidden=True,
                    meta={
                        "index": cell_index,
                        "metadata": dict(nb_cell["metadata"].items()),
                    },
                    map=[0, len(nb_cell["source"].splitlines()) - 1],
                ),
            ]
            with mdit_parser.reset_rules():
                # enable only rules up to block
                rules = mdit_parser.core.ruler.get_active_rules()
                mdit_parser.core.ruler.enableOnly(rules[: rules.index("inline")])
                tokens.extend(mdit_parser.parse(nb_cell["source"], mdit_env))
            tokens.append(
                Token(
                    "nb_cell_markdown_close",
                    "",
                    -1,
                    hidden=True,
                ),
            )
        elif nb_cell["cell_type"] == "raw":
            tokens = [
                Token(
                    "nb_cell_raw",
                    "code",
                    0,
                    content=nb_cell["source"],
                    meta={
                        "index": cell_index,
                        "metadata": dict(nb_cell["metadata"].items()),
                    },
                    map=[0, 0],
                )
            ]
        elif nb_cell["cell_type"] == "code":
            # we don't copy the outputs here, since this would
            # greatly increase the memory consumption,
            # instead they will referenced by the cell index
            tokens = [
                Token(
                    "nb_cell_code",
                    "code",
                    0,
                    content=nb_cell["source"],
                    meta={
                        "index": cell_index,
                        "execution_count": nb_cell.get("execution_count", None),
                        "lexer": lexer,
                        # TODO add notebook node to dict function and apply here etc
                        "metadata": dict(nb_cell["metadata"].items()),
                    },
                    map=[0, 0],
                )
            ]
        else:
            pass  # TODO create warning

        # update token's source lines, using either a source_map (index -> line),
        # set when converting to a notebook, or a pseudo base of the cell index
        smap = notebook.metadata.get("source_map", None)
        start_line = smap[cell_index] if smap else (cell_index + 1) * 10000
        start_line += 1  # use base 1 rather than 0
        for token in tokens:
            if token.map:
                token.map = [start_line + token.map[0], start_line + token.map[1]]
        # also update the source lines for duplicate references
        for dup_ref in mdit_env.get("duplicate_refs", []):
            if "fixed" not in dup_ref:
                dup_ref["map"] = [
                    start_line + dup_ref["map"][0],
                    start_line + dup_ref["map"][1],
                ]
                dup_ref["fixed"] = True

        # add tokens to list
        block_tokens.extend(tokens)

    # The widget state will be embedded as a script, at the end of HTML output
    widget_state = (widgets or {}).get(WIDGET_STATE_MIMETYPE, None)
    if widget_state and widget_state.get("state", None):
        block_tokens.append(
            Token(
                "nb_widget_state",
                "script",
                0,
                attrs={"type": WIDGET_STATE_MIMETYPE},
                meta={"state": widget_state},
                map=[0, 0],
            )
        )

    # Now all definitions have been gathered, run the inline parsing phase
    state = StateCore("", mdit_parser, mdit_env, block_tokens)
    with mdit_parser.reset_rules():
        rules = mdit_parser.core.ruler.get_active_rules()
        mdit_parser.core.ruler.enableOnly(rules[rules.index("inline") :])
        mdit_parser.core.process(state)

    return state.tokens


@lru_cache(maxsize=10)
def load_renderer(name: str) -> "NbOutputRenderer":
    """Load a renderer,
    given a name within the ``myst_nb.output_renderer`` entry point group
    """
    all_eps = entry_points()
    if hasattr(all_eps, "select"):
        # importlib_metadata >= 3.6 or importlib.metadata in python >=3.10
        eps = all_eps.select(group="myst_nb.output_renderer", name=name)
        found = name in eps.names
    else:
        eps = {ep.name: ep for ep in all_eps.get("myst_nb.output_renderer", [])}
        found = name in eps
    if found:
        klass = eps[name].load()
        if not issubclass(klass, NbOutputRenderer):
            raise Exception(
                f"Entry Point for myst_nb.output_renderer:{name} "
                f"is not a subclass of `NbOutputRenderer`: {klass}"
            )
        return klass

    raise Exception(f"No Entry Point found for myst_nb.output_renderer:{name}")


def strip_ansi(text: str) -> str:
    """Strip ANSI escape sequences from a string"""
    return _ANSI_RE.sub("", text)


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


class DocutilsNbRenderer(DocutilsRenderer):
    """ "A docutils-only renderer for Jupyter Notebooks."""

    # TODO upstream
    def add_line_and_source_path_r(
        self, nodes: List[nodes.Node], token: SyntaxTreeNode
    ) -> None:
        """Add the source and line recursively to all nodes."""
        for node in nodes:
            self.add_line_and_source_path(node, token)
            for child in node.traverse():
                self.add_line_and_source_path(child, token)

    # TODO maybe move more things to NbOutputRenderer?
    # and change name to e.g. NbElementRenderer

    def get_nb_config(self, key: str, cell_index: int) -> Any:
        # TODO selection between config/notebook/cell level
        # TODO handle KeyError better
        return self.config["nb_config"][key]

    def render_nb_spec_data(self, token: SyntaxTreeNode) -> None:
        """Add a notebook spec data to the document attributes."""
        self.document["nb_kernelspec"] = token.meta["kernelspec"]
        self.document["nb_language_info"] = token.meta["language_info"]

    def render_nb_cell_markdown(self, token: SyntaxTreeNode) -> None:
        """Render a notebook markdown cell."""
        # TODO this is currently just a "pass-through", but we could utilise the metadata
        # it would be nice to "wrap" this in a container that included the metadata,
        # but unfortunately this would break the heading structure of docutils/sphinx.
        # perhaps we add an "invisible" (non-rendered) marker node to the document tree,
        self.render_children(token)

    def render_nb_cell_raw(self, token: SyntaxTreeNode) -> None:
        """Render a notebook raw cell."""
        # TODO

    def render_nb_cell_code(self, token: SyntaxTreeNode) -> None:
        """Render a notebook code cell."""
        cell_index = token.meta["index"]
        exec_count = token.meta["execution_count"]
        tags = token.meta["metadata"].get("tags", [])
        # create a container for all the output
        classes = ["cell"]
        for tag in tags:
            classes.append(f"tag_{tag.replace(' ', '_')}")
        cell_container = nodes.container(
            nb_type="cell_code",  # TODO maybe nb_cell="code"/"markdown"/"raw"
            cell_index=cell_index,
            # TODO some way to use this to output cell indexes in HTML?
            exec_count=exec_count,
            cell_metadata=token.meta["metadata"],
            classes=classes,
        )
        self.add_line_and_source_path(cell_container, token)
        with self.current_node_context(cell_container, append=True):

            # TODO do we need this -/_ duplication of tag names, or can deprecate one?
            # TODO it would be nice if remove_input/remove_output were also config

            # render the code source code
            if (
                (not self.get_nb_config("remove_code_source", cell_index))
                and ("remove_input" not in tags)
                and ("remove-input" not in tags)
            ):
                cell_input = nodes.container(
                    nb_type="cell_code_source", classes=["cell_input"]
                )
                self.add_line_and_source_path(cell_input, token)
                with self.current_node_context(cell_input, append=True):
                    self.render_nb_cell_code_source(token)
            # render the execution output, if any
            has_outputs = self.config["notebook"]["cells"][cell_index].get(
                "outputs", []
            )
            if (
                has_outputs
                and (not self.get_nb_config("remove_code_outputs", cell_index))
                and ("remove_output" not in tags)
                and ("remove-output" not in tags)
            ):
                cell_output = nodes.container(
                    nb_type="cell_code_output", classes=["cell_output"]
                )
                self.add_line_and_source_path(cell_output, token)
                with self.current_node_context(cell_output, append=True):
                    self.render_nb_cell_code_outputs(token)

    def render_nb_cell_code_source(self, token: SyntaxTreeNode) -> None:
        """Render a notebook code cell's source."""
        cell_index = token.meta["index"]
        lexer = token.meta.get("lexer", None)
        node = self.create_highlighted_code_block(
            token.content,
            lexer,
            number_lines=self.get_nb_config("number_source_lines", cell_index),
            source=self.document["source"],
            line=token_line(token),
        )
        self.add_line_and_source_path(node, token)
        self.current_node.append(node)

    def render_nb_cell_code_outputs(self, token: SyntaxTreeNode) -> None:
        """Render a notebook code cell's outputs."""
        cell_index = token.meta["index"]
        line = token_line(token)
        # metadata = token.meta["metadata"]
        outputs: List[NotebookNode] = self.config["notebook"]["cells"][cell_index].get(
            "outputs", []
        )
        if self.get_nb_config("merge_streams", cell_index):
            outputs = coalesce_streams(outputs)
        render_priority = self.get_nb_config("render_priority", cell_index)
        renderer_name = self.get_nb_config("render_plugin", cell_index)
        # get folder path for external outputs (like images)
        # TODO for sphinx we use a set output folder
        output_folder = self.get_nb_config("output_folder", cell_index)
        # load renderer class from name
        renderer: NbOutputRenderer = load_renderer(renderer_name)(self, output_folder)
        for output in outputs:
            if output.output_type == "stream":
                if output.name == "stdout":
                    _nodes = renderer.render_stdout(output, cell_index, line)
                    self.add_line_and_source_path_r(_nodes, token)
                    self.current_node.extend(_nodes)
                elif output.name == "stderr":
                    _nodes = renderer.render_stderr(output, cell_index, line)
                    self.add_line_and_source_path_r(_nodes, token)
                    self.current_node.extend(_nodes)
                else:
                    pass  # TODO warning
            elif output.output_type == "error":
                _nodes = renderer.render_error(output, cell_index, line)
                self.add_line_and_source_path_r(_nodes, token)
                self.current_node.extend(_nodes)
            elif output.output_type in ("display_data", "execute_result"):
                # TODO how to handle figures and other means of wrapping an output:
                # TODO unwrapped Markdown (so you can output headers)
                # maybe in a transform, we grab the containers and move them
                # "below" the code cell container?
                # if embed_markdown_outputs is True,
                # this should be top priority and we "mark" the container for the transform
                try:
                    mime_type = next(x for x in render_priority if x in output["data"])
                except StopIteration:
                    self.create_warning(
                        "No output mime type found from render_priority",
                        line=line,
                        append_to=self.current_node,
                        subtype="nb_mime_type",
                    )
                else:
                    container = nodes.container(mime_type=mime_type)
                    with self.current_node_context(container, append=True):
                        _nodes = renderer.render_mime_type(
                            mime_type, output["data"][mime_type], cell_index, line
                        )
                        self.add_line_and_source_path_r(_nodes, token)
                        self.current_node.extend(_nodes)
            else:
                self.create_warning(
                    f"Unsupported output type: {output.output_type}",
                    line=line,
                    append_to=self.current_node,
                    subtype="nb_output_type",
                )

    def render_nb_widget_state(self, token: SyntaxTreeNode) -> None:
        """Render the HTML defining the ipywidget state."""
        # The JSON inside the script tag is identified and parsed by:
        # https://github.com/jupyter-widgets/ipywidgets/blob/32f59acbc63c3ff0acf6afa86399cb563d3a9a86/packages/html-manager/src/libembed.ts#L36
        # TODO we also need to load JS URLs if widgets are present and HTML
        html = (
            f'<script type="{token.attrGet("type")}">\n'
            f"{sanitize_script_content(json.dumps(token.meta['state']))}\n"
            "</script>"
        )
        node = nodes.raw("", html, format="html", nb_type="widget_state")
        self.add_line_and_source_path(node, token)
        # always append to bottom of the document
        self.document.append(node)


def sanitize_script_content(content: str) -> str:
    """Sanitize the content of a ``<script>`` tag."""
    # note escaping addresses https://github.com/jupyter/jupyter-sphinx/issues/184
    return content.replace("</script>", r"<\/script>")


class NbOutputRenderer:
    """A class for rendering notebook outputs."""

    def __init__(self, renderer: DocutilsNbRenderer, output_folder: str) -> None:
        """Initialize the renderer.

        :params output_folder: the folder path for external outputs (like images)
        """
        self._renderer = renderer
        self._output_folder = output_folder

    @property
    def renderer(self) -> DocutilsNbRenderer:
        """The renderer this output renderer is associated with."""
        return self._renderer

    def write_file(
        self, path: List[str], content: bytes, overwrite=False, exists_ok=False
    ) -> Path:
        """Write a file to the external output folder.

        :param path: the path to write the file to, relative to the output folder
        :param content: the content to write to the file
        :param overwrite: whether to overwrite an existing file
        :param exists_ok: whether to ignore an existing file if overwrite is False
        """
        folder = Path(self._output_folder)
        filepath = folder.joinpath(*path)
        if filepath.exists():
            if overwrite:
                filepath.write_bytes(content)
            elif not exists_ok:
                # TODO raise or just report?
                raise FileExistsError(f"File already exists: {filepath}")
        else:
            filepath.parent.mkdir(parents=True, exist_ok=True)
            filepath.write_bytes(content)

        return filepath

    @property
    def source(self):
        """The source of the notebook."""
        return self.renderer.document["source"]

    def report(
        self, level: Literal["warning", "error", "severe"], message: str, line: int
    ) -> nodes.system_message:
        """Report an issue."""
        # TODO add cell index to message
        # TODO handle for sphinx (including type/subtype)
        reporter = self.renderer.document.reporter
        levels = {
            "warning": reporter.WARNING_LEVEL,
            "error": reporter.ERROR_LEVEL,
            "severe": reporter.SEVERE_LEVEL,
        }
        return reporter.system_message(
            levels.get(level, reporter.WARNING_LEVEL), message, line=line
        )

    def get_cell_metadata(self, cell_index: int) -> NotebookNode:
        # TODO handle key/index error
        return self._renderer.config["notebook"]["cells"][cell_index]["metadata"]

    # TODO add support for specifying inline types (for glue etc)

    def render_stdout(
        self, output: NotebookNode, cell_index: int, source_line: int
    ) -> List[nodes.Element]:
        """Render a notebook stdout output."""
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
        """Render a notebook stderr output."""
        metadata = self.get_cell_metadata(cell_index)
        if "remove-stdout" in metadata.get("tags", []):
            return []
        output_stderr = self.renderer.get_nb_config("output_stderr", cell_index)
        msg = "output render: stderr was found in the cell outputs"
        outputs = []
        if output_stderr == "remove":
            return []
        elif output_stderr == "remove-warn":
            return [self.report("warning", msg, line=source_line)]
        elif output_stderr == "warn":
            outputs.append(self.report("warning", msg, line=source_line))
        elif output_stderr == "error":
            outputs.append(self.report("error", msg, line=source_line))
        elif output_stderr == "severe":
            outputs.append(self.report("severe", msg, line=source_line))
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
        """Render a notebook error output."""
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
        """Render a notebook mime output."""
        if mime_type == "text/plain":
            return self.render_text_plain(data, cell_index, source_line)
        if mime_type in {"image/png", "image/jpeg", "application/pdf"}:
            # TODO move a2b_base64 to method? (but need to handle render_svg)
            return self.render_image(
                mime_type, a2b_base64(data), cell_index, source_line
            )
        if mime_type == "image/svg+xml":
            return self.render_svg(data, cell_index, source_line)
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
        """Render a notebook output of unknown mime type."""
        return self.report(
            "warning",
            f"skipping unknown output mime type: {mime_type}",
            line=source_line,
        )

    def render_markdown(
        self, data: str, cell_index: int, source_line: int
    ) -> List[nodes.Element]:
        """Render a notebook text/markdown output."""
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
        """Render a notebook text/plain output."""
        lexer = self.renderer.get_nb_config("render_text_lexer", cell_index)
        node = self.renderer.create_highlighted_code_block(
            data, lexer, source=self.source, line=source_line
        )
        node["classes"] += ["output", "text_plain"]
        return [node]

    def render_text_html(
        self, data: str, cell_index: int, source_line: int
    ) -> List[nodes.Element]:
        """Render a notebook text/html output."""
        return [nodes.raw(text=data, format="html", classes=["output", "text_html"])]

    def render_text_latex(
        self, data: str, cell_index: int, source_line: int
    ) -> List[nodes.Element]:
        """Render a notebook text/latex output."""
        # TODO should we always assume this is math?
        return [
            nodes.math_block(
                text=strip_latex_delimiters(data),
                nowrap=False,
                number=None,
                classes=["output", "text_latex"],
            )
        ]

    def render_svg(
        self, data: bytes, cell_index: int, source_line: int
    ) -> List[nodes.Element]:
        """Render a notebook image/svg+xml output."""
        data = data if isinstance(data, str) else data.decode("utf-8")
        data = os.linesep.join(data.splitlines()).encode("utf-8")
        return self.render_image("image/svg+xml", data, source_line)

    def render_image(
        self, mime_type: str, data: bytes, cell_index: int, source_line: int
    ) -> List[nodes.Element]:
        """Render a notebook image output."""
        # Adapted from ``nbconvert.ExtractOutputPreprocessor``
        # TODO add additional attributes
        # create filename
        extension = guess_extension(mime_type) or "." + mime_type.rsplit("/")[-1]
        # latex does not read the '.jpe' extension
        extension = ".jpeg" if extension == ".jpe" else extension
        # ensure de-duplication of outputs by using hash as filename
        # TODO note this is a change to the current implementation,
        # which names by {notbook_name}-{cell_index}-{output-index}.{extension}
        data_hash = hashlib.sha256(data).hexdigest()
        filename = f"{data_hash}{extension}"
        path = self.write_file([filename], data, overwrite=False, exists_ok=True)
        return [nodes.image(uri=str(path))]

    def render_javascript(
        self, data: str, cell_index: int, source_line: int
    ) -> List[nodes.Element]:
        """Render a notebook application/javascript output."""
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
        """Render a notebook application/vnd.jupyter.widget-view+json output."""
        content = json.dumps(sanitize_script_content(data))
        return [
            nodes.raw(
                text=f'<script type="{WIDGET_VIEW_MIMETYPE}">{content}</script>',
                format="html",
            )
        ]


def _run_cli(writer_name: str, writer_description: str, argv: Optional[List[str]]):
    """Run the command line interface for a particular writer."""
    publish_cmdline(
        parser=Parser(),
        writer_name=writer_name,
        description=(
            f"Generates {writer_description} from standalone MyST Notebook sources.\n"
            f"{default_description}"
        ),
        argv=argv,
    )


def cli_html(argv: Optional[List[str]] = None) -> None:
    """Cmdline entrypoint for converting MyST to HTML."""
    _run_cli("html", "(X)HTML documents", argv)


def cli_html5(argv: Optional[List[str]] = None):
    """Cmdline entrypoint for converting MyST to HTML5."""
    _run_cli("html5", "HTML5 documents", argv)


def cli_latex(argv: Optional[List[str]] = None):
    """Cmdline entrypoint for converting MyST to LaTeX."""
    _run_cli("latex", "LaTeX documents", argv)


def cli_xml(argv: Optional[List[str]] = None):
    """Cmdline entrypoint for converting MyST to XML."""
    _run_cli("xml", "Docutils-native XML", argv)


def cli_pseudoxml(argv: Optional[List[str]] = None):
    """Cmdline entrypoint for converting MyST to pseudo-XML."""
    _run_cli("pseudoxml", "pseudo-XML", argv)

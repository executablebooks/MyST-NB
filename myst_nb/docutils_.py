"""A parser for docutils."""
import json
import logging
from typing import Any, Dict, List, Optional, Tuple

from docutils import nodes
from docutils.core import default_description, publish_cmdline
from markdown_it.tree import SyntaxTreeNode
from myst_parser.docutils_ import DOCUTILS_EXCLUDED_ARGS as DOCUTILS_EXCLUDED_ARGS_MYST
from myst_parser.docutils_ import Parser as MystParser
from myst_parser.docutils_ import create_myst_config, create_myst_settings_spec
from myst_parser.docutils_renderer import DocutilsRenderer, token_line
from myst_parser.main import MdParserConfig, create_md_parser
from nbformat import NotebookNode

from myst_nb.configuration import NbParserConfig
from myst_nb.new.execute import update_notebook
from myst_nb.new.parse import notebook_to_tokens
from myst_nb.new.read import create_nb_reader
from myst_nb.new.render import NbElementRenderer, load_renderer, sanitize_script_content
from myst_nb.render_outputs import coalesce_streams

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
        nb_reader, md_config = create_nb_reader(
            inputstring, document["source"], md_config, nb_config
        )
        notebook = nb_reader(inputstring)

        # potentially execute notebook and/or populate outputs from cache
        notebook = update_notebook(notebook, document["source"], nb_config, logger)

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


class DocutilsNbRenderer(DocutilsRenderer):
    """ "A docutils-only renderer for Jupyter Notebooks."""

    # TODO maybe move more things to NbOutputRenderer?
    # and change name to e.g. NbElementRenderer

    def get_nb_config(self, key: str, cell_index: Optional[int]) -> Any:
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
        outputs: List[NotebookNode] = self.config["notebook"]["cells"][cell_index].get(
            "outputs", []
        )
        if self.get_nb_config("merge_streams", cell_index):
            # TODO should this be moved to the parsing phase?
            outputs = coalesce_streams(outputs)
        render_priority = self.get_nb_config("render_priority", cell_index)
        renderer_name = self.get_nb_config("render_plugin", cell_index)
        # get folder path for external outputs (like images)
        # TODO for sphinx we use a set output folder
        output_folder = self.get_nb_config("output_folder", cell_index)
        # load renderer class from name
        renderer: NbElementRenderer = load_renderer(renderer_name)(self, output_folder)
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

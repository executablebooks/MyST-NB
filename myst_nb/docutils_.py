"""A parser for docutils."""
from contextlib import suppress
from functools import partial
from typing import Any, Dict, List, Optional, Tuple

from docutils import nodes
from docutils.core import default_description, publish_cmdline
from docutils.parsers.rst.directives import register_directive
from markdown_it.token import Token
from markdown_it.tree import SyntaxTreeNode
from myst_parser.docutils_ import DOCUTILS_EXCLUDED_ARGS as DOCUTILS_EXCLUDED_ARGS_MYST
from myst_parser.docutils_ import Parser as MystParser
from myst_parser.docutils_ import create_myst_config, create_myst_settings_spec
from myst_parser.docutils_renderer import DocutilsRenderer, token_line
from myst_parser.main import MdParserConfig, create_md_parser
import nbformat
from nbformat import NotebookNode

from myst_nb.configuration import NbParserConfig
from myst_nb.execute import update_notebook
from myst_nb.loggers import DEFAULT_LOG_TYPE, DocutilsDocLogger
from myst_nb.parse import nb_node_to_dict, notebook_to_tokens
from myst_nb.read import (
    NbReader,
    UnexpectedCellDirective,
    read_myst_markdown_notebook,
    standard_nb_read,
)
from myst_nb.render import (
    NbElementRenderer,
    coalesce_streams,
    create_figure_context,
    load_renderer,
)

DOCUTILS_EXCLUDED_ARGS = {
    f.name for f in NbParserConfig.get_fields() if f.metadata.get("docutils_exclude")
}


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

    def parse(self, inputstring: str, document: nodes.document) -> None:
        """Parse source text.

        :param inputstring: The source string to parse
        :param document: The root docutils node to add AST elements to
        """
        document_source = document["source"]

        # register special directives
        register_directive("code-cell", UnexpectedCellDirective)
        register_directive("raw-cell", UnexpectedCellDirective)

        # get a logger for this document
        logger = DocutilsDocLogger(document)

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
        # note docutils does not support the full custom format mechanism
        if nb_config.read_as_md:
            nb_reader = NbReader(
                partial(
                    read_myst_markdown_notebook,
                    config=md_config,
                    add_source_map=True,
                ),
                md_config,
            )
        else:
            nb_reader = NbReader(standard_nb_read, md_config)
        notebook = nb_reader.read(inputstring)

        # Update mystnb configuration with notebook level metadata
        if nb_config.metadata_key in notebook.metadata:
            overrides = nb_node_to_dict(notebook.metadata[nb_config.metadata_key])
            try:
                nb_config = nb_config.copy(**overrides)
            except Exception as exc:
                logger.warning(
                    f"Failed to update configuration with notebook metadata: {exc}",
                    subtype="config",
                )
            else:
                logger.debug(
                    "Updated configuration with notebook metadata", subtype="config"
                )

        # potentially execute notebook and/or populate outputs from cache
        notebook, exec_data = update_notebook(
            notebook, document_source, nb_config, logger
        )
        if exec_data:
            document["nb_exec_data"] = exec_data

        # Setup the markdown parser
        mdit_parser = create_md_parser(nb_reader.md_config, DocutilsNbRenderer)
        mdit_parser.options["document"] = document
        mdit_parser.options["notebook"] = notebook
        mdit_parser.options["nb_config"] = nb_config
        mdit_env: Dict[str, Any] = {}

        # load notebook element renderer class from entry-point name
        # this is separate from DocutilsNbRenderer, so that users can override it
        renderer_name = nb_config.render_plugin
        nb_renderer: NbElementRenderer = load_renderer(renderer_name)(
            mdit_parser.renderer, logger
        )
        mdit_parser.options["nb_renderer"] = nb_renderer

        # parse to tokens
        mdit_tokens = notebook_to_tokens(notebook, mdit_parser, mdit_env, logger)
        # convert to docutils AST, which is added to the document
        mdit_parser.renderer.render(mdit_tokens, mdit_parser.options, mdit_env)

        # write updated notebook to output folder
        # TODO currently this has to be done after the render has been called/setup
        # TODO maybe docutils should be optional on whether to do this?
        # utf-8 is the de-facto standard encoding for notebooks.
        content = nbformat.writes(notebook).encode("utf-8")
        path = ["rendered.ipynb"]
        nb_renderer.write_file(path, content, overwrite=True)
        # TODO also write CSS to output folder if necessary or always?
        # TODO we also need to load JS URLs if ipywidgets are present and HTML


class DocutilsNbRenderer(DocutilsRenderer):
    """A docutils-only renderer for Jupyter Notebooks."""

    @property
    def nb_renderer(self) -> NbElementRenderer:
        """Get the notebook element renderer."""
        return self.config["nb_renderer"]

    def get_nb_config(self, key: str) -> Any:
        """Get a notebook level configuration value.

        :raises: KeyError if the key is not found
        """
        return self.config["nb_config"][key]

    def get_cell_render_config(
        self,
        cell_index: int,
        key: str,
        nb_key: Optional[str] = None,
        has_nb_key: bool = True,
    ) -> Any:
        """Get a cell level render configuration value.

        :param has_nb_key: Whether to also look in the notebook level configuration
        :param nb_key: The notebook level configuration key to use if the cell
            level key is not found. if None, use the ``key`` argument

        :raises: IndexError if the cell index is out of range
        :raises: KeyError if the key is not found
        """
        cell = self.config["notebook"].cells[cell_index]
        cell_metadata_key = self.get_nb_config("cell_render_key")
        if (
            cell_metadata_key not in cell.metadata
            or key not in cell.metadata[cell_metadata_key]
        ):
            if not has_nb_key:
                raise KeyError(key)
            return self.get_nb_config(nb_key if nb_key is not None else key)
        # TODO validate?
        return cell.metadata[cell_metadata_key][key]

    def render_nb_metadata(self, token: SyntaxTreeNode) -> None:
        """Render the notebook metadata."""
        metadata = dict(token.meta)

        # save these special keys on the document, rather than as docinfo
        self.document["nb_kernelspec"] = metadata.pop("kernelspec", None)
        self.document["nb_language_info"] = metadata.pop("language_info", None)

        # TODO should we provide hook for NbElementRenderer?

        # TODO how to handle ipywidgets in docutils?
        ipywidgets = metadata.pop("widgets", None)  # noqa: F841
        # ipywidgets_mime = (ipywidgets or {}).get(WIDGET_STATE_MIMETYPE, {})

        # forward the rest to the front_matter renderer
        self.render_front_matter(
            Token(
                "front_matter",
                "",
                0,
                map=[0, 0],
                content=metadata,  # type: ignore[arg-type]
            ),
        )

    def render_nb_widget_state(self, token: SyntaxTreeNode) -> None:
        """Render the HTML defining the ipywidget state."""
        # TODO handle this more generally,
        # by just passing all notebook metadata to the nb_renderer
        node = self.nb_renderer.render_widget_state(
            mime_type=token.attrGet("type"), data=token.meta
        )
        node["nb_element"] = "widget_state"
        self.add_line_and_source_path(node, token)
        # always append to bottom of the document
        self.document.append(node)

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
        tags = token.meta["metadata"].get("tags", [])

        # TODO do we need this -/_ duplication of tag names, or can we deprecate one?
        remove_input = (
            self.get_cell_render_config(cell_index, "remove_code_source")
            or ("remove_input" in tags)
            or ("remove-input" in tags)
        )
        remove_output = (
            self.get_cell_render_config(cell_index, "remove_code_outputs")
            or ("remove_output" in tags)
            or ("remove-output" in tags)
        )

        # if we are remove both the input and output, we can skip the cell
        if remove_input and remove_output:
            return

        # create a container for all the input/output
        classes = ["cell"]
        for tag in tags:
            classes.append(f"tag_{tag.replace(' ', '_')}")
        cell_container = nodes.container(
            nb_element="cell_code",
            cell_index=cell_index,
            # TODO some way to use this to allow repr of count in outputs like HTML?
            exec_count=token.meta["execution_count"],
            cell_metadata=token.meta["metadata"],
            classes=classes,
        )
        self.add_line_and_source_path(cell_container, token)
        with self.current_node_context(cell_container, append=True):

            # TODO do we need this -/_ duplication of tag names, or can deprecate one?

            # render the code source code
            if not remove_input:
                cell_input = nodes.container(
                    nb_element="cell_code_source", classes=["cell_input"]
                )
                self.add_line_and_source_path(cell_input, token)
                with self.current_node_context(cell_input, append=True):
                    self.render_nb_cell_code_source(token)

            # render the execution output, if any
            has_outputs = self.config["notebook"]["cells"][cell_index].get(
                "outputs", []
            )
            if (not remove_output) and has_outputs:
                cell_output = nodes.container(
                    nb_element="cell_code_output", classes=["cell_output"]
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
            number_lines=self.get_cell_render_config(cell_index, "number_source_lines"),
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
        if self.get_cell_render_config(cell_index, "merge_streams"):
            outputs = coalesce_streams(outputs)

        mime_priority = self.get_cell_render_config(cell_index, "mime_priority")

        # render the outputs
        for output in outputs:
            if output.output_type == "stream":
                if output.name == "stdout":
                    _nodes = self.nb_renderer.render_stdout(output, cell_index, line)
                    self.add_line_and_source_path_r(_nodes, token)
                    self.current_node.extend(_nodes)
                elif output.name == "stderr":
                    _nodes = self.nb_renderer.render_stderr(output, cell_index, line)
                    self.add_line_and_source_path_r(_nodes, token)
                    self.current_node.extend(_nodes)
                else:
                    pass  # TODO warning
            elif output.output_type == "error":
                _nodes = self.nb_renderer.render_error(output, cell_index, line)
                self.add_line_and_source_path_r(_nodes, token)
                self.current_node.extend(_nodes)
            elif output.output_type in ("display_data", "execute_result"):

                # TODO unwrapped Markdown (so you can output headers)
                # maybe in a transform, we grab the containers and move them
                # "below" the code cell container?
                # if embed_markdown_outputs is True,
                # this should be top priority and we "mark" the container for the transform

                try:
                    mime_type = next(x for x in mime_priority if x in output["data"])
                except StopIteration:
                    self.create_warning(
                        "No output mime type found from render_priority",
                        line=line,
                        append_to=self.current_node,
                        wtype=DEFAULT_LOG_TYPE,
                        subtype="mime_type",
                    )
                else:
                    figure_options = None
                    with suppress(KeyError):
                        figure_options = self.get_cell_render_config(
                            cell_index, "figure", has_nb_key=False
                        )

                    with create_figure_context(self, figure_options, line):
                        container = nodes.container(mime_type=mime_type)
                        with self.current_node_context(container, append=True):
                            _nodes = self.nb_renderer.render_mime_type(
                                mime_type, output["data"][mime_type], cell_index, line
                            )
                            self.current_node.extend(_nodes)
                        self.add_line_and_source_path_r([container], token)
            else:
                self.create_warning(
                    f"Unsupported output type: {output.output_type}",
                    line=line,
                    append_to=self.current_node,
                    wtype=DEFAULT_LOG_TYPE,
                    subtype="output_type",
                )


def _run_cli(writer_name: str, writer_description: str, argv: Optional[List[str]]):
    """Run the command line interface for a particular writer."""
    # TODO note to run this with --report="info", to see notebook execution
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

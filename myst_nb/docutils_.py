"""A parser for docutils."""
from contextlib import suppress
from functools import partial
from typing import Any, Dict, List, Optional, Tuple

from docutils import nodes
from docutils.core import default_description, publish_cmdline
from docutils.parsers.rst.directives import _directives
from docutils.parsers.rst.roles import _roles
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
from myst_nb.execute import execute_notebook
from myst_nb.loggers import DEFAULT_LOG_TYPE, DocutilsDocLogger
from myst_nb.nb_glue.elements import (
    PasteDirective,
    PasteFigureDirective,
    PasteMarkdownDirective,
    PasteMarkdownRole,
    PasteMathDirective,
    PasteRole,
    PasteTextRole,
)
from myst_nb.parse import nb_node_to_dict, notebook_to_tokens
from myst_nb.preprocess import preprocess_notebook
from myst_nb.read import (
    NbReader,
    UnexpectedCellDirective,
    read_myst_markdown_notebook,
    standard_nb_read,
)
from myst_nb.render import (
    MimeData,
    NbElementRenderer,
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
        # register/unregister special directives and roles
        new_directives = (
            ("code-cell", UnexpectedCellDirective),
            ("raw-cell", UnexpectedCellDirective),
            ("glue:", PasteDirective),
            ("glue:any", PasteDirective),
            ("glue:figure", PasteFigureDirective),
            ("glue:math", PasteMathDirective),
            ("glue:md", PasteMarkdownDirective),
        )
        new_roles = (
            ("glue:", PasteRole()),
            ("glue:any", PasteRole()),
            ("glue:text", PasteTextRole()),
            ("glue:md", PasteMarkdownRole()),
        )
        for name, directive in new_directives:
            _directives[name] = directive
        for name, role in new_roles:
            _roles[name] = role
        try:
            return self._parse(inputstring, document)
        finally:
            for name, _ in new_directives:
                _directives.pop(name, None)
            for name, _ in new_roles:
                _roles.pop(name, None)

    def _parse(self, inputstring: str, document: nodes.document) -> None:
        """Parse source text.

        :param inputstring: The source string to parse
        :param document: The root docutils node to add AST elements to
        """
        document_source = document["source"]

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
        notebook, exec_data = execute_notebook(
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
        # we currently do this early, so that the nb_renderer has access to things
        mdit_parser.renderer.setup_render(mdit_parser.options, mdit_env)

        # pre-process notebook and store resources for render
        resources = preprocess_notebook(
            notebook, logger, mdit_parser.renderer.get_cell_render_config
        )
        mdit_parser.renderer.md_options["nb_resources"] = resources
        # we temporarily store nb_renderer on the document,
        # so that roles/directives can access it
        document.attributes["nb_renderer"] = nb_renderer

        # parse to tokens
        mdit_tokens = notebook_to_tokens(notebook, mdit_parser, mdit_env, logger)
        # convert to docutils AST, which is added to the document
        mdit_parser.renderer.render(mdit_tokens, mdit_parser.options, mdit_env)

        # write final (updated) notebook to output folder (utf8 is standard encoding)
        content = nbformat.writes(notebook).encode("utf-8")
        path = ["processed.ipynb"]
        nb_renderer.write_file(path, content, overwrite=True)
        # TODO also write CSS to output folder if necessary or always?
        # TODO we also need to load JS URLs if ipywidgets are present and HTML

        document.attributes.pop("nb_renderer")


class DocutilsNbRenderer(DocutilsRenderer):
    """A docutils-only renderer for Jupyter Notebooks."""

    @property
    def nb_config(self) -> NbParserConfig:
        """Get the notebook element renderer."""
        return self.md_options["nb_config"]

    @property
    def nb_renderer(self) -> NbElementRenderer:
        """Get the notebook element renderer."""
        return self.md_options["nb_renderer"]

    def get_cell_render_config(
        self,
        cell_metadata: Dict[str, Any],
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
        # TODO allow output level configuration?
        use_nb_level = True
        cell_metadata_key = self.nb_config.cell_render_key
        if cell_metadata_key in cell_metadata:
            if isinstance(cell_metadata[cell_metadata_key], dict):
                if key in cell_metadata[cell_metadata_key]:
                    use_nb_level = False
            else:
                # TODO log warning
                pass
        if use_nb_level:
            if not has_nb_key:
                raise KeyError(key)
            return self.nb_config[nb_key if nb_key is not None else key]
        # TODO validate?
        return cell_metadata[cell_metadata_key][key]

    def render_nb_metadata(self, token: SyntaxTreeNode) -> None:
        """Render the notebook metadata."""
        metadata = dict(token.meta)

        # save these special keys on the document, rather than as docinfo
        for key in ("kernelspec", "language_info", "source_map"):
            if key in metadata:
                self.document[f"nb_{key}"] = metadata.pop(key)

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
        line = token_line(token, 0)
        _nodes = self.nb_renderer.render_raw_cell(
            token.content, token.meta["metadata"], token.meta["index"], line
        )
        self.add_line_and_source_path_r(_nodes, token)
        self.current_node.extend(_nodes)

    def render_nb_cell_code(self, token: SyntaxTreeNode) -> None:
        """Render a notebook code cell."""
        cell_index = token.meta["index"]
        tags = token.meta["metadata"].get("tags", [])

        # TODO do we need this -/_ duplication of tag names, or can we deprecate one?
        remove_input = (
            self.get_cell_render_config(token.meta["metadata"], "remove_code_source")
            or ("remove_input" in tags)
            or ("remove-input" in tags)
        )
        remove_output = (
            self.get_cell_render_config(token.meta["metadata"], "remove_code_outputs")
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

            # render the code source code
            if not remove_input:
                cell_input = nodes.container(
                    nb_element="cell_code_source", classes=["cell_input"]
                )
                self.add_line_and_source_path(cell_input, token)
                with self.current_node_context(cell_input, append=True):
                    self.render_nb_cell_code_source(token)

            # render the execution output, if any
            has_outputs = self.md_options["notebook"]["cells"][cell_index].get(
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
        lexer = token.meta.get("lexer", None)
        node = self.create_highlighted_code_block(
            token.content,
            lexer,
            number_lines=self.get_cell_render_config(
                token.meta["metadata"], "number_source_lines"
            ),
            source=self.document["source"],
            line=token_line(token),
        )
        self.add_line_and_source_path(node, token)
        self.current_node.append(node)

    def render_nb_cell_code_outputs(self, token: SyntaxTreeNode) -> None:
        """Render a notebook code cell's outputs."""
        cell_index = token.meta["index"]
        metadata = token.meta["metadata"]
        line = token_line(token)
        outputs: List[NotebookNode] = self.md_options["notebook"]["cells"][
            cell_index
        ].get("outputs", [])
        # render the outputs
        mime_priority = self.get_cell_render_config(metadata, "mime_priority")
        for output_index, output in enumerate(outputs):
            if output.output_type == "stream":
                if output.name == "stdout":
                    _nodes = self.nb_renderer.render_stdout(
                        output, metadata, cell_index, line
                    )
                    self.add_line_and_source_path_r(_nodes, token)
                    self.current_node.extend(_nodes)
                elif output.name == "stderr":
                    _nodes = self.nb_renderer.render_stderr(
                        output, metadata, cell_index, line
                    )
                    self.add_line_and_source_path_r(_nodes, token)
                    self.current_node.extend(_nodes)
                else:
                    pass  # TODO warning
            elif output.output_type == "error":
                _nodes = self.nb_renderer.render_error(
                    output, metadata, cell_index, line
                )
                self.add_line_and_source_path_r(_nodes, token)
                self.current_node.extend(_nodes)
            elif output.output_type in ("display_data", "execute_result"):

                # Note, this is different to the sphinx implementation,
                # here we directly select a single output, based on the mime_priority,
                # as opposed to output all mime types, and select in a post-transform
                # (the mime_priority must then be set for the output format)

                # TODO how to output MyST Markdown?
                # currently text/markdown is set to be rendered as CommonMark only,
                # with headings dissallowed,
                # to avoid "side effects" if the mime is discarded but contained
                # targets, etc, and because we can't parse headings within containers.
                # perhaps we could have a config option to allow this?
                # - for non-commonmark, the text/markdown would always be considered
                #   the top priority, and all other mime types would be ignored.
                # - for headings, we would also need to parsing the markdown
                #   at the "top-level", i.e. not nested in container(s)

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
                            metadata, "figure", has_nb_key=False
                        )

                    with create_figure_context(self, figure_options, line):
                        _nodes = self.nb_renderer.render_mime_type(
                            MimeData(
                                mime_type,
                                output["data"][mime_type],
                                cell_metadata=metadata,
                                output_metadata=output.get("metadata", {}),
                                cell_index=cell_index,
                                output_index=output_index,
                                line=line,
                            ),
                        )
                        self.current_node.extend(_nodes)
                        self.add_line_and_source_path_r(_nodes, token)
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

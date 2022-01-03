"""An extension for sphinx"""
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

import nbformat
from docutils import nodes
from markdown_it.tree import SyntaxTreeNode
from myst_parser import setup_sphinx as setup_myst_parser
from myst_parser.docutils_renderer import token_line
from myst_parser.main import MdParserConfig, create_md_parser
from myst_parser.sphinx_parser import MystParser
from myst_parser.sphinx_renderer import SphinxRenderer
from nbformat import NotebookNode
from sphinx.application import Sphinx
from sphinx.transforms.post_transforms import SphinxPostTransform
from sphinx.util import logging as sphinx_logging

from myst_nb import __version__
from myst_nb.configuration import NbParserConfig
from myst_nb.new.execute import update_notebook
from myst_nb.new.loggers import DEFAULT_LOG_TYPE, SphinxDocLogger
from myst_nb.new.parse import notebook_to_tokens
from myst_nb.new.read import create_nb_reader
from myst_nb.new.render import NbElementRenderer, load_renderer
from myst_nb.render_outputs import coalesce_streams

SPHINX_LOGGER = sphinx_logging.getLogger(__name__)
UNSET = "--unset--"


def setup(app):
    return sphinx_setup(app)


def sphinx_setup(app: Sphinx):
    """Initialize Sphinx extension."""
    # TODO perhaps there should be a way to turn this off,
    # app.add_source_suffix(".md", "myst-nb")
    app.add_source_suffix(".ipynb", "myst-nb")
    app.add_source_parser(MystNbParser)

    # Add myst-parser transforms and configuration
    setup_myst_parser(app)

    for name, default, field in NbParserConfig().as_triple():
        if not field.metadata.get("sphinx_exclude"):
            # TODO add types?
            app.add_config_value(f"nb_{name}", default, "env", Any)
            if "legacy_name" in field.metadata:
                app.add_config_value(
                    f"{field.metadata['legacy_name']}", UNSET, "env", Any
                )

    # generate notebook configuration from Sphinx configuration
    app.connect("builder-inited", create_mystnb_config)

    # ensure notebook checkpoints are excluded
    app.connect("config-inited", add_exclude_patterns)
    # add HTML resources
    app.connect("builder-inited", add_static_path)
    app.add_css_file("mystnb.css")
    # add post-transform for selecting mime type from a bundle
    app.add_post_transform(SelectMimeType)

    # TODO do we need to add lexers, if they are anyhow added via entry-points?

    return {
        "version": __version__,
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }


def create_mystnb_config(app):
    """Generate notebook configuration from Sphinx configuration"""

    # Ignore type checkers because the attribute is dynamically assigned
    from sphinx.util.console import bold  # type: ignore[attr-defined]

    values = {}
    for name, _, field in NbParserConfig().as_triple():
        if not field.metadata.get("sphinx_exclude"):
            values[name] = app.config[f"nb_{name}"]
            if "legacy_name" in field.metadata:
                legacy_value = app.config[field.metadata["legacy_name"]]
                if legacy_value != UNSET:
                    legacy_name = field.metadata["legacy_name"]
                    SPHINX_LOGGER.warning(
                        f"{legacy_name!r} is deprecated for 'nb_{name}' "
                        f"[{DEFAULT_LOG_TYPE}.config]",
                        type=DEFAULT_LOG_TYPE,
                        subtype="config",
                    )
                    values[name] = legacy_value

    try:
        app.env.mystnb_config = NbParserConfig(**values)
        SPHINX_LOGGER.info(
            bold("myst-nb v%s:") + " %s", __version__, app.env.mystnb_config
        )
    except (TypeError, ValueError) as error:
        SPHINX_LOGGER.error("myst-nb configuration invalid: %s", error.args[0])
        app.env.mystnb_config = NbParserConfig()

    # update the output_folder (for writing external files like images),
    # to a set path within the sphinx build folder
    output_folder = Path(app.outdir).parent.joinpath("jupyter_execute").resolve()
    app.env.mystnb_config = app.env.mystnb_config.copy(output_folder=str(output_folder))


def add_exclude_patterns(app: Sphinx, config):
    """Add default exclude patterns (if not already present)."""
    if "**.ipynb_checkpoints" not in config.exclude_patterns:
        config.exclude_patterns.append("**.ipynb_checkpoints")


def add_static_path(app: Sphinx):
    """Add static path for myst-nb."""
    static_path = Path(__file__).absolute().with_name("_static")
    app.config.html_static_path.append(str(static_path))


class MystNbParser(MystParser):
    """Sphinx parser for Jupyter Notebook formats, containing MyST Markdown."""

    supported = ("myst-nb",)
    translate_section_name = None

    config_section = "myst-nb parser"
    config_section_dependencies = ("parsers",)

    def parse(self, inputstring: str, document: nodes.document) -> None:
        """Parse source text.

        :param inputstring: The source string to parse
        :param document: The root docutils node to add AST elements to
        """
        document_source = self.env.doc2path(self.env.docname)

        # get a logger for this document
        logger = SphinxDocLogger(document)

        # get markdown parsing configuration
        md_config: MdParserConfig = self.env.myst_config
        # get notebook rendering configuration
        nb_config: NbParserConfig = self.env.mystnb_config

        # convert inputstring to notebook
        # TODO in sphinx, we also need to allow for the fact
        # that the input could be a standard markdown file
        nb_reader, md_config = create_nb_reader(
            inputstring, document_source, md_config, nb_config
        )
        notebook = nb_reader(inputstring)

        # TODO update nb_config from notebook metadata

        # Setup the markdown parser
        mdit_parser = create_md_parser(md_config, SphinxNbRenderer)
        mdit_parser.options["document"] = document
        mdit_parser.options["notebook"] = notebook
        mdit_parser.options["nb_config"] = nb_config.as_dict()
        mdit_env: Dict[str, Any] = {}

        # load notebook element renderer class from entry-point name
        # this is separate from DocutilsNbRenderer, so that users can override it
        renderer_name = nb_config.render_plugin
        nb_renderer: NbElementRenderer = load_renderer(renderer_name)(
            mdit_parser.renderer, logger
        )
        mdit_parser.options["nb_renderer"] = nb_renderer

        # potentially execute notebook and/or populate outputs from cache
        notebook, exec_data = update_notebook(
            notebook, document_source, nb_config, logger
        )
        if exec_data:
            # TODO note this is a different location to previous env.nb_execution_data
            # but it is a more standard place, which will be merged on parallel builds
            # (via MetadataCollector)
            # Also to note, in docutils we store it on the document
            # TODO should we deal with this getting overwritten by docinfo?
            self.env.metadata[self.env.docname]["nb_exec_data"] = exec_data
            # self.env.nb_exec_data_changed = True
            # TODO how to do this in a "parallel friendly" way? perhaps we don't store
            # this and just check the mtime of the exec_data instead,
            # using that for the the exec_table extension

        # TODO store/print error traceback?

        # parse to tokens
        mdit_tokens = notebook_to_tokens(notebook, mdit_parser, mdit_env, logger)
        # convert to docutils AST, which is added to the document
        mdit_parser.renderer.render(mdit_tokens, mdit_parser.options, mdit_env)

        # write updated notebook to output folder
        # TODO currently this has to be done after the render has been called/setup
        # utf-8 is the de-facto standard encoding for notebooks.
        content = nbformat.writes(notebook).encode("utf-8")
        path = self.env.docname.split("/")
        path[-1] += ".ipynb"
        nb_renderer.write_file(path, content, overwrite=True)


class SphinxNbRenderer(SphinxRenderer):
    """A sphinx renderer for Jupyter Notebooks."""

    # TODO de-duplication with DocutilsNbRenderer

    @property
    def nb_renderer(self) -> NbElementRenderer:
        """Get the notebook element renderer."""
        return self.config["nb_renderer"]

    # TODO maybe move more things to NbOutputRenderer?
    # and change name to e.g. NbElementRenderer

    def get_nb_config(self, key: str, cell_index: Optional[int]) -> Any:
        # TODO selection between config/notebook/cell level
        # (we can maybe update the nb_config with notebook level metadata in parser)
        # TODO handle KeyError better
        return self.config["nb_config"][key]

    def render_nb_spec_data(self, token: SyntaxTreeNode) -> None:
        """Add a notebook spec data to the document attributes."""
        # This is different to docutils-only, where we store it on the document
        env = self.sphinx_env
        env.metadata[env.docname]["kernelspec"] = token.meta["kernelspec"]
        env.metadata[env.docname]["language_info"] = token.meta["language_info"]

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
        # create a container for all the output
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
            # TODO it would be nice if remove_input/remove_output were also config

            # render the code source code
            if (
                (not self.get_nb_config("remove_code_source", cell_index))
                and ("remove_input" not in tags)
                and ("remove-input" not in tags)
            ):
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
            if (
                has_outputs
                and (not self.get_nb_config("remove_code_outputs", cell_index))
                and ("remove_output" not in tags)
                and ("remove-output" not in tags)
            ):
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
                # TODO how to handle figures and other means of wrapping an output:
                # TODO unwrapped Markdown (so you can output headers)
                # maybe in a transform, we grab the containers and move them
                # "below" the code cell container?
                # if embed_markdown_outputs is True,
                # this should be top priority and we "mark" the container for the transform

                # We differ from the docutils-only renderer here, because we need to
                # cache all rendered outputs, then choose one from the priority list
                # in a post-transform, once we know which builder is required.
                mime_bundle = nodes.container(nb_element="mime_bundle")
                with self.current_node_context(mime_bundle, append=True):
                    for mime_type, data in output["data"].items():
                        container = nodes.container(mime_type=mime_type)
                        with self.current_node_context(container, append=True):
                            _nodes = self.nb_renderer.render_mime_type(
                                mime_type, data, cell_index, line
                            )
                            self.current_node.extend(_nodes)
                self.add_line_and_source_path_r([mime_bundle], token)
            else:
                self.create_warning(
                    f"Unsupported output type: {output.output_type}",
                    line=line,
                    append_to=self.current_node,
                    wtype=DEFAULT_LOG_TYPE,
                    subtype="output_type",
                )

    def render_nb_widget_state(self, token: SyntaxTreeNode) -> None:
        """Render the HTML defining the ipywidget state."""
        # TODO handle this more generally,
        # by just passing all notebook metadata to the nb_renderer
        # TODO in docutils we also need to load JS URLs if widgets are present and HTML
        node = self.nb_renderer.render_widget_state(
            mime_type=token.attrGet("type"), data=token.meta
        )
        node["nb_element"] = "widget_state"
        self.add_line_and_source_path(node, token)
        # always append to bottom of the document
        self.document.append(node)


class SelectMimeType(SphinxPostTransform):
    """Select the mime type to render from mime bundles,
    based on the builder and its associated priority list.
    """

    default_priority = 4  # TODO set correct priority

    def run(self, **kwargs: Any) -> None:
        """Run the transform."""
        # get priority list for this builder
        # TODO allow for per-notebook/cell priority dicts
        priority_lookup: Dict[str, Sequence[str]] = self.config["nb_render_priority"]
        name = self.app.builder.name
        if name not in priority_lookup:
            SPHINX_LOGGER.warning(
                f"Builder name {name!r} not available in 'nb_render_priority', "
                f"defaulting to 'html' [{DEFAULT_LOG_TYPE}.mime_priority]",
                type=DEFAULT_LOG_TYPE,
                subtype="mime_priority",
            )
            priority_list = priority_lookup["html"]
        else:
            priority_list = priority_lookup[name]

        # findall replaces traverse in docutils v0.18
        iterator = getattr(self.document, "findall", self.document.traverse)
        condition = (
            lambda node: isinstance(node, nodes.container)
            and node.attributes.get("nb_element", "") == "mime_bundle"
        )
        # remove/replace_self will not work with an iterator
        for node in list(iterator(condition)):
            # get available mime types
            mime_types = [node["mime_type"] for node in node.children]
            # select top priority
            index = None
            for mime_type in priority_list:
                try:
                    index = mime_types.index(mime_type)
                except ValueError:
                    continue
                else:
                    break
            if index is None:
                SPHINX_LOGGER.warning(
                    f"No mime type available in priority list builder {name!r} "
                    f"[{DEFAULT_LOG_TYPE}.mime_priority]",
                    type=DEFAULT_LOG_TYPE,
                    subtype="mime_priority",
                    location=node,
                )
                node.parent.remove(node)
            else:
                node.replace_self(node.children[index])

"""An extension for sphinx"""
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from docutils import nodes
from markdown_it.token import Token
from markdown_it.tree import SyntaxTreeNode
from myst_parser import setup_sphinx as setup_myst_parser
from myst_parser.docutils_renderer import token_line
from myst_parser.main import MdParserConfig, create_md_parser
from myst_parser.sphinx_parser import MystParser
from myst_parser.sphinx_renderer import SphinxRenderer
import nbformat
from nbformat import NotebookNode
from sphinx.addnodes import download_reference
from sphinx.application import Sphinx
from sphinx.environment import BuildEnvironment
from sphinx.transforms.post_transforms import SphinxPostTransform
from sphinx.util import logging as sphinx_logging
from sphinx.util.docutils import ReferenceRole

from myst_nb import __version__
from myst_nb.configuration import NbParserConfig
from myst_nb.execute import update_notebook
from myst_nb.execution_tables import setup_exec_table_extension
from myst_nb.loggers import DEFAULT_LOG_TYPE, SphinxDocLogger
from myst_nb.nb_glue.domain import NbGlueDomain
from myst_nb.parse import notebook_to_tokens
from myst_nb.read import UnexpectedCellDirective, create_nb_reader
from myst_nb.render import (
    WIDGET_STATE_MIMETYPE,
    NbElementRenderer,
    coalesce_streams,
    load_renderer,
    sanitize_script_content,
)

SPHINX_LOGGER = sphinx_logging.getLogger(__name__)
UNSET = "--unset--"
OUTPUT_FOLDER = "jupyter_execute"


def sphinx_setup(app: Sphinx):
    """Initialize Sphinx extension."""
    # note, for core events overview, see:
    # https://www.sphinx-doc.org/en/master/extdev/appapi.html#sphinx-core-events

    # Add myst-parser configuration and transforms (but does not add the parser)
    setup_myst_parser(app)

    # add myst-nb configuration variables
    for name, default, field in NbParserConfig().as_triple():
        if not field.metadata.get("sphinx_exclude"):
            # TODO add types?
            app.add_config_value(f"nb_{name}", default, "env", Any)
            if "legacy_name" in field.metadata:
                app.add_config_value(
                    f"{field.metadata['legacy_name']}", UNSET, "env", Any
                )

    # generate notebook configuration from Sphinx configuration
    # this also validates the configuration values
    app.connect("builder-inited", create_mystnb_config)

    # add parser and default associated file suffixes
    app.add_source_parser(MystNbParser)
    app.add_source_suffix(".md", "myst-nb", override=True)
    app.add_source_suffix(".ipynb", "myst-nb")
    # add additional file suffixes for parsing
    app.connect("config-inited", add_nb_custom_formats)
    # ensure notebook checkpoints are excluded from parsing
    app.connect("config-inited", add_exclude_patterns)

    # TODO add an event which, if any files have been removed,
    # all stage records with a non-existent path are removed

    # add directive to ensure all notebook cells are converted
    app.add_directive("code-cell", UnexpectedCellDirective)
    app.add_directive("raw-cell", UnexpectedCellDirective)

    # add directive for downloading an executed notebook
    app.add_role("nb-download", NbDownloadRole())

    # add post-transform for selecting mime type from a bundle
    app.add_post_transform(SelectMimeType)

    # add HTML resources
    app.connect("builder-inited", add_html_static_path)
    app.add_css_file("mystnb.css")
    # note, this event is only available in Sphinx >= 3.5
    app.connect("html-page-context", install_ipywidgets)

    # add configuration for hiding cell input/output
    # TODO replace this, or make it optional
    app.setup_extension("sphinx_togglebutton")
    app.connect("config-inited", update_togglebutton_classes)

    # Note lexers are registered as `pygments.lexers` entry-points
    # and so do not need to be added here.

    # setup extension for execution statistics tables
    setup_exec_table_extension(app)

    # add glue domain
    app.add_domain(NbGlueDomain)

    return {
        "version": __version__,
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }


def add_nb_custom_formats(app: Sphinx, config):
    """Add custom conversion formats."""
    for suffix in config.nb_custom_formats:
        app.add_source_suffix(suffix, "myst-nb", override=True)


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
    # and the execution_cache_path (for caching notebook outputs)
    # to a set path within the sphinx build folder
    output_folder = Path(app.outdir).parent.joinpath(OUTPUT_FOLDER).resolve()
    exec_cache_path = app.env.mystnb_config.execution_cache_path
    if not exec_cache_path:
        exec_cache_path = Path(app.outdir).parent.joinpath(".jupyter_cache").resolve()
    app.env.mystnb_config = app.env.mystnb_config.copy(
        output_folder=str(output_folder), execution_cache_path=str(exec_cache_path)
    )


def add_exclude_patterns(app: Sphinx, config):
    """Add default exclude patterns (if not already present)."""
    if "**.ipynb_checkpoints" not in config.exclude_patterns:
        config.exclude_patterns.append("**.ipynb_checkpoints")


def add_html_static_path(app: Sphinx):
    """Add static path for HTML resources."""
    # TODO better to use importlib_resources here, or perhaps now there is another way?
    static_path = Path(__file__).absolute().with_name("_static")
    app.config.html_static_path.append(str(static_path))


def install_ipywidgets(app: Sphinx, pagename: str, *args: Any, **kwargs: Any) -> None:
    """Install ipywidgets Javascript, if required on the page."""
    if app.builder.format != "html":
        return
    ipywidgets_state = get_doc_metadata(app.env, pagename, "ipywidgets_state")
    if ipywidgets_state is not None:
        # see: https://ipywidgets.readthedocs.io/en/7.6.5/embedding.html

        for path, kwargs in app.env.config["nb_ipywidgets_js"].items():
            app.add_js_file(path, **kwargs)

        # The state of all the widget models on the page
        # TODO how to add data-jupyter-widgets-cdn="https://cdn.jsdelivr.net/npm/"?
        app.add_js_file(
            None,
            type="application/vnd.jupyter.widget-state+json",
            body=ipywidgets_state,
        )


def update_togglebutton_classes(app: Sphinx, config):
    """Update togglebutton classes to recognise hidden cell inputs/outputs."""
    to_add = [
        ".tag_hide_input div.cell_input",
        ".tag_hide-input div.cell_input",
        ".tag_hide_output div.cell_output",
        ".tag_hide-output div.cell_output",
        ".tag_hide_cell.cell",
        ".tag_hide-cell.cell",
    ]
    for selector in to_add:
        config.togglebutton_selector += f", {selector}"


def store_doc_metadata(env: BuildEnvironment, docname: str, key: str, value: Any):
    """Store myst-nb metadata for a document."""
    # Data in env.metadata is correctly handled, by sphinx.MetadataCollector,
    # for clearing removed documents and for merging on parallel builds

    # however, one drawback is that it also extracts all docinfo to here,
    # so we prepend the key name to hopefully avoid it being overwritten

    # TODO is it worth implementing a custom MetadataCollector?
    if docname not in env.metadata:
        env.metadata[docname] = {}
    env.metadata[docname][f"__mystnb__{key}"] = value


def get_doc_metadata(
    env: BuildEnvironment, docname: str, key: str, default=None
) -> Any:
    """Get myst-nb metadata for a document."""
    return env.metadata.get(docname, {}).get(f"__mystnb__{key}", default)


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
        document_path = self.env.doc2path(self.env.docname)

        # get a logger for this document
        logger = SphinxDocLogger(document)

        # get markdown parsing configuration
        md_config: MdParserConfig = self.env.myst_config
        # get notebook rendering configuration
        nb_config: NbParserConfig = self.env.mystnb_config

        # create a reader for the notebook
        nb_reader = create_nb_reader(document_path, md_config, nb_config, inputstring)

        # If the nb_reader is None, then we default to a standard Markdown parser
        if nb_reader is None:
            return super().parse(inputstring, document)

        notebook = nb_reader.read(inputstring)

        # TODO update nb_config from notebook metadata

        # potentially execute notebook and/or populate outputs from cache
        notebook, exec_data = update_notebook(
            notebook, document_path, nb_config, logger
        )
        if exec_data:
            store_doc_metadata(self.env, self.env.docname, "exec_data", exec_data)

            # TODO store error traceback in outdir and log its path

        # Setup the parser
        mdit_parser = create_md_parser(nb_reader.md_config, SphinxNbRenderer)
        mdit_parser.options["document"] = document
        mdit_parser.options["notebook"] = notebook
        mdit_parser.options["nb_config"] = nb_config.as_dict()
        mdit_env: Dict[str, Any] = {}

        # load notebook element renderer class from entry-point name
        # this is separate from SphinxNbRenderer, so that users can override it
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

    def render_nb_metadata(self, token: SyntaxTreeNode) -> None:
        """Render the notebook metadata."""
        metadata = dict(token.meta)

        # save these special keys on the metadata, rather than as docinfo
        env = self.sphinx_env
        env.metadata[env.docname]["kernelspec"] = metadata.pop("kernelspec", None)
        env.metadata[env.docname]["language_info"] = metadata.pop("language_info", None)

        # TODO should we provide hook for NbElementRenderer?

        # store ipywidgets state in metadata,
        # which will be later added to HTML page context
        # The JSON inside the script tag is identified and parsed by:
        # https://github.com/jupyter-widgets/ipywidgets/blob/32f59acbc63c3ff0acf6afa86399cb563d3a9a86/packages/html-manager/src/libembed.ts#L36
        ipywidgets = metadata.pop("widgets", None)
        ipywidgets_mime = (ipywidgets or {}).get(WIDGET_STATE_MIMETYPE, {})
        if ipywidgets_mime.get("state", None):
            string = sanitize_script_content(json.dumps(ipywidgets_mime))
            store_doc_metadata(
                self.sphinx_env, self.sphinx_env.docname, "ipywidgets_state", string
            )

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
                # TODO ignore if glue mime types present?
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


class NbDownloadRole(ReferenceRole):
    """Role to download an executed notebook."""

    def run(self):
        """Run the role."""
        # get a path relative to the current document
        path = Path(self.env.mystnb_config.output_folder).joinpath(
            *(self.env.docname.split("/")[:-1] + self.target.split("/"))
        )
        reftarget = (
            path.as_posix()
            if os.name == "nt"
            else ("/" + os.path.relpath(path, self.env.app.srcdir))
        )
        node = download_reference(self.rawtext, reftarget=reftarget)
        self.set_source_info(node)
        title = self.title if self.has_explicit_title else self.target
        node += nodes.literal(
            self.rawtext, title, classes=["xref", "download", "myst-nb"]
        )
        return [node], []

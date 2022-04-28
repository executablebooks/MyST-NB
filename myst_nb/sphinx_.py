"""The sphinx parser implementation for myst-nb."""
from __future__ import annotations

from collections import defaultdict
import json
from pathlib import Path
import re
from typing import Any, DefaultDict, cast

from docutils import nodes
from markdown_it.token import Token
from markdown_it.tree import SyntaxTreeNode
from myst_parser.docutils_renderer import token_line
from myst_parser.main import MdParserConfig, create_md_parser
from myst_parser.sphinx_parser import MystParser
from myst_parser.sphinx_renderer import SphinxRenderer
import nbformat
from sphinx.application import Sphinx
from sphinx.environment import BuildEnvironment
from sphinx.environment.collectors import EnvironmentCollector
from sphinx.transforms.post_transforms import SphinxPostTransform
from sphinx.util import logging as sphinx_logging

from myst_nb._compat import findall
from myst_nb.core.config import NbParserConfig
from myst_nb.core.execute import ExecutionResult, execute_notebook
from myst_nb.core.loggers import DEFAULT_LOG_TYPE, SphinxDocLogger
from myst_nb.core.parse import nb_node_to_dict, notebook_to_tokens
from myst_nb.core.preprocess import preprocess_notebook
from myst_nb.core.read import create_nb_reader
from myst_nb.core.render import (
    MimeData,
    NbElementRenderer,
    create_figure_context,
    get_mime_priority,
    load_renderer,
)

SPHINX_LOGGER = sphinx_logging.getLogger(__name__)


class SphinxEnvType(BuildEnvironment):
    """Sphinx build environment, including attributes set by myst_nb."""

    myst_config: MdParserConfig
    mystnb_config: NbParserConfig
    nb_metadata: DefaultDict[str, dict]
    nb_new_exec_data: bool


class Parser(MystParser):
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
        assert self.env is not None, "env not set"
        self.env: SphinxEnvType
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

        # potentially replace kernel name with alias
        kernel_name = notebook.metadata.get("kernelspec", {}).get("name", None)
        if kernel_name is not None and nb_config.kernel_rgx_aliases:
            for rgx, alias in nb_config.kernel_rgx_aliases.items():
                if re.fullmatch(rgx, kernel_name):
                    logger.debug(
                        f"Replaced kernel name: {kernel_name!r} -> {alias!r}",
                        subtype="kernel",
                    )
                    notebook.metadata["kernelspec"]["name"] = alias
                    break

        # Update mystnb configuration with notebook level metadata
        if nb_config.metadata_key in notebook.metadata:
            overrides = nb_node_to_dict(notebook.metadata[nb_config.metadata_key])
            overrides.pop("output_folder", None)  # this should not be overridden
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
            notebook, document_path, nb_config, logger, nb_reader.read_fmt
        )
        if exec_data:
            NbMetadataCollector.set_exec_data(self.env, self.env.docname, exec_data)
            if exec_data["traceback"]:
                # store error traceback in outdir and log its path
                reports_file = Path(self.env.app.outdir).joinpath(
                    "reports", *(self.env.docname + ".err.log").split("/")
                )
                reports_file.parent.mkdir(parents=True, exist_ok=True)
                reports_file.write_text(exec_data["traceback"], encoding="utf8")
                logger.warning(
                    f"Notebook exception traceback saved in: {reports_file}",
                    subtype="exec",
                )

        # Setup the parser
        mdit_parser = create_md_parser(nb_reader.md_config, SphinxNbRenderer)
        mdit_parser.options["document"] = document
        mdit_parser.options["notebook"] = notebook
        mdit_parser.options["nb_config"] = nb_config
        mdit_renderer: SphinxNbRenderer = mdit_parser.renderer  # type: ignore
        mdit_env: dict[str, Any] = {}

        # load notebook element renderer class from entry-point name
        # this is separate from SphinxNbRenderer, so that users can override it
        renderer_name = nb_config.render_plugin
        nb_renderer: NbElementRenderer = load_renderer(renderer_name)(
            mdit_renderer, logger
        )
        # we temporarily store nb_renderer on the document,
        # so that roles/directives can access it
        document.attributes["nb_renderer"] = nb_renderer
        # we currently do this early, so that the nb_renderer has access to things
        mdit_renderer.setup_render(mdit_parser.options, mdit_env)

        # pre-process notebook and store resources for render
        resources = preprocess_notebook(notebook, logger, nb_config)
        mdit_renderer.md_options["nb_resources"] = resources

        # parse to tokens
        mdit_tokens = notebook_to_tokens(notebook, mdit_parser, mdit_env, logger)
        # convert to docutils AST, which is added to the document
        mdit_renderer.render(mdit_tokens, mdit_parser.options, mdit_env)

        # write final (updated) notebook to output folder (utf8 is standard encoding)
        path = self.env.docname.split("/")
        ipynb_path = path[:-1] + [path[-1] + ".ipynb"]
        content = nbformat.writes(notebook).encode("utf-8")
        nb_renderer.write_file(ipynb_path, content, overwrite=True)

        # write glue data to the output folder,
        # and store the keys to environment doc metadata,
        # so that they may be used in any post-transform steps
        if resources.get("glue", None):
            glue_path = path[:-1] + [path[-1] + ".glue.json"]
            nb_renderer.write_file(
                glue_path,
                json.dumps(resources["glue"], cls=BytesEncoder).encode("utf8"),
                overwrite=True,
            )
            NbMetadataCollector.set_doc_data(
                self.env, self.env.docname, "glue", list(resources["glue"].keys())
            )

        # move some document metadata to environment metadata,
        # so that we can later read it from the environment,
        # rather than having to load the whole doctree
        for key, (uri, kwargs) in document.attributes.pop("nb_js_files", {}).items():
            NbMetadataCollector.add_js_file(
                self.env, self.env.docname, key, uri, kwargs
            )

        # remove temporary state
        document.attributes.pop("nb_renderer")


class SphinxNbRenderer(SphinxRenderer):
    """A sphinx renderer for Jupyter Notebooks."""

    @property
    def nb_config(self) -> NbParserConfig:
        """Get the notebook element renderer."""
        return self.md_options["nb_config"]

    @property
    def nb_renderer(self) -> NbElementRenderer:
        """Get the notebook element renderer."""
        return self.document["nb_renderer"]

    def get_cell_level_config(
        self,
        field: str,
        cell_metadata: dict[str, Any],
        line: int | None = None,
    ) -> Any:
        """Get a configuration value at the cell level.

        Takes the highest priority configuration from:
        `cell > document > global > default`

        :param field: the field name from ``NbParserConfig`` to get the value for
        :param cell_metadata: the metadata for the cell
        """

        def _callback(msg: str, subtype: str):
            self.create_warning(msg, line=line, subtype=subtype)

        return self.nb_config.get_cell_level_config(field, cell_metadata, _callback)

    def render_nb_metadata(self, token: SyntaxTreeNode) -> None:
        """Render the notebook metadata."""
        env = cast(BuildEnvironment, self.sphinx_env)
        metadata = dict(token.meta)
        special_keys = ("kernelspec", "language_info", "source_map")
        for key in special_keys:
            if key in metadata:
                # save these special keys on the metadata, rather than as docinfo
                # note, sphinx_book_theme checks kernelspec is in the metadata
                env.metadata[env.docname][key] = metadata.get(key)

        metadata = self.nb_renderer.render_nb_metadata(metadata)

        # forward the remaining metadata to the front_matter renderer
        top_matter = {k: v for k, v in metadata.items() if k not in special_keys}
        self.render_front_matter(
            Token(  # type: ignore
                "front_matter",
                "",
                0,
                map=[0, 0],
                content=top_matter,  # type: ignore[arg-type]
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
            self.get_cell_level_config(
                "remove_code_source",
                token.meta["metadata"],
                line=token_line(token, 0) or None,
            )
            or ("remove_input" in tags)
            or ("remove-input" in tags)
        )
        remove_output = (
            self.get_cell_level_config(
                "remove_code_outputs",
                token.meta["metadata"],
                line=token_line(token, 0) or None,
            )
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
        # cell_index = token.meta["index"]
        lexer = token.meta.get("lexer", None)
        node = self.create_highlighted_code_block(
            token.content,
            lexer,
            number_lines=self.get_cell_level_config(
                "number_source_lines",
                token.meta["metadata"],
                line=token_line(token, 0) or None,
            ),
            source=self.document["source"],
            line=token_line(token),
        )
        self.add_line_and_source_path(node, token)
        self.current_node.append(node)

    def render_nb_cell_code_outputs(self, token: SyntaxTreeNode) -> None:
        """Render a notebook code cell's outputs."""
        line = token_line(token, 0)
        cell_index = token.meta["index"]
        metadata = token.meta["metadata"]
        outputs: list[nbformat.NotebookNode] = self.md_options["notebook"]["cells"][
            cell_index
        ].get("outputs", [])
        # render the outputs
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

                # Note, this is different to the docutils implementation,
                # where we directly select a single output, based on the mime_priority.
                # Here, we do not know the mime priority until we know the output format
                # so we output all the outputs during this parsing phase
                # (this is what sphinx caches as "output format agnostic" AST),
                # and replace the mime_bundle with the format specific output
                # in a post-transform (run per output format on the cached AST)

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

                figure_options = (
                    self.get_cell_level_config(
                        "render_figure_options", metadata, line=line
                    )
                    or None
                )

                with create_figure_context(self, figure_options, line):
                    mime_bundle = nodes.container(nb_element="mime_bundle")
                    with self.current_node_context(mime_bundle):
                        for mime_type, data in output["data"].items():
                            mime_container = nodes.container(mime_type=mime_type)
                            with self.current_node_context(mime_container):
                                _nodes = self.nb_renderer.render_mime_type(
                                    MimeData(
                                        mime_type,
                                        data,
                                        cell_metadata=metadata,
                                        output_metadata=output.get("metadata", {}),
                                        cell_index=cell_index,
                                        output_index=output_index,
                                        line=line,
                                    )
                                )
                                self.current_node.extend(_nodes)
                            if mime_container.children:
                                self.current_node.append(mime_container)
                    if mime_bundle.children:
                        self.add_line_and_source_path_r([mime_bundle], token)
                        self.current_node.append(mime_bundle)
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
        # TODO allow for per-notebook/cell priority dicts?
        bname = self.app.builder.name  # type: ignore
        priority_list = get_mime_priority(
            bname, self.config["nb_mime_priority_overrides"]
        )
        condition = (
            lambda node: isinstance(node, nodes.container)
            and node.attributes.get("nb_element", "") == "mime_bundle"
        )
        # remove/replace_self will not work with an iterator
        for node in list(findall(self.document)(condition)):
            # get available mime types
            mime_types = [node["mime_type"] for node in node.children]
            if not mime_types:
                node.parent.remove(node)
                continue
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
                mime_string = ",".join(repr(m) for m in mime_types)
                SPHINX_LOGGER.warning(
                    f"No mime type available in priority list for builder {bname!r} "
                    f"({mime_string}) [{DEFAULT_LOG_TYPE}.mime_priority]",
                    type=DEFAULT_LOG_TYPE,
                    subtype="mime_priority",
                    location=node,
                )
                node.parent.remove(node)
            elif not node.children[index].children:
                node.parent.remove(node)
            else:
                node.replace_self(node.children[index].children)


class NbMetadataCollector(EnvironmentCollector):
    """Collect myst-nb specific metdata, and handle merging of parallel builds."""

    @staticmethod
    def set_doc_data(env: SphinxEnvType, docname: str, key: str, value: Any) -> None:
        """Add nb metadata for a docname to the environment."""
        if not hasattr(env, "nb_metadata"):
            env.nb_metadata = defaultdict(dict)
        env.nb_metadata.setdefault(docname, {})[key] = value

    @staticmethod
    def get_doc_data(env: SphinxEnvType) -> DefaultDict[str, dict]:
        """Get myst-nb docname -> metadata dict."""
        if not hasattr(env, "nb_metadata"):
            env.nb_metadata = defaultdict(dict)
        return env.nb_metadata

    @classmethod
    def set_exec_data(
        cls, env: SphinxEnvType, docname: str, value: ExecutionResult
    ) -> None:
        """Add nb metadata for a docname to the environment."""
        cls.set_doc_data(env, docname, "exec_data", value)
        # TODO this does not take account of cache data
        cls.note_exec_update(env)

    @classmethod
    def get_exec_data(cls, env: SphinxEnvType, docname: str) -> ExecutionResult | None:
        """Get myst-nb docname -> execution data."""
        return cls.get_doc_data(env)[docname].get("exec_data")

    def get_outdated_docs(  # type: ignore[override]
        self,
        app: Sphinx,
        env: SphinxEnvType,
        added: set[str],
        changed: set[str],
        removed: set[str],
    ) -> list[str]:
        # called before any docs are read
        env.nb_new_exec_data = False
        return []

    @staticmethod
    def note_exec_update(env: SphinxEnvType) -> None:
        """Note that a notebook has been executed."""
        env.nb_new_exec_data = True

    @staticmethod
    def new_exec_data(env: SphinxEnvType) -> bool:
        """Return whether any notebooks have updated execution data."""
        return getattr(env, "nb_new_exec_data", False)

    @classmethod
    def add_js_file(
        cls,
        env: SphinxEnvType,
        docname: str,
        key: str,
        uri: str | None,
        kwargs: dict[str, str],
    ):
        """Register a JavaScript file to include in the HTML output."""
        if not hasattr(env, "nb_metadata"):
            env.nb_metadata = defaultdict(dict)
        js_files = env.nb_metadata.setdefault(docname, {}).setdefault("js_files", {})
        # TODO handle whether overrides are allowed
        js_files[key] = (uri, kwargs)

    @classmethod
    def get_js_files(
        cls, env: SphinxEnvType, docname: str
    ) -> dict[str, tuple[str | None, dict[str, str]]]:
        """Get myst-nb docname -> execution data."""
        return cls.get_doc_data(env)[docname].get("js_files", {})

    def clear_doc(  # type: ignore[override]
        self,
        app: Sphinx,
        env: SphinxEnvType,
        docname: str,
    ) -> None:
        if not hasattr(env, "nb_metadata"):
            env.nb_metadata = defaultdict(dict)
        env.nb_metadata.pop(docname, None)

    def process_doc(self, app: Sphinx, doctree: nodes.document) -> None:
        pass

    def merge_other(  # type: ignore[override]
        self,
        app: Sphinx,
        env: SphinxEnvType,
        docnames: set[str],
        other: SphinxEnvType,
    ) -> None:
        if not hasattr(env, "nb_metadata"):
            env.nb_metadata = defaultdict(dict)
        other_metadata = getattr(other, "nb_metadata", defaultdict(dict))
        for docname in docnames:
            env.nb_metadata[docname] = other_metadata[docname]
        if other.nb_new_exec_data:
            env.nb_new_exec_data = True


class BytesEncoder(json.JSONEncoder):
    """A JSON encoder that accepts b64 (and other *ascii*) bytestrings."""

    def default(self, obj):
        if isinstance(obj, bytes):
            return obj.decode("ascii")
        return json.JSONEncoder.default(self, obj)

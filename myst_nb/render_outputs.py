"""A Sphinx post-transform, to convert notebook outpus to AST nodes."""
from abc import ABC, abstractmethod
import os
from typing import List, Optional

from importlib_metadata import entry_points
from docutils import nodes
from sphinx.environment import BuildEnvironment
from sphinx.environment.collectors.asset import ImageCollector
from sphinx.errors import SphinxError
from sphinx.transforms.post_transforms import SphinxPostTransform
from sphinx.util import logging

import nbconvert
from nbformat import NotebookNode

from jupyter_sphinx.ast import (
    JupyterWidgetViewNode,
    strip_latex_delimiters,
)
from jupyter_sphinx.utils import sphinx_abs_dir

from .nodes import CellOutputBundleNode

LOGGER = logging.getLogger(__name__)

WIDGET_VIEW_MIMETYPE = "application/vnd.jupyter.widget-view+json"


def get_default_render_priority(builder: str) -> Optional[List[str]]:
    priority = {
        builder: (
            WIDGET_VIEW_MIMETYPE,
            "application/javascript",
            "text/html",
            "image/svg+xml",
            "image/png",
            "image/jpeg",
            "text/latex",
            "text/plain",
        )
        for builder in (
            "html",
            "readthedocs",
            "singlehtml",
            "dirhtml",
            "linkcheck",
            "readthedocsdirhtml",
            "readthedocssinglehtml",
            "readthedocssinglehtmllocalmedia",
            "epub",
        )
    }
    # TODO: add support for "image/svg+xml"
    priority["latex"] = (
        "application/pdf",
        "image/png",
        "image/jpeg",
        "text/latex",
        "text/plain",
    )
    return priority.get(builder, None)


class MystNbEntryPointError(SphinxError):
    category = "MyST NB Renderer Load"


def load_renderer(name) -> "CellOutputRendererBase":
    ep_list = set(ep for ep in entry_points()["myst_nb.mime_render"] if ep.name == name)
    if len(ep_list) == 1:
        klass = ep_list.pop().load()
        if not issubclass(klass, CellOutputRendererBase):
            raise MystNbEntryPointError(
                f"Entry Point for myst_nb.mime_render:{name} "
                f"is not a subclass of `CellOutputRendererBase`: {klass}"
            )
        return klass
    elif not ep_list:
        raise MystNbEntryPointError(
            f"No Entry Point found for myst_nb.mime_render:{name}"
        )
    raise MystNbEntryPointError(
        f"Multiple Entry Points found for myst_nb.mime_render:{name}: {ep_list}"
    )


class CellOutputsToNodes(SphinxPostTransform):
    """Use the builder context to transform a CellOutputNode into Sphinx nodes."""

    # process very early, before CitationReferenceTransform (5), ReferencesResolver (10)
    # https://www.sphinx-doc.org/en/master/extdev/appapi.html#sphinx.application.Sphinx.add_transform
    default_priority = 4

    def run(self):
        abs_dir = sphinx_abs_dir(self.env)
        renderers = {}  # cache renderers

        for node in self.document.traverse(CellOutputBundleNode):
            try:
                renderer_cls = renderers[node.renderer]
            except KeyError:
                renderer_cls = load_renderer(node.renderer)
                renderers[node.renderer] = renderer_cls
            renderer = renderer_cls(self.env, node, abs_dir)
            output_nodes = renderer.cell_output_to_nodes(self.env.nb_render_priority)
            node.replace_self(output_nodes)

        # Image collect extra nodes from cell outputs that we need to process
        # this normally gets called as a `doctree-read` event
        for node in self.document.traverse(nodes.image):
            # If the image node has `candidates` then it's already been processed
            # as in-line markdown, so skip it
            if "candidates" in node:
                continue
            col = ImageCollector()
            col.process_doc(self.app, node)


class CellOutputRendererBase(ABC):
    """An abstract base class for rendering Notebook outputs to docutils nodes.

    Subclasses should implement the ``render`` method.
    """

    def __init__(
        self, env: BuildEnvironment, node: CellOutputBundleNode, sphinx_dir: str
    ):
        """
        :param sphinx_dir: Sphinx "absolute path" to the output folder,
            so it is a relative path to the source folder prefixed with ``/``.
        """
        self.env = env
        self.node = node
        self.sphinx_dir = sphinx_dir

    def cell_output_to_nodes(self, data_priority: List[str]) -> List[nodes.Node]:
        """Convert a jupyter cell with outputs and filenames to doctree nodes.

        :param outputs: a list of outputs from a Jupyter cell
        :param data_priority: media type by priority.

        :returns: list of docutils nodes

        """
        output_nodes = []
        for idx, output in enumerate(self.node.outputs):
            output_type = output["output_type"]
            if output_type == "stream":
                if output["name"] == "stderr":
                    output_nodes.extend(self.render("stderr", output, idx))
                else:
                    output_nodes.extend(self.render("stdout", output, idx))
            elif output_type == "error":
                output_nodes.extend(self.render("traceback", output, idx))

            elif output_type in ("display_data", "execute_result"):
                try:
                    # First mime_type by priority that occurs in output.
                    mime_type = next(x for x in data_priority if x in output["data"])
                except StopIteration:
                    # TODO this is incompatible with glue outputs
                    # perhaps have sphinx config to turn on/off this error reporting?
                    # and/or only warn if "scrapbook" not in output.metadata
                    # (then enable tests/test_render_outputs.py::test_unknown_mimetype)
                    # LOGGER.warning(
                    #     "MyST-NB: output contains no MIME type in priority list: %s",
                    #     list(output["data"].keys()),
                    #     location=location,
                    # )
                    continue
                output_nodes.extend(self.render(mime_type, output, idx))

        return output_nodes

    @abstractmethod
    def render(
        self, mime_type: str, output: NotebookNode, index: int
    ) -> List[nodes.Node]:
        pass


class CellOutputRenderer(CellOutputRendererBase):
    def __init__(
        self, env: BuildEnvironment, node: CellOutputBundleNode, sphinx_dir: str
    ):
        """
        :param sphinx_dir: Sphinx "absolute path" to the output folder,
            so it is a relative path to the source folder prefixed with ``/``.
        """
        super().__init__(env, node, sphinx_dir)
        self._render_map = {
            "stderr": self.render_stderr,
            "stdout": self.render_stdout,
            "traceback": self.render_traceback,
            "text/plain": self.render_text_plain,
            "text/html": self.render_text_html,
            "text/latex": self.render_text_latex,
            "application/javascript": self.render_application_javascript,
            WIDGET_VIEW_MIMETYPE: self.render_widget,
        }

    def render(
        self, mime_type: str, output: NotebookNode, index: int
    ) -> List[nodes.Node]:
        if mime_type.startswith("image"):
            return self.create_render_image(mime_type)(output, index)
        if mime_type in self._render_map:
            return self._render_map[mime_type](output, index)

        LOGGER.warning(
            "MyST-NB: No renderer found for output MIME: %s",
            mime_type,
            location=(self.node.source, self.node.line),
        )
        return []

    def render_stderr(self, output: NotebookNode, index: int):
        """Output a container with an unhighlighted literal block."""

        if "remove-stderr" in self.node.metadata.get("tags", []):
            return []

        container = nodes.container(classes=["stderr"])
        container.append(
            nodes.literal_block(
                text=output["text"],
                rawsource="",  # disables Pygment highlighting
                language="none",
                classes=["stderr"],
            )
        )
        return [container]

    def render_stdout(self, output: NotebookNode, index: int):

        if "remove-stdout" in self.node.metadata.get("tags", []):
            return []

        return [
            nodes.literal_block(
                text=output["text"],
                rawsource=output["text"],
                language="none",
                classes=["output", "stream"],
            )
        ]

    def render_traceback(self, output: NotebookNode, index: int):
        traceback = "\n".join(output["traceback"])
        text = nbconvert.filters.strip_ansi(traceback)
        return [
            nodes.literal_block(
                text=text,
                rawsource=text,
                language="ipythontb",
                classes=["output", "traceback"],
            )
        ]

    def render_text_html(self, output: NotebookNode, index: int):
        data = output["data"]["text/html"]
        return [nodes.raw(text=data, format="html", classes=["output", "text_html"])]

    def render_text_latex(self, output: NotebookNode, index: int):
        data = output["data"]["text/latex"]
        return [
            nodes.math_block(
                text=strip_latex_delimiters(data),
                nowrap=False,
                number=None,
                classes=["output", "text_latex"],
            )
        ]

    def render_text_plain(self, output: NotebookNode, index: int):
        data = output["data"]["text/plain"]
        return [
            nodes.literal_block(
                text=data,
                rawsource=data,
                language="none",
                classes=["output", "text_plain"],
            )
        ]

    def render_application_javascript(self, output: NotebookNode, index: int):
        data = output["data"]["application/javascript"]
        return [
            nodes.raw(
                text='<script type="{mime_type}">{data}</script>'.format(
                    mime_type="application/javascript", data=data
                ),
                format="html",
            )
        ]

    def render_widget(self, output: NotebookNode, index: int):
        data = output["data"][WIDGET_VIEW_MIMETYPE]
        return [JupyterWidgetViewNode(view_spec=data)]

    def create_render_image(self, mime_type: str):
        def _render_image(output: NotebookNode, index: int):
            # Sphinx treats absolute paths as being rooted at the source
            # directory, so make a relative path, which Sphinx treats
            # as being relative to the current working directory.
            filename = os.path.basename(output.metadata["filenames"][mime_type])

            # checks if file dir path is inside a subdir of dir
            filedir = os.path.dirname(output.metadata["filenames"][mime_type])
            subpaths = filedir.split(self.sphinx_dir)
            final_dir = self.sphinx_dir
            if subpaths and len(subpaths) > 1:
                subpath = subpaths[1]
                final_dir += subpath

            uri = os.path.join(final_dir, filename)
            return [nodes.image(uri=uri)]

        return _render_image


class CellOutputRendererInline(CellOutputRenderer):
    """Replaces literal/math blocks with non-block versions"""

    def render_stderr(self, output: NotebookNode, index: int):
        """Output a container with an unhighlighted literal"""
        return [
            nodes.literal(
                text=output["text"],
                rawsource="",  # disables Pygment highlighting
                language="none",
                classes=["stderr"],
            )
        ]

    def render_stdout(self, output: NotebookNode, index: int):
        """Output a container with an unhighlighted literal"""
        return [
            nodes.literal(
                text=output["text"],
                rawsource="",  # disables Pygment highlighting
                language="none",
                classes=["output", "stream"],
            )
        ]

    def render_traceback(self, output: NotebookNode, index: int):
        traceback = "\n".join(output["traceback"])
        text = nbconvert.filters.strip_ansi(traceback)
        return [
            nodes.literal(
                text=text,
                rawsource=text,
                language="ipythontb",
                classes=["output", "traceback"],
            )
        ]

    def render_text_latex(self, output: NotebookNode, index: int):
        data = output["data"]["text/latex"]
        return [
            nodes.math(
                text=strip_latex_delimiters(data),
                nowrap=False,
                number=None,
                classes=["output", "text_latex"],
            )
        ]

    def render_text_plain(self, output: NotebookNode, index: int):
        data = output["data"]["text/plain"]
        return [
            nodes.literal(
                text=data,
                rawsource=data,
                language="none",
                classes=["output", "text_plain"],
            )
        ]

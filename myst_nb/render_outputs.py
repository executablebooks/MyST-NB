"""A Sphinx post-transform, to convert notebook outpus to AST nodes."""
import os
from typing import Callable, List, Optional, Tuple

from docutils import nodes
from sphinx.environment.collectors.asset import ImageCollector
from sphinx.transforms.post_transforms import SphinxPostTransform
from sphinx.util import logging

import nbconvert
from nbformat import NotebookNode

from jupyter_sphinx.ast import (
    JupyterWidgetViewNode,
    strip_latex_delimiters,
)
from jupyter_sphinx.utils import sphinx_abs_dir

from .parser import CellOutputBundleNode

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


class CellOutputsToNodes(SphinxPostTransform):
    """Use the builder context to transform a CellOutputNode into Sphinx nodes."""

    # process very early, before CitationReferenceTransform (5), ReferencesResolver (10)
    # https://www.sphinx-doc.org/en/master/extdev/appapi.html#sphinx.application.Sphinx.add_transform
    default_priority = 4

    def run(self):
        abs_dir = sphinx_abs_dir(self.env)
        renderer = CellOutputRenderer()
        renderer_inline = CellOutputRendererInline()
        for node in self.document.traverse(CellOutputBundleNode):
            output_nodes = cell_output_to_nodes(
                node,
                self.env.nb_render_priority,
                renderer_inline if node.get("inline", False) else renderer,
                abs_dir,
            )
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


def cell_output_to_nodes(
    node: CellOutputBundleNode,
    data_priority: List[str],
    renderer: "CellOutputRenderer",
    output_dir: str,
) -> List[nodes.Node]:
    """Convert a jupyter cell with outputs and filenames to doctree nodes.

    :param outputs: a list of outputs from a Jupyter cell
    :param data_priority: media type by priority.
    :param abs_dir: Sphinx "absolute path" to the output folder,
        so it is a relative path to the source folder prefixed with ``/``.
     :param location: (docname, lineno)

    :returns: list of docutils nodes

    """
    location = (node.source, node.line)
    tags = node.metadata.get("tags", [])

    output_nodes = []
    for idx, output in enumerate(node.outputs):
        output_type = output["output_type"]
        if output_type == "stream":
            if output["name"] == "stderr" and "remove-stderr" not in tags:
                output_nodes.extend(
                    renderer.get_renderer("stderr", location)(output, idx, output_dir)
                )
            elif "remove-stdout" not in tags:
                output_nodes.extend(
                    renderer.get_renderer("stdout", location)(output, idx, output_dir)
                )
        elif output_type == "error":
            output_nodes.extend(
                renderer.get_renderer("traceback", location)(output, idx, output_dir)
            )

        elif output_type in ("display_data", "execute_result"):
            try:
                # First mime_type by priority that occurs in output.
                mime_type = next(x for x in data_priority if x in output["data"])
            except StopIteration:
                # TODO this is incompatible with glue outputs
                # perhaps have sphinx config to turn on/off this error reporting?
                # and/or only warn if "scrapbook" not in output.metadata
                # (then can enable tests/test_render_outputs.py::test_unknown_mimetype)
                # LOGGER.warning(
                #     "MyST-NB: output contains no MIME type in priority list: %s",
                #     list(output["data"].keys()),
                #     location=location,
                # )
                continue
            output_nodes.extend(
                renderer.get_renderer(mime_type, location)(output, idx, output_dir)
            )

    return output_nodes


class CellOutputRenderer:
    def __init__(self):
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

    def get_renderer(
        self, mime_type: str, location: Tuple[str, int]
    ) -> Callable[[NotebookNode, int, str], List[nodes.Node]]:
        if mime_type.startswith("image"):
            return self.create_render_image(mime_type)
        if mime_type in self._render_map:
            return self._render_map[mime_type]
        else:
            LOGGER.warning(
                "MyST-NB: No renderer found for output MIME: %s",
                mime_type,
                location=location,
            )
            return self.render_default

    def render_default(self, output: NotebookNode, index: int, abs_dir: str):
        return []

    def render_stderr(self, output: NotebookNode, index: int, abs_dir: str):
        """Output a container with an unhighlighted literal block."""
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

    def render_stdout(self, output: NotebookNode, index: int, abs_dir: str):
        return [
            nodes.literal_block(
                text=output["text"],
                rawsource=output["text"],
                language="none",
                classes=["output", "stream"],
            )
        ]

    def render_traceback(self, output: NotebookNode, index: int, abs_dir: str):
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

    def render_text_html(self, output: NotebookNode, index: int, abs_dir: str):
        data = output["data"]["text/html"]
        return [nodes.raw(text=data, format="html", classes=["output", "text_html"])]

    def render_text_latex(self, output: NotebookNode, index: int, abs_dir: str):
        data = output["data"]["text/latex"]
        return [
            nodes.math_block(
                text=strip_latex_delimiters(data),
                nowrap=False,
                number=None,
                classes=["output", "text_latex"],
            )
        ]

    def render_text_plain(self, output: NotebookNode, index: int, abs_dir: str):
        data = output["data"]["text/plain"]
        return [
            nodes.literal_block(
                text=data,
                rawsource=data,
                language="none",
                classes=["output", "text_plain"],
            )
        ]

    def render_application_javascript(
        self, output: NotebookNode, index: int, abs_dir: str
    ):
        data = output["data"]["application/javascript"]
        return [
            nodes.raw(
                text='<script type="{mime_type}">{data}</script>'.format(
                    mime_type="application/javascript", data=data
                ),
                format="html",
            )
        ]

    def render_widget(self, output: NotebookNode, index: int, abs_dir: str):
        data = output["data"][WIDGET_VIEW_MIMETYPE]
        return [JupyterWidgetViewNode(view_spec=data)]

    def create_render_image(self, mime_type: str):
        def _render_image(output: NotebookNode, index: int, abs_dir: str):
            # Sphinx treats absolute paths as being rooted at the source
            # directory, so make a relative path, which Sphinx treats
            # as being relative to the current working directory.
            filename = os.path.basename(output.metadata["filenames"][mime_type])

            # checks if file dir path is inside a subdir of dir
            filedir = os.path.dirname(output.metadata["filenames"][mime_type])
            subpaths = filedir.split(abs_dir)
            if subpaths and len(subpaths) > 1:
                subpath = subpaths[1]
                abs_dir += subpath

            uri = os.path.join(abs_dir, filename)
            return [nodes.image(uri=uri)]

        return _render_image


class CellOutputRendererInline(CellOutputRenderer):
    """Replaces literal/math blocks with non-block versions"""

    def render_stderr(self, output: NotebookNode, index: int, abs_dir: str):
        """Output a container with an unhighlighted literal"""
        return [
            nodes.literal(
                text=output["text"],
                rawsource="",  # disables Pygment highlighting
                language="none",
                classes=["stderr"],
            )
        ]

    def render_stdout(self, output: NotebookNode, index: int, abs_dir: str):
        """Output a container with an unhighlighted literal"""
        return [
            nodes.literal(
                text=output["text"],
                rawsource="",  # disables Pygment highlighting
                language="none",
                classes=["output", "stream"],
            )
        ]

    def render_traceback(self, output: NotebookNode, index: int, abs_dir: str):
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

    def render_text_latex(self, output: NotebookNode, index: int, abs_dir: str):
        data = output["data"]["text/latex"]
        return [
            nodes.math(
                text=strip_latex_delimiters(data),
                nowrap=False,
                number=None,
                classes=["output", "text_latex"],
            )
        ]

    def render_text_plain(self, output: NotebookNode, index: int, abs_dir: str):
        data = output["data"]["text/plain"]
        return [
            nodes.literal(
                text=data,
                rawsource=data,
                language="none",
                classes=["output", "text_plain"],
            )
        ]

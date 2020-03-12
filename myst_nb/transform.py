"""Defines the MIMEtype docutils node."""
from docutils import nodes
from sphinx.transforms import SphinxTransform
from sphinx.util import logging
from jupyter_sphinx.ast import cell_output_to_nodes
from jupyter_sphinx.utils import sphinx_abs_dir
from .parser import CellOutputBundleNode
from sphinx.environment.collectors.asset import ImageCollector

logger = logging.getLogger(__name__)

WIDGET_VIEW_MIMETYPE = "application/vnd.jupyter.widget-view+json"
RENDER_PRIORITY = {
    "html": [
        WIDGET_VIEW_MIMETYPE,
        "application/javascript",
        "text/html",
        "image/svg+xml",
        "image/png",
        "image/jpeg",
        "text/latex",
        "text/plain",
    ],
    "latex": ["text/latex", "text/plain"],
}
RENDER_PRIORITY["readthedocs"] = RENDER_PRIORITY["html"]


class CellOutputsToNodes(SphinxTransform):
    """Use the builder context to transform a CellOutputNode into Sphinx nodes."""

    default_priority = 700

    def apply(self):
        builder = self.app.builder.name
        output_dir = sphinx_abs_dir(self.env)
        for node in self.document.traverse(CellOutputBundleNode):
            cell = {"outputs": node.outputs}
            output_nodes = cell_output_to_nodes(
                cell, RENDER_PRIORITY[builder], True, output_dir, None
            )
            node.replace_self(output_nodes)

        # Image collect extra nodes from cell outputs that we need to process
        for node in self.document.traverse(nodes.image):
            # If the image node has `candidates` then it's already been processed
            # as in-line markdown, so skip it
            if "candidates" in node:
                continue
            col = ImageCollector()
            col.process_doc(self.app, node)

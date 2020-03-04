"""Defines the MIMEtype docutils node."""
from docutils import nodes
from sphinx.transforms import SphinxTransform
from sphinx.util import logging
import nbconvert
from jupyter_sphinx.execute import JupyterWidgetViewNode, strip_latex_delimiters

from .parser import CellOutputBundleNode, CellImageNode


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
        for node in self.document.traverse(CellOutputBundleNode):
            # Create doctree nodes for cell outputs.
            output_nodes = cell_output_to_nodes(node.outputs, RENDER_PRIORITY[builder])
            node.replace_self(output_nodes)


def cell_output_to_nodes(outputs, data_priority):
    """Convert a jupyter cell with outputs and filenames to doctree nodes.

    Iterates through outputs, checks their type, and converts to the appropriate node.

    Parameters
    ----------
    cell : jupyter cell
    data_priority : list of mime types
        Which media types to prioritize.
    """

    to_add = []
    for index, output in enumerate(outputs):
        output_type = output["output_type"]
        if output_type == "stream":
            if output["name"] == "stderr":
                # Output a container with an unhighlighted literal block for
                # `stderr` messages.
                #
                # Adds a "stderr" class that can be customized by the user for both
                # the container and the literal_block.
                #
                # Not setting "rawsource" disables Pygment hightlighting, which
                # would otherwise add a <div class="highlight">.
                container = nodes.container(classes=["stderr"])
                container.append(
                    nodes.literal_block(
                        text=output["text"],
                        rawsource="",  # disables Pygment highlighting
                        language="none",
                        classes=["stderr"],
                    )
                )
                to_add.append(container)
            else:
                to_add.append(
                    nodes.literal_block(
                        text=output["text"],
                        rawsource=output["text"],
                        language="none",
                        classes=["output", "stream"],
                    )
                )
        elif output_type == "error":
            traceback = "\n".join(output["traceback"])
            text = nbconvert.filters.strip_ansi(traceback)
            to_add.append(
                nodes.literal_block(
                    text=text,
                    rawsource=text,
                    language="ipythontb",
                    classes=["output", "traceback"],
                )
            )

        elif output_type in ("display_data", "execute_result"):
            try:
                # First mime_type by priority that occurs in output.
                mime_type = next(x for x in data_priority if x in output["data"])
            except StopIteration:
                continue
            data = output["data"][mime_type]
            if mime_type.startswith("image"):
                image_data = output["data"]["image/png"]
                # Manually adding some things docutils expects (like 'candidates')
                # We are also over-riding the URI in order to pass the base64 data
                img_node = CellImageNode(
                    uri=image_data,
                    alt="",
                    candidates={"?": ""},
                    classes=["output", "image_png"],
                )
                to_add.append(img_node)
            elif mime_type == "text/html":
                to_add.append(
                    nodes.raw(text=data, format="html", classes=["output", "text_html"])
                )
            elif mime_type == "text/latex":
                to_add.append(
                    nodes.math_block(
                        text=strip_latex_delimiters(data),
                        nowrap=False,
                        number=None,
                        classes=["output", "text_latex"],
                    )
                )
            elif mime_type == "text/plain":
                to_add.append(
                    nodes.literal_block(
                        text=data,
                        rawsource=data,
                        language="none",
                        classes=["output", "text_plain"],
                    )
                )
            elif mime_type == "application/javascript":
                to_add.append(
                    nodes.raw(
                        text='<script type="{mime_type}">{data}</script>'.format(
                            mime_type=mime_type, data=data
                        ),
                        format="html",
                    )
                )
            elif mime_type == WIDGET_VIEW_MIMETYPE:
                to_add.append(JupyterWidgetViewNode(view_spec=data))
    return to_add

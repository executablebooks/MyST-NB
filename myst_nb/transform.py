"""Defines the MIMEtype docutils node."""
from docutils import nodes
from sphinx.transforms import SphinxTransform
from sphinx.util import logging

from jupyter_sphinx.ast import (
    cell_output_to_nodes,
    JupyterWidgetViewNode,
    strip_latex_delimiters,
)
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
            if node.get("inline", False):
                output_nodes = cell_output_to_nodes_inline(
                    cell, RENDER_PRIORITY[builder], True, output_dir, None
                )
            else:
                output_nodes = cell_output_to_nodes(
                    cell, RENDER_PRIORITY[builder], True, output_dir, None
                )
            # TODO add warning if output_nodes is empty
            node.replace_self(output_nodes)

        # Image collect extra nodes from cell outputs that we need to process
        for node in self.document.traverse(nodes.image):
            # If the image node has `candidates` then it's already been processed
            # as in-line markdown, so skip it
            if "candidates" in node:
                continue
            col = ImageCollector()
            col.process_doc(self.app, node)


# TODO this needs to be upstreamed to jupyter-sphinx
def cell_output_to_nodes_inline(cell, data_priority, write_stderr, dir, thebe_config):
    """Convert a jupyter cell with outputs and filenames to doctree nodes.

    Parameters
    ----------
    cell : jupyter cell
    data_priority : list of mime types
        Which media types to prioritize.
    write_stderr : bool
        If True include stderr in cell output
    dir : string
        Sphinx "absolute path" to the output folder, so it is a relative path
        to the source folder prefixed with ``/``.
    thebe_config: dict
        Thebelab configuration object or None
    """
    import os
    import docutils
    import nbconvert

    to_add = []
    for _, output in enumerate(cell.get("outputs", [])):
        output_type = output["output_type"]
        if output_type == "stream":
            if output["name"] == "stderr":
                if not write_stderr:
                    continue
                else:
                    # Output a container with an unhighlighted literal block for
                    # `stderr` messages.
                    #
                    # Adds a "stderr" class that can be customized by the user for both
                    # the container and the literal_block.
                    #
                    # Not setting "rawsource" disables Pygment hightlighting, which
                    # would otherwise add a <div class="highlight">.

                    # container = docutils.nodes.container(classes=["stderr"])
                    literal = docutils.nodes.literal(
                        text=output["text"],
                        rawsource="",  # disables Pygment highlighting
                        language="none",
                        classes=["stderr"],
                    )

                    to_add.append(literal)
            else:

                to_add.append(
                    docutils.nodes.literal(
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
                docutils.nodes.literal(
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
                # Sphinx treats absolute paths as being rooted at the source
                # directory, so make a relative path, which Sphinx treats
                # as being relative to the current working directory.
                filename = os.path.basename(output.metadata["filenames"][mime_type])
                uri = os.path.join(dir, filename)
                to_add.append(docutils.nodes.image(uri=uri))
            elif mime_type == "text/html":
                to_add.append(
                    docutils.nodes.raw(
                        text=data, format="html", classes=["output", "text_html"]
                    )
                )
            elif mime_type == "text/latex":
                to_add.append(
                    docutils.nodes.math(
                        text=strip_latex_delimiters(data),
                        nowrap=False,
                        number=None,
                        classes=["output", "text_latex"],
                    )
                )
            elif mime_type == "text/plain":
                to_add.append(
                    docutils.nodes.literal(
                        text=data,
                        rawsource=data,
                        language="none",
                        classes=["output", "text_plain"],
                    )
                )
            elif mime_type == "application/javascript":
                to_add.append(
                    docutils.nodes.raw(
                        text='<script type="{mime_type}">{data}</script>'.format(
                            mime_type=mime_type, data=data
                        ),
                        format="html",
                    )
                )
            elif mime_type == WIDGET_VIEW_MIMETYPE:
                to_add.append(JupyterWidgetViewNode(view_spec=data))

    return to_add

from docutils import nodes
from sphinx.transforms import SphinxTransform
from sphinx.util import logging

from myst_nb.parser import CellNode, CellInputNode, CellOutputBundleNode
from myst_nb.glue import GLUE_PREFIX
from myst_nb.glue.domain import PasteNode


SPHINX_LOGGER = logging.getLogger(__name__)


class PasteNodesToDocutils(SphinxTransform):
    """Use the builder context to transform a CellOutputNode into Sphinx nodes."""

    default_priority = 699  # must be applied before CellOutputsToNodes

    def apply(self):
        glue_data = self.app.env.glue_data
        for paste_node in self.document.traverse(PasteNode):

            # First check if we have both key:format in the key
            parts = paste_node.key.rsplit(":", 1)
            if len(parts) == 2:
                key, formatting = parts
            else:
                key = parts[0]
                formatting = None

            if key not in glue_data:
                SPHINX_LOGGER.warning(
                    f"Couldn't find key `{key}` in keys defined across all pages.",
                    location=paste_node.location,
                )
                continue

            # Grab the output for this key and replace `glue` specific prefix info
            output = glue_data.get(key).copy()
            output["data"] = {
                key.replace(GLUE_PREFIX, ""): val for key, val in output["data"].items()
            }

            # Roles will be parsed as text, with some formatting fanciness
            if paste_node.kind == "role":
                # Currently only plain text is supported
                if "text/plain" in output["data"]:
                    text = output["data"]["text/plain"].strip("'")
                    # If formatting is specified, see if we have a number of some kind
                    if formatting:
                        try:
                            newtext = float(text)
                            text = f"{newtext:>{formatting}}"
                        except ValueError:
                            pass
                    out_node = nodes.inline(text, text, classes=["pasted-text"])
                else:
                    SPHINX_LOGGER.warning(
                        f"Couldn't find compatible output format for key `{key}`",
                        location=paste_node.location,
                    )
            # Directives will have the whole output chunk deposited and rendered later
            elif paste_node.kind == "directive":
                output_node = CellOutputBundleNode(outputs=[output])
                out_node = CellNode()
                out_node += CellInputNode()
                out_node += output_node
            else:
                SPHINX_LOGGER.error(
                    (
                        "`kind` must by one of `role` or `directive`,"
                        f"not `{paste_node.kind}`"
                    ),
                    location=paste_node.location,
                )

            paste_node.replace_self(out_node)

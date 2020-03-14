from pathlib import Path
from sphinx.util.docutils import SphinxDirective
from sphinx.transforms import SphinxTransform
from docutils import nodes
from docutils.parsers.rst import directives
from sphinx.util import logging

from myst_nb.parser import CellNode, CellInputNode, CellOutputBundleNode
from myst_nb.glue import GLUE_PREFIX

SPHINX_LOGGER = logging.getLogger(__name__)


# Role and directive for pasting
class Paste(SphinxDirective):
    required_arguments = 1
    final_argument_whitespace = True
    has_content = False

    option_spec = {"id": directives.unchanged}

    def run(self):
        # TODO: Figure out how to report cell number in the location
        #       currently, line numbers in ipynb files are not reliable
        path, lineno = self.state_machine.get_source_and_line(self.lineno)
        # Remove line number if we have a notebook because it is unreliable
        if path.endswith(".ipynb"):
            lineno = None
        # Remove the suffix from path so its suffix is printed properly in logs
        path = str(Path(path).with_suffix(""))
        return [PasteNode(self.arguments[0], "directive", location=(path, lineno))]


def paste_role(name, rawtext, text, lineno, inliner, options={}, content=[]):
    path = inliner.document.current_source
    # Remove line number if we have a notebook because it is unreliable
    if path.endswith(".ipynb"):
        lineno = None
    path = str(Path(path).with_suffix(""))
    return [PasteNode(text, "role", location=(path, lineno))], []


# Transform to replace nodes with outputs
class PasteNode(nodes.container):
    """Represent a MimeBundle in the Sphinx AST, to be transformed later."""

    def __init__(self, key, kind, location=None, rawsource="", *children, **attributes):
        self.key = key
        self.kind = kind
        self.location = location
        super().__init__("", **attributes)


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

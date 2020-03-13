import nbformat as nbf
from pathlib import Path
import IPython
from IPython.display import display as ipy_display
from sphinx.util.docutils import SphinxDirective
from sphinx.transforms import SphinxTransform
from docutils import nodes
from docutils.parsers.rst import directives
from sphinx.util import logging

from .parser import CellNode, CellInputNode, CellOutputBundleNode

SPHINX_LOGGER = logging.getLogger(__name__)

mime_prefix = "application/papermill.record/"


def glue(name, variable, display=True):
    """Glue an variable into the notebook's cell metadata.

    Parameters
    ==========
    name: string
        A unique name for the variable. You can use this name to refer to the variable
        later on.
    variable: python object
        A variable in Python for which you'd like to store its display value. This is
        not quite the same as storing the object itself - the stored information is
        what is *displayed* when you print or show the object in a Jupyter Notebook.
    display: bool
        Display the object you are gluing. This is helpful in sanity-checking the
        state of the object at glue-time.
    """
    mimebundle, metadata = IPython.core.formatters.format_display_data(variable)
    mime_prefix = "" if display else "application/papermill.record/"
    metadata["scrapbook"] = dict(name=name, mime_prefix=mime_prefix)
    ipy_display(
        {mime_prefix + k: v for k, v in mimebundle.items()},
        raw=True,
        metadata=metadata,
    )


# Helper functions
def find_glued_key(path_ntbk, key):
    """Find an output mimebundle in a notebook based on a key."""
    # Read in the notebook
    if isinstance(path_ntbk, Path):
        path_ntbk = str(path_ntbk)
    ntbk = nbf.read(path_ntbk, nbf.NO_CONVERT)
    outputs = []
    for cell in ntbk.cells:
        if cell.cell_type != "code":
            continue

        # If we have outputs, look for scrapbook metadata and reference the key
        for output in cell["outputs"]:
            meta = output.get("metadata", {})
            if "scrapbook" in meta:
                this_key = meta["scrapbook"]["name"].replace(mime_prefix, "")
                if key == this_key:
                    bundle = output["data"]
                    bundle = {this_key: val for key, val in bundle.items()}
                    outputs.append(bundle)
    if len(outputs) == 0:
        print(f"Warning: did not find key {this_key} in notebook {path_ntbk}")
        return
    if len(outputs) > 1:
        print(
            f"Warning: multiple variables found for key: {this_key}. Returning first value."
        )
    return outputs[0]


def find_all_keys(ntbk, keys=None):
    """Find all `glue` keys in a notebook and return a dictionary with key: outputs."""
    if keys is None:
        keys = {}

    for cell in ntbk.cells:
        if cell.cell_type != "code":
            continue

        for output in cell["outputs"]:
            meta = output.get("metadata", {})
            if "scrapbook" in meta:
                this_key = meta["scrapbook"]["name"]
                if this_key in keys:
                    SPHINX_LOGGER.warn(
                        f"Over-writing pre-existing glue key: {this_key}"
                    )
                keys[this_key] = output
    return keys


# Role and directive for pasting
class Paste(SphinxDirective):
    required_arguments = 1
    final_argument_whitespace = True
    has_content = False

    option_spec = {"id": directives.unchanged}

    def run(self):
        return [PasteNode(self.arguments[0], "directive")]


def paste_role(name, rawtext, text, lineno, inliner, options={}, content=[]):
    return [PasteNode(text, "role")], []


# Transform to replace nodes with outputs
class PasteNode(nodes.container):
    """Represent a MimeBundle in the Sphinx AST, to be transformed later."""

    def __init__(self, key, kind, rawsource="", *children, **attributes):
        self.key = key
        self.kind = kind
        super().__init__("", **attributes)


class PasteNodesToDocutils(SphinxTransform):
    """Use the builder context to transform a CellOutputNode into Sphinx nodes."""

    default_priority = 700

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
                raise KeyError(
                    f"Couldn't find key {key} in keys defined across all pages."
                )

            # Grab the output for this key and replace `glue` specific prefix info
            output = glue_data.get(key).copy()
            output["data"] = {
                key.replace(mime_prefix, ""): val for key, val in output["data"].items()
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
                    SPHINX_LOGGER.warn(
                        f"Couldn't find compatible output format for key {key}"
                    )
            # Directives will have the whole output chunk deposited and rendered later
            elif paste_node.kind == "directive":
                output_node = CellOutputBundleNode(outputs=[output])
                out_node = CellNode()
                out_node += CellInputNode()
                out_node += output_node
            else:
                raise ValueError(
                    f"`kind` must by one of `role` or `directive`, not {paste_node.kind}"
                )
            paste_node.replace_self(out_node)

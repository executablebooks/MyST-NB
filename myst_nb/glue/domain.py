from pathlib import Path

from docutils import nodes
from docutils.parsers.rst import directives
from sphinx.util.docutils import SphinxDirective
from sphinx.util import logging

SPHINX_LOGGER = logging.getLogger(__name__)


class PasteNode(nodes.container):
    """Represent a MimeBundle in the Sphinx AST, to be transformed later."""

    def __init__(self, key, kind, location=None, rawsource="", *children, **attributes):
        self.key = key
        self.kind = kind
        self.location = location
        super().__init__("", **attributes)


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

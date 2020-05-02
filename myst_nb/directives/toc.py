from typing import List

from docutils import nodes
from docutils.nodes import Node

from sphinx.util.docutils import SphinxDirective
from sphinx.util import logging
from sphinx import addnodes

logger = logging.getLogger(__name__)


class TableOfContentsNode(nodes.General, nodes.Element):
    pass


def visit_TableOfContentsNode(self, node):
    pass


def depart_TableOfContentsNode(self, node):
    pass


class TableofContents(SphinxDirective):
    # this enables content in the directive
    has_content = True
    option_spec = {"maxdepth": int}

    def run(self) -> List[Node]:
        subnode = addnodes.toctree().deepcopy()
        subnode["glob"] = False
        subnode["maxdepth"] = self.options.get("maxdepth", 1)
        ret = []  # type: List[Node]
        subnode["entries"] = []
        subnode["includefiles"] = []
        self.set_source_info(subnode)
        wrappernode = nodes.compound(classes=["toctree-wrapper"])
        wrappernode.append(subnode)
        self.add_name(wrappernode)
        all_docnames = self.env.found_docs.copy()
        all_docnames.remove(self.env.docname)  # remove current document

        for docname in all_docnames:
            if "index" in docname:
                continue
            subnode["entries"].append((None, docname))
            subnode["includefiles"].append(docname)

        ret.append(wrappernode)
        return ret

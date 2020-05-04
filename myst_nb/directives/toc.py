from typing import List

from docutils import nodes
from docutils.nodes import Node

from sphinx import addnodes
from sphinx.util import logging
from sphinx.util.nodes import clean_astext
from sphinx.util.docutils import SphinxDirective

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
        ret = []  # type: List[Node]
        wrappernode = nodes.compound(classes=["toctree-wrapper"])
        subnode = nodes.bullet_list()
        wrappernode.append(subnode)
        self.add_name(wrappernode)
        depth = 0
        if hasattr(self.config, "globaltoc"):
            # case where _toc.yml is present
            self._has_toc_yaml(subnode, self.config.globaltoc, depth)
        else:
            # case where _toc.yml is not present (Not sure if necessary)
            all_docnames = self.env.found_docs.copy()
            all_docnames.remove(self.env.docname)  # remove current document

            for docname in all_docnames:
                if "index" in docname:
                    continue
                subnode["entries"].append((None, docname))
                subnode["includefiles"].append(docname)

        ret.append(wrappernode)
        return ret

    def _has_toc_yaml(self, subnode, tocdict, depth):
        depth += 1
        for key, val in tocdict.items():
            if key == "header":
                self._handle_toc_header(subnode, val, depth)
            if key == "file":
                if val not in self.env.titles:
                    continue
                title = clean_astext(self.env.titles[val])
                val = "/" + val + ".html"
                reference = nodes.reference(
                    "",
                    "",
                    internal=False,
                    refuri=val,
                    anchorname="",
                    *[nodes.Text(title)]
                )
                para = addnodes.compact_paragraph("", "", reference)
                item = nodes.list_item("", para)
                item["classes"].append("toctree-l%d" % (depth))
                subnode.append(item)
            if key == "sections":
                sectionlist = nodes.bullet_list().deepcopy()
                sectionheader = None
                headerlist = None
                for item in val:
                    if "header" in item:
                        if headerlist:
                            sectionlist.append(sectionheader)
                            sectionlist.append(headerlist)
                        headerlist = nodes.bullet_list().deepcopy()
                        sectionheader = self._handle_toc_header(
                            sectionlist, item["header"], depth
                        )
                    else:
                        if headerlist:
                            self._has_toc_yaml(headerlist, item, depth)
                        else:
                            self._has_toc_yaml(sectionlist, item, depth)
                if headerlist:
                    sectionlist.append(sectionheader)
                    sectionlist.append(headerlist)
                subnode.append(sectionlist)

    def _handle_toc_header(self, subnode, val, depth):
        if val in self.env.titles:
            title = clean_astext(self.env.titles[val])
            val = "/" + val + ".html"
            reference = nodes.reference(
                "", "", internal=False, refuri=val, anchorname="", *[nodes.Text(title)]
            )
            para = addnodes.compact_paragraph("", "", reference)
        else:
            para = addnodes.compact_paragraph("", "", nodes.Text(val))
        para["classes"].append("toctree-l%d" % (depth))
        item = nodes.list_item("", para)
        item["classes"].append("toctree-l%d" % (depth))
        return item

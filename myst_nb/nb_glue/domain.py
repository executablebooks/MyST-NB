import json
from pathlib import Path
from typing import List, Dict

from docutils import nodes
from docutils.parsers.rst import directives
from sphinx.domains import Domain
from sphinx.util.docutils import SphinxDirective
from sphinx.util import logging

from myst_nb.nb_glue.utils import find_all_keys

SPHINX_LOGGER = logging.getLogger(__name__)


class PasteNode(nodes.container):
    """Represent a MimeBundle in the Sphinx AST, to be transformed later."""

    def __init__(self, key, kind, location=None, rawsource="", *children, **attributes):
        self.key = key
        self.kind = kind
        self.location = location
        super().__init__("", **attributes)

    def copy(self):
        return self.__class__(
            self.key, self.kind, location=self.location, **self.attributes
        )


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


class PasteFigure(Paste):
    def align(argument):
        return directives.choice(argument, ("left", "center", "right"))

    def figwidth_value(argument):
        return directives.length_or_percentage_or_unitless(argument, "px")

    option_spec = Paste.option_spec.copy()
    option_spec["figwidth"] = figwidth_value
    option_spec["figclass"] = directives.class_option
    option_spec["align"] = align
    # TODO how to add label that can be referenced?
    has_content = True

    def run(self):
        figwidth = self.options.pop("figwidth", None)
        figclasses = self.options.pop("figclass", None)
        align = self.options.pop("align", None)
        # On the Paste node we should add an attribute to specify that only image
        # type mimedata is allowed, then this would be used by
        # PasteNodesToDocutils -> CellOutputsToNodes to alter the render priority
        # and/or log warnings if that type of mimedata is not available
        (paste_node,) = Paste.run(self)
        if isinstance(paste_node, nodes.system_message):
            return [paste_node]
        figure_node = nodes.figure("", paste_node)
        if figwidth is not None:
            figure_node["width"] = figwidth
        if figclasses:
            figure_node["classes"] += figclasses
        if align:
            figure_node["align"] = align
        if self.content:
            node = nodes.Element()  # anonymous container for parsing
            self.state.nested_parse(self.content, self.content_offset, node)
            first_node = node[0]
            if isinstance(first_node, nodes.paragraph):
                caption = nodes.caption(first_node.rawsource, "", *first_node.children)
                caption.source = first_node.source
                caption.line = first_node.line
                figure_node += caption
            elif not (isinstance(first_node, nodes.comment) and len(first_node) == 0):
                error = self.state_machine.reporter.error(
                    "Figure caption must be a paragraph or empty comment.",
                    nodes.literal_block(self.block_text, self.block_text),
                    line=self.lineno,
                )
                return [figure_node, error]
            if len(node) > 1:
                figure_node += nodes.legend("", *node[1:])
        return [figure_node]


def paste_role(name, rawtext, text, lineno, inliner, options={}, content=[]):
    path = inliner.document.current_source
    # Remove line number if we have a notebook because it is unreliable
    if path.endswith(".ipynb"):
        lineno = None
    path = str(Path(path).with_suffix(""))
    return [PasteNode(text, "role", location=(path, lineno))], []


class NbGlueDomain(Domain):
    """A sphinx domain for handling glue data """

    name = "nb"
    label = "NotebookGlue"
    # data version, bump this when the format of self.data changes
    data_version = 0.1
    # data value for a fresh environment
    # - cache is the mapping of all keys to outputs
    # - docmap is the mapping of docnames to the set of keys it contains
    # TODO storing all the outputs in the cache, could allow it to get very big
    # we may need to consider storing outputs on disc?
    initial_data = {"cache": {}, "docmap": {}}

    directives = {"paste": Paste, "figure": PasteFigure}

    roles = {"paste": paste_role}

    @property
    def cache(self) -> dict:
        return self.env.domaindata[self.name]["cache"]

    @property
    def docmap(self) -> dict:
        return self.env.domaindata[self.name]["docmap"]

    def __contains__(self, key):
        return key in self.cache

    def get(self, key):
        return self.cache.get(key)

    @classmethod
    def from_env(cls, env) -> "NbGlueDomain":
        return env.domains[cls.name]

    def write_cache(self, path=None):
        """If None, write to doctreedir"""
        if path is None:
            path = Path(self.env.doctreedir).joinpath("glue_cache.json")
        if isinstance(path, str):
            path = Path(path)
        with path.open("w") as handle:
            json.dump(
                {
                    d: {k: self.cache[k] for k in vs if k in self.cache}
                    for d, vs in self.docmap.items()
                    if vs
                },
                handle,
                indent=2,
            )

    def add_notebook(self, ntbk, docname):
        """Find all glue keys from the notebook and add to the cache."""
        new_keys = find_all_keys(
            ntbk,
            existing_keys={v: k for k, vs in self.docmap.items() for v in vs},
            path=str(docname),
            logger=SPHINX_LOGGER,
        )
        self.docmap[str(docname)] = set(new_keys)
        self.cache.update(new_keys)

    def clear_doc(self, docname: str) -> None:
        """Remove traces of a document in the domain-specific inventories."""
        for key in self.docmap.get(docname, []):
            self.cache.pop(key, None)
        self.docmap.pop(docname, None)

    def merge_domaindata(self, docnames: List[str], otherdata: Dict) -> None:
        """Merge in data regarding *docnames* from a different domaindata
        inventory (coming from a subprocess in parallel builds).
        """
        # TODO need to deal with key clashes
        raise NotImplementedError(
            "merge_domaindata must be implemented in %s "
            "to be able to do parallel builds!" % self.__class__
        )

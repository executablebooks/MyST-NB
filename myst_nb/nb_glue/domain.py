"""A domain to register in sphinx.

This is required for any directive/role names using `:`.
"""
from typing import List

from sphinx.domains import Domain
from sphinx.ext.autodoc.directive import DummyOptionSpec
from sphinx.util.docutils import SphinxDirective

from myst_nb.nb_glue.elements import (
    PasteDirective,
    PasteFigureDirective,
    PasteRole,
    PasteTextRole,
)


class DummyDirective(SphinxDirective):
    required_arguments = 1
    final_argument_whitespace = True
    has_content = False
    option_spec = DummyOptionSpec()

    def run(self):
        return []


class NbGlueDomain(Domain):
    """A sphinx domain for defining glue roles and directives."""

    name = "glue"
    label = "NotebookGlue"

    # data version, bump this when the format of self.data changes
    data_version = 0.2

    directives = {
        "": PasteDirective,
        "any": PasteDirective,
        "figure": PasteFigureDirective,
        "math": DummyDirective,
    }
    roles = {"": PasteRole(), "any": PasteRole(), "text": PasteTextRole()}

    def merge_domaindata(self, docnames: List[str], otherdata: dict) -> None:
        pass

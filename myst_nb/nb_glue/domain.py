"""A domain to register in sphinx.

This is required for any directive/role names using `:`.
"""
from typing import List

from sphinx.domains import Domain

from myst_nb.nb_glue.elements import (
    PasteDirective,
    PasteFigureDirective,
    PasteMarkdownDirective,
    PasteMarkdownRole,
    PasteMathDirective,
    PasteRole,
    PasteTextRole,
)


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
        "math": PasteMathDirective,
        "md": PasteMarkdownDirective,
    }
    roles = {
        "": PasteRole(),
        "any": PasteRole(),
        "text": PasteTextRole(),
        "md": PasteMarkdownRole(),
    }

    def merge_domaindata(self, docnames: List[str], otherdata: dict) -> None:
        pass

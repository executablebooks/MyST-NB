"""A domain to register in sphinx.

This is required for any directive/role names using `:`.
"""
from typing import List

from sphinx.domains import Domain

from . import get_glue_directives, get_glue_roles


class NbGlueDomain(Domain):
    """A sphinx domain for defining glue roles and directives."""

    name = "glue"
    label = "NotebookGlue"

    # data version, bump this when the format of self.data changes
    data_version = 1

    directives = get_glue_directives(prefix="")
    roles = get_glue_roles(prefix="")

    def merge_domaindata(self, docnames: List[str], otherdata: dict) -> None:
        pass

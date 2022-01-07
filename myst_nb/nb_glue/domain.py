from typing import List

from sphinx.domains import Domain
from sphinx.ext.autodoc.directive import DummyOptionSpec
from sphinx.util.docutils import SphinxDirective, SphinxRole

from myst_nb.nb_glue.elements import PasteDirective, PasteFigureDirective


class DummyDirective(SphinxDirective):
    required_arguments = 1
    final_argument_whitespace = True
    has_content = False
    option_spec = DummyOptionSpec()

    def run(self):
        return []


class DummyDirective2(DummyDirective):
    has_content = True


class DummyRole(SphinxRole):
    def run(self):
        return [], []


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
    roles = {"": DummyRole(), "any": DummyRole(), "text": DummyRole()}

    def merge_domaindata(self, docnames: List[str], otherdata: dict) -> None:
        pass

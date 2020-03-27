from collections import defaultdict
from pathlib import Path

from docutils import nodes
from docutils.frontend import OptionParser
from docutils.parsers.rst import Parser as RSTParser
from docutils.utils import new_document

from sphinx.domains.math import MathDomain
from sphinx.util.docutils import sphinx_domains

from myst_nb.nb_glue.domain import NbGlueDomain

import pytest

NB_DIR = Path(__file__).parent.joinpath("notebooks")


class MockEnv:
    def __init__(self, tmp_path):
        self.docname = "source/nb"
        self.dependencies = defaultdict(set)
        self.domaindata = {}
        self.domains = {
            NbGlueDomain.name: NbGlueDomain(self),
            MathDomain.name: MathDomain(self),
        }
        self._tmp_path = tmp_path
        self.path_cache = str(tmp_path) + "/.jupyter_cache"

        class app:
            class builder:
                name = "html"

            class config:
                language = None

            env = self
            srcdir = tmp_path / "source"
            outdir = tmp_path / "build" / "outdir"

        class env:
            srcdir = str(tmp_path) + "/source"
            outdir = str(tmp_path) + "/build" + "/outdir"
            config = {
                "jupyter_execute_notebooks": "off",
                "execution_excludepatterns": [],
                "jupyter_cache": "",
            }

        self.app = app
        self.env = env
        self.env.app = app
        self.config = env.config

    def get_domain(self, name):
        return self.domains[name]

    def relfn2path(self, imguri, docname):
        return ("image.png", self._tmp_path / "build" / "image.png")

    def new_serialno(self, name):
        return 1

    def set_config(self, config_val):
        for key, val in self.env.config.items():
            if config_val[0] == key:
                self.env.config[key] = config_val[1]

    def set_srcdir(self, srcdir):
        self.env.srcdir = srcdir

    def set_docname(self, docname):
        self.docname = docname


@pytest.fixture()
def mock_document(tmp_path) -> nodes.document:
    settings = OptionParser(components=(RSTParser,)).get_default_values()
    document = new_document("notset", settings=settings)
    document.settings.env = MockEnv(tmp_path)
    with sphinx_domains(document.settings.env):
        yield document


@pytest.fixture()
def get_notebook():
    def _get_notebook(name):
        return NB_DIR.joinpath(name)

    return _get_notebook

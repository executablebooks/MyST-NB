import os
from pathlib import Path
import pickle

from docutils.utils import Reporter

import pytest

NB_DIR = Path(__file__).parent.joinpath("notebooks")


@pytest.fixture()
def get_notebook():
    def _get_notebook(name):
        return NB_DIR.joinpath(name)

    return _get_notebook


@pytest.fixture()
def nb_params(request):
    """Parameters that are specified by 'pytest.mark.doc_params'
    are passed to the ``mock_document`` fixture.
    """
    markers = request.node.iter_markers("nb_params")
    kwargs = {}
    if markers is not None:
        for info in reversed(list(markers)):
            kwargs.update(info.kwargs)
    return kwargs


class SphinxFixture:
    def __init__(self, app, nb_file):
        self.app = app
        self.nb_file = nb_file
        self.nb_name = os.path.splitext(nb_file)[0]

    def build(self):
        self.app.build()

    def status(self):
        return self.app._status.getvalue().strip()

    def warnings(self):
        return self.app._warning.getvalue().strip()

    def get_doctree(self):
        _path = self.app.doctreedir / (self.nb_name + ".doctree")
        if not _path.exists():
            pytest.fail("doctree not output")
        doctree = pickle.loads(_path.bytes())
        doctree["source"] = self.nb_name
        doctree.reporter = Reporter(self.nb_name, 1, 5)
        self.app.env.temp_data["docname"] = self.nb_name
        doctree.settings.env = self.app.env
        return doctree

    def get_html(self):
        _path = self.app.outdir / (self.nb_name + ".html")
        if not _path.exists():
            pytest.fail("html not output")
        return _path.text()

    def get_nb(self):
        _path = self.app.srcdir / "_build" / "jupyter_execute" / self.nb_file
        if not _path.exists():
            pytest.fail("notebook not output")
        return _path.text()

    def get_report_file(self):
        _path = self.app.outdir / "reports" / (self.nb_name + ".log")
        if not _path.exists():
            pytest.fail("report log not output")
        return _path.text()


@pytest.fixture()
def nb_run(nb_params, make_app, tempdir):
    nb_file = nb_params["nb"]
    conf = nb_params.get("conf", {})

    nb_name = os.path.splitext(nb_file)[0]
    nb_path = NB_DIR.joinpath(nb_file)
    assert nb_path.exists(), nb_path

    os.chdir(tempdir)
    srcdir = tempdir / "source"
    srcdir.makedirs()
    (srcdir / "conf.py").write_text("")

    (srcdir / nb_file).write_text(nb_path.read_text())
    confoverrides = {"extensions": ["myst_nb"], "master_doc": nb_name}
    confoverrides.update(conf)
    app = make_app(buildername="html", srcdir=srcdir, confoverrides=confoverrides)

    return SphinxFixture(app, nb_file)

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


class SphinxFixture:
    """A class returned by the ``nb_run`` fixture, to run sphinx,
    and retrieve aspects of the build.
    """

    def __init__(self, app, nb_file):
        self.app = app
        self.env = app.env
        self.nb_file = nb_file
        self.nb_name = os.path.splitext(nb_file)[0]

    def build(self):
        """Run the sphinx build."""
        # reset streams before each build
        self.app._status.truncate(0)
        self.app._status.seek(0)
        self.app._warning.truncate(0)
        self.app._warning.seek(0)
        self.app.build()

    def status(self):
        """Return the stdout stream of the sphinx build."""
        return self.app._status.getvalue().strip()

    def warnings(self):
        """Return the stderr stream of the sphinx build."""
        return self.app._warning.getvalue().strip()

    def invalidate_notebook(self):
        """Invalidate the notebook file, such that it will be flagged for a re-read."""
        self.env.all_docs.pop(self.nb_name)

    def get_doctree(self):
        """Load and return the built docutils.document."""
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
        """Return the built HTML file."""
        _path = self.app.outdir / (self.nb_name + ".html")
        if not _path.exists():
            pytest.fail("html not output")
        return _path.text()

    def get_nb(self):
        """Return the output notebook (after any execution)."""
        _path = self.app.srcdir / "_build" / "jupyter_execute" / self.nb_file
        if not _path.exists():
            pytest.fail("notebook not output")
        return _path.text()

    def get_report_file(self):
        """Return the report file for a failed execution."""
        _path = self.app.outdir / "reports" / (self.nb_name + ".log")
        if not _path.exists():
            pytest.fail("report log not output")
        return _path.text()


@pytest.fixture()
def nb_params(request):
    """Parameters that are specified by 'pytest.mark.nb_params'
    are passed to the ``nb_run`` fixture::

        @pytest.mark.nb_params(nb="name.ipynb", conf={"option": "value"})
        def test_something(nb_run):
            ...
    """
    markers = request.node.iter_markers("nb_params")
    kwargs = {}
    if markers is not None:
        for info in reversed(list(markers)):
            kwargs.update(info.kwargs)
    return kwargs

    nb_name = os.path.splitext(nb_file)[0]
    nb_path = NB_DIR.joinpath(nb_file)
    assert nb_path.exists(), nb_path

@pytest.fixture()
def nb_run(nb_params, make_app, tempdir):
    """A fixture to setup and run a sphinx build,
    with the `myst_nb` extension for a single notebook, in a sandboxed folder."""
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
    confoverrides = {
        "extensions": ["myst_nb"],
        "master_doc": nb_name,
        "exclude_patterns": ["_build"],
    }
    confoverrides.update(conf)
    app = make_app(buildername="html", srcdir=srcdir, confoverrides=confoverrides)

    return SphinxFixture(app, nb_file)

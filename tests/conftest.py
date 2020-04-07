import os
from pathlib import Path
import pickle

import pytest

from docutils.utils import Reporter
from nbdime.diffing.notebooks import (
    diff_notebooks,
    set_notebook_diff_targets,
    set_notebook_diff_ignores,
)
from nbdime.prettyprint import pretty_print_diff
import nbformat as nbf


# -Diff Configuration-#
NB_VERSION = 4
set_notebook_diff_ignores({"/nbformat_minor": True})
set_notebook_diff_targets(metadata=False)

TEST_FILE_DIR = Path(__file__).parent.joinpath("notebooks")


@pytest.fixture()
def get_test_path():
    def _get_test_path(name):
        return TEST_FILE_DIR.joinpath(name)

    return _get_test_path


class SphinxFixture:
    """A class returned by the ``sphinx_run`` fixture, to run sphinx,
    and retrieve aspects of the build.
    """

    def __init__(self, app, filenames):
        self.app = app
        self.env = app.env
        self.files = [os.path.splitext(f) for f in filenames]

        # self.nb_file = nb_file
        # self.nb_name = os.path.splitext(nb_file)[0]

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

    def invalidate_files(self):
        """Invalidate the files, such that it will be flagged for a re-read."""
        for name, _ in self.files:
            self.env.all_docs.pop(name)

    def get_doctree(self, index=0):
        """Load and return the built docutils.document."""
        name = self.files[index][0]
        _path = self.app.doctreedir / (name + ".doctree")
        if not _path.exists():
            pytest.fail("doctree not output")
        doctree = pickle.loads(_path.bytes())
        doctree["source"] = name
        doctree.reporter = Reporter(name, 1, 5)
        self.app.env.temp_data["docname"] = name
        doctree.settings.env = self.app.env
        return doctree

    def get_html(self, index=0):
        """Return the built HTML file."""
        name = self.files[index][0]
        _path = self.app.outdir / (name + ".html")
        if not _path.exists():
            pytest.fail("html not output")
        return _path.text()

    def get_nb(self, index=0):
        """Return the output notebook (after any execution)."""
        name = self.files[index][0]
        _path = self.app.srcdir / "_build" / "jupyter_execute" / (name + ".ipynb")
        if not _path.exists():
            pytest.fail("notebook not output")
        return _path.text()

    def get_report_file(self, index=0):
        """Return the report file for a failed execution."""
        name = self.files[index][0]
        _path = self.app.outdir / "reports" / (name + ".log")
        if not _path.exists():
            pytest.fail("report log not output")
        return _path.text()


@pytest.fixture()
def sphinx_params(request):
    """Parameters that are specified by 'pytest.mark.sphinx_params'
    are passed to the ``sphinx_run`` fixture::

        @pytest.mark.sphinx_params("name.ipynb", conf={"option": "value"})
        def test_something(sphinx_run):
            ...
    """
    markers = request.node.iter_markers("sphinx_params")
    kwargs = {}
    if markers is not None:
        for info in reversed(list(markers)):
            kwargs.update(info.kwargs)
            kwargs["files"] = info.args
    return kwargs


@pytest.fixture()
def sphinx_run(sphinx_params, make_app, tempdir):
    """A fixture to setup and run a sphinx build, in a sandboxed folder.

    The `myst_nb` extension ius added by default,
    and the first file will be set as the materdoc

    """
    assert len(sphinx_params["files"]) > 0, sphinx_params["files"]
    conf = sphinx_params.get("conf", {})

    current_dir = os.getcwd()
    if "working_dir" in sphinx_params:
        from sphinx.testing.path import path

        base_dir = path(sphinx_params["working_dir"])
    else:
        base_dir = tempdir
    srcdir = base_dir / "source"
    srcdir.makedirs()
    os.chdir(base_dir)
    (srcdir / "conf.py").write_text("")

    for nb_file in sphinx_params["files"]:
        nb_path = TEST_FILE_DIR.joinpath(nb_file)
        assert nb_path.exists(), nb_path
        (srcdir / nb_file).write_text(nb_path.read_text())

    confoverrides = {
        "extensions": ["myst_nb"],
        "master_doc": os.path.splitext(sphinx_params["files"][0])[0],
        "exclude_patterns": ["_build"],
    }
    confoverrides.update(conf)
    app = make_app(buildername="html", srcdir=srcdir, confoverrides=confoverrides)

    yield SphinxFixture(app, sphinx_params["files"])

    # reset working directory
    os.chdir(current_dir)


def empty_non_deterministic_outputs(cell):
    if "outputs" in cell and len(cell.outputs):
        for item in cell.outputs:
            if "data" in item and "image/png" in item.data:
                item.data["image/png"] = ""
            if "filenames" in item.get("metadata", {}):
                item["metadata"]["filenames"] = {
                    k: os.path.basename(v)
                    for k, v in item["metadata"]["filenames"].items()
                }


@pytest.fixture()
def check_nbs():
    def _check_nbs(obtained_filename, expected_filename):
        obtained_nb = nbf.read(str(obtained_filename), nbf.NO_CONVERT)
        expect_nb = nbf.read(str(expected_filename), nbf.NO_CONVERT)
        for cell in expect_nb.cells:
            empty_non_deterministic_outputs(cell)
        for cell in obtained_nb.cells:
            empty_non_deterministic_outputs(cell)
        diff = diff_notebooks(obtained_nb, expect_nb)
        filename_without_path = str(expected_filename)[
            str(expected_filename).rfind("/") + 1 :
        ]
        if diff:
            raise AssertionError(
                pretty_print_diff(obtained_nb, diff, str(filename_without_path))
            )

    return _check_nbs

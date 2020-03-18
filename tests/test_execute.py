from myst_nb.cache import stage_and_execute, add_notebook_outputs
from nbdime.diffing.notebooks import (
    diff_notebooks,
    set_notebook_diff_targets,
    set_notebook_diff_ignores,
)
import nbformat as nbf

import pytest

# -Diff Configuration-#
NB_VERSION = 4
set_notebook_diff_ignores({"/nbformat_minor": True})
set_notebook_diff_targets(metadata=False)


class MockEnv:
    def __init__(self, tmp_path):
        self._tmp_path = tmp_path

        class app:
            class builder:
                name = "html"

            env = self
            srcdir = tmp_path / "source"
            outdir = tmp_path / "build" / "outdir"
            path_cache = tmp_path / ".jupyter_cache"

        self.app = app
        self.config = {
            "jupyter_execute_notebooks": True,
            "jupyter_notebook_force_run": True,
            "execution_excludepatterns": [],
        }


@pytest.fixture()
def mock_environment(tmp_path):
    env = MockEnv(tmp_path)
    return env


def test_basic_unrun(mock_environment, mock_document, get_notebook):
    first_nb = get_notebook("basic_unrun.ipynb")
    nb_list = [str(first_nb.relative_to(first_nb.cwd()))]

    stage_and_execute(mock_environment, nb_list, mock_environment.app.path_cache)
    ntbk = nbf.reads(first_nb.read_text(), nbf.NO_CONVERT)
    ntbk = add_notebook_outputs(str(first_nb), ntbk, mock_environment.app.path_cache)

    second_nb = get_notebook("basic_run.ipynb")
    ntbk2 = nbf.reads(second_nb.read_text(), nbf.NO_CONVERT)

    diff = diff_notebooks(ntbk, ntbk2)
    assert len(diff) == 0

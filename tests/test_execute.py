from myst_nb.cache import execution_cache, add_notebook_outputs
from myst_nb.parser import NotebookParser
from nbdime.diffing.notebooks import (
    diff_notebooks,
    set_notebook_diff_targets,
    set_notebook_diff_ignores,
)
from nbdime.prettyprint import pretty_print_diff
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

        class env:
            srcdir = (tmp_path,)
            outdir = (tmp_path / "build" / "outdir",)
            path_cache = (tmp_path / ".jupyter_cache",)
            config = {
                "jupyter_execute_notebooks": True,
                "jupyter_notebook_force_run": True,
                "execution_excludepatterns": [],
                "jupyter_cache": True,
            }

        self.app = app
        self.env = env
        self.config = env.config


@pytest.fixture()
def mock_environment(tmp_path):
    env = MockEnv(tmp_path)
    return env


def check_nbs(obtained_filename, expected_filename):
    obtained_nb = nbf.read(str(obtained_filename), nbf.NO_CONVERT)
    expect_nb = nbf.read(str(expected_filename), nbf.NO_CONVERT)
    diff = diff_notebooks(obtained_nb, expect_nb)
    filename_without_path = str(expected_filename)[
        str(expected_filename).rfind("/") + 1 :
    ]
    if diff:
        raise AssertionError(
            pretty_print_diff(obtained_nb, diff, str(filename_without_path))
        )


def test_basic_unrun(mock_environment, mock_document, get_notebook, file_regression):
    first_nb = get_notebook("basic_unrun.ipynb")
    nb_list = {str(first_nb.relative_to(first_nb.cwd()))}  # A set

    execution_cache(
        mock_environment,
        mock_environment.env,
        nb_list,
        [],
        [],
        str(mock_environment.env.path_cache),
    )
    ntbk = nbf.reads(first_nb.read_text(), nbf.NO_CONVERT)
    ntbk_output = add_notebook_outputs(
        str(first_nb), ntbk, mock_environment.env.path_cache
    )

    # for testing the generated notebook output
    file_regression.check(
        nbf.writes(ntbk_output), check_fn=check_nbs, extension=".ipynb"
    )

    # for testing the generated docutils xml
    parser = NotebookParser()
    parser.parse(nbf.writes(ntbk), mock_document)
    file_regression.check(mock_document.pformat(), extension=".xml")


# def test_rerun_if_outputs(mock_environment, mock_document, get_notebook):
#     first_nb = get_notebook("basic_run.ipynb")
#     nb_list = [str(first_nb.relative_to(first_nb.cwd()))]

#     stage_and_execute(mock_environment, nb_list, mock_environment.app.path_cache)
#     ntbk = nbf.reads(first_nb.read_text(), nbf.NO_CONVERT)
#     ntbk = add_notebook_outputs(str(first_nb), ntbk, mock_environment.app.path_cache)

#     ntbk2 = nbf.reads(first_nb.read_text(), nbf.NO_CONVERT)

#     diff = diff_notebooks(ntbk, ntbk2)
#     assert len(diff) == 0

from nbdime.diffing.notebooks import (
    diff_notebooks,
    set_notebook_diff_targets,
    set_notebook_diff_ignores,
)
from nbdime.prettyprint import pretty_print_diff

import nbformat as nbf

import pytest
import os

# -Diff Configuration-#
NB_VERSION = 4
set_notebook_diff_ignores({"/nbformat_minor": True})
set_notebook_diff_targets(metadata=False)


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


def check_nbs(obtained_filename, expected_filename):
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


@pytest.mark.nb_params(
    nb="basic_unrun.ipynb", conf={"jupyter_execute_notebooks": "cache"}
)
def test_basic_unrun(nb_run, file_regression):
    nb_run.build()
    # print(nb_run.status())
    assert nb_run.warnings() == ""
    assert "test_name" in nb_run.app.env.metadata["basic_unrun"]
    file_regression.check(nb_run.get_nb(), check_fn=check_nbs, extension=".ipynb")
    file_regression.check(nb_run.get_doctree().pformat(), extension=".xml")


@pytest.mark.nb_params(
    nb="basic_failing.ipynb", conf={"jupyter_execute_notebooks": "cache"}
)
def test_basic_failing(nb_run, file_regression):
    nb_run.build()
    # print(nb_run.status())
    assert "Execution Failed" in nb_run.warnings()
    assert (
        "Couldn't find cache key for notebook file source/basic_failing.ipynb"
        in nb_run.warnings()
    )
    file_regression.check(nb_run.get_nb(), check_fn=check_nbs, extension=".ipynb")
    file_regression.check(nb_run.get_doctree().pformat(), extension=".xml")
    nb_run.get_report_file()


@pytest.mark.nb_params(
    nb="basic_unrun.ipynb", conf={"jupyter_execute_notebooks": "auto"}
)
def test_basic_unrun_nbclient(nb_run, file_regression):
    nb_run.build()
    # print(nb_run.status())
    assert nb_run.warnings() == ""
    assert "test_name" in nb_run.app.env.metadata["basic_unrun"]
    file_regression.check(nb_run.get_nb(), check_fn=check_nbs, extension=".ipynb")
    file_regression.check(nb_run.get_doctree().pformat(), extension=".xml")


@pytest.mark.nb_params(
    nb="basic_unrun.ipynb", conf={"jupyter_execute_notebooks": "force"}
)
def test_outputs_present(nb_run, file_regression):
    nb_run.build()
    # print(nb_run.status())
    assert nb_run.warnings() == ""
    assert "test_name" in nb_run.app.env.metadata["basic_unrun"]
    file_regression.check(nb_run.get_nb(), check_fn=check_nbs, extension=".ipynb")
    file_regression.check(nb_run.get_doctree().pformat(), extension=".xml")


@pytest.mark.nb_params(
    nb="complex_outputs_unrun.ipynb", conf={"jupyter_execute_notebooks": "cache"}
)
def test_complex_outputs_unrun(nb_run, file_regression):
    nb_run.build()
    # print(nb_run.status())
    assert nb_run.warnings() == ""
    file_regression.check(nb_run.get_nb(), check_fn=check_nbs, extension=".ipynb")
    file_regression.check(nb_run.get_doctree().pformat(), extension=".xml")


@pytest.mark.nb_params(
    nb="complex_outputs_unrun.ipynb", conf={"jupyter_execute_notebooks": "auto"}
)
def test_complex_outputs_unrun_nbclient(nb_run, file_regression):
    nb_run.build()
    # print(nb_run.status())
    assert nb_run.warnings() == ""
    file_regression.check(nb_run.get_nb(), check_fn=check_nbs, extension=".ipynb")
    file_regression.check(nb_run.get_doctree().pformat(), extension=".xml")


@pytest.mark.nb_params(
    nb="basic_unrun.ipynb", conf={"jupyter_execute_notebooks": "off"}
)
def test_no_execute(nb_run, file_regression):
    nb_run.build()
    # print(nb_run.status())
    assert nb_run.warnings() == ""
    file_regression.check(nb_run.get_nb(), check_fn=check_nbs, extension=".ipynb")
    file_regression.check(nb_run.get_doctree().pformat(), extension=".xml")


@pytest.mark.nb_params(
    nb="basic_unrun.ipynb", conf={"jupyter_execute_notebooks": "cache"}
)
def test_jupyter_cache_path(nb_run, file_regression):
    nb_run.build()
    assert "Execution Succeeded" in nb_run.status()
    assert nb_run.warnings() == ""
    file_regression.check(nb_run.get_nb(), check_fn=check_nbs, extension=".ipynb")
    file_regression.check(nb_run.get_doctree().pformat(), extension=".xml")

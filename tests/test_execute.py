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


def execute_and_merge(mock_environment, nb_list, first_nb):
    ntbk = nbf.reads(first_nb.read_text(), nbf.NO_CONVERT)
    execution_cache(
        mock_environment,
        mock_environment.env,
        nb_list,
        [],
        [],
        mock_environment.path_cache,
    )
    ntbk_output = add_notebook_outputs(mock_environment, ntbk, str(first_nb))
    return ntbk, ntbk_output


def check_docutils_xml(mock_document, ntbk, first_nb, file_regression):
    # for testing the generated docutils xml
    parser = NotebookParser()
    parser.parse(nbf.writes(ntbk), mock_document, str(first_nb))
    file_regression.check(mock_document.pformat(), extension=".xml")


def check_report_file(dest_path, nb):
    report_dir = dest_path + "/reports"
    if os.path.isdir(report_dir):
        filename = str(nb)[str(nb).rfind("/") + 1 : str(nb).rfind(".")]
        file_path = report_dir + "/{}.log".format(filename)
        if not os.path.exists(file_path):
            pytest.fail("log file for {} was not created".format(filename))


def test_basic_unrun(mock_document, get_notebook, file_regression):
    first_nb = get_notebook("basic_unrun.ipynb")
    mock_document.settings.env.set_config(["jupyter_execute_notebooks", "cache"])
    mock_document.settings.env.set_docname("basic_unrun.ipynb")
    nb_list = {str(first_nb.relative_to(first_nb.cwd()))}  # A set
    ntbk, ntbk_output = execute_and_merge(mock_document.settings.env, nb_list, first_nb)
    # for testing the generated notebook output
    file_regression.check(
        nbf.writes(ntbk_output), check_fn=check_nbs, extension=".ipynb"
    )
    check_docutils_xml(mock_document, ntbk, first_nb, file_regression)


def test_basic_failing(mock_document, get_notebook, file_regression):
    first_nb = get_notebook("basic_failing.ipynb")
    mock_document.settings.env.set_config(["jupyter_execute_notebooks", "cache"])
    mock_document.settings.env.set_docname("basic_failing.ipynb")
    nb_list = {str(first_nb.relative_to(first_nb.cwd()))}  # A set

    ntbk, ntbk_output = execute_and_merge(mock_document.settings.env, nb_list, first_nb)
    # for testing the generated notebook output
    file_regression.check(
        nbf.writes(ntbk_output), check_fn=check_nbs, extension=".ipynb"
    )

    check_report_file(mock_document.settings.env.env.outdir, first_nb)

    check_docutils_xml(mock_document, ntbk, first_nb, file_regression)


def test_basic_unrun_nbclient(mock_document, get_notebook, file_regression):
    mock_document.settings.env.set_config(["jupyter_execute_notebooks", "auto"])
    test_basic_unrun(mock_document, get_notebook, file_regression)


def test_outputs_present(mock_document, get_notebook, file_regression):
    mock_document.settings.env.set_config(["jupyter_execute_notebooks", "force"])
    first_nb = get_notebook("basic_run.ipynb")
    mock_document.settings.env.set_docname("basic_run.ipynb")
    nb_list = {str(first_nb.relative_to(first_nb.cwd()))}  # A set

    ntbk, ntbk_output = execute_and_merge(mock_document.settings.env, nb_list, first_nb)
    # for testing the generated notebook output
    file_regression.check(
        nbf.writes(ntbk_output), check_fn=check_nbs, extension=".ipynb"
    )

    check_docutils_xml(mock_document, ntbk, first_nb, file_regression)


def test_complex_outputs_unrun(mock_document, get_notebook, file_regression):
    first_nb = get_notebook("complex_outputs_unrun.ipynb")
    mock_document.settings.env.set_config(["jupyter_execute_notebooks", "cache"])
    mock_document.settings.env.set_docname("complex_outputs_unrun.ipynb")
    nb_list = {str(first_nb.relative_to(first_nb.cwd()))}  # A set

    ntbk, ntbk_output = execute_and_merge(mock_document.settings.env, nb_list, first_nb)
    # for testing the generated notebook output
    file_regression.check(
        nbf.writes(ntbk_output), check_fn=check_nbs, extension=".ipynb"
    )

    check_docutils_xml(mock_document, ntbk, first_nb, file_regression)


def test_complex_outputs_unrun_nbclient(mock_document, get_notebook, file_regression):
    mock_document.settings.env.set_config(["jupyter_execute_notebooks", "auto"])
    first_nb = get_notebook("complex_outputs_unrun.ipynb")
    mock_document.settings.env.set_docname("complex_outputs_unrun.ipynb")
    nb_list = {str(first_nb.relative_to(first_nb.cwd()))}  # A set

    ntbk, ntbk_output = execute_and_merge(mock_document.settings.env, nb_list, first_nb)
    # for testing the generated notebook output
    file_regression.check(
        nbf.writes(ntbk_output), check_fn=check_nbs, extension=".ipynb"
    )

    check_docutils_xml(mock_document, ntbk, first_nb, file_regression)


def test_no_execute(mock_document, get_notebook, file_regression):
    mock_document.settings.env.set_config(["jupyter_execute_notebooks", "off"])
    first_nb = get_notebook("basic_unrun.ipynb")
    mock_document.settings.env.set_docname("basic_unrun.ipynb")
    nb_list = {str(first_nb.relative_to(first_nb.cwd()))}  # A set

    ntbk, ntbk_output = execute_and_merge(mock_document.settings.env, nb_list, first_nb)
    # for testing the generated notebook output
    file_regression.check(
        nbf.writes(ntbk_output), check_fn=check_nbs, extension=".ipynb"
    )

    check_docutils_xml(mock_document, ntbk, first_nb, file_regression)


def test_jupyter_cache_path(mock_document, get_notebook, file_regression):
    jupyter_cache = mock_document.settings.env.env.outdir + "/.jupyter_cache"
    os.makedirs(jupyter_cache)
    mock_document.settings.env.set_config(["jupyter_cache", jupyter_cache])
    mock_document.settings.env.set_config(["jupyter_execute_notebooks", "cache"])

    first_nb = get_notebook("basic_unrun.ipynb")
    mock_document.settings.env.set_docname("basic_unrun.ipynb")
    nb_list = {str(first_nb.relative_to(first_nb.cwd()))}  # A set

    ntbk, ntbk_output = execute_and_merge(mock_document.settings.env, nb_list, first_nb)
    # for testing the generated notebook output
    file_regression.check(
        nbf.writes(ntbk_output), check_fn=check_nbs, extension=".ipynb"
    )

    check_docutils_xml(mock_document, ntbk, first_nb, file_regression)

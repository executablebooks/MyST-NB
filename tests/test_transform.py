import pytest

from myst_nb.transform import CellOutputsToNodes


@pytest.mark.sphinx_params("basic_run.ipynb", conf={"jupyter_execute_notebooks": "off"})
def test_basic_run(sphinx_run, file_regression):
    sphinx_run.build()
    assert sphinx_run.warnings() == ""
    document = sphinx_run.get_doctree()
    transform = CellOutputsToNodes(document)
    transform.apply()
    file_regression.check(document.pformat(), extension=".xml")


@pytest.mark.sphinx_params(
    "complex_outputs.ipynb", conf={"jupyter_execute_notebooks": "off"}
)
def test_complex_outputs(sphinx_run, file_regression):
    sphinx_run.build()
    assert sphinx_run.warnings() == ""
    document = sphinx_run.get_doctree()
    transform = CellOutputsToNodes(document)
    transform.apply()
    file_regression.check(document.pformat().replace(".jpeg", ".jpg"), extension=".xml")


@pytest.mark.sphinx_params(
    "complex_outputs.ipynb",
    conf={"jupyter_execute_notebooks": "off"},
    buildername="latex",
)
def test_complex_outputs_latex(sphinx_run, file_regression):
    sphinx_run.build()
    assert sphinx_run.warnings() == ""
    document = sphinx_run.get_doctree()
    transform = CellOutputsToNodes(document)
    transform.apply()
    file_regression.check(document.pformat().replace(".jpeg", ".jpg"), extension=".xml")

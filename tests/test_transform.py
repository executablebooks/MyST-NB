import pytest

from myst_nb.transform import CellOutputsToNodes


@pytest.mark.nb_params(nb="basic_run.ipynb", conf={"jupyter_execute_notebooks": "off"})
def test_basic_run(nb_run, file_regression):
    nb_run.build()
    assert nb_run.warnings() == ""
    document = nb_run.get_doctree()
    transform = CellOutputsToNodes(document)
    transform.apply()
    file_regression.check(document.pformat(), extension=".xml")


@pytest.mark.nb_params(
    nb="complex_outputs.ipynb", conf={"jupyter_execute_notebooks": "off"}
)
def test_complex_outputs(nb_run, file_regression):
    nb_run.build()
    assert nb_run.warnings() == ""
    document = nb_run.get_doctree()
    transform = CellOutputsToNodes(document)
    transform.apply()
    file_regression.check(document.pformat().replace(".jpeg", ".jpg"), extension=".xml")

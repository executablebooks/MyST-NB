from myst_nb.parser import NotebookParser
from myst_nb.transform import CellOutputsToNodes


def test_basic_run(mock_document, get_notebook, file_regression):
    parser = NotebookParser()
    parser.parse(get_notebook("basic_run.ipynb").read_text(), mock_document)
    transform = CellOutputsToNodes(mock_document)
    transform.apply()
    file_regression.check(mock_document.pformat(), extension=".xml")


def test_complex_outputs(mock_document, get_notebook, file_regression):
    parser = NotebookParser()
    parser.parse(get_notebook("complex_outputs.ipynb").read_text(), mock_document)
    transform = CellOutputsToNodes(mock_document)
    transform.apply()
    file_regression.check(mock_document.pformat(), extension=".xml")

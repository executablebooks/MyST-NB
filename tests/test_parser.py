from myst_nb.parser import NotebookParser


def test_basic_run(new_document_in_temp, get_notebook, file_regression):
    parser = NotebookParser()
    parser.parse(get_notebook("basic_run.ipynb").read_text(), new_document_in_temp)
    file_regression.check(new_document_in_temp.pformat(), extension=".xml")


def test_complex_outputs(new_document_in_temp, get_notebook, file_regression):
    parser = NotebookParser()
    parser.parse(
        get_notebook("complex_outputs.ipynb").read_text(), new_document_in_temp
    )
    file_regression.check(new_document_in_temp.pformat(), extension=".xml")

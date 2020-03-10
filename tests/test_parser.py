from myst_nb.parser import NotebookParser


def test_basic_run(new_document_in_temp, get_notebook, file_regression):
    parser = NotebookParser()
    parser.parse(get_notebook("basic_run.ipynb").read_text(), new_document_in_temp)
    file_regression.check(new_document_in_temp.pformat(), extension=".xml")
    filenames = [
        p.name for p in new_document_in_temp.settings.env.app.srcdir.glob("**/*")
    ]
    assert filenames == ["nb.ipynb", "nb.py"]


def test_complex_outputs(new_document_in_temp, get_notebook, file_regression):
    parser = NotebookParser()
    parser.parse(
        get_notebook("complex_outputs.ipynb").read_text(), new_document_in_temp
    )
    file_regression.check(new_document_in_temp.pformat(), extension=".xml")
    filenames = [
        p.name.replace(".jpeg", ".jpg") for p in new_document_in_temp.settings.env.app.srcdir.glob("**/*")
    ]
    assert filenames == [
        "nb.ipynb",
        "nb.py",
        "nb_13_0.jpg",
        "nb_17_0.pdf",
        "nb_17_0.svg",
        "nb_24_0.png",
    ]

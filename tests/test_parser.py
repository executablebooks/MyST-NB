from myst_nb.parser import NotebookParser


def test_basic_run(mock_document, get_notebook, file_regression):
    parser = NotebookParser()
    parser.parse(get_notebook("basic_run.ipynb").read_text(), mock_document)
    file_regression.check(mock_document.pformat(), extension=".xml")
    filenames = {
        p.name for p in mock_document.settings.env.app.outdir.parent.glob("**/*")
    }
    assert filenames == {"nb.py", "nb.ipynb", "source", "jupyter_execute"}


def test_complex_outputs(mock_document, get_notebook, file_regression):
    parser = NotebookParser()
    parser.parse(get_notebook("complex_outputs.ipynb").read_text(), mock_document)
    file_regression.check(mock_document.pformat(), extension=".xml")
    filenames = {
        p.name.replace(".jpeg", ".jpg")
        for p in mock_document.settings.env.app.outdir.parent.glob("**/*")
    }
    assert filenames == {
        "source",
        "jupyter_execute",
        "nb.ipynb",
        "nb.py",
        "nb_13_0.jpg",
        "nb_17_0.pdf",
        "nb_17_0.svg",
        "nb_24_0.png",
    }

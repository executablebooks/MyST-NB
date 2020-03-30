import pytest


@pytest.mark.nb_params(nb="basic_run.ipynb", conf={"jupyter_execute_notebooks": "off"})
def test_basic_run(nb_run, file_regression):
    nb_run.build()
    # print(nb_run.status())
    assert nb_run.warnings() == ""
    assert nb_run.app.env.metadata == {"basic_run": {"test_name": "notebook1"}}
    file_regression.check(nb_run.get_doctree().pformat(), extension=".xml")

    filenames = {
        p for p in (nb_run.app.srcdir / "_build" / "jupyter_execute").listdir()
    }
    assert filenames == {"basic_run.py", "basic_run.ipynb"}


@pytest.mark.nb_params(
    nb="complex_outputs.ipynb", conf={"jupyter_execute_notebooks": "off"}
)
def test_complex_outputs(nb_run, file_regression):
    nb_run.build()
    # print(nb_run.status())
    assert nb_run.warnings() == ""
    assert nb_run.app.env.metadata == {
        "complex_outputs": {"celltoolbar": "Edit Metadata", "hide_input": "False"}
    }
    file_regression.check(nb_run.get_doctree().pformat(), extension=".xml")

    filenames = {
        p.replace(".jpeg", ".jpg")
        for p in (nb_run.app.srcdir / "_build" / "jupyter_execute").listdir()
    }
    print(filenames)
    assert filenames == {
        "complex_outputs_17_0.svg",
        "complex_outputs.ipynb",
        "complex_outputs_17_0.pdf",
        "complex_outputs.py",
        "complex_outputs_24_0.png",
        "complex_outputs_13_0.jpg",
    }

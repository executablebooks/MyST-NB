import pytest


@pytest.mark.sphinx_params("basic_run.ipynb", conf={"jupyter_execute_notebooks": "off"})
def test_basic_run(sphinx_run, file_regression):
    sphinx_run.build()
    # print(sphinx_run.status())
    assert sphinx_run.warnings() == ""
    assert sphinx_run.app.env.metadata == {"basic_run": {"test_name": "notebook1"}}
    file_regression.check(sphinx_run.get_doctree().pformat(), extension=".xml")

    filenames = {
        p for p in (sphinx_run.app.srcdir / "_build" / "jupyter_execute").listdir()
    }
    assert filenames == {"basic_run.py", "basic_run.ipynb"}


@pytest.mark.sphinx_params(
    "complex_outputs.ipynb", conf={"jupyter_execute_notebooks": "off"}
)
def test_complex_outputs(sphinx_run, file_regression):
    sphinx_run.build()
    # print(sphinx_run.status())
    assert sphinx_run.warnings() == ""
    assert sphinx_run.app.env.metadata == {
        "complex_outputs": {"celltoolbar": "Edit Metadata", "hide_input": "False"}
    }
    file_regression.check(sphinx_run.get_doctree().pformat(), extension=".xml")

    filenames = {
        p.replace(".jpeg", ".jpg")
        for p in (sphinx_run.app.srcdir / "_build" / "jupyter_execute").listdir()
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


@pytest.mark.sphinx_params(
    "toctree.ipynb",
    "basic_run.ipynb",
    conf={"jupyter_execute_notebooks": "off"},
    # working_dir="/Users/cjs14/GitHub/MyST-NB-actual/outputs"
)
def test_toctree_in_ipynb(sphinx_run):
    sphinx_run.build()
    print(sphinx_run.status())
    assert sphinx_run.warnings() == ""

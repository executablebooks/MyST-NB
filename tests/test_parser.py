import pytest


@pytest.mark.sphinx_params("basic_run.ipynb", conf={"jupyter_execute_notebooks": "off"})
def test_basic_run(sphinx_run, file_regression):
    sphinx_run.build()
    # print(sphinx_run.status())
    assert sphinx_run.warnings() == ""
    assert set(sphinx_run.app.env.metadata["basic_run"].keys()) == {
        "test_name",
        "kernelspec",
        "language_info",
    }
    assert sphinx_run.app.env.metadata["basic_run"]["test_name"] == "notebook1"
    assert (
        sphinx_run.app.env.metadata["basic_run"]["kernelspec"]
        == '{"display_name": "Python 3", "language": "python", "name": "python3"}'
    )
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
    assert sphinx_run.warnings() == ""

    assert set(sphinx_run.app.env.metadata["complex_outputs"].keys()) == {
        "ipub",
        "hide_input",
        "nav_menu",
        "celltoolbar",
        "latex_envs",
        "kernelspec",
        "language_info",
        "jupytext",
        "toc",
        "varInspector",
    }
    assert (
        sphinx_run.app.env.metadata["complex_outputs"]["celltoolbar"] == "Edit Metadata"
    )
    assert sphinx_run.app.env.metadata["complex_outputs"]["hide_input"] == "False"
    assert (
        sphinx_run.app.env.metadata["complex_outputs"]["kernelspec"]
        == '{"display_name": "Python 3", "language": "python", "name": "python3"}'
    )
    file_regression.check(sphinx_run.get_doctree().pformat(), extension=".xml")

    filenames = {
        p.replace(".jpeg", ".jpg")
        for p in (sphinx_run.app.srcdir / "_build" / "jupyter_execute").listdir()
    }
    print(filenames)
    assert filenames == {
        "complex_outputs_17_0.png",
        "complex_outputs.ipynb",
        "complex_outputs.py",
        "complex_outputs_24_0.png",
        "complex_outputs_13_0.jpg",
    }


@pytest.mark.sphinx_params(
    "latex_build/index.ipynb",
    "latex_build/other.ipynb",
    conf={"jupyter_execute_notebooks": "off"},
    buildername="latex",
    # working_dir="/Users/cjs14/GitHub/MyST-NB-actual/outputs"
)
def test_toctree_in_ipynb(sphinx_run, file_regression):
    sphinx_run.build()
    print(sphinx_run.status())
    print(sphinx_run.warnings())
    file_regression.check(sphinx_run.get_doctree(1).pformat(), extension=".xml")
    assert sphinx_run.warnings() == ""


@pytest.mark.sphinx_params(
    "complex_markdown_displays.ipynb", conf={"jupyter_execute_notebooks": "off"}
)
def test_complex_markdown(sphinx_run, file_regression, check_nbs):
    sphinx_run.build()
    # print(sphinx_run.status())
    assert sphinx_run.warnings() == ""
    file_regression.check(sphinx_run.get_nb(), check_fn=check_nbs, extension=".ipynb")
    file_regression.check(sphinx_run.get_doctree().pformat(), extension=".xml")

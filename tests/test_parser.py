"""Test parsing of already executed notebooks."""
import pytest


@pytest.mark.sphinx_params("basic_run.ipynb", conf={"nb_execution_mode": "off"})
def test_basic_run(sphinx_run, file_regression):
    sphinx_run.build()
    # print(sphinx_run.status())
    assert sphinx_run.warnings() == ""
    assert set(sphinx_run.env.metadata["basic_run"].keys()) == {
        "test_name",
        "wordcount",
    }
    assert set(sphinx_run.env.nb_metadata["basic_run"].keys()) == {
        "kernelspec",
        "language_info",
    }
    assert sphinx_run.env.metadata["basic_run"]["test_name"] == "notebook1"
    assert sphinx_run.env.nb_metadata["basic_run"]["kernelspec"] == {
        "display_name": "Python 3",
        "language": "python",
        "name": "python3",
    }
    file_regression.check(
        sphinx_run.get_doctree().pformat(), extension=".xml", encoding="utf8"
    )

    filenames = {
        p for p in (sphinx_run.app.srcdir / "_build" / "jupyter_execute").listdir()
    }
    assert filenames == {"basic_run.ipynb"}


@pytest.mark.sphinx_params("complex_outputs.ipynb", conf={"nb_execution_mode": "off"})
def test_complex_outputs(sphinx_run, file_regression):
    sphinx_run.build()
    assert sphinx_run.warnings() == ""

    assert set(sphinx_run.env.metadata["complex_outputs"].keys()) == {
        "ipub",
        "hide_input",
        "nav_menu",
        "celltoolbar",
        "latex_envs",
        "jupytext",
        "toc",
        "varInspector",
        "wordcount",
    }
    assert set(sphinx_run.env.nb_metadata["complex_outputs"].keys()) == {
        "kernelspec",
        "language_info",
    }
    assert sphinx_run.env.metadata["complex_outputs"]["celltoolbar"] == "Edit Metadata"
    assert sphinx_run.env.metadata["complex_outputs"]["hide_input"] == "False"
    assert sphinx_run.env.nb_metadata["complex_outputs"]["kernelspec"] == {
        "display_name": "Python 3",
        "language": "python",
        "name": "python3",
    }
    file_regression.check(
        sphinx_run.get_doctree().pformat(), extension=".xml", encoding="utf8"
    )

    filenames = {
        p.replace(".jpeg", ".jpg")
        for p in (sphinx_run.app.srcdir / "_build" / "jupyter_execute").listdir()
    }
    # print(filenames)
    assert filenames == {
        "16832f45917c1c9862c50f0948f64a498402d6ccde1f3a291da17f240797b160.png",
        "a4c9580c74dacf6f3316a3bd2e2a347933aa4463834dcf1bb8f20b4fcb476ae1.jpg",
        "8c43e5c8cccf697754876b7fec1b0a9b731d7900bb585e775a5fa326b4de8c5a.png",
        "complex_outputs.ipynb",
    }


@pytest.mark.sphinx_params(
    "latex_build/index.ipynb",
    "latex_build/other.ipynb",
    conf={"nb_execution_mode": "off"},
    buildername="latex",
)
def test_toctree_in_ipynb(sphinx_run, file_regression):
    sphinx_run.build()
    print(sphinx_run.status())
    print(sphinx_run.warnings())
    file_regression.check(
        sphinx_run.get_doctree("latex_build/other").pformat(), extension=".xml"
    )
    assert sphinx_run.warnings() == ""

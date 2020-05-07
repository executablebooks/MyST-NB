import pytest


@pytest.mark.sphinx_params(
    "basic_unrun.md",
    conf={"jupyter_execute_notebooks": "cache", "source_suffix": {".md": "myst-nb"}},
)
def test_basic_run(sphinx_run, file_regression, check_nbs):
    sphinx_run.build()
    # print(sphinx_run.status())
    assert sphinx_run.warnings() == ""
    assert set(sphinx_run.app.env.metadata["basic_unrun"].keys()) == {
        "jupytext",
        "kernelspec",
        "author",
        "source_map",
        "language_info",
    }
    assert sphinx_run.app.env.metadata["basic_unrun"]["author"] == "Chris"
    assert (
        sphinx_run.app.env.metadata["basic_unrun"]["kernelspec"]
        == '{"display_name": "Python 3", "language": "python", "name": "python3"}'
    )
    file_regression.check(sphinx_run.get_nb(), check_fn=check_nbs, extension=".ipynb")
    file_regression.check(sphinx_run.get_doctree().pformat(), extension=".xml")

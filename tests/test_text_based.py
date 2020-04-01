import pytest


@pytest.mark.nb_params(
    nb="basic_unrun.md",
    conf={"jupyter_execute_notebooks": "cache", "source_suffix": {".md": "myst-nb"}},
)
def test_basic_run(nb_run, file_regression, check_nbs):
    nb_run.build()
    # print(nb_run.status())
    assert nb_run.warnings() == ""
    assert nb_run.app.env.metadata == {"basic_unrun": {"author": "Chris"}}
    file_regression.check(nb_run.get_nb(), check_fn=check_nbs, extension=".ipynb")
    file_regression.check(nb_run.get_doctree().pformat(), extension=".xml")

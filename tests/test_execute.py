import pytest


@pytest.mark.nb_params(
    nb="basic_unrun.ipynb", conf={"jupyter_execute_notebooks": "cache"}
)
def test_basic_unrun(nb_run, file_regression, check_nbs):
    """The outputs should be populated."""
    nb_run.build()
    assert nb_run.warnings() == ""
    assert "test_name" in nb_run.app.env.metadata["basic_unrun"]
    file_regression.check(nb_run.get_nb(), check_fn=check_nbs, extension=".ipynb")
    file_regression.check(nb_run.get_doctree().pformat(), extension=".xml")


@pytest.mark.nb_params(
    nb="basic_unrun.ipynb", conf={"jupyter_execute_notebooks": "cache"}
)
def test_rebuild_cache(nb_run):
    """The notebook should only be executed once."""
    nb_run.build()
    assert "Executing" in nb_run.status(), nb_run.status()
    nb_run.invalidate_notebook()
    nb_run.build()
    assert "Executing" not in nb_run.status(), nb_run.status()


@pytest.mark.nb_params(
    nb="basic_unrun.ipynb", conf={"jupyter_execute_notebooks": "force"}
)
def test_rebuild_force(nb_run):
    """The notebook should be executed twice."""
    nb_run.build()
    assert "Executing" in nb_run.status(), nb_run.status()
    nb_run.invalidate_notebook()
    nb_run.build()
    assert "Executing" in nb_run.status(), nb_run.status()


@pytest.mark.nb_params(
    nb="basic_unrun.ipynb",
    conf={
        "jupyter_execute_notebooks": "cache",
        "execution_excludepatterns": ["basic_*"],
    },
)
def test_exclude_path(nb_run, file_regression):
    """The notebook should not be executed."""
    nb_run.build()
    assert len(nb_run.app.env.excluded_nb_exec_paths) == 1
    assert "Executing" not in nb_run.status(), nb_run.status()
    file_regression.check(nb_run.get_doctree().pformat(), extension=".xml")


@pytest.mark.nb_params(
    nb="basic_failing.ipynb", conf={"jupyter_execute_notebooks": "cache"}
)
def test_basic_failing(nb_run, file_regression, check_nbs):
    nb_run.build()
    # print(nb_run.status())
    assert "Execution Failed" in nb_run.warnings()
    assert (
        "Couldn't find cache key for notebook file source/basic_failing.ipynb"
        in nb_run.warnings()
    )
    file_regression.check(nb_run.get_nb(), check_fn=check_nbs, extension=".ipynb")
    file_regression.check(nb_run.get_doctree().pformat(), extension=".xml")
    nb_run.get_report_file()


@pytest.mark.nb_params(
    nb="basic_unrun.ipynb", conf={"jupyter_execute_notebooks": "auto"}
)
def test_basic_unrun_nbclient(nb_run, file_regression, check_nbs):
    nb_run.build()
    # print(nb_run.status())
    assert nb_run.warnings() == ""
    assert "test_name" in nb_run.app.env.metadata["basic_unrun"]
    file_regression.check(nb_run.get_nb(), check_fn=check_nbs, extension=".ipynb")
    file_regression.check(nb_run.get_doctree().pformat(), extension=".xml")


@pytest.mark.nb_params(
    nb="basic_unrun.ipynb", conf={"jupyter_execute_notebooks": "force"}
)
def test_outputs_present(nb_run, file_regression, check_nbs):
    nb_run.build()
    # print(nb_run.status())
    assert nb_run.warnings() == ""
    assert "test_name" in nb_run.app.env.metadata["basic_unrun"]
    file_regression.check(nb_run.get_nb(), check_fn=check_nbs, extension=".ipynb")
    file_regression.check(nb_run.get_doctree().pformat(), extension=".xml")


@pytest.mark.nb_params(
    nb="complex_outputs_unrun.ipynb", conf={"jupyter_execute_notebooks": "cache"}
)
def test_complex_outputs_unrun(nb_run, file_regression, check_nbs):
    nb_run.build()
    # print(nb_run.status())
    assert nb_run.warnings() == ""
    file_regression.check(nb_run.get_nb(), check_fn=check_nbs, extension=".ipynb")
    file_regression.check(nb_run.get_doctree().pformat(), extension=".xml")


@pytest.mark.nb_params(
    nb="complex_outputs_unrun.ipynb", conf={"jupyter_execute_notebooks": "auto"}
)
def test_complex_outputs_unrun_nbclient(nb_run, file_regression, check_nbs):
    nb_run.build()
    # print(nb_run.status())
    assert nb_run.warnings() == ""
    file_regression.check(nb_run.get_nb(), check_fn=check_nbs, extension=".ipynb")
    file_regression.check(nb_run.get_doctree().pformat(), extension=".xml")


@pytest.mark.nb_params(
    nb="basic_unrun.ipynb", conf={"jupyter_execute_notebooks": "off"}
)
def test_no_execute(nb_run, file_regression, check_nbs):
    nb_run.build()
    # print(nb_run.status())
    assert nb_run.warnings() == ""
    file_regression.check(nb_run.get_nb(), check_fn=check_nbs, extension=".ipynb")
    file_regression.check(nb_run.get_doctree().pformat(), extension=".xml")


@pytest.mark.nb_params(
    nb="basic_unrun.ipynb", conf={"jupyter_execute_notebooks": "cache"}
)
def test_jupyter_cache_path(nb_run, file_regression, check_nbs):
    nb_run.build()
    assert "Execution Succeeded" in nb_run.status()
    assert nb_run.warnings() == ""
    file_regression.check(nb_run.get_nb(), check_fn=check_nbs, extension=".ipynb")
    file_regression.check(nb_run.get_doctree().pformat(), extension=".xml")

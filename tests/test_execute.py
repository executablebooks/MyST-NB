import pytest


@pytest.mark.sphinx_params(
    "basic_unrun.ipynb", conf={"jupyter_execute_notebooks": "auto"}
)
def test_basic_unrun_auto(sphinx_run, file_regression, check_nbs):
    sphinx_run.build()
    # print(sphinx_run.status())
    assert sphinx_run.warnings() == ""
    assert "test_name" in sphinx_run.app.env.metadata["basic_unrun"]
    file_regression.check(sphinx_run.get_nb(), check_fn=check_nbs, extension=".ipynb")
    file_regression.check(sphinx_run.get_doctree().pformat(), extension=".xml")

    # Test execution statistics, should look like:
    # {'basic_unrun': {'mtime': '2020-08-20T03:32:27.061454', 'runtime': 0.964572671,
    #                  'method': 'auto', 'succeeded': True}}
    assert sphinx_run.env.nb_execution_data_changed is True
    assert "basic_unrun" in sphinx_run.env.nb_execution_data
    assert sphinx_run.env.nb_execution_data["basic_unrun"]["method"] == "auto"
    assert sphinx_run.env.nb_execution_data["basic_unrun"]["succeeded"] is True


@pytest.mark.sphinx_params(
    "basic_unrun.ipynb", conf={"jupyter_execute_notebooks": "cache"}
)
def test_basic_unrun_cache(sphinx_run, file_regression, check_nbs):
    """The outputs should be populated."""
    sphinx_run.build()
    assert sphinx_run.warnings() == ""
    assert "test_name" in sphinx_run.app.env.metadata["basic_unrun"]
    file_regression.check(sphinx_run.get_nb(), check_fn=check_nbs, extension=".ipynb")
    file_regression.check(sphinx_run.get_doctree().pformat(), extension=".xml")

    # Test execution statistics, should look like:
    # {'basic_unrun': {'mtime': '2020-08-20T03:32:27.061454', 'runtime': 0.964572671,
    #                  'method': 'cache', 'succeeded': True}}
    assert sphinx_run.env.nb_execution_data_changed is True
    assert "basic_unrun" in sphinx_run.env.nb_execution_data
    assert sphinx_run.env.nb_execution_data["basic_unrun"]["method"] == "cache"
    assert sphinx_run.env.nb_execution_data["basic_unrun"]["succeeded"] is True


@pytest.mark.sphinx_params(
    "basic_unrun.ipynb", conf={"jupyter_execute_notebooks": "cache"}
)
def test_rebuild_cache(sphinx_run):
    """The notebook should only be executed once."""
    sphinx_run.build()
    assert "Executing" in sphinx_run.status(), sphinx_run.status()
    sphinx_run.invalidate_files()
    sphinx_run.build()
    assert "Executing" not in sphinx_run.status(), sphinx_run.status()


@pytest.mark.sphinx_params(
    "basic_unrun.ipynb", conf={"jupyter_execute_notebooks": "force"}
)
def test_rebuild_force(sphinx_run):
    """The notebook should be executed twice."""
    sphinx_run.build()
    assert "Executing" in sphinx_run.status(), sphinx_run.status()
    sphinx_run.invalidate_files()
    sphinx_run.build()
    assert "Executing" in sphinx_run.status(), sphinx_run.status()


@pytest.mark.sphinx_params(
    "basic_unrun.ipynb",
    conf={
        "jupyter_execute_notebooks": "cache",
        "execution_excludepatterns": ["basic_*"],
    },
)
def test_exclude_path(sphinx_run, file_regression):
    """The notebook should not be executed."""
    sphinx_run.build()
    assert len(sphinx_run.app.env.nb_excluded_exec_paths) == 1
    assert "Executing" not in sphinx_run.status(), sphinx_run.status()
    file_regression.check(sphinx_run.get_doctree().pformat(), extension=".xml")


@pytest.mark.sphinx_params(
    "basic_failing.ipynb", conf={"jupyter_execute_notebooks": "cache"}
)
def test_basic_failing_cache(sphinx_run, file_regression, check_nbs):
    sphinx_run.build()
    # print(sphinx_run.status())
    assert "Execution Failed" in sphinx_run.warnings()
    assert (
        "Couldn't find cache key for notebook file source/basic_failing.ipynb"
        in sphinx_run.warnings()
    )
    file_regression.check(sphinx_run.get_nb(), check_fn=check_nbs, extension=".ipynb")
    file_regression.check(sphinx_run.get_doctree().pformat(), extension=".xml")
    sphinx_run.get_report_file()

    assert "basic_failing" in sphinx_run.env.nb_execution_data
    assert sphinx_run.env.nb_execution_data["basic_failing"]["method"] == "cache"
    assert sphinx_run.env.nb_execution_data["basic_failing"]["succeeded"] is False
    assert "error_log" in sphinx_run.env.nb_execution_data["basic_failing"]


@pytest.mark.sphinx_params(
    "basic_failing.ipynb", conf={"jupyter_execute_notebooks": "auto"}
)
def test_basic_failing_auto(sphinx_run, file_regression, check_nbs):
    sphinx_run.build()
    # print(sphinx_run.status())
    assert "Execution Failed" in sphinx_run.warnings()
    assert "Execution Failed with traceback saved in" in sphinx_run.warnings()
    file_regression.check(sphinx_run.get_nb(), check_fn=check_nbs, extension=".ipynb")
    file_regression.check(sphinx_run.get_doctree().pformat(), extension=".xml")
    sphinx_run.get_report_file()

    assert "basic_failing" in sphinx_run.env.nb_execution_data
    assert sphinx_run.env.nb_execution_data["basic_failing"]["method"] == "auto"
    assert sphinx_run.env.nb_execution_data["basic_failing"]["succeeded"] is False
    assert "error_log" in sphinx_run.env.nb_execution_data["basic_failing"]


@pytest.mark.sphinx_params(
    "basic_failing.ipynb",
    conf={"jupyter_execute_notebooks": "cache", "execution_allow_errors": True},
)
def test_allow_errors_cache(sphinx_run, file_regression, check_nbs):
    sphinx_run.build()
    # print(sphinx_run.status())
    assert not sphinx_run.warnings()
    file_regression.check(sphinx_run.get_nb(), check_fn=check_nbs, extension=".ipynb")
    file_regression.check(sphinx_run.get_doctree().pformat(), extension=".xml")


@pytest.mark.sphinx_params(
    "basic_failing.ipynb",
    conf={"jupyter_execute_notebooks": "auto", "execution_allow_errors": True},
)
def test_allow_errors_auto(sphinx_run, file_regression, check_nbs):
    sphinx_run.build()
    # print(sphinx_run.status())
    assert not sphinx_run.warnings()
    file_regression.check(sphinx_run.get_nb(), check_fn=check_nbs, extension=".ipynb")
    file_regression.check(sphinx_run.get_doctree().pformat(), extension=".xml")


@pytest.mark.sphinx_params(
    "basic_unrun.ipynb", conf={"jupyter_execute_notebooks": "force"}
)
def test_outputs_present(sphinx_run, file_regression, check_nbs):
    sphinx_run.build()
    # print(sphinx_run.status())
    assert sphinx_run.warnings() == ""
    assert "test_name" in sphinx_run.app.env.metadata["basic_unrun"]
    file_regression.check(sphinx_run.get_nb(), check_fn=check_nbs, extension=".ipynb")
    file_regression.check(sphinx_run.get_doctree().pformat(), extension=".xml")


@pytest.mark.sphinx_params(
    "complex_outputs_unrun.ipynb", conf={"jupyter_execute_notebooks": "cache"}
)
def test_complex_outputs_unrun_cache(sphinx_run, file_regression, check_nbs):
    sphinx_run.build()
    # print(sphinx_run.status())
    assert sphinx_run.warnings() == ""
    file_regression.check(sphinx_run.get_nb(), check_fn=check_nbs, extension=".ipynb")
    file_regression.check(sphinx_run.get_doctree().pformat(), extension=".xml")

    # Widget view and widget state should make it into the HTML
    html = sphinx_run.get_html()
    assert '<script type="application/vnd.jupyter.widget-view+json">' in html
    assert '<script type="application/vnd.jupyter.widget-state+json">' in html


@pytest.mark.sphinx_params(
    "complex_outputs_unrun.ipynb", conf={"jupyter_execute_notebooks": "auto"}
)
def test_complex_outputs_unrun_auto(sphinx_run, file_regression, check_nbs):
    sphinx_run.build()
    # print(sphinx_run.status())
    assert sphinx_run.warnings() == ""
    file_regression.check(sphinx_run.get_nb(), check_fn=check_nbs, extension=".ipynb")
    file_regression.check(sphinx_run.get_doctree().pformat(), extension=".xml")

    # Widget view and widget state should make it into the HTML
    html = sphinx_run.get_html()
    assert '<script type="application/vnd.jupyter.widget-view+json">' in html
    assert '<script type="application/vnd.jupyter.widget-state+json">' in html


@pytest.mark.sphinx_params(
    "basic_unrun.ipynb", conf={"jupyter_execute_notebooks": "off"}
)
def test_no_execute(sphinx_run, file_regression, check_nbs):
    sphinx_run.build()
    # print(sphinx_run.status())
    assert sphinx_run.warnings() == ""
    file_regression.check(sphinx_run.get_nb(), check_fn=check_nbs, extension=".ipynb")
    file_regression.check(sphinx_run.get_doctree().pformat(), extension=".xml")


@pytest.mark.sphinx_params(
    "basic_unrun.ipynb", conf={"jupyter_execute_notebooks": "cache"}
)
def test_jupyter_cache_path(sphinx_run, file_regression, check_nbs):
    sphinx_run.build()
    assert "Execution Succeeded" in sphinx_run.status()
    assert sphinx_run.warnings() == ""
    file_regression.check(sphinx_run.get_nb(), check_fn=check_nbs, extension=".ipynb")
    file_regression.check(sphinx_run.get_doctree().pformat(), extension=".xml")


# Testing relative paths within the notebook
@pytest.mark.sphinx_params(
    "basic_relative.ipynb", conf={"jupyter_execute_notebooks": "cache"}
)
def test_relative_path_cache(sphinx_run, file_regression, check_nbs):
    sphinx_run.build()
    assert "Execution Succeeded" in sphinx_run.status(), sphinx_run.status()


@pytest.mark.sphinx_params(
    "basic_relative.ipynb", conf={"jupyter_execute_notebooks": "force"}
)
def test_relative_path_force(sphinx_run, file_regression, check_nbs):
    sphinx_run.build()
    assert "Execution Succeeded" in sphinx_run.status(), sphinx_run.status()


# Execution timeout configuration
@pytest.mark.sphinx_params(
    "complex_outputs_unrun.ipynb",
    conf={"jupyter_execute_notebooks": "cache", "execution_timeout": 1},
)
def test_execution_timeout(sphinx_run, file_regression, check_nbs):
    """ execution should fail given the low timeout value"""
    sphinx_run.build()
    # print(sphinx_run.status())
    assert "execution failed" in sphinx_run.warnings()


@pytest.mark.sphinx_params(
    "complex_outputs_unrun_timeout.ipynb",
    conf={"jupyter_execute_notebooks": "cache", "execution_timeout": 60},
)
def test_execution_metadata_timeout(sphinx_run, file_regression, check_nbs):
    """ notebook timeout metadata has higher preference then execution_timeout config"""
    sphinx_run.build()
    assert "execution failed" in sphinx_run.warnings()


@pytest.mark.sphinx_params(
    "nb_exec_table.md", conf={"jupyter_execute_notebooks": "auto"},
)
def test_nb_exec_table(sphinx_run, file_regression, check_nbs):
    """Test that the table gets output into the HTML,
    including a row for the executed notebook.
    """
    sphinx_run.build()
    assert not sphinx_run.warnings()
    file_regression.check(sphinx_run.get_doctree().pformat(), extension=".xml")
    assert '<tr class="row-even"><td><p>nb_exec_table</p></td>' in sphinx_run.get_html()


@pytest.mark.sphinx_params(
    "custom-formats.Rmd",
    conf={
        "jupyter_execute_notebooks": "auto",
        "nb_custom_formats": {".Rmd": ["jupytext.reads", {"fmt": "Rmd"}]},
    },
)
def test_custom_convert_auto(sphinx_run, file_regression, check_nbs):
    sphinx_run.build()
    # print(sphinx_run.status())
    assert sphinx_run.warnings() == ""

    file_regression.check(sphinx_run.get_nb(), check_fn=check_nbs, extension=".ipynb")
    file_regression.check(sphinx_run.get_doctree().pformat(), extension=".xml")

    assert sphinx_run.env.nb_execution_data_changed is True
    assert "custom-formats" in sphinx_run.env.nb_execution_data
    assert sphinx_run.env.nb_execution_data["custom-formats"]["method"] == "auto"
    assert sphinx_run.env.nb_execution_data["custom-formats"]["succeeded"] is True


@pytest.mark.sphinx_params(
    "custom-formats.Rmd",
    conf={
        "jupyter_execute_notebooks": "cache",
        "nb_custom_formats": {".Rmd": ["jupytext.reads", {"fmt": "Rmd"}]},
    },
)
def test_custom_convert_cache(sphinx_run, file_regression, check_nbs):
    """The outputs should be populated."""
    sphinx_run.build()
    assert sphinx_run.warnings() == ""
    file_regression.check(sphinx_run.get_nb(), check_fn=check_nbs, extension=".ipynb")
    file_regression.check(sphinx_run.get_doctree().pformat(), extension=".xml")

    assert sphinx_run.env.nb_execution_data_changed is True
    assert "custom-formats" in sphinx_run.env.nb_execution_data
    assert sphinx_run.env.nb_execution_data["custom-formats"]["method"] == "cache"
    assert sphinx_run.env.nb_execution_data["custom-formats"]["succeeded"] is True

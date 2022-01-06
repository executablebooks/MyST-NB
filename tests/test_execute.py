"""Test sphinx builds which execute notebooks."""
import pytest

from myst_nb.sphinx_ import NbMetadataCollector


def regress_nb_doc(file_regression, sphinx_run, check_nbs):
    try:
        file_regression.check(
            sphinx_run.get_nb(), check_fn=check_nbs, extension=".ipynb", encoding="utf8"
        )
    finally:
        doctree = sphinx_run.get_doctree()
        file_regression.check(doctree.pformat(), extension=".xml", encoding="utf8")


@pytest.mark.sphinx_params("basic_unrun.ipynb", conf={"nb_execution_mode": "auto"})
def test_basic_unrun_auto(sphinx_run, file_regression, check_nbs):
    sphinx_run.build()
    # print(sphinx_run.status())
    assert sphinx_run.warnings() == ""
    assert "test_name" in sphinx_run.app.env.metadata["basic_unrun"]
    regress_nb_doc(file_regression, sphinx_run, check_nbs)

    assert NbMetadataCollector.new_exec_data(sphinx_run.env)
    data = NbMetadataCollector.get_exec_data(sphinx_run.env, "basic_unrun")
    assert data
    assert data["method"] == "auto"
    assert data["succeeded"] is True


@pytest.mark.sphinx_params("basic_unrun.ipynb", conf={"nb_execution_mode": "cache"})
def test_basic_unrun_cache(sphinx_run, file_regression, check_nbs):
    """The outputs should be populated."""
    sphinx_run.build()
    assert sphinx_run.warnings() == ""
    assert "test_name" in sphinx_run.app.env.metadata["basic_unrun"]
    regress_nb_doc(file_regression, sphinx_run, check_nbs)

    assert NbMetadataCollector.new_exec_data(sphinx_run.env)
    data = NbMetadataCollector.get_exec_data(sphinx_run.env, "basic_unrun")
    assert data
    assert data["method"] == "cache"
    assert data["succeeded"] is True


@pytest.mark.sphinx_params("basic_unrun.ipynb", conf={"nb_execution_mode": "cache"})
def test_rebuild_cache(sphinx_run):
    """The notebook should only be executed once."""
    sphinx_run.build()
    assert NbMetadataCollector.new_exec_data(sphinx_run.env)
    sphinx_run.invalidate_files()
    sphinx_run.build()
    assert "Using cached" in sphinx_run.status()


@pytest.mark.sphinx_params("basic_unrun.ipynb", conf={"nb_execution_mode": "force"})
def test_rebuild_force(sphinx_run):
    """The notebook should be executed twice."""
    sphinx_run.build()
    assert NbMetadataCollector.new_exec_data(sphinx_run.env)
    sphinx_run.invalidate_files()
    sphinx_run.build()
    assert NbMetadataCollector.new_exec_data(sphinx_run.env)


@pytest.mark.sphinx_params(
    "basic_unrun.ipynb",
    conf={
        "nb_execution_mode": "cache",
        "nb_execution_excludepatterns": ["basic_*"],
    },
)
def test_exclude_path(sphinx_run, file_regression):
    """The notebook should not be executed."""
    sphinx_run.build()
    assert not NbMetadataCollector.new_exec_data(sphinx_run.env)
    assert "Executing" not in sphinx_run.status(), sphinx_run.status()
    file_regression.check(
        sphinx_run.get_doctree().pformat(), extension=".xml", encoding="utf8"
    )


@pytest.mark.sphinx_params("basic_failing.ipynb", conf={"nb_execution_mode": "cache"})
def test_basic_failing_cache(sphinx_run, file_regression, check_nbs):
    sphinx_run.build()
    # print(sphinx_run.warnings())
    assert "Executing notebook failed" in sphinx_run.warnings()
    regress_nb_doc(file_regression, sphinx_run, check_nbs)

    data = NbMetadataCollector.get_exec_data(sphinx_run.env, "basic_failing")
    assert data
    assert data["method"] == "cache"
    assert data["succeeded"] is False
    sphinx_run.get_report_file()


@pytest.mark.sphinx_params("basic_failing.ipynb", conf={"nb_execution_mode": "auto"})
def test_basic_failing_auto(sphinx_run, file_regression, check_nbs):
    sphinx_run.build()
    assert "Executing notebook failed" in sphinx_run.warnings()
    regress_nb_doc(file_regression, sphinx_run, check_nbs)

    data = NbMetadataCollector.get_exec_data(sphinx_run.env, "basic_failing")
    assert data
    assert data["method"] == "auto"
    assert data["succeeded"] is False
    assert data["traceback"]
    sphinx_run.get_report_file()


@pytest.mark.sphinx_params(
    "basic_failing.ipynb",
    conf={"nb_execution_mode": "cache", "nb_execution_allow_errors": True},
)
def test_allow_errors_cache(sphinx_run, file_regression, check_nbs):
    sphinx_run.build()
    # print(sphinx_run.status())
    assert not sphinx_run.warnings()
    regress_nb_doc(file_regression, sphinx_run, check_nbs)


@pytest.mark.sphinx_params(
    "basic_failing.ipynb",
    conf={"nb_execution_mode": "auto", "nb_execution_allow_errors": True},
)
def test_allow_errors_auto(sphinx_run, file_regression, check_nbs):
    sphinx_run.build()
    # print(sphinx_run.status())
    assert not sphinx_run.warnings()
    regress_nb_doc(file_regression, sphinx_run, check_nbs)


@pytest.mark.sphinx_params("basic_unrun.ipynb", conf={"nb_execution_mode": "force"})
def test_outputs_present(sphinx_run, file_regression, check_nbs):
    sphinx_run.build()
    # print(sphinx_run.status())
    assert sphinx_run.warnings() == ""
    assert "test_name" in sphinx_run.app.env.metadata["basic_unrun"]
    regress_nb_doc(file_regression, sphinx_run, check_nbs)


@pytest.mark.sphinx_params(
    "complex_outputs_unrun.ipynb", conf={"nb_execution_mode": "cache"}
)
def test_complex_outputs_unrun_cache(sphinx_run, file_regression, check_nbs):
    sphinx_run.build()
    # print(sphinx_run.status())
    assert sphinx_run.warnings() == ""
    regress_nb_doc(file_regression, sphinx_run, check_nbs)

    # Widget view and widget state should make it into the HTML
    scripts = sphinx_run.get_html().select("script")
    assert any(
        "application/vnd.jupyter.widget-view+json" in script.get("type", "")
        for script in scripts
    )
    assert any(
        "application/vnd.jupyter.widget-state+json" in script.get("type", "")
        for script in scripts
    )


@pytest.mark.sphinx_params(
    "complex_outputs_unrun.ipynb", conf={"nb_execution_mode": "auto"}
)
def test_complex_outputs_unrun_auto(sphinx_run, file_regression, check_nbs):
    sphinx_run.build()
    # print(sphinx_run.status())
    assert sphinx_run.warnings() == ""
    regress_nb_doc(file_regression, sphinx_run, check_nbs)

    # Widget view and widget state should make it into the HTML
    scripts = sphinx_run.get_html().select("script")
    assert any(
        "application/vnd.jupyter.widget-view+json" in script.get("type", "")
        for script in scripts
    )
    assert any(
        "application/vnd.jupyter.widget-state+json" in script.get("type", "")
        for script in scripts
    )


@pytest.mark.sphinx_params("basic_unrun.ipynb", conf={"nb_execution_mode": "off"})
def test_no_execute(sphinx_run, file_regression, check_nbs):
    sphinx_run.build()
    # print(sphinx_run.status())
    assert sphinx_run.warnings() == ""
    regress_nb_doc(file_regression, sphinx_run, check_nbs)


@pytest.mark.sphinx_params("basic_unrun.ipynb", conf={"nb_execution_mode": "cache"})
def test_jupyter_cache_path(sphinx_run, file_regression, check_nbs):
    sphinx_run.build()
    assert "Cached executed notebook" in sphinx_run.status()
    assert sphinx_run.warnings() == ""
    regress_nb_doc(file_regression, sphinx_run, check_nbs)


# Testing relative paths within the notebook
@pytest.mark.sphinx_params("basic_relative.ipynb", conf={"nb_execution_mode": "cache"})
def test_relative_path_cache(sphinx_run, file_regression, check_nbs):
    sphinx_run.build()
    assert "Execution Failed" not in sphinx_run.status(), sphinx_run.status()


@pytest.mark.sphinx_params("basic_relative.ipynb", conf={"nb_execution_mode": "force"})
def test_relative_path_force(sphinx_run, file_regression, check_nbs):
    sphinx_run.build()
    assert "Execution Failed" not in sphinx_run.status(), sphinx_run.status()


# Execution timeout configuration
@pytest.mark.sphinx_params(
    "sleep_10.ipynb",
    conf={"nb_execution_mode": "cache", "nb_execution_timeout": 1},
)
def test_execution_timeout(sphinx_run, file_regression, check_nbs):
    """execution should fail given the low timeout value"""
    sphinx_run.build()
    # print(sphinx_run.warnings())
    assert "Executing notebook failed" in sphinx_run.warnings()


@pytest.mark.sphinx_params(
    "sleep_10_metadata_timeout.ipynb",
    conf={"nb_execution_mode": "cache", "nb_execution_timeout": 60},
)
def test_execution_metadata_timeout(sphinx_run, file_regression, check_nbs):
    """notebook timeout metadata has higher preference then execution_timeout config"""
    sphinx_run.build()
    # print(sphinx_run.warnings())
    assert "Executing notebook failed" in sphinx_run.warnings()


@pytest.mark.sphinx_params(
    "nb_exec_table.md",
    conf={"nb_execution_mode": "auto"},
)
def test_nb_exec_table(sphinx_run, file_regression, check_nbs):
    """Test that the table gets output into the HTML,
    including a row for the executed notebook.
    """
    sphinx_run.build()
    # print(sphinx_run.status())
    assert not sphinx_run.warnings()
    file_regression.check(
        sphinx_run.get_doctree().pformat(), extension=".xml", encoding="utf8"
    )
    # print(sphinx_run.get_html())
    rows = sphinx_run.get_html().select("table.docutils tr")
    assert any("nb_exec_table" in row.text for row in rows)


@pytest.mark.sphinx_params(
    "custom-formats.Rmd",
    conf={
        "nb_execution_mode": "auto",
        "nb_custom_formats": {".Rmd": ["jupytext.reads", {"fmt": "Rmd"}]},
    },
)
def test_custom_convert_auto(sphinx_run, file_regression, check_nbs):
    sphinx_run.build()
    # print(sphinx_run.status())
    assert sphinx_run.warnings() == ""
    regress_nb_doc(file_regression, sphinx_run, check_nbs)

    assert NbMetadataCollector.new_exec_data(sphinx_run.env)
    data = NbMetadataCollector.get_exec_data(sphinx_run.env, "custom-formats")
    assert data
    assert data["method"] == "auto"
    assert data["succeeded"] is True


@pytest.mark.sphinx_params(
    "custom-formats.Rmd",
    conf={
        "nb_execution_mode": "cache",
        "nb_custom_formats": {".Rmd": ["jupytext.reads", {"fmt": "Rmd"}]},
    },
)
def test_custom_convert_cache(sphinx_run, file_regression, check_nbs):
    """The outputs should be populated."""
    sphinx_run.build()
    assert sphinx_run.warnings() == ""
    regress_nb_doc(file_regression, sphinx_run, check_nbs)

    assert NbMetadataCollector.new_exec_data(sphinx_run.env)
    data = NbMetadataCollector.get_exec_data(sphinx_run.env, "custom-formats")
    assert data
    assert data["method"] == "cache"
    assert data["succeeded"] is True

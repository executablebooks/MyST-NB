"""Test full sphinx builds."""
import bs4
import pytest


@pytest.mark.sphinx_params("basic_run.ipynb", conf={"nb_execution_mode": "off"})
def test_basic_run(sphinx_run, file_regression):
    sphinx_run.build()
    # print(sphinx_run.status())
    assert sphinx_run.warnings() == ""
    assert set(sphinx_run.app.env.metadata["basic_run"].keys()) == {
        "test_name",
        "kernelspec",
        "language_info",
        "wordcount",
    }
    file_regression.check(
        sphinx_run.get_doctree().pformat(), extension=".xml", encoding="utf8"
    )


@pytest.mark.sphinx_params("basic_unrun.md", conf={"nb_execution_mode": "off"})
def test_basic_run_md(sphinx_run, file_regression):
    sphinx_run.build()
    # print(sphinx_run.status())
    assert sphinx_run.warnings() == ""
    file_regression.check(
        sphinx_run.get_doctree().pformat(), extension=".xml", encoding="utf8"
    )


@pytest.mark.sphinx_params("complex_outputs.ipynb", conf={"nb_execution_mode": "off"})
def test_complex_outputs_run(sphinx_run, file_regression):
    sphinx_run.build()
    # print(sphinx_run.status())
    assert sphinx_run.warnings() == ""
    try:
        file_regression.check(
            sphinx_run.get_doctree().pformat(), extension=".xml", encoding="utf8"
        )
    finally:
        file_regression.check(
            sphinx_run.get_resolved_doctree().pformat(),
            extension=".resolved.xml",
            encoding="utf8",
        )


@pytest.mark.sphinx_params("ipywidgets.ipynb", conf={"nb_execution_mode": "off"})
def test_ipywidgets(sphinx_run):
    """Test that ipywidget state is extracted and JS is included in the HTML head."""
    sphinx_run.build()
    # print(sphinx_run.status())
    assert sphinx_run.warnings() == ""
    assert "__mystnb__ipywidgets_state" in sphinx_run.env.metadata["ipywidgets"]
    html = bs4.BeautifulSoup(sphinx_run.get_html(), "html.parser")
    head_scripts = html.select("head > script")
    assert any("require.js" in script.get("src", "") for script in head_scripts)
    assert any("embed-amd.js" in script.get("src", "") for script in head_scripts)

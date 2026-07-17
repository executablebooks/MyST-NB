import pytest


@pytest.mark.sphinx_params(
    "basic_unrun.md",
    conf={"nb_execution_mode": "cache", "source_suffix": {".md": "myst-nb"}},
)
def test_basic_run(sphinx_run, file_regression, check_nbs):
    sphinx_run.build()
    # print(sphinx_run.status())
    assert sphinx_run.warnings() == ""
    assert set(sphinx_run.env.metadata["basic_unrun"].keys()) == {
        "file_format",
        "author",
        "source_map",
        "wordcount",
        "kernelspec",
        "language_info",
    }
    assert set(sphinx_run.env.nb_metadata["basic_unrun"].keys()) == {
        "exec_data",
    }
    assert sphinx_run.env.metadata["basic_unrun"]["author"] == "Chris"
    assert sphinx_run.env.metadata["basic_unrun"]["kernelspec"] == {
        "display_name": "Python 3",
        "language": "python",
        "name": "python3",
    }
    file_regression.check(
        sphinx_run.get_nb(), check_fn=check_nbs, extension=".ipynb", encoding="utf-8"
    )
    file_regression.check(
        sphinx_run.get_doctree().pformat(), extension=".xml", encoding="utf-8"
    )


@pytest.mark.sphinx_params(
    "basic_unrun.md",
    conf={"nb_execution_mode": "off", "source_suffix": {".md": "myst-nb"}},
)
def test_basic_run_exec_off(sphinx_run, file_regression, check_nbs):
    sphinx_run.build()
    # print(sphinx_run.status())
    assert set(sphinx_run.env.metadata["basic_unrun"].keys()) == {
        "file_format",
        "author",
        "source_map",
        "wordcount",
        "kernelspec",
    }
    assert set(sphinx_run.env.nb_metadata["basic_unrun"].keys()) == set()
    assert sphinx_run.env.metadata["basic_unrun"]["author"] == "Chris"

    file_regression.check(
        sphinx_run.get_nb(), check_fn=check_nbs, extension=".ipynb", encoding="utf-8"
    )
    file_regression.check(
        sphinx_run.get_doctree().pformat(), extension=".xml", encoding="utf-8"
    )


@pytest.mark.sphinx_params(
    "basic_nometadata.md",
    conf={"nb_execution_mode": "off", "source_suffix": {".md": "myst-nb"}},
)
def test_basic_nometadata(sphinx_run):
    """A myst-markdown notebook with no jupytext metadata should raise a warning."""
    sphinx_run.build()
    # print(sphinx_run.status())
    assert "Found an unexpected `code-cell`" in sphinx_run.warnings()


@pytest.mark.sphinx_params(
    "nested_code_cell_in_tab.md",
    conf={
        "nb_execution_mode": "off",
        "source_suffix": {".md": "myst-nb"},
        "extensions": ["myst_nb"],
    },
)
def test_nested_code_cell_in_tab(sphinx_run):
    """Code cells nested inside a tab-set should render their source as code blocks."""
    sphinx_run.build()
    # Warnings are expected since the cells are nested (not converted to notebook cells)
    assert "Found an unexpected `code-cell`" in sphinx_run.warnings()
    # But the code content must still appear in the HTML output
    html = sphinx_run.get_html()
    code_blocks = html.find_all("div", class_="highlight")
    sources = [block.get_text() for block in code_blocks]
    assert any("hello from standalone cell" in s for s in sources)
    assert any("hello from tab 1" in s for s in sources)
    assert any("hello from tab 2" in s for s in sources)

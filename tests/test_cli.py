"""Test the quickstart CLI"""
from pathlib import Path

import nbformat
from sphinx.testing.path import path as sphinx_path

from myst_nb.cli import md_to_nb, quickstart


def test_quickstart(tmp_path: Path, make_app):
    """Test the quickstart CLI builds a valid sphinx project."""
    path = tmp_path / "project"
    quickstart([str(path)])
    assert {p.name for p in path.iterdir()} == {
        ".gitignore",
        "conf.py",
        "index.md",
        "notebook1.ipynb",
        "notebook2.md",
    }
    app = make_app(srcdir=sphinx_path(str(path)), buildername="html")
    app.build()
    assert app._warning.getvalue().strip() == ""
    assert (path / "_build/html/index.html").exists()


def test_md_to_nb(tmp_path: Path):
    """Test the md_to_nb CLI."""
    path = tmp_path / "notebook.md"
    outpath = path.with_suffix(".ipynb")
    path.write_text(
        """\
---
kernelspec:
    name: python3
---
# Title
+++
next cell
""",
        "utf8",
    )
    md_to_nb([str(path)])
    assert path.exists()
    with outpath.open("r") as handle:
        nb = nbformat.read(handle, as_version=4)
    assert nb.metadata == {"kernelspec": {"display_name": "python3", "name": "python3"}}
    assert len(nb.cells) == 2

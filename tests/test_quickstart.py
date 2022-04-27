"""Test the quickstart CLI"""
from pathlib import Path

from sphinx.testing.path import path as sphinx_path

from myst_nb.cli import quickstart


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

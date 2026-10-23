"""Regression: sphinx-build -D boolean overrides are real bools."""

from pathlib import Path

from sphinx.application import Sphinx


def _app_with_allow_errors(root: Path, allow_errors: str) -> Sphinx:
    """Build a Sphinx app the way ``sphinx-build -D`` supplies a string."""
    src = root / "src"
    src.mkdir(parents=True)
    (src / "conf.py").write_text(
        "extensions = ['myst_nb']\nnb_execution_mode = 'off'\n",
        encoding="utf-8",
    )
    (src / "index.md").write_text("# hi\n", encoding="utf-8")
    return Sphinx(
        srcdir=src,
        confdir=src,
        outdir=root / "out",
        doctreedir=root / "doctree",
        buildername="html",
        confoverrides={"nb_execution_allow_errors": allow_errors},
    )


def test_dash_d_allow_errors_string_is_bool(tmp_path: Path) -> None:
    """``-D nb_execution_allow_errors=True`` is a bool, and ``False`` stays false."""
    true_app = _app_with_allow_errors(tmp_path / "true", "True")
    assert true_app.env.mystnb_config.execution_allow_errors is True

    false_app = _app_with_allow_errors(tmp_path / "false", "False")
    assert false_app.env.mystnb_config.execution_allow_errors is False


def test_dash_d_legacy_allow_errors_string_is_bool(tmp_path: Path) -> None:
    """The deprecated ``execution_allow_errors`` override is a bool too."""
    src = tmp_path / "src"
    src.mkdir()
    (src / "conf.py").write_text(
        "extensions = ['myst_nb']\nnb_execution_mode = 'off'\n",
        encoding="utf-8",
    )
    (src / "index.md").write_text("# hi\n", encoding="utf-8")
    app = Sphinx(
        srcdir=src,
        confdir=src,
        outdir=tmp_path / "out",
        doctreedir=tmp_path / "doctree",
        buildername="html",
        confoverrides={"execution_allow_errors": "False"},
    )
    assert app.env.mystnb_config.execution_allow_errors is False

from unittest.mock import patch

from importlib_metadata import EntryPoint
import pytest

from myst_nb.render import EntryPointError, load_renderer


def test_load_renderer_not_found():
    """Test that an error is raised when the renderer is not found."""
    with pytest.raises(EntryPointError, match="No Entry Point found"):
        load_renderer("other")


# TODO sometimes fails in full tests
# def test_load_renderer_not_subclass(monkeypatch):
#     """Test that an error is raised when the renderer is not a subclass."""
#     monkeypatch.setattr(EntryPoint, "load", lambda self: object)
#     with pytest.raises(EntryPointError, match="Entry Point .* not a subclass"):
#         load_renderer("default")


@pytest.mark.sphinx_params("basic_run.ipynb", conf={"nb_execution_mode": "off"})
def test_basic_run(sphinx_run, file_regression):
    sphinx_run.build()
    assert sphinx_run.warnings() == ""
    doctree = sphinx_run.get_resolved_doctree("basic_run")
    file_regression.check(doctree.pformat(), extension=".xml", encoding="utf8")


@pytest.mark.sphinx_params("complex_outputs.ipynb", conf={"nb_execution_mode": "off"})
def test_complex_outputs(sphinx_run, clean_doctree, file_regression):
    sphinx_run.build()
    assert sphinx_run.warnings() == ""
    doctree = clean_doctree(sphinx_run.get_resolved_doctree("complex_outputs"))
    file_regression.check(
        doctree.pformat().replace(".jpeg", ".jpg"), extension=".xml", encoding="utf8"
    )


@pytest.mark.sphinx_params(
    "complex_outputs.ipynb",
    conf={"nb_execution_mode": "off"},
    buildername="latex",
)
def test_complex_outputs_latex(sphinx_run, clean_doctree, file_regression):
    sphinx_run.build()
    assert sphinx_run.warnings() == ""
    doctree = clean_doctree(sphinx_run.get_resolved_doctree("complex_outputs"))
    file_regression.check(
        doctree.pformat().replace(".jpeg", ".jpg"), extension=".xml", encoding="utf8"
    )


@pytest.mark.sphinx_params(
    "basic_stderr.ipynb",
    conf={"nb_execution_mode": "off", "nb_output_stderr": "remove"},
)
def test_stderr_remove(sphinx_run, file_regression):
    """Test configuring all stderr outputs to be removed."""
    sphinx_run.build()
    assert sphinx_run.warnings() == ""
    doctree = sphinx_run.get_resolved_doctree("basic_stderr")
    file_regression.check(doctree.pformat(), extension=".xml", encoding="utf8")


@pytest.mark.sphinx_params("basic_stderr.ipynb", conf={"nb_execution_mode": "off"})
def test_stderr_tag(sphinx_run, file_regression):
    """Test configuring stderr outputs to be removed from a single cell,
    using `remove-stderr` in the `cell.metadata.tags`.
    """
    sphinx_run.build()
    assert sphinx_run.warnings() == ""
    doctree = sphinx_run.get_resolved_doctree("basic_stderr")
    file_regression.check(doctree.pformat(), extension=".xml", encoding="utf8")


@pytest.mark.sphinx_params(
    "merge_streams.ipynb",
    conf={"nb_execution_mode": "off", "nb_merge_streams": True},
)
def test_merge_streams(sphinx_run, file_regression):
    """Test configuring multiple concurrent stdout/stderr outputs to be merged."""
    sphinx_run.build()
    assert sphinx_run.warnings() == ""
    doctree = sphinx_run.get_resolved_doctree("merge_streams")
    file_regression.check(doctree.pformat(), extension=".xml", encoding="utf8")


@pytest.mark.sphinx_params(
    "metadata_image.ipynb",
    conf={"nb_execution_mode": "off", "nb_cell_render_key": "myst"},
)
def test_metadata_image(sphinx_run, clean_doctree, file_regression):
    """Test configuring image attributes to be rendered from cell metadata."""
    sphinx_run.build()
    assert sphinx_run.warnings() == ""
    doctree = clean_doctree(sphinx_run.get_resolved_doctree("metadata_image"))
    file_regression.check(
        doctree.pformat().replace(".jpeg", ".jpg"), extension=".xml", encoding="utf8"
    )


# TODO add test for figures


@pytest.mark.sphinx_params("unknown_mimetype.ipynb", conf={"nb_execution_mode": "off"})
def test_unknown_mimetype(sphinx_run, file_regression):
    """Test that unknown mimetypes provide a warning."""
    sphinx_run.build()
    warning = "skipping unknown output mime type: unknown [mystnb.unknown_mime_type]"
    assert warning in sphinx_run.warnings()
    doctree = sphinx_run.get_resolved_doctree("unknown_mimetype")
    file_regression.check(doctree.pformat(), extension=".xml", encoding="utf8")

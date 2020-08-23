import pytest


@pytest.mark.sphinx_params("basic_run.ipynb", conf={"jupyter_execute_notebooks": "off"})
def test_basic_run(sphinx_run, file_regression):
    sphinx_run.build()
    assert sphinx_run.warnings() == ""
    doctree = sphinx_run.get_resolved_doctree("basic_run")
    file_regression.check(doctree.pformat(), extension=".xml")


@pytest.mark.sphinx_params(
    "complex_outputs.ipynb", conf={"jupyter_execute_notebooks": "off"}
)
def test_complex_outputs(sphinx_run, file_regression):
    sphinx_run.build()
    assert sphinx_run.warnings() == ""
    doctree = sphinx_run.get_resolved_doctree("complex_outputs")
    file_regression.check(doctree.pformat().replace(".jpeg", ".jpg"), extension=".xml")


@pytest.mark.sphinx_params(
    "complex_outputs.ipynb",
    conf={"jupyter_execute_notebooks": "off"},
    buildername="latex",
)
def test_complex_outputs_latex(sphinx_run, file_regression):
    sphinx_run.build()
    assert sphinx_run.warnings() == ""
    doctree = sphinx_run.get_resolved_doctree("complex_outputs")
    file_regression.check(doctree.pformat().replace(".jpeg", ".jpg"), extension=".xml")


# @pytest.mark.sphinx_params(
#     "unknown_mimetype.ipynb", conf={"jupyter_execute_notebooks": "off"}
# )
# def test_unknown_mimetype(sphinx_run, file_regression):
#     sphinx_run.build()
#     warning = (
#         "unknown_mimetype.ipynb.rst:10002: WARNING: MyST-NB: "
#         "output contains no MIME type in priority list"
#     )
#     assert warning in sphinx_run.warnings()
#     doctree = sphinx_run.get_resolved_doctree("unknown_mimetype")
#     file_regression.check(doctree.pformat(), extension=".xml")

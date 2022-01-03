"""Test full sphinx builds."""
import pytest


@pytest.mark.sphinx_params(
    "basic_run.ipynb",
    conf={"extensions": ["myst_nb.new.sphinx_"], "nb_execution_mode": "off"},
)
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


@pytest.mark.sphinx_params(
    "complex_outputs.ipynb",
    conf={"extensions": ["myst_nb.new.sphinx_"], "nb_execution_mode": "off"},
)
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

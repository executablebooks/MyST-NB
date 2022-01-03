"""Test full sphinx builds."""
import pytest


@pytest.mark.sphinx_params(
    "basic_run.ipynb", conf={"extensions": ["myst_nb.new.sphinx_"]}
)
def test_basic_run(sphinx_run, file_regression):
    sphinx_run.build()
    # print(sphinx_run.status())
    assert sphinx_run.warnings() == ""
    # TODO implement "cleaning" of doctree["nb_language_info"] this on SphinxFixture
    # e.g. remove/replace the python 'version' key
    file_regression.check(
        sphinx_run.get_doctree().pformat(), extension=".xml", encoding="utf8"
    )

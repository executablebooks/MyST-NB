"""Run parsing tests against the docutils parser."""
from io import StringIO
import json
from pathlib import Path

from docutils.core import publish_doctree
import pytest
import yaml

from myst_nb.docutils_ import Parser

FIXTURE_PATH = Path(__file__).parent.joinpath("nb_fixtures")


@pytest.mark.param_file(FIXTURE_PATH / "basic.txt")
def test_basic(file_params):
    """Test basic parsing."""
    dct = yaml.safe_load(file_params.content)
    dct.update({"nbformat": 4, "nbformat_minor": 4})
    dct.setdefault("metadata", {})
    report_stream = StringIO()
    doctree = publish_doctree(
        json.dumps(dct),
        parser=Parser(),
        settings_overrides={
            "nb_execution_mode": "off",
            "nb_output_folder": "",
            "myst_all_links_external": True,
            "warning_stream": report_stream,
        },
    )
    assert report_stream.getvalue().rstrip() == ""

    file_params.assert_expected(doctree.pformat(), rstrip=True)


@pytest.mark.param_file(FIXTURE_PATH / "reporter_warnings.txt")
def test_reporting(file_params):
    """Test that warnings and errors are reported as expected."""
    dct = yaml.safe_load(file_params.content)
    dct.update({"metadata": {}, "nbformat": 4, "nbformat_minor": 4})
    report_stream = StringIO()
    publish_doctree(
        json.dumps(dct),
        parser=Parser(),
        settings_overrides={
            "nb_execution_mode": "off",
            "nb_output_folder": "",
            "warning_stream": report_stream,
        },
    )
    file_params.assert_expected(report_stream.getvalue(), rstrip=True)

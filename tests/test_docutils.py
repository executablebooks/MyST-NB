"""Run parsing tests against the docutils parser."""
from io import StringIO
import json
from pathlib import Path

from docutils.core import publish_doctree
from markdown_it.utils import read_fixture_file
import pytest
import yaml

from myst_nb.docutils_ import Parser

FIXTURE_PATH = Path(__file__).parent.joinpath("nb_fixtures")


@pytest.mark.parametrize(
    "line,title,input,expected",
    read_fixture_file(FIXTURE_PATH.joinpath("basic.txt")),
    ids=[f"{i[0]}-{i[1]}" for i in read_fixture_file(FIXTURE_PATH / "basic.txt")],
)
def test_basic(line, title, input, expected):
    """Test basic parsing."""
    dct = yaml.safe_load(input)
    dct.update({"nbformat": 4, "nbformat_minor": 4})
    dct.setdefault("metadata", {})
    report_stream = StringIO()
    doctree = publish_doctree(
        json.dumps(dct),
        parser=Parser(),
        settings_overrides={
            "nb_execution_mode": "off",
            "myst_all_links_external": True,
            "warning_stream": report_stream,
        },
    )
    assert report_stream.getvalue().rstrip() == ""

    try:
        assert doctree.pformat().rstrip() == expected.rstrip()
    except AssertionError:
        print(doctree.pformat().rstrip())
        raise


@pytest.mark.parametrize(
    "line,title,input,expected",
    read_fixture_file(FIXTURE_PATH.joinpath("reporter_warnings.txt")),
    ids=[
        f"{i[0]}-{i[1]}"
        for i in read_fixture_file(FIXTURE_PATH / "reporter_warnings.txt")
    ],
)
def test_reporting(line, title, input, expected):
    """Test that warnings and errors are reported as expected."""
    dct = yaml.safe_load(input)
    dct.update({"metadata": {}, "nbformat": 4, "nbformat_minor": 4})
    report_stream = StringIO()
    publish_doctree(
        json.dumps(dct),
        parser=Parser(),
        settings_overrides={
            "nb_execution_mode": "off",
            "warning_stream": report_stream,
        },
    )

    assert report_stream.getvalue().rstrip() == expected.rstrip()

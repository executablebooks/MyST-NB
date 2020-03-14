from collections import defaultdict
from pathlib import Path

from docutils import nodes
from docutils.frontend import OptionParser
from docutils.parsers.rst import Parser as RSTParser
from docutils.utils import new_document

import pytest

NB_DIR = Path(__file__).parent.joinpath("notebooks")


class MockEnv:
    class app:
        class builder:
            name = "html"

        class config:
            language = None

    dependencies = defaultdict(set)


@pytest.fixture()
def mock_document() -> nodes.document:
    source_path = "notset"
    settings = OptionParser(components=(RSTParser,)).get_default_values()
    document = new_document(source_path, settings=settings)
    document.settings.env = MockEnv
    document.settings.env.glue_data = {}
    document.settings.env.app.env = document.settings.env
    yield document


@pytest.fixture()
def mock_document_in_temp(mock_document, tmp_path) -> nodes.document:
    mock_document.settings.env.docname = "source/nb"
    mock_document.settings.env.app.outdir = tmp_path / "build" / "outdir"
    mock_document.settings.env.app.srcdir = tmp_path / "source"
    mock_document.settings.env.relfn2path = lambda imguri, docname: (
        "image.png",
        tmp_path / "build" / "image.png",
    )
    yield mock_document


@pytest.fixture()
def get_notebook():
    def _get_notebook(name):
        return NB_DIR.joinpath(name)

    return _get_notebook

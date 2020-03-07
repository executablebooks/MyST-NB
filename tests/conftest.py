from pathlib import Path

from docutils import nodes
from docutils.frontend import OptionParser
from docutils.parsers.rst import Parser as RSTParser
from docutils.utils import new_document as _new_document

import pytest

NB_DIR = Path(__file__).parent.joinpath("notebooks")


@pytest.fixture()
def new_document() -> nodes.document:
    source_path = "notset"
    settings = OptionParser(components=(RSTParser,)).get_default_values()
    return _new_document(source_path, settings=settings)


@pytest.fixture()
def get_notebook():
    def _get_notebook(name):
        return NB_DIR.joinpath(name)

    return _get_notebook

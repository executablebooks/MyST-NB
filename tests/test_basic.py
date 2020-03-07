from pathlib import Path

from docutils import nodes
from docutils.frontend import OptionParser
from docutils.parsers.rst import Parser as RSTParser
from docutils.utils import new_document

from myst_nb.parser import NotebookParser


NB_DIR = Path(__file__).parent.joinpath("notebooks")


def get_document(source_path="notset") -> nodes.document:
    settings = OptionParser(components=(RSTParser,)).get_default_values()
    return new_document(source_path, settings=settings)


def test_basic(file_regression):
    parser = NotebookParser()
    document = get_document()
    parser.parse(NB_DIR.joinpath("basic_run.ipynb").read_text(), document)
    file_regression.check(document.pformat(), extension=".xml")

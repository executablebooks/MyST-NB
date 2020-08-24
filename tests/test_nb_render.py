from pathlib import Path

import nbformat
import pytest
import yaml

from markdown_it.utils import read_fixture_file
from myst_parser.docutils_renderer import make_document
from myst_parser.main import MdParserConfig
from myst_parser.sphinx_renderer import mock_sphinx_env

from myst_nb.parser import nb_to_tokens, tokens_to_docutils


FIXTURE_PATH = Path(__file__).parent.joinpath("nb_fixtures")


@pytest.mark.parametrize(
    "line,title,input,expected", read_fixture_file(FIXTURE_PATH.joinpath("basic.txt"))
)
def test_render(line, title, input, expected):
    dct = yaml.safe_load(input)
    dct.setdefault("metadata", {})
    ntbk = nbformat.from_dict(dct)
    md, env, tokens = nb_to_tokens(ntbk, MdParserConfig(), "default")
    document = make_document()
    with mock_sphinx_env(document=document):
        tokens_to_docutils(md, env, tokens, document)
    output = document.pformat().rstrip()
    if output != expected.rstrip():
        print(output)
    assert output == expected.rstrip()


@pytest.mark.parametrize(
    "line,title,input,expected",
    read_fixture_file(FIXTURE_PATH.joinpath("reporter_warnings.txt")),
)
def test_reporting(line, title, input, expected):
    dct = yaml.safe_load(input)
    dct.setdefault("metadata", {})
    ntbk = nbformat.from_dict(dct)
    md, env, tokens = nb_to_tokens(ntbk, MdParserConfig(), "default")
    document = make_document("source/path")
    messages = []

    def observer(msg_node):
        if msg_node["level"] > 1:
            messages.append(msg_node.astext())

    document.reporter.attach_observer(observer)
    with mock_sphinx_env(document=document):
        tokens_to_docutils(md, env, tokens, document)

    assert "\n".join(messages).rstrip() == expected.rstrip()

from copy import copy

import pytest
from IPython.core.interactiveshell import InteractiveShell
from IPython.core.displaypub import DisplayPublisher
from docutils.parsers.rst import directives, roles
from docutils.transforms import Transformer

from myst_nb import glue
from myst_nb.parser import NotebookParser
from myst_nb.transform import CellOutputsToNodes


class MockDisplayPublisher(DisplayPublisher):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.publish_calls = []

    def publish(self, data, **kwargs):
        kwargs["data"] = data
        self.publish_calls.append(kwargs)


@pytest.fixture()
def mock_ipython():
    shell = InteractiveShell.instance()  # type: InteractiveShell
    shell.display_pub = MockDisplayPublisher()
    yield shell.display_pub
    InteractiveShell.clear_instance()


@pytest.fixture()
def patch_docutils():
    _directives = copy(directives._directives)
    _roles = copy(roles._roles)
    directives._directives["paste"] = glue.Paste
    roles._roles["paste"] = glue.paste_role
    yield None
    directives._directives = _directives
    roles._roles = _roles


def test_glue_func_text(mock_ipython):
    glue.glue("a", "b")
    assert mock_ipython.publish_calls == [
        {
            "metadata": {"scrapbook": {"name": "a", "mime_prefix": ""}},
            "data": {"text/plain": "'b'"},
        }
    ]


def test_glue_func_obj(mock_ipython):
    class Obj:
        def __repr__(self):
            return "repr"

        def _repr_html_(self):
            return "<p>repr</p>"

    glue.glue("a", Obj())
    assert mock_ipython.publish_calls == [
        {
            "metadata": {"scrapbook": {"name": "a", "mime_prefix": ""}},
            "data": {"text/html": "<p>repr</p>", "text/plain": "repr"},
        }
    ]


def test_glue_func_obj_no_display(mock_ipython):
    class Obj:
        def __repr__(self):
            return "repr"

        def _repr_html_(self):
            return "<p>repr</p>"

    glue.glue("a", Obj(), display=False)
    assert mock_ipython.publish_calls == [
        {
            "metadata": {
                "scrapbook": {
                    "name": "a",
                    "mime_prefix": "application/papermill.record/",
                }
            },
            "data": {
                "application/papermill.record/text/html": "<p>repr</p>",
                "application/papermill.record/text/plain": "repr",
            },
        }
    ]


def test_find_glued_key(get_notebook):

    bundle = glue.find_glued_key(get_notebook("with_glue.ipynb"), "key_text1")
    assert bundle == {"key_text1": "'text1'"}

    with pytest.raises(KeyError):
        glue.find_glued_key(get_notebook("with_glue.ipynb"), "unknown")


def test_find_all_keys(get_notebook):
    keys = glue.find_all_keys(get_notebook("with_glue.ipynb"))
    assert set(keys) == {
        "key_text1",
        "key_float",
        "key_undisplayed",
        "key_df",
        "key_plt",
    }


def test_parser(patch_docutils, mock_document_in_temp, get_notebook, file_regression):
    parser = NotebookParser()
    parser.parse(get_notebook("with_glue.ipynb").read_text(), mock_document_in_temp)

    transformer = Transformer(mock_document_in_temp)
    transformer.add_transforms([CellOutputsToNodes, glue.PasteNodesToDocutils])
    transformer.apply_transforms()

    file_regression.check(mock_document_in_temp.pformat(), extension=".xml")
    assert set(mock_document_in_temp.document.settings.env.glue_data) == {
        "key_text1",
        "key_float",
        "key_undisplayed",
        "key_df",
        "key_plt",
    }

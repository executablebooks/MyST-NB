import pytest

from IPython.core.interactiveshell import InteractiveShell
from IPython.core.displaypub import DisplayPublisher

from myst_nb import glue


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
            "data": {"text/html": "<p>repr</p>", "text/plain": "repr"},
        }
    ]

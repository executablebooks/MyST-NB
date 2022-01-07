from IPython.core.displaypub import DisplayPublisher
from IPython.core.interactiveshell import InteractiveShell
import nbformat
import pytest

from myst_nb.nb_glue import extract_glue_data, glue


class MockDisplayPublisher(DisplayPublisher):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.publish_calls = []

    def publish(self, data, **kwargs):
        kwargs["data"] = data
        self.publish_calls.append(kwargs)


@pytest.fixture()
def mock_ipython():
    """A mock IPython shell for testing notebook cell executions."""
    shell = InteractiveShell.instance()  # type: InteractiveShell
    shell.display_pub = MockDisplayPublisher()
    yield shell.display_pub
    InteractiveShell.clear_instance()


def test_glue_func_text(mock_ipython):
    glue("a", "b")
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

    glue("a", Obj())
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

    glue("a", Obj(), display=False)
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


def test_extract_glue_data(get_test_path):
    path = get_test_path("with_glue.ipynb")
    with open(path, "r") as handle:
        notebook = nbformat.read(handle, as_version=4)
    resources = {}
    extract_glue_data(notebook, resources, [], None)
    assert set(resources["glue"]) == {
        "key_text1",
        "key_float",
        "key_undisplayed",
        "key_df",
        "key_plt",
        "sym_eq",
    }


@pytest.mark.sphinx_params("with_glue.ipynb", conf={"nb_execution_mode": "off"})
def test_parser(sphinx_run, clean_doctree, file_regression):
    """Test a sphinx build."""
    # TODO test duplicate warning in docutils
    sphinx_run.build()
    # print(sphinx_run.status())
    # print(sphinx_run.warnings())
    assert sphinx_run.warnings() == ""
    doctree = clean_doctree(sphinx_run.get_resolved_doctree("with_glue"))
    file_regression.check(
        doctree.pformat(),
        extension=f"{sphinx_run.software_versions}.xml",
        encoding="utf8",
    )
    # from myst_nb.nb_glue.domain import NbGlueDomain
    # glue_domain = NbGlueDomain.from_env(sphinx_run.app.env)
    # assert set(glue_domain.cache) == {
    #     "key_text1",
    #     "key_float",
    #     "key_undisplayed",
    #     "key_df",
    #     "key_plt",
    #     "sym_eq",
    # }
    # glue_domain.clear_doc("with_glue")
    # assert glue_domain.cache == {}
    # assert glue_domain.docmap == {}

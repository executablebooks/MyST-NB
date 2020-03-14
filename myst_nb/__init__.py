__version__ = "0.3.0"

from docutils import nodes
from jupyter_sphinx.ast import (  # noqa: F401
    JupyterWidgetStateNode,
    JupyterWidgetViewNode,
    JupyterCell,
)

from pathlib import Path
import json

from .parser import (
    NotebookParser,
    CellNode,
    CellInputNode,
    CellOutputNode,
    CellOutputBundleNode,
)
from .transform import CellOutputsToNodes
from .glue.domain import Paste, paste_role
from .glue.transform import PasteNodesToDocutils


def static_path(app):
    static_path = Path(__file__).absolute().with_name("_static")
    app.config.html_static_path.append(str(static_path))


def update_togglebutton_classes(app, config):
    to_add = [
        ".tag_hide_input div.cell_input",
        ".tag_hide_output div.cell_output",
        ".tag_hide_cell.cell",
    ]
    for selector in to_add:
        config.togglebutton_selector += f", {selector}"


def init_glue_cache(app):
    if not hasattr(app.env, "glue_data"):
        app.env.glue_data = {}


def save_glue_cache(app, env):
    path_cache = Path(env.doctreedir).joinpath("glue_cache.json")
    with path_cache.open("w") as handle:
        json.dump(env.glue_data, handle)


def setup(app):
    """Initialize Sphinx extension."""
    # Sllow parsing ipynb files
    app.add_source_suffix(".ipynb", "ipynb")
    app.add_source_parser(NotebookParser)
    app.setup_extension("sphinx_togglebutton")

    # Helper functions for the registry, pulled from jupyter-sphinx
    def skip(self, node):
        raise nodes.SkipNode

    # Used to render an element node as HTML
    def visit_element_html(self, node):
        self.body.append(node.html())
        raise nodes.SkipNode

    # Shortcut for registering our container nodes
    render_container = (
        lambda self, node: self.visit_container(node),
        lambda self, node: self.depart_container(node),
    )

    # Register our container nodes, these should behave just like a regular container
    for node in [CellNode, CellInputNode, CellOutputNode]:
        app.add_node(
            node,
            override=True,
            html=(render_container),
            latex=(render_container),
            textinfo=(render_container),
            text=(render_container),
            man=(render_container),
        )

    # Register the output bundle node.
    # No translators should touch this node because we'll replace it in a post-transform
    app.add_node(
        CellOutputBundleNode,
        override=True,
        html=(skip, None),
        latex=(skip, None),
        textinfo=(skip, None),
        text=(skip, None),
        man=(skip, None),
    )

    # Register our post-transform which will convert output bundles to nodes
    app.add_post_transform(PasteNodesToDocutils)
    app.add_post_transform(CellOutputsToNodes)

    app.connect("builder-inited", init_glue_cache)
    app.connect("builder-inited", static_path)
    app.connect("config-inited", update_togglebutton_classes)
    app.connect("env-updated", save_glue_cache)
    app.add_css_file("mystnb.css")
    # We use `execute` here instead of `jupyter-execute`
    app.add_directive("execute", JupyterCell)
    app.add_directive("paste", Paste)
    app.add_role("paste", paste_role)
    app.setup_extension("jupyter_sphinx")

    return {"version": __version__, "parallel_read_safe": True}

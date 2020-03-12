__version__ = "0.1.0"

from docutils import nodes
from myst_nb.cache import execution_cache
from jupyter_sphinx.ast import (  # noqa: F401
    JupyterWidgetStateNode,
    JupyterWidgetViewNode,
    JupyterCell,
)

# from ipywidgets import embed
from pathlib import Path

from .parser import (
    NotebookParser,
    CellNode,
    CellInputNode,
    CellOutputNode,
    CellOutputBundleNode,
    CellImageNode,
)
from .transform import CellOutputsToNodes


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


# Just in case we have a jupyter cache in the doc folder, exclude it
def skip_cache_notebooks(app, config):
    config['exclude_patterns'].append('**.jupyter_cache')

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

    # Add configuration for the cache
    app.add_config_value("jupyter_cache", False, "env")
    app.add_config_value("execution_excludepatterns", [], "env")
    app.add_config_value("jupyter_notebook_force_run", False, "env")

    # So that we can in-line images in HTML outputs
    def visit_cell_image(self, node):
        atts = {"src": f"data:image/png;base64, {node['uri']}", "alt": f"{node['alt']}"}
        self.body.append(self.emptytag(node, "img", "\n", **atts))

    app.add_node(
        CellImageNode, override=True, html=(visit_cell_image, lambda self, node: "")
    )

    # Register our post-transform which will convert output bundles to nodes
    app.add_post_transform(CellOutputsToNodes)

    app.connect("builder-inited", static_path)
    app.connect("env-get-outdated", execution_cache)
    app.connect("config-inited", update_togglebutton_classes)
    app.connect("config-inited", skip_cache_notebooks)

    app.add_css_file("mystnb.css")
    # We use `execute` here instead of `jupyter-execute`
    app.add_directive("execute", JupyterCell)
    app.setup_extension("jupyter_sphinx")

    return {"version": __version__, "parallel_read_safe": True}

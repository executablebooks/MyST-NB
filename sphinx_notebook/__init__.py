__version__ = "0.1.0"

import docutils
from jupyter_sphinx.execute import JupyterWidgetStateNode, JupyterWidgetViewNode
from .parser import (
    NotebookParser,
    CellNode,
    CellInputNode,
    CellOutputNode,
    CellOutputBundleNode,
    CellImageNode
)
from .transform import CellOutputsToNodes


def setup(app):
    """Initialize Sphinx extension."""
    # Sllow parsing ipynb files
    app.add_source_suffix(".ipynb", "ipynb")
    app.add_source_parser(NotebookParser)

    # Helper functions for the registry, pulled from jupyter-sphinx
    def skip(self, node):
        raise docutils.nodes.SkipNode

    # Used to render an element node as HTML
    def visit_element_html(self, node):
        self.body.append(node.html())
        raise docutils.nodes.SkipNode

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

    # So that we can in-line images in HTML outputs
    def visit_cell_image(self, node):
        atts = {
            "src": f"data:image/png;base64, {node['uri']}",
            "alt": f"{node['alt']}"
        }
        self.body.append(self.emptytag(node, 'img', "\n", **atts))
    app.add_node(
        CellImageNode,
        override=True,
        html=(visit_cell_image, lambda self, node: ''),
    )

    # JupyterWidgetViewNode holds widget view JSON,
    # but is only rendered properly in HTML documents.
    app.add_node(
        JupyterWidgetViewNode,
        html=(visit_element_html, None),
        latex=(skip, None),
        textinfo=(skip, None),
        text=(skip, None),
        man=(skip, None),
    )
    # JupyterWidgetStateNode holds the widget state JSON,
    # but is only rendered in HTML documents.
    app.add_node(
        JupyterWidgetStateNode,
        html=(visit_element_html, None),
        latex=(skip, None),
        textinfo=(skip, None),
        text=(skip, None),
        man=(skip, None),
    )

    # Register our post-transform which will convert output bundles to nodes
    app.add_post_transform(CellOutputsToNodes)

    return {"version": __version__, "parallel_read_safe": True}

"""AST nodes to designate notebook components."""
import json
from typing import Any, List

from docutils import nodes
from nbformat import NotebookNode

from myst_nb.jsphinx import snippet_template, widget_view_template


class CellNode(nodes.container):
    """Represent a cell in the Sphinx AST."""


class CellInputNode(nodes.container):
    """Represent an input cell in the Sphinx AST."""


class CellOutputNode(nodes.container):
    """Represent an output cell in the Sphinx AST."""


class CellOutputBundleNode(nodes.container):
    """Represent a MimeBundle in the Sphinx AST, to be transformed later."""

    def __init__(self, outputs, renderer: str, metadata=None, **attributes):
        self._outputs = outputs
        self._renderer = renderer
        self._metadata = metadata or NotebookNode()
        attributes["output_count"] = len(outputs)  # for debugging with pformat
        super().__init__("", **attributes)

    @property
    def outputs(self) -> List[NotebookNode]:
        """The outputs associated with this cell."""
        return self._outputs

    @property
    def metadata(self) -> NotebookNode:
        """The cell level metadata for this output."""
        return self._metadata

    @property
    def renderer(self) -> str:
        """The renderer for this output cell."""
        return self._renderer

    def copy(self):
        obj = self.__class__(
            outputs=self._outputs,
            renderer=self._renderer,
            metadata=self._metadata,
            **self.attributes,
        )
        obj.document = self.document
        obj.source = self.source
        obj.line = self.line
        return obj


class JupyterWidgetStateNode(nodes.Element):
    """Appended to doctree if any Jupyter cell produced a widget as output.

    Contains the state needed to render a collection of Jupyter widgets.

    Per doctree there is 1 JupyterWidgetStateNode per kernel that produced
    Jupyter widgets when running. This is fine as (presently) the
    'html-manager' Javascript library, which embeds widgets, loads the state
    from all script tags on the page of the correct mimetype.
    """

    def __init__(
        self, rawsource: str = "", *children: nodes.Element, **attributes: Any
    ):
        if "state" not in attributes:
            raise ValueError("No 'state' specified")
        super().__init__(rawsource, *children, **attributes)

    def html(self):
        """Set in extension setup for html rendering visits."""
        # TODO: render into a separate file if 'html-manager' starts fully
        #       parsing script tags, and not just grabbing their innerHTML
        # https://github.com/jupyter-widgets/ipywidgets/blob/master/packages/html-manager/src/libembed.ts#L36
        return snippet_template.format(
            load="", widget_views="", json_data=json.dumps(self["state"])
        )


class JupyterWidgetViewNode(nodes.Element):
    """Inserted into doctree whenever a Jupyter cell produces a widget as output.

    Contains a unique ID for this widget; enough information for the widget
    embedding javascript to render it, given the widget state. For non-HTML
    outputs this doctree node is rendered generically.
    """

    def __init__(
        self, rawsource: str = "", *children: nodes.Element, **attributes: Any
    ):
        if "view_spec" not in attributes:
            raise ValueError("No 'view_spec' specified")
        super().__init__(rawsource, *children, **attributes)

    def html(self):
        """Set in extension setup for html rendering visits."""
        return widget_view_template.format(view_spec=json.dumps(self["view_spec"]))

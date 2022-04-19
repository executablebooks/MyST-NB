"""Roles which can be used by both docutils and sphinx.

We intentionally do no import sphinx in this module,
in order to allow docutils-only use without sphinx installed.
"""
from typing import List, Optional, Tuple

from docutils import nodes
from docutils.parsers.rst.states import Inliner
from docutils.utils import unescape

from myst_nb.core.render import MimeData

from .utils import (
    RetrievalError,
    render_glue_output,
    retrieve_glue_data,
    set_source_info,
    warning,
)


class _PasteRoleBase:
    """A role for pasting inline code outputs from notebooks."""

    @property
    def document(self) -> nodes.document:
        """Get the document."""
        return self.inliner.document

    def get_source_info(self, lineno: Optional[int] = None) -> Tuple[str, int]:
        """Get source and line number."""
        if lineno is None:
            lineno = self.lineno
        return self.inliner.reporter.get_source_and_line(lineno)

    def set_source_info(self, node: nodes.Node, lineno: Optional[int] = None) -> None:
        """Set the source info for a node and its descendants."""
        source, line = self.get_source_info(lineno)
        set_source_info(node, source, line)

    def __call__(
        self,
        name: str,
        rawtext: str,
        text: str,
        lineno: int,
        inliner: Inliner,
        options=None,
        content=(),
    ) -> Tuple[List[nodes.Node], List[nodes.system_message]]:
        self.text: str = unescape(text)
        self.lineno = lineno
        self.inliner = inliner
        self.rawtext = rawtext
        return self.run()

    def run(self) -> Tuple[List[nodes.Node], List[nodes.system_message]]:
        """Run the role."""
        raise NotImplementedError


class PasteRoleAny(_PasteRoleBase):
    """A role for pasting inline code outputs from notebooks,
    using render priority to decide the output mime type.
    """

    def run(self) -> Tuple[List[nodes.Node], List[nodes.system_message]]:
        source, line = self.get_source_info()
        try:
            data = retrieve_glue_data(self.document, self.text)
        except RetrievalError as exc:
            return [], [warning(str(exc), self.document, line)]
        paste_nodes = render_glue_output(
            data,
            self.document,
            line,
            source,
            inline=True,
        )
        return paste_nodes, []


class PasteTextRole(_PasteRoleBase):
    """A role for pasting text outputs from notebooks."""

    def run(self) -> Tuple[List[nodes.Node], List[nodes.system_message]]:
        # check if we have both key:format in the key
        parts = self.text.rsplit(":", 1)
        if len(parts) == 2:
            key, formatting = parts
        else:
            key = parts[0]
            formatting = None

        # now retrieve the data

        try:
            result = retrieve_glue_data(self.document, key)
        except RetrievalError as exc:
            return [], [warning(str(exc), self.document, self.lineno)]
        if "text/plain" not in result.data:
            return [], [
                warning(
                    f"No text/plain found in {key!r} data", self.document, self.lineno
                )
            ]

        text = str(result.data["text/plain"]).strip("'")

        # If formatting is specified, see if we have a number of some kind
        if formatting:
            try:
                newtext = float(text)
                text = f"{newtext:>{formatting}}"
            except ValueError:
                pass

        node = nodes.inline(text, text, classes=["pasted-text"])
        self.set_source_info(node)
        return [node], []


class PasteMarkdownRole(_PasteRoleBase):
    """A role for pasting markdown outputs from notebooks as inline MyST Markdown."""

    def run(self) -> Tuple[List[nodes.Node], List[nodes.system_message]]:
        # check if we have both key:format in the key
        parts = self.text.rsplit(":", 1)
        if len(parts) == 2:
            key, fmt = parts
        else:
            key = parts[0]
            fmt = "commonmark"
        # TODO - check fmt is valid
        # retrieve the data

        try:
            result = retrieve_glue_data(self.document, key)
        except RetrievalError as exc:
            return [], [warning(str(exc), self.document, self.lineno)]
        if "text/markdown" not in result.data:
            return [], [
                warning(
                    f"No text/markdown found in {key!r} data",
                    self.document,
                    self.lineno,
                )
            ]

        # TODO this feels a bit hacky
        cell_key = result.nb_renderer.renderer.nb_config.cell_render_key
        mime = MimeData(
            "text/markdown",
            result.data["text/markdown"],
            cell_metadata={
                cell_key: {"markdown_format": fmt},
            },
            output_metadata=result.metadata,
            line=self.lineno,
        )
        _nodes = result.nb_renderer.render_markdown_inline(mime)
        for node in _nodes:
            self.set_source_info(node)
        return _nodes, []

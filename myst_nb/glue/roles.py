"""Roles which can be used by both docutils and sphinx.

We intentionally do no import sphinx in this module,
in order to allow docutils-only use without sphinx installed.
"""
from typing import List, Tuple

from docutils import nodes
from docutils.parsers.rst.states import Inliner
from docutils.utils import unescape

from myst_nb.core.render import MimeData

from .utils import (
    PendingGlueReferenceError,
    RetrievalError,
    create_pending_glue_ref,
    format_plain_text,
    glue_warning,
    render_glue_output,
    retrieve_glue_data,
    set_source_info,
)


class _PasteRoleBase:
    """A role for pasting inline code outputs from notebooks."""

    @property
    def document(self) -> nodes.document:
        """Get the document."""
        return self.inliner.document

    def set_source_info(self, node: nodes.Node) -> None:
        """Set the source info for a node and its descendants."""
        set_source_info(node, self.source, self.line)

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
        self.inliner = inliner
        self.rawtext = rawtext
        source, line = inliner.reporter.get_source_and_line(lineno)
        self.source: str = source
        self.line: int = line
        return self.run()

    def run(self) -> Tuple[List[nodes.Node], List[nodes.system_message]]:
        """Run the role."""
        raise NotImplementedError


class PasteRoleAny(_PasteRoleBase):
    """A role for pasting inline code outputs from notebooks,
    using render priority to decide the output mime type.
    """

    def run(self) -> Tuple[List[nodes.Node], List[nodes.system_message]]:

        # check if this is a pending reference
        doc_key = self.text.split("::", 1)
        if len(doc_key) == 2:
            doc, key = doc_key
            try:
                ref = create_pending_glue_ref(
                    self.document, self.source, self.line, doc, key, inline=True
                )
            except PendingGlueReferenceError as exc:
                return [], [
                    glue_warning(
                        str(exc),
                        self.document,
                        self.line,
                    )
                ]
            return [ref], []

        try:
            data = retrieve_glue_data(self.document, self.text)
        except RetrievalError as exc:
            return [], [glue_warning(str(exc), self.document, self.line)]
        paste_nodes = render_glue_output(
            data,
            self.document,
            self.line,
            self.source,
            inline=True,
        )
        return paste_nodes, []


class PasteTextRole(_PasteRoleBase):
    """A role for pasting text/plain outputs from notebooks.

    The role content should follow the format: ``<docpath>::<key>:<format_spec>``, where:

    - ``<docpath>`` (optional) is the relative path to another notebook, defaults to local.
    - ``<key>`` is the key
    - ``<format_spec>`` (optional) is a format specifier,
      defined in: https://docs.python.org/3/library/string.html#format-specification-mini-language,
      it must end in the type character.
    """

    def run(self) -> Tuple[List[nodes.Node], List[nodes.system_message]]:
        # check if we have both key:format in the key
        key_format = self.text.rsplit(":", 1)
        if len(key_format) == 2:
            key, fmt_spec = key_format
        else:
            key = key_format[0]
            fmt_spec = "s"

        # check if this is a pending reference
        doc_key = key.split("::", 1)
        if len(doc_key) == 2:
            doc, key = doc_key
            try:
                ref = create_pending_glue_ref(
                    self.document,
                    self.source,
                    self.line,
                    doc,
                    key,
                    inline=True,
                    gtype="text",
                    fmt_spec=fmt_spec,
                )
            except PendingGlueReferenceError as exc:
                return [], [
                    glue_warning(
                        str(exc),
                        self.document,
                        self.line,
                    )
                ]
            return [ref], []

        # now retrieve the data

        try:
            result = retrieve_glue_data(self.document, key)
        except RetrievalError as exc:
            return [], [
                glue_warning(
                    f"{exc} (use `path::key`, to glue from another document)",
                    self.document,
                    self.line,
                )
            ]
        if "text/plain" not in result.data:
            return [], [
                glue_warning(
                    f"No text/plain found in {key!r} data", self.document, self.line
                )
            ]

        try:
            text = format_plain_text(result.data["text/plain"], fmt_spec)
        except Exception as exc:
            return [], [
                glue_warning(
                    f"Failed to format text/plain data: {exc}", self.document, self.line
                )
            ]
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
            return [], [glue_warning(str(exc), self.document, self.line)]
        if "text/markdown" not in result.data:
            return [], [
                glue_warning(
                    f"No text/markdown found in {key!r} data",
                    self.document,
                    self.line,
                )
            ]

        # TODO this feels a bit hacky
        cell_key = result.nb_renderer.renderer.nb_config.cell_metadata_key
        mime = MimeData(
            "text/markdown",
            result.data["text/markdown"],
            cell_metadata={
                cell_key: {"markdown_format": fmt},
            },
            output_metadata=result.metadata,
            line=self.line,
        )
        _nodes = result.nb_renderer.render_markdown_inline(mime)
        for node in _nodes:
            self.set_source_info(node)
        return _nodes, []

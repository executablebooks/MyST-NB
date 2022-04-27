"""Utilities for working with docutils and sphinx.

We intentionally do no import sphinx in this module,
in order to allow docutils-only use without sphinx installed.
"""
from ast import literal_eval
import dataclasses as dc
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

from docutils import nodes

from myst_nb._compat import findall
from myst_nb.core.loggers import DocutilsDocLogger, SphinxDocLogger
from myst_nb.core.render import MimeData, NbElementRenderer, get_mime_priority

if TYPE_CHECKING:
    from sphinx.environment import BuildEnvironment


def is_sphinx(document) -> bool:
    """Return True if we are in sphinx, otherwise docutils."""
    return hasattr(document.settings, "env")


def glue_warning(
    message: str, document: nodes.document, line: int
) -> nodes.system_message:
    """Create a warning related to glue functionality."""
    logger: Union[DocutilsDocLogger, SphinxDocLogger]
    if is_sphinx(document):
        logger = SphinxDocLogger(document)
    else:
        logger = DocutilsDocLogger(document)
    logger.warning(message, line=line, subtype="glue")
    return nodes.system_message(
        message,
        type="WARNING",
        level=2,
        line=line,
        source=document["source"],
    )


def set_source_info(node: nodes.Node, source: str, line: int) -> None:
    """Set the source info for a node and its descendants."""
    for _node in findall(node)(include_self=True):
        _node.source = source
        _node.line = line


@dc.dataclass()
class RetrievedData:
    """A class to store retrieved mime data."""

    data: Dict[str, Any]
    metadata: Dict[str, Any]
    nb_renderer: NbElementRenderer


class RetrievalError(Exception):
    """An error occurred while retrieving the glue data."""


def retrieve_glue_data(document: nodes.document, key: str) -> RetrievedData:
    """Retrieve the glue data from a specific document."""
    msg = f"No key {key!r} found in glue data for this document."
    if "nb_renderer" not in document:
        raise RetrievalError(msg)
    nb_renderer: NbElementRenderer = document["nb_renderer"]
    resources = nb_renderer.get_resources()
    if "glue" not in resources:
        raise RetrievalError(msg)

    if key not in resources["glue"]:
        raise RetrievalError(msg)

    return RetrievedData(
        data=resources["glue"][key]["data"],
        metadata=resources["glue"][key].get("metadata", {}),
        nb_renderer=nb_renderer,
    )


def render_glue_output(
    data: RetrievedData,
    document: nodes.document,
    line: int,
    source: str,
    *,
    inline: bool = False,
    render: Optional[Dict[str, Any]] = None,
) -> List[nodes.Node]:
    """Retrive the notebook output data for this glue key,
    then return the docutils/sphinx nodes relevant to this data.

    :param key: The glue key to retrieve.
    :param document: The current docutils document.
    :param line: The current source line number of the directive or role.
    :param source: The current source path or description.
    :param inline: Whether to render the output as inline (or block).
    :param render: Cell-level render metadata

    :returns: A tuple of (was the key found, the docutils/sphinx nodes).
    """
    cell_metadata = {}
    if render:
        cell_metadata[data.nb_renderer.config.cell_metadata_key] = render
    if is_sphinx(document):
        _nodes = _render_output_sphinx(
            data.nb_renderer,
            data.data,
            cell_metadata,
            data.metadata,
            source,
            line,
            inline,
        )
    else:
        _nodes = _render_output_docutils(
            data.nb_renderer,
            data.data,
            cell_metadata,
            data.metadata,
            document,
            line,
            inline,
        )
    # TODO rendering should perhaps return if it succeeded explicitly,
    # and whether system_messages or not (required for roles)
    return _nodes


def _render_output_docutils(
    nb_renderer: NbElementRenderer,
    data: Dict[str, Any],
    cell_metadata: Dict[str, Any],
    output_metadata: Dict[str, Any],
    document: nodes.document,
    line: int,
    inline=False,
) -> List[nodes.Node]:
    """Render the output in docutils (select mime priority directly)."""
    mime_priority = get_mime_priority(
        nb_renderer.config.builder_name,
        nb_renderer.config.mime_priority_overrides,
    )
    try:
        mime_type = next(x for x in mime_priority if x in data)
    except StopIteration:
        return [
            glue_warning(
                "No output mime type found from render_priority",
                document,
                line,
            )
        ]
    else:
        mime_data = MimeData(
            mime_type,
            data[mime_type],
            cell_metadata=cell_metadata,
            output_metadata=output_metadata,
            line=line,
        )
        if inline:
            return nb_renderer.render_mime_type_inline(mime_data)
        return nb_renderer.render_mime_type(mime_data)


def _render_output_sphinx(
    nb_renderer: NbElementRenderer,
    data: Dict[str, Any],
    cell_metadata: Dict[str, Any],
    output_metadata: Dict[str, Any],
    source: str,
    line: int,
    inline=False,
) -> List[nodes.Node]:
    """Render the output in sphinx (defer mime priority selection)."""
    mime_bundle = nodes.container(nb_element="mime_bundle")
    set_source_info(mime_bundle, source, line)
    for mime_type, content in data.items():
        mime_container = nodes.container(mime_type=mime_type)
        set_source_info(mime_container, source, line)
        mime_data = MimeData(
            mime_type,
            content,
            cell_metadata=cell_metadata,
            output_metadata=output_metadata,
            line=line,
        )
        if inline:
            _nodes = nb_renderer.render_mime_type_inline(mime_data)
        else:
            _nodes = nb_renderer.render_mime_type(mime_data)
        if _nodes:
            mime_container.extend(_nodes)
            mime_bundle.append(mime_container)
    return [mime_bundle]


class PendingGlueReference(nodes.Element):
    """A glue reference to another document."""

    @property
    def refdoc(self) -> str:
        return self.attributes["refdoc"]

    @property
    def key(self) -> str:
        return self.attributes["key"]

    @property
    def inline(self) -> bool:
        return self.attributes.get("inline", False)

    @property
    def gtype(self) -> Optional[str]:
        return self.attributes.get("gtype", None)


class PendingGlueReferenceError(Exception):
    """An error occurred while resolving a pending glue reference."""


def create_pending_glue_ref(
    document: nodes.document,
    source: str,
    line: int,
    rel_doc: str,
    key: str,
    inline: bool = False,
    gtype: Optional[str] = None,
    **kwargs: Any,
) -> PendingGlueReference:
    """Create a pending glue reference."""
    if not is_sphinx(document):
        raise PendingGlueReferenceError(
            "Pending glue references are only supported in sphinx."
        )
    env: "BuildEnvironment" = document.settings.env
    _, filepath = env.relfn2path(rel_doc, env.docname)
    refdoc = env.path2doc(filepath)
    if refdoc is None:
        raise PendingGlueReferenceError(
            f"Pending glue reference document not found: {filepath!r}."
        )
    ref = PendingGlueReference(
        refdoc=refdoc, key=key, inline=inline, gtype=gtype, **kwargs
    )
    ref.source = source
    ref.line = line
    return ref


def format_plain_text(text: str, fmt_spec: str) -> str:
    """Format plain text for display in a docutils node."""
    # literal eval, to remove surrounding quotes
    try:
        value = literal_eval(text)
    except (SyntaxError, ValueError):
        value = text
    if fmt_spec == "":
        return str(value)
    type_char = fmt_spec[-1]
    if type_char == "s":
        value = str(value)
    elif type_char in ("b", "c", "d", "o", "x", "X"):
        value = int(value)
    elif type_char in ("e", "E", "f", "F", "g", "G", "n", "%"):
        value = float(value)
    return format(value, fmt_spec)

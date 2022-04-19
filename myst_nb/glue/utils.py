"""Utilities for working with docutils and sphinx.

We intentionally do no import sphinx in this module,
in order to allow docutils-only use without sphinx installed.
"""
import dataclasses as dc
from typing import Any, Dict, List, Union

from docutils import nodes

from myst_nb.core.loggers import DocutilsDocLogger, SphinxDocLogger
from myst_nb.core.render import MimeData, NbElementRenderer


def is_sphinx(document) -> bool:
    """Return True if we are in sphinx, otherwise docutils."""
    return hasattr(document.settings, "env")


def warning(message: str, document: nodes.document, line: int) -> nodes.system_message:
    """Create a warning."""
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
    iterator = getattr(node, "findall", node.traverse)  # findall for docutils 0.18
    for _node in iterator(include_self=True):
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
    if "nb_renderer" not in document:
        raise RetrievalError("No 'nb_renderer' found on the document.")
    nb_renderer: NbElementRenderer = document["nb_renderer"]
    resources = nb_renderer.get_resources()
    if "glue" not in resources:
        raise RetrievalError(f"No key {key!r} found in glue data.")

    if key not in resources["glue"]:
        raise RetrievalError(f"No key {key!r} found in glue data.")

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
    inline=False,
) -> List[nodes.Node]:
    """Retrive the notebook output data for this glue key,
    then return the docutils/sphinx nodes relevant to this data.

    :param key: The glue key to retrieve.
    :param document: The current docutils document.
    :param line: The current source line number of the directive or role.
    :param source: The current source path or description.
    :param inline: Whether to render the output as inline (or block).

    :returns: A tuple of (was the key found, the docutils/sphinx nodes).
    """
    if is_sphinx(document):
        _nodes = _render_output_sphinx(
            data.nb_renderer, data.data, data.metadata, source, line, inline
        )
    else:
        _nodes = _render_output_docutils(
            data.nb_renderer, data.data, data.metadata, document, line, inline
        )
    # TODO rendering should perhaps return if it succeeded explicitly,
    # and whether system_messages or not (required for roles)
    return _nodes


def _render_output_docutils(
    nb_renderer: NbElementRenderer,
    data: Dict[str, Any],
    metadata: Dict[str, Any],
    document: nodes.document,
    line: int,
    inline=False,
) -> List[nodes.Node]:
    """Render the output in docutils (select mime priority directly)."""
    mime_priority = nb_renderer.renderer.nb_config.mime_priority
    try:
        mime_type = next(x for x in mime_priority if x in data)
    except StopIteration:
        return [
            warning(
                "No output mime type found from render_priority",
                document,
                line,
            )
        ]
    else:
        mime_data = MimeData(
            mime_type,
            data[mime_type],
            output_metadata=metadata,
            line=line,
        )
        if inline:
            return nb_renderer.render_mime_type_inline(mime_data)
        return nb_renderer.render_mime_type(mime_data)


def _render_output_sphinx(
    nb_renderer: NbElementRenderer,
    data: Dict[str, Any],
    metadata: Dict[str, Any],
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
        mime_data = MimeData(mime_type, content, output_metadata=metadata, line=line)
        if inline:
            _nodes = nb_renderer.render_mime_type_inline(mime_data)
        else:
            _nodes = nb_renderer.render_mime_type(mime_data)
        if _nodes:
            mime_container.extend(_nodes)
            mime_bundle.append(mime_container)
    return [mime_bundle]

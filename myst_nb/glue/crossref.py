"""Sphinx only cross-document gluing.

Note, we restrict this to a only a subset of mime-types and data -> nodes transforms,
since adding these nodes in a post-transform will not apply any transforms to them.
"""
from functools import lru_cache
import json
from pathlib import Path
from typing import Any, Dict, List, Sequence

from docutils import nodes
from sphinx.transforms.post_transforms import SphinxPostTransform
from sphinx.util import logging as sphinx_logging

from myst_nb._compat import findall
from myst_nb.core.loggers import DEFAULT_LOG_TYPE

from .utils import PendingGlueReference

SPHINX_LOGGER = sphinx_logging.getLogger(__name__)


@lru_cache(maxsize=3)
def read_glue_cache(folder: str, docname: str) -> Dict[str, Any]:
    """Read a glue cache from the build folder, for a particular document."""
    docpath = docname.split("/")
    path = Path(folder).joinpath(*docpath[:-1]).joinpath(f"{docpath[-1]}.glue.json")
    if not path.exists():
        return {}
    with path.open("r") as f:
        return json.load(f)


def generate_nodes(
    cell: Dict[str, Any], priority_list: Sequence[str], inline: bool
) -> List[nodes.Element]:
    data = cell["data"]
    for mime_type in priority_list:
        if mime_type not in data:
            continue
        if mime_type == "text/plain":
            if inline:
                return [nodes.literal(data[mime_type], data[mime_type])]
            else:
                return [nodes.literal_block(data[mime_type], data[mime_type])]
        if mime_type == "text/html":
            return [
                nodes.raw(
                    text=data[mime_type], format="html", classes=["output", "text_html"]
                )
            ]
    return []


class ReplacePendingGlueReferences(SphinxPostTransform):
    """Sphinx only cross-document gluing.

    Note, we restrict this to a only a subset of mime-types and data -> nodes transforms,
    since adding these nodes in a post-transform will not apply any transforms to them.
    """

    default_priority = 5

    def apply(self, **kwargs):
        """Apply the transform."""
        cache_folder = self.env.mystnb_config.output_folder  # type: ignore
        priority_lookup: Dict[str, Sequence[str]] = self.config["nb_render_priority"]
        name = self.app.builder.name  # type: ignore
        if name not in priority_lookup:
            SPHINX_LOGGER.warning(
                f"Builder name {name!r} not available in 'nb_render_priority', "
                f"defaulting to 'html' [{DEFAULT_LOG_TYPE}.mime_priority]",
                type=DEFAULT_LOG_TYPE,
                subtype="mime_priority",
            )
            priority_list = priority_lookup["html"]
        else:
            priority_list = priority_lookup[name]
        node: PendingGlueReference
        for node in list(findall(self.document)(PendingGlueReference)):
            data = read_glue_cache(cache_folder, node.refdoc)
            if node.key not in data:
                SPHINX_LOGGER.warning(
                    f"Glue reference {node.key!r} not found in doc {node.refdoc!r} "
                    f"[{DEFAULT_LOG_TYPE}.glue_ref]",
                    type=DEFAULT_LOG_TYPE,
                    subtype="glue_ref",
                    location=node,
                )
                node.parent.remove(node)
                continue
            _nodes = generate_nodes(data[node.key], priority_list, node.inline)
            if not _nodes:
                SPHINX_LOGGER.warning(
                    f"No allowed mime type found in {node.key!r}: {list(data[node.key]['data'])}"
                    f"[{DEFAULT_LOG_TYPE}.glue_ref]",
                    type=DEFAULT_LOG_TYPE,
                    subtype="glue_ref",
                    location=node,
                )
                node.parent.remove(node)
                continue
            node.replace_self(_nodes)

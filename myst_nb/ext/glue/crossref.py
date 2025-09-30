"""Sphinx only cross-document gluing.

Note, we restrict this to a only a subset of mime-types and data -> nodes transforms,
since adding these nodes in a post-transform will not apply any transforms to them.
"""

from __future__ import annotations

from binascii import a2b_base64
from functools import lru_cache
import hashlib
import json
from mimetypes import guess_extension
from pathlib import Path
from typing import Any, Sequence
import os

from docutils import nodes
from sphinx.builders import Builder
from sphinx.environment import BuildEnvironment
from sphinx.transforms.post_transforms import SphinxPostTransform
from sphinx.util import logging as sphinx_logging

from myst_nb._compat import findall
from myst_nb.core.loggers import DEFAULT_LOG_TYPE
from myst_nb.core.render import get_mime_priority
from myst_nb.core.variables import format_plain_text

from .utils import PendingGlueReference

SPHINX_LOGGER = sphinx_logging.getLogger(__name__)


@lru_cache(maxsize=3)
def read_glue_cache(folder: str, docname: str) -> dict[str, Any]:
    """Read a glue cache from the build folder, for a particular document."""
    docpath = docname.split("/")
    path = Path(folder).joinpath(*docpath[:-1]).joinpath(f"{docpath[-1]}.glue.json")
    if not path.exists():
        return {}
    with path.open("r") as f:
        return json.load(f)


class ReplacePendingGlueReferences(SphinxPostTransform):
    """Sphinx only cross-document gluing.

    Note, we restrict this to a only a subset of mime-types and data -> nodes transforms,
    since adding these nodes in a post-transform will not apply any transforms to them.
    """

    default_priority = 5

    def apply(self, **kwargs):
        """Apply the transform."""
        cache_folder = self.env.mystnb_config.output_folder  # type: ignore
        bname = self.app.builder.name
        priority_list = get_mime_priority(
            bname, self.config["nb_mime_priority_overrides"]
        )
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
            output = data[node.key]
            if node.gtype == "text":
                _nodes = generate_text_nodes(node, output)
            else:
                _nodes = generate_any_nodes(
                    node,
                    output,
                    priority_list,
                    self.app.builder,
                    self.env,
                )

            if _nodes:
                node.replace_self(_nodes)
            else:
                node.parent.remove(node)


def ref_warning(msg: str, node) -> None:
    """Log a warning for a reference."""
    SPHINX_LOGGER.warning(
        f"{msg} [{DEFAULT_LOG_TYPE}.glue_ref]",
        type=DEFAULT_LOG_TYPE,
        subtype="glue_ref",
        location=node,
    )


def generate_any_nodes(
    node: PendingGlueReference,
    output: dict[str, Any],
    priority_list: Sequence[str],
    builder: Builder,
    env: BuildEnvironment,
) -> list[nodes.Element]:
    """Generate nodes for a cell, according to the highest priority mime type."""
    data = output["data"]
    for mime_type in priority_list:
        if mime_type not in data:
            continue
        if mime_type == "text/plain":
            if node.inline:
                return [nodes.literal(data[mime_type], data[mime_type])]
            else:
                return [nodes.literal_block(data[mime_type], data[mime_type])]
        if mime_type == "text/html":
            return [
                nodes.raw(
                    text=data[mime_type], format="html", classes=["output", "text_html"]
                )
            ]
        if mime_type in {
            "image/png",
            "image/jpeg",
            "image/gif",
            "application/pdf",
        }:
            # this is mostly a copy of mystnb/core/render.py::render_image

            # data is b64-encoded as text
            data_bytes = a2b_base64(data[mime_type])

            # create filename
            extension = guess_extension(mime_type) or "." + mime_type.rsplit("/")[-1]
            # latex does not recognize the '.jpe' extension
            extension = ".jpeg" if extension == ".jpe" else extension

            data_hash = hashlib.sha256(data_bytes).hexdigest()
            filename = f"{data_hash}{extension}"

            # now we resolve the relative path to the image
            imgdir = Path(builder.imagedir)
            outdir = Path(builder.outdir)
            page_dir = (outdir / env.docname).parent
            filepath = outdir / imgdir / filename

            uri = os.path.relpath(filepath, page_dir)
            image_node = nodes.image(uri=uri)
            image_node["candidates"] = {"*": uri}

            return [image_node]

    ref_warning(
        f"No allowed mime type found in {node.key!r}: {list(output['data'])}", node
    )
    return []


def generate_text_nodes(node: PendingGlueReference, output: dict[str, Any]):
    """Generate nodes for a cell, for formatted text/plain."""
    data = output["data"]
    if "text/plain" not in data:
        ref_warning(f"No text/plain found in {node.key!r}", node)
        return []
    try:
        text = format_plain_text(data["text/plain"], node["fmt_spec"])
    except Exception as exc:
        ref_warning(f"Failed to format text/plain: {exc}", node)
        return []
    return [nodes.inline(text, text, classes=["pasted-text"])]

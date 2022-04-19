"""Functionality for storing special data in notebook code cells,
which can then be inserted into the document body.
"""
from typing import Any, Dict, List

import IPython
from IPython.display import display as ipy_display
from nbformat import NotebookNode

from myst_nb.core.loggers import LoggerType

GLUE_PREFIX = "application/papermill.record/"


def get_glue_roles(prefix: str = "glue:") -> Dict[str, Any]:
    """Return mapping of role names to role functions."""
    from .roles import PasteMarkdownRole, PasteRoleAny, PasteTextRole

    return {
        f"{prefix}": PasteRoleAny(),
        f"{prefix}any": PasteRoleAny(),
        f"{prefix}text": PasteTextRole(),
        f"{prefix}md": PasteMarkdownRole(),
    }


def get_glue_directives(prefix: str = "glue:") -> Dict[str, Any]:
    """Return mapping of directive names to directive functions."""
    from .directives import (
        PasteAnyDirective,
        PasteFigureDirective,
        PasteMarkdownDirective,
        PasteMathDirective,
    )

    return {
        f"{prefix}": PasteAnyDirective,
        f"{prefix}any": PasteAnyDirective,
        f"{prefix}figure": PasteFigureDirective,
        f"{prefix}math": PasteMathDirective,
        f"{prefix}md": PasteMarkdownDirective,
    }


def glue(name: str, variable, display: bool = True) -> None:
    """Glue a variable into the notebook's cell metadata.

    Parameters
    ----------
    name: string
        A unique name for the variable. You can use this name to refer to the variable
        later on.
    variable: Python object
        A variable in Python for which you'd like to store its display value. This is
        not quite the same as storing the object itself - the stored information is
        what is *displayed* when you print or show the object in a Jupyter Notebook.
    display: bool
        Display the object you are gluing. This is helpful in sanity-checking the
        state of the object at glue-time.
    """
    mimebundle, metadata = IPython.core.formatters.format_display_data(variable)
    mime_prefix = "" if display else GLUE_PREFIX
    metadata["scrapbook"] = dict(name=name, mime_prefix=mime_prefix)
    ipy_display(
        {mime_prefix + k: v for k, v in mimebundle.items()}, raw=True, metadata=metadata
    )


def extract_glue_data(
    notebook: NotebookNode,
    resources: Dict[str, Any],
    source_map: List[int],
    logger: LoggerType,
) -> None:
    """Extract all the glue data from the notebook, into the resources dictionary."""
    # note this assumes v4 notebook format
    data: Dict[str, NotebookNode] = resources.setdefault("glue", {})
    for index, cell in enumerate(notebook.cells):
        if cell.cell_type != "code":
            continue
        outputs = []
        for output in cell.get("outputs", []):
            meta = output.get("metadata", {})
            if "scrapbook" not in meta:
                outputs.append(output)
                continue
            key = meta["scrapbook"]["name"]
            mime_prefix = len(meta["scrapbook"].get("mime_prefix", ""))
            if key in data:
                logger.warning(
                    f"glue key {key!r} duplicate",
                    subtype="glue",
                    line=source_map[index],
                )
            output["data"] = {k[mime_prefix:]: v for k, v in output["data"].items()}
            data[key] = output
            if not mime_prefix:
                # assume that the output is a displayable object
                outputs.append(output)
        cell.outputs = outputs

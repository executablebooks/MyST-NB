"""notebook "pre-processing" (after execution, but before parsing)"""
from __future__ import annotations

import re
from typing import Any

from nbformat import NotebookNode

from myst_nb.core.config import NbParserConfig
from myst_nb.core.loggers import LoggerType
from myst_nb.glue import extract_glue_data


def preprocess_notebook(
    notebook: NotebookNode, logger: LoggerType, nb_config: NbParserConfig
) -> dict[str, Any]:
    """Modify notebook and resources in-place."""
    # TODO make this pluggable
    # (similar to nbconvert preprocessors, but parse config, source map and logger)

    resources: dict[str, Any] = {}

    # create source map
    source_map = notebook.metadata.get("source_map", None)
    # use 1-based indexing rather than 0, or pseudo base of the cell index
    source_map = [
        (source_map[i] if source_map else ((i + 1) * 10000)) + 1
        for i, _ in enumerate(notebook.cells)
    ]

    # coalesce_streams
    for i, cell in enumerate(notebook.cells):
        if cell.cell_type == "code":
            _callback = lambda m, t: logger.warning(  # noqa: E731
                m, subtype=t, line=source_map[i]
            )
            if nb_config.get_cell_level_config(
                "merge_streams", cell.metadata, _callback
            ):
                cell["outputs"] = coalesce_streams(cell.get("outputs", []))

    # extract all scrapbook (aka glue) outputs from notebook
    extract_glue_data(notebook, resources, source_map, logger)

    return resources


_RGX_CARRIAGERETURN = re.compile(r".*\r(?=[^\n])")
_RGX_BACKSPACE = re.compile(r"[^\n]\b")


def coalesce_streams(outputs: list[NotebookNode]) -> list[NotebookNode]:
    """Merge all stream outputs with shared names into single streams.

    This ensure deterministic outputs.

    Adapted from:
    https://github.com/computationalmodelling/nbval/blob/master/nbval/plugin.py.
    """
    if not outputs:
        return []

    new_outputs = []
    streams: dict[str, NotebookNode] = {}
    for output in outputs:
        if output["output_type"] == "stream":
            if output["name"] in streams:
                streams[output["name"]]["text"] += output["text"]
            else:
                new_outputs.append(output)
                streams[output["name"]] = output
        else:
            new_outputs.append(output)

    # process \r and \b characters
    for output in streams.values():
        old = output["text"]
        while len(output["text"]) < len(old):
            old = output["text"]
            # Cancel out anything-but-newline followed by backspace
            output["text"] = _RGX_BACKSPACE.sub("", output["text"])
        # Replace all carriage returns not followed by newline
        output["text"] = _RGX_CARRIAGERETURN.sub("", output["text"])

    # We also want to ensure stdout and stderr are always in the same consecutive order,
    # because they are asynchronous, so order isn't guaranteed.
    for i, output in enumerate(new_outputs):
        if output["output_type"] == "stream" and output["name"] == "stderr":
            if (
                len(new_outputs) >= i + 2
                and new_outputs[i + 1]["output_type"] == "stream"
                and new_outputs[i + 1]["name"] == "stdout"
            ):
                stdout = new_outputs.pop(i + 1)
                new_outputs.insert(i, stdout)

    return new_outputs

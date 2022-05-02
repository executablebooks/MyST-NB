"""Module for executing notebooks."""
from __future__ import annotations

from contextlib import nullcontext, suppress
from datetime import datetime
import os
from pathlib import Path, PurePosixPath
from tempfile import TemporaryDirectory
from typing import Any, ContextManager

from jupyter_cache import get_cache
from jupyter_cache.base import CacheBundleIn
from jupyter_cache.cache.db import NbProjectRecord
from jupyter_cache.executors.utils import single_nb_execution
from nbformat import NotebookNode
from typing_extensions import TypedDict

from myst_nb.core.config import NbParserConfig
from myst_nb.core.loggers import LoggerType
from myst_nb.core.nb_to_tokens import nb_node_to_dict
from myst_nb.glue import extract_glue_data


class ExecutionResult(TypedDict):
    """Result of executing a notebook."""

    mtime: float
    """POSIX timestamp of the execution time"""
    runtime: float | None
    """runtime in seconds"""
    method: str
    """method used to execute the notebook"""
    succeeded: bool
    """True if the notebook executed successfully"""
    error: str | None
    """error type if the notebook failed to execute"""
    traceback: str | None
    """traceback if the notebook failed"""


class ExecutionError(Exception):
    """An exception for failed execution and `execution_raise_on_error` is true."""


def execute_notebook(
    notebook: NotebookNode,
    source: str,
    nb_config: NbParserConfig,
    logger: LoggerType,
    read_fmt: None | dict = None,
) -> NotebookClientBase:
    """Update a notebook's outputs using the given configuration.

    This function may execute the notebook if necessary, to update its outputs,
    or populate from a cache.

    :param notebook: The notebook to update.
    :param source: Path to or description of the input source being processed.
    :param nb_config: The configuration for the notebook parser.
    :param logger: The logger to use.
    :param read_fmt: The format of the input source (to parse to jupyter cache)

    :returns: The updated notebook, and the (optional) execution metadata.
    """
    # TODO should any of the logging messages be debug instead of info?

    # path should only be None when using docutils programmatically,
    # e.g. source="<string>"
    try:
        path = Path(source) if Path(source).is_file() else None
    except OSError:
        path = None  # occurs on Windows for `source="<string>"`

    # check if the notebook is excluded from execution by pattern
    if path is not None and nb_config.execution_excludepatterns:
        posix_path = PurePosixPath(path.as_posix())
        for pattern in nb_config.execution_excludepatterns:
            if posix_path.match(pattern):
                logger.info(f"Excluded from execution by pattern: {pattern!r}")
                return NotebookClientBase(notebook, logger, None)

    # 'auto' mode only executes the notebook if it is missing at least one output
    missing_outputs = (
        len(cell.outputs) == 0 for cell in notebook.cells if cell["cell_type"] == "code"
    )
    if nb_config.execution_mode == "auto" and not any(missing_outputs):
        logger.info("Skipped execution in 'auto' mode (all outputs present)")
        return NotebookClientBase(notebook, logger, None)

    if nb_config.execution_mode in ("auto", "force"):

        # setup the execution current working directory
        cwd_context: ContextManager[str]
        if nb_config.execution_in_temp:
            cwd_context = TemporaryDirectory()
        else:
            if path is None:
                raise ValueError(
                    f"source must exist as file, if execution_in_temp=False: {source}"
                )
            cwd_context = nullcontext(str(path.parent))

        # execute in the context of the current working directory
        with cwd_context as cwd:
            cwd = os.path.abspath(cwd)
            logger.info(
                "Executing notebook using "
                + ("temporary" if nb_config.execution_in_temp else "local")
                + " CWD"
            )
            result = single_nb_execution(
                notebook,
                cwd=cwd,
                allow_errors=nb_config.execution_allow_errors,
                timeout=nb_config.execution_timeout,
                meta_override=True,  # TODO still support this?
            )

        if result.err is not None:
            if nb_config.execution_raise_on_error:
                raise ExecutionError(str(source)) from result.err
            msg = f"Executing notebook failed: {result.err.__class__.__name__}"
            if nb_config.execution_show_tb:
                msg += f"\n{result.exc_string}"
            logger.warning(msg, subtype="exec")
        else:
            logger.info(f"Executed notebook in {result.time:.2f} seconds")

        exec_metadata: ExecutionResult = {
            "mtime": datetime.now().timestamp(),
            "runtime": result.time,
            "method": nb_config.execution_mode,
            "succeeded": False if result.err else True,
            "error": f"{result.err.__class__.__name__}" if result.err else None,
            "traceback": result.exc_string if result.err else None,
        }
        return NotebookClientBase(notebook, logger, exec_metadata)

    elif nb_config.execution_mode == "cache":
        return _execute_from_cache(notebook, source, path, nb_config, logger, read_fmt)

    return NotebookClientBase(notebook, logger, None)


def _execute_from_cache(
    notebook: NotebookNode,
    source: str,
    path: Path | None,
    nb_config: NbParserConfig,
    logger: LoggerType,
    read_fmt: None | dict = None,
) -> NotebookClientBase:
    """Execute a notebook from the cache."""

    exec_metadata: ExecutionResult

    # setup the cache
    cache = get_cache(nb_config.execution_cache_path or ".jupyter_cache")
    # TODO config on what notebook/cell metadata to hash/merge

    # attempt to match the notebook to one in the cache
    cache_record = None
    with suppress(KeyError):
        cache_record = cache.match_cache_notebook(notebook)

    # use the cached notebook if it exists
    if cache_record is not None:
        logger.info(f"Using cached notebook: ID={cache_record.pk}")
        _, notebook = cache.merge_match_into_notebook(notebook)
        exec_metadata = {
            "mtime": cache_record.created.timestamp(),
            "runtime": cache_record.data.get("execution_seconds", None),
            "method": nb_config.execution_mode,
            "succeeded": True,
            "error": None,
            "traceback": None,
        }
        return NotebookClientBase(notebook, logger, exec_metadata)

    if path is None:
        raise ValueError(
            f"source must exist as file, if execution_mode is 'cache': {source}"
        )

    # attempt to execute the notebook
    if read_fmt is not None:
        stage_record = cache.add_nb_to_project(str(path), read_data=read_fmt)
    else:
        stage_record = cache.add_nb_to_project(str(path))
    # TODO do in try/except, in case of db write errors
    NbProjectRecord.remove_tracebacks([stage_record.pk], cache.db)
    cwd_context: ContextManager[str] = (
        TemporaryDirectory()  # type: ignore
        if nb_config.execution_in_temp
        else nullcontext(str(path.parent))
    )
    with cwd_context as cwd:
        cwd = os.path.abspath(cwd)
        logger.info(
            "Executing notebook using "
            + ("temporary" if nb_config.execution_in_temp else "local")
            + " CWD"
        )
        result = single_nb_execution(
            notebook,
            cwd=cwd,
            allow_errors=nb_config.execution_allow_errors,
            timeout=nb_config.execution_timeout,
            meta_override=True,  # TODO still support this?
        )

    # handle success / failure cases
    # TODO do in try/except to be careful (in case of database write errors?
    if result.err is not None:
        if nb_config.execution_raise_on_error:
            raise ExecutionError(str(source)) from result.err
        msg = f"Executing notebook failed: {result.err.__class__.__name__}"
        if nb_config.execution_show_tb:
            msg += f"\n{result.exc_string}"
        logger.warning(msg, subtype="exec")
        NbProjectRecord.set_traceback(stage_record.uri, result.exc_string, cache.db)
    else:
        logger.info(f"Executed notebook in {result.time:.2f} seconds")
        cache_record = cache.cache_notebook_bundle(
            CacheBundleIn(
                notebook, stage_record.uri, data={"execution_seconds": result.time}
            ),
            check_validity=False,
            overwrite=True,
        )
        logger.info(f"Cached executed notebook: ID={cache_record.pk}")

    exec_metadata = {
        "mtime": datetime.now().timestamp(),
        "runtime": result.time,
        "method": nb_config.execution_mode,
        "succeeded": False if result.err else True,
        "error": f"{result.err.__class__.__name__}" if result.err else None,
        "traceback": result.exc_string if result.err else None,
    }

    return NotebookClientBase(notebook, logger, exec_metadata)


class NotebookClientBase:
    """A client for interacting with Jupyter notebooks.

    This class is intended to be used as a context manager.
    """

    def __init__(
        self,
        notebook: NotebookNode,
        logger: LoggerType,
        exec_metadata: ExecutionResult | None = None,
    ):
        """Initialize the client."""
        self._notebook = notebook
        self._logger = logger
        self._exec_metadata = exec_metadata

        # get or create source map of cell to source line
        # use 1-based indexing rather than 0, or pseudo base of the cell index
        _source_map: list[int] = notebook.metadata.get("source_map", None)
        self._source_map = [
            (_source_map[i] if _source_map else ((i + 1) * 10000)) + 1
            for i, _ in enumerate(notebook.cells)
        ]

        # extract glue data from the notebook
        self._glue_data = extract_glue_data(notebook, _source_map, logger)

    def __enter__(self):
        """Enter the context manager."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context manager."""

    @property
    def notebook(self) -> NotebookNode:
        """Get the notebook."""
        return self._notebook

    @property
    def logger(self) -> LoggerType:
        """Get the logger."""
        return self._logger

    def cell_line(self, cell_index: int) -> int:
        """Get the source line number of a cell."""
        return self._source_map[cell_index]

    @property
    def exec_metadata(self) -> ExecutionResult | None:
        """Get the execution metadata."""
        return self._exec_metadata

    @property
    def glue_data(self) -> dict[str, NotebookNode]:
        """Get the glue data."""
        return self._glue_data

    @property
    def nb_metadata(self) -> dict[str, Any]:
        """Get the notebook level metadata."""
        return nb_node_to_dict(self.notebook.get("metadata", {}))

    def nb_source_code_lexer(self) -> str | None:
        """Get the lexer for the notebook source code."""
        metadata = self.notebook.get("metadata", {})
        langinfo = metadata.get("language_info") or {}
        lexer = langinfo.get("pygments_lexer") or langinfo.get("name", None)
        if lexer is None:
            lexer = (metadata.get("kernelspec") or {}).get("language", None)
        return lexer

    def code_cell_outputs(
        self, cell_index: int
    ) -> tuple[int | None, list[NotebookNode]]:
        """Get the outputs of a cell.

        :returns: a tuple of the execution_count and the outputs
        :raises IndexError: if the cell index is out of range
        """
        cells = self.notebook.get("cells", [])
        cell = cells[cell_index]
        return cell.get("execution_count", None), cell.get("outputs", [])

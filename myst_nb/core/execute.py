"""Module for executing notebooks."""
from __future__ import annotations

from contextlib import nullcontext, suppress
from datetime import datetime
import os
from pathlib import Path, PurePosixPath
from tempfile import TemporaryDirectory

from jupyter_cache import get_cache
from jupyter_cache.base import CacheBundleIn
from jupyter_cache.cache.db import NbProjectRecord
from jupyter_cache.executors.utils import single_nb_execution
from nbformat import NotebookNode
from typing_extensions import TypedDict

from myst_nb.core.config import NbParserConfig
from myst_nb.core.loggers import LoggerType


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
) -> tuple[NotebookNode, ExecutionResult | None]:
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

    exec_metadata: ExecutionResult | None = None

    # check if the notebook is excluded from execution by pattern
    if path is not None and nb_config.execution_excludepatterns:
        posix_path = PurePosixPath(path.as_posix())
        for pattern in nb_config.execution_excludepatterns:
            if posix_path.match(pattern):
                logger.info(f"Excluded from execution by pattern: {pattern!r}")
                return notebook, exec_metadata

    # 'auto' mode only executes the notebook if it is missing at least one output
    missing_outputs = (
        len(cell.outputs) == 0 for cell in notebook.cells if cell["cell_type"] == "code"
    )
    if nb_config.execution_mode == "auto" and not any(missing_outputs):
        logger.info("Skipped execution in 'auto' mode (all outputs present)")
        return notebook, exec_metadata

    if nb_config.execution_mode in ("auto", "force"):

        # setup the execution current working directory
        if nb_config.execution_in_temp:
            cwd_context = TemporaryDirectory()
        else:
            if path is None:
                raise ValueError(
                    f"source must exist as file, if execution_in_temp=False: {source}"
                )
            cwd_context = nullcontext(str(path.parent))  # type: ignore

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

        exec_metadata = {
            "mtime": datetime.now().timestamp(),
            "runtime": result.time,
            "method": nb_config.execution_mode,
            "succeeded": False if result.err else True,
            "error": f"{result.err.__class__.__name__}" if result.err else None,
            "traceback": result.exc_string if result.err else None,
        }

    elif nb_config.execution_mode == "cache":

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
            return notebook, exec_metadata

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
        cwd_context = (
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

    return notebook, exec_metadata

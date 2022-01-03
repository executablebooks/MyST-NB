"""Module for executing notebooks."""
import os
from contextlib import nullcontext
from datetime import datetime
from logging import Logger
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Optional, Tuple

from jupyter_cache import get_cache
from jupyter_cache.executors import load_executor
from jupyter_cache.executors.utils import single_nb_execution
from nbformat import NotebookNode
from typing_extensions import TypedDict

from myst_nb.configuration import NbParserConfig


class ExecutionResult(TypedDict):
    """Result of executing a notebook."""

    mtime: float
    """POSIX timestamp of the execution time"""
    runtime: Optional[float]
    """runtime in seconds"""
    method: str
    """method used to execute the notebook"""
    succeeded: bool
    """True if the notebook executed successfully"""
    # TODO error_log: str


def update_notebook(
    notebook: NotebookNode,
    source: str,
    nb_config: NbParserConfig,
    logger: Logger,
) -> Tuple[NotebookNode, Optional[ExecutionResult]]:
    """Update a notebook using the given configuration.

    This function may execute the notebook if necessary.

    :param notebook: The notebook to update.
    :param source: Path to or description of the input source being processed.
    :param nb_config: The configuration for the notebook parser.
    :param logger: The logger to use.

    :returns: The updated notebook, and the (optional) execution metadata.
    """
    exec_metadata: Optional[ExecutionResult] = None

    if nb_config.execution_mode == "force":
        # TODO what if source is a descriptor?
        path = str(Path(source).parent)
        cwd_context = (
            TemporaryDirectory() if nb_config.execution_in_temp else nullcontext(path)
        )
        with cwd_context as cwd:
            cwd = os.path.abspath(cwd)
            logger.info(f"Executing notebook in {cwd}")
            result = single_nb_execution(
                notebook,
                cwd=cwd,
                allow_errors=nb_config.execution_allow_errors,
                timeout=nb_config.execution_timeout,
            )
            logger.info(f"Executed notebook in {result.time:.2f} seconds")

        exec_metadata = {
            "mtime": datetime.now().timestamp(),
            "runtime": result.time,
            "method": nb_config.execution_mode,
            "succeeded": False if result.err else True,
        }

        # TODO handle errors

    elif nb_config.execution_mode == "cache":

        # TODO for sphinx, the default would be in the output directory
        cache = get_cache(nb_config.execution_cache_path or ".cache")
        stage_record = cache.stage_notebook_file(source)
        # TODO handle converters
        if cache.get_cache_record_of_staged(stage_record.pk) is None:
            executor = load_executor("basic", cache, logger=logger)
            executor.run_and_cache(
                filter_pks=[stage_record.pk],  # TODO specitfy, rather than filter
                allow_errors=nb_config.execution_allow_errors,
                timeout=nb_config.execution_timeout,
                run_in_temp=nb_config.execution_in_temp,
            )
        else:
            logger.info("Using cached notebook outputs")

        _, notebook = cache.merge_match_into_notebook(notebook)

        exec_metadata = {
            "mtime": datetime.now().timestamp(),
            "runtime": None,  # TODO get runtime from cache
            "method": nb_config.execution_mode,
            "succeeded": True,  # TODO handle errors
        }

    return notebook, exec_metadata

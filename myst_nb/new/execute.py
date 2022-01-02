"""Module for executing notebooks."""
import os
from contextlib import nullcontext
from logging import Logger
from pathlib import Path
from tempfile import TemporaryDirectory

from jupyter_cache import get_cache
from jupyter_cache.executors import load_executor
from jupyter_cache.executors.utils import single_nb_execution
from nbformat import NotebookNode

from myst_nb.configuration import NbParserConfig


def update_notebook(
    notebook: NotebookNode,
    source: str,
    nb_config: NbParserConfig,
    logger: Logger,
) -> NotebookNode:
    """Update a notebook using the given configuration.

    This function may execute the notebook if necessary.

    :param notebook: The notebook to update.
    :param source: Path to or description of the input source being processed.
    :param nb_config: The configuration for the notebook parser.
    :param logger: The logger to use.

    :returns: The updated notebook.
    """
    # TODO also look at notebook metadata
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
            # TODO save execution data on document (and environment if sphinx)
            # TODO handle errors
    elif nb_config.execution_mode == "cache":
        # TODO for sphinx, the default would be in the output directory
        cache = get_cache(nb_config.execution_cache_path or ".cache")
        stage_record = cache.stage_notebook_file(source)
        # TODO handle converters
        if cache.get_cache_record_of_staged(stage_record.pk) is None:
            executor = load_executor("basic", cache, logger=logger)
            executor.run_and_cache(
                filter_pks=[stage_record.pk],
                allow_errors=nb_config.execution_allow_errors,
                timeout=nb_config.execution_timeout,
                run_in_temp=nb_config.execution_in_temp,
            )
        else:
            logger.info("Using cached notebook outputs")
        # TODO save execution data on document (and environment if sphinx)
        # TODO handle errors
        _, notebook = cache.merge_match_into_notebook(notebook)

    return notebook

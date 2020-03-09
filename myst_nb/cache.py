"""
Implements integration of jupyter-cache
"""
import os
from sphinx.util import logging
from jupyter_cache.cache import main as cache
from jupyter_cache.cli.utils import get_cache
from jupyter_cache.executors import load_executor
from nbclient import execute
import datetime

logger = logging.getLogger(__name__)

def add_notebook_outputs(file_path, ntbk, path_cache):
    """
    Add outputs to a NotebookNode by pulling from cache and/or executing.

    Function to get the database instance and stage notebooks to it.
    Then cache the staged notebooks after execution, if not already present in the cache.
    The executed output is then merged with the original notebook. 
    """
    # If we have a jupyter_cache, see if there's a cache for this notebook
    if path_cache:
        try:
            from jupyter_cache.cache.main import JupyterCacheBase
        except ImportError:
            logger.error(("Using caching functionality requires that "
                          "jupyter_cache is installed. Install it first."))

        db = get_cache(path_cache)

        # stage the notebook for execution
        stage_record = db.stage_notebook_file(file_path)

        # execute the notebook
        execution_result = execute_staged_nb(db, stage_record)

        if len(execution_result['errored']) or len(execution_result['excepted']):
            #handle case for errored and excpeted
            pass
        else:
            pk, ntbk = db.merge_match_into_notebook(ntbk)

        try:
            _, ntbk = db.merge_match_into_notebook(ntbk)
        except KeyError:
            logger.error((f"Couldn't find cache key for notebook file {ntbk_name}. "
                            "Outputs will not be inserted"))
    else:
        # If we explicitly do not wish to cache, then just execute the notebook
        ntbk = execute(ntbk)
    return ntbk

def execute_staged_nb(db, stage_record):
    """
    executing the staged notebook
    """
    try:
        executor = load_executor("basic", db, logger=logger)
    except ImportError as error:
        logger.error(str(error))
        return 1
    result = executor.run_and_cache(filter_pks=[stage_record.pk] or None)
    return result

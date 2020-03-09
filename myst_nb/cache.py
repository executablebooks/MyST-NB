"""
Implements integration of jupyter-cache
"""
import os
from sphinx.util import logging
from jupyter_cache.cache import main as cache
from jupyter_cache.cli.utils import get_cache
from jupyter_cache.executors import load_executor
import datetime

logger = logging.getLogger(__name__)

def cached_execution_and_merge(file_path, ntbk):
    """
    Function to get the database instance and stage notebooks to it.
    Then cache the staged notebooks after execution, if not already present in the cache.
    The executed output is then merged with the original notebook. 
    """
    cache_path = os.environ.get("JUPYTERCACHE", os.path.join(os.getcwd(), ".jupyter_cache"))

    db = get_cache(cache_path) #gets the db in the cache_path, if the db does not exist, then creates a db in this path

    # stage the notebook for execution
    stage_record = db.stage_notebook_file(file_path)

    # execute the notebook
    execution_result = execute_nb(db, stage_record)

    if len(execution_result['errored']) or len(execution_result['excepted']):
        #handle case for errored and excpeted
        pass
    else:
        pk, ntbk = db.merge_match_into_notebook(ntbk)

    return ntbk

def execute_nb(db, stage_record):
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

import os
from sphinx.util import logging
from jupyter_cache.cache import main as cache
from jupyter_cache.cli.utils import get_cache
from jupyter_cache.executors import load_executor

logger = logging.getLogger(__name__)

def cached_execution_and_merge(file_path, ntbk):
    try:
        cache_path = os.environ.get("JUPYTERCACHE", os.path.join(os.getcwd(), ".jupyter_cache"))
    except:
        # create a new cache here
        pass
    
    # stage the notebook for execution
    db = get_cache(cache_path)
    stage_record = db.stage_notebook_file(file_path)
    logger.info("Successfully staged {}".format(file_path))

    # execute the notebook
    execution_result = execute_nb(db, stage_record)

    pk, ntbk = db.merge_match_into_notebook(ntbk)

    return ntbk

def execute_nb(db, stage_record):
    try:
        executor = load_executor("basic", db, logger=logger)
    except ImportError as error:
        logger.error(str(error))
        return 1
    result = executor.run_and_cache(filter_pks=[stage_record.pk] or None)
    return result

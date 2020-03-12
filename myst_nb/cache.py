"""
Implements integration of jupyter-cache
"""
import os
import json
import nbformat as nbf
from pathlib import Path
from sphinx.util import logging
from sphinx.util.osutil import ensuredir
from jupyter_cache.cache import main as cache
from jupyter_cache.cli.utils import get_cache
from jupyter_cache.executors import load_executor
from nbclient import execute
import datetime

logger = logging.getLogger(__name__)


### Functions
def execution_cache(app, env, added, changed, removed):
    """
    If cacheing is required, stages and executes the added or modified notebooks, and caches then for further use.
    """
    path_cache = env.env.config['jupyter_cache']

    if path_cache is True:
        path_cache = Path(env.env.srcdir).joinpath('.jupyter_cache')
        app.env.path_cache = path_cache #TODO: is there a better way to make it accessible?

    nb_list = added.union(changed) #all the added and changed notebooks should be operated on.

    stage_and_execute(env, nb_list, path_cache)

    return nb_list #TODO: can also compare timestamps between inputs outputs, for outdated nbs
    

def stage_and_execute(env, nb_list, path_cache):
    pk_list = None
    
    if path_cache:
        try:
            from jupyter_cache.cache.main import JupyterCacheBase
        except ImportError:
            logger.error(("Using caching functionality requires that "
                          "jupyter_cache is installed. Install it first."))

        db = get_cache(path_cache)
        do_run = env.env.config['jupyter_notebook_force_run']


        for nb in nb_list:
            # excludes the file with patterns given in execution_excludepatterns conf variable from executing, like index.rst
            exclude_file = [x in nb for x in env.env.config['execution_excludepatterns']]
            if True in exclude_file:
                continue

            has_outputs = False
            source_path = env.env.doc2path(nb)

            with open(source_path, "r") as f:
                ntbk = nbf.read(f, as_version=4)
                has_outputs = all(len(cell.outputs) != 0 for cell in ntbk.cells if cell['cell_type'] == "code")

            # If outputs are in the notebook, assume we just use those outputs
            if do_run or not has_outputs:
                if pk_list is None:
                    pk_list = []
                stage_record = db.stage_notebook_file(source_path)
                pk_list.append(stage_record.pk)
            else:
                logger.error(f"Will not run notebook with pre-populated outputs or no output cells: {source_path}")
        
        execution_result = execute_staged_nb(db, pk_list) #can leverage parallel execution implemented in jupyter-cache here

def add_notebook_outputs(file_path, ntbk, path_cache, dest_path):
    """
    Add outputs to a NotebookNode by pulling from cache.

    Function to get the database instance. Get the cached output of the notebook and merge it with the original notebook.
    If there is no cached output, checks if there was error during execution, then saves the traceback to a log file.
    """
    # If we have a jupyter_cache, see if there's a cache for this notebook
    reports_dir = dest_path + "/reports"

    if path_cache:

        db = get_cache(path_cache)

        r_file_path = _relative_file_path(file_path)
        cache_record = db.get_cache_record_of_staged(r_file_path)

        if cache_record:
            try:
                _, ntbk = db.merge_match_into_notebook(ntbk)
            except KeyError:
                logger.error((f"Couldn't find cache key for notebook file {ntbk_name}. "
                                "Outputs will not be inserted"))
        else:
            stage_record = db.get_staged_record(r_file_path)

            if stage_record and stage_record.traceback:
                #save the traceback to a log file
                ensuredir(reports_dir)
                file_name = r_file_path[r_file_path.rfind('/') + 1: r_file_path.rfind('.')]
                full_path = reports_dir + "/{}.log".format(file_name)
                with open(full_path, "w") as log_file:
                    log_file.write(stage_record.traceback)
                logger.info("Execution traceback for {} is saved in {}".format(file_name, full_path))
    
    return ntbk

def execute_staged_nb(db, pk_list):
    """
    executing the staged notebook
    """
    try:
        executor = load_executor("basic", db, logger=logger)
    except ImportError as error:
        logger.error(str(error))
        return 1
    result = executor.run_and_cache(filter_pks=pk_list or None)
    return result

def _relative_file_path(file_path):
    currentdir = os.getcwd()
    dir_index = currentdir.rfind('/')
    r_file_path = file_path[dir_index + 1:]
    return file_path

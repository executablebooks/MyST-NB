"""
Implements integration of jupyter-cache
"""
import os
import nbformat as nbf
from nbclient import execute
from pathlib import Path

from sphinx.util import logging
from sphinx.util.osutil import ensuredir

from jupyter_cache.cache.db import NbCacheRecord
from jupyter_cache import get_cache
from jupyter_cache.executors import load_executor

logger = logging.getLogger(__name__)


def execution_cache(app, env, added, changed, removed, path_cache=None):
    """
    If cacheing is required, stages and executes the added or modified notebooks,
    and caches them for further use.
    """
    jupyter_cache = False
    nb_list = added.union(
        changed
    )  # all the added and changed notebooks should be operated on.

    if env.config["jupyter_execute_notebooks"] not in ["force", "auto", "off"]:
        logger.error(
            "Conf jupyter_execute_notebooks can either be `force`, `auto` or `off`"
        )
        exit(1)

    if env.config["jupyter_execute_notebooks"] in ["force", "auto"]:
        jupyter_cache = env.config["jupyter_cache"]

    if jupyter_cache:
        if jupyter_cache is True:
            path_cache = path_cache or Path(env.outdir).parent.joinpath(
                ".jupyter_cache"
            )
        elif os.path.isdir(jupyter_cache):
            path_cache = jupyter_cache
        else:
            logger.error(
                "Conf jupyter_cache is invalid, either use True or a path to an"
                "existing cache"
            )
            exit(1)
        app.env.path_cache = (
            path_cache  # TODO: is there a better way to make it accessible?
        )

        _stage_and_execute(env, nb_list, path_cache)

    return nb_list  # TODO: can also compare timestamps for inputs outputs


def _stage_and_execute(env, nb_list, path_cache):
    pk_list = None

    if path_cache:
        try:
            from jupyter_cache.cache.main import JupyterCacheBase  # noqa: F401
        except ImportError:
            logger.error(
                (
                    "Using caching functionality requires that "
                    "jupyter_cache is uninstalled. Install it first."
                )
            )

        cache_base = get_cache(path_cache)

        for nb in nb_list:

            has_outputs = False
            if "." in nb:  # nb includes the path to notebook
                source_path = nb
            else:
                source_path = env.env.doc2path(nb)

            # excludes the file with patterns given in execution_excludepatterns
            # conf variable from executing, like index.rst
            exclude_file = [xx in nb for xx in env.config["execution_excludepatterns"]]
            if True in exclude_file or ".ipynb" not in source_path:
                continue

            has_outputs = _read_nb_output_cells(
                source_path, has_outputs, env.config["jupyter_execute_notebooks"]
            )

            if not has_outputs:
                if pk_list is None:
                    pk_list = []
                stage_record = cache_base.stage_notebook_file(source_path)
                pk_list.append(stage_record.pk)
            else:
                # directly cache the already executed notebooks
                cache_base.cache_notebook_file(source_path, overwrite=True)
                logger.warning(
                    f"Will not run notebook with pre-populated outputs/no output cells, will directly cache: {source_path}"  # noqa:E501
                )

        execute_staged_nb(
            cache_base, pk_list
        )  # can leverage parallel execution implemented in jupyter-cache here


def add_notebook_outputs(env, ntbk, file_path=None):
    """
    Add outputs to a NotebookNode by pulling from cache.

    Function to get the database instance. Get the cached output of the notebook
    and merge it with the original notebook. If there is no cached output,
    checks if there was error during execution, then saves the traceback to a log file.
    """
    # If we have a jupyter_cache, see if there's a cache for this notebook
    file_path = file_path or env.doc2path(env.docname)
    dest_path = Path(env.app.outdir)
    reports_dir = str(dest_path) + "/reports"
    path_cache = False

    if env.config["jupyter_cache"]:
        path_cache = env.path_cache

    if not path_cache:
        # If we explicitly did not wish to cache, then just execute the notebook
        ntbk = execute(ntbk)
        return ntbk

    cache_base = get_cache(path_cache)
    db = cache_base.db
    cache_record = None
    r_file_path = Path(file_path).relative_to(Path(file_path).cwd())

    try:
        cache_list = NbCacheRecord.records_from_uri(file_path, db)
        if len(cache_list):
            latest = None
            for item in cache_list:
                if latest is None or (latest < item.created):
                    latest = item.created
                    latest_record = item
            cache_record = latest_record
    except KeyError:
        cache_record = None
        logger.error(
            (
                f"Couldn't find cache key for notebook file {str(r_file_path)}. "
                "Outputs will not be inserted"
            )
        )

    if cache_record:
        _, ntbk = cache_base.merge_match_into_notebook(ntbk)
    else:
        try:
            stage_record = cache_base.get_staged_record(file_path)
        except KeyError:
            stage_record = None
        if stage_record and stage_record.traceback:
            # save the traceback to a log file
            ensuredir(reports_dir)
            file_name = os.path.splitext(r_file_path.name)[0]
            full_path = reports_dir + "/{}.log".format(file_name)
            with open(full_path, "w") as log_file:
                log_file.write(stage_record.traceback)
            logger.info(
                "Execution traceback for {} is saved in {}".format(file_name, full_path)
            )

    return ntbk


def execute_staged_nb(cache_base, pk_list):
    """
    executing the staged notebook
    """
    try:
        executor = load_executor("basic", cache_base, logger=logger)
    except ImportError as error:
        logger.error(str(error))
        return 1
    result = executor.run_and_cache(filter_pks=pk_list or None)
    return result


def _read_nb_output_cells(source_path, has_outputs, jupyter_execute_notebooks):
    if jupyter_execute_notebooks and jupyter_execute_notebooks == "auto":
        with open(source_path, "r") as f:
            ntbk = nbf.read(f, as_version=4)
            has_outputs = all(
                len(cell.outputs) != 0
                for cell in ntbk.cells
                if cell["cell_type"] == "code"
            )
    return has_outputs

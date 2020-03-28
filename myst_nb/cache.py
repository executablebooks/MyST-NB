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

filtered_nb_list = set()


def execution_cache(app, env, added, changed, removed, path_cache=None):
    """
    If cacheing is required, stages and executes the added or modified notebooks,
    and caches them for further use.
    """
    jupyter_cache = False
    exclude_files = []
    nb_list = added.union(
        changed
    )  # all the added and changed notebooks should be operated on.

    if env.config["jupyter_execute_notebooks"] not in ["force", "auto", "cache", "off"]:
        logger.error(
            "Conf jupyter_execute_notebooks can either be `force`, `auto`, `cache` or `off`"  # noqa: E501
        )
        exit(1)

    jupyter_cache = env.config["jupyter_cache"]

    # excludes the file with patterns given in execution_excludepatterns
    # conf variable from executing, like index.rst
    for path in env.config["execution_excludepatterns"]:
        exclude_files.extend(Path().cwd().rglob(path))

    for nb in nb_list:
        exclude = False
        for files in exclude_files:
            if nb in str(files):
                exclude = True
        if not exclude:
            filtered_nb_list.add(nb)

    if "cache" in env.config["jupyter_execute_notebooks"]:
        if jupyter_cache:
            if os.path.isdir(jupyter_cache):
                path_cache = jupyter_cache
            else:
                logger.error("Path to jupyter_cache is not a directory")
                exit(1)
        else:
            path_cache = path_cache or Path(env.outdir).parent.joinpath(
                ".jupyter_cache"
            )

        app.env.path_cache = str(
            path_cache
        )  # TODO: is there a better way to make it accessible?

        _stage_and_execute(env, filtered_nb_list, path_cache)

    elif jupyter_cache:
        logger.error(
            "If using conf jupyter_cache, please set jupyter_execute_notebooks"  # noqa: E501
            " to `cache`"
        )
        exit(1)

    return nb_list  # TODO: can also compare timestamps for inputs outputs


def _stage_and_execute(env, nb_list, path_cache):
    pk_list = None

    try:
        from jupyter_cache.cache.main import JupyterCacheBase  # noqa: F401
    except ImportError:
        logger.error(
            "Using caching requires that jupyter_cache is installed."  # noqa: E501
        )

    cache_base = get_cache(path_cache)

    for nb in nb_list:
        if "." in nb:  # nb includes the path to notebook
            source_path = nb
        else:
            source_path = env.env.doc2path(nb)

        # prevents execution of other formats like .md
        if ".ipynb" not in source_path:
            continue

        if pk_list is None:
            pk_list = []
        stage_record = cache_base.stage_notebook_file(source_path)
        pk_list.append(stage_record.pk)

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

    # checking if filename in execute_excludepattern
    file_present = [env.docname in nb for nb in filtered_nb_list]
    if True not in file_present:
        return ntbk

    if "cache" in env.config["jupyter_execute_notebooks"]:
        path_cache = env.path_cache

    if not path_cache:
        if "off" not in env.config["jupyter_execute_notebooks"]:
            has_outputs = _read_nb_output_cells(
                file_path, env.config["jupyter_execute_notebooks"]
            )
            if not has_outputs:
                logger.info("Executing: {}".format(env.docname))
                ntbk = execute(ntbk)
            else:
                logger.info(
                    "Did not execute {}. "
                    "Set jupyter_execute_notebooks to `force` to execute".format(
                        env.docname
                    )
                )
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


def _read_nb_output_cells(source_path, jupyter_execute_notebooks):
    has_outputs = False
    if jupyter_execute_notebooks and jupyter_execute_notebooks == "auto":
        with open(source_path, "r") as f:
            ntbk = nbf.read(f, as_version=4)
            has_outputs = all(
                len(cell.outputs) != 0
                for cell in ntbk.cells
                if cell["cell_type"] == "code"
            )
    return has_outputs

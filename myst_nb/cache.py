"""
Implements integration of jupyter-cache
"""
import os
import nbformat as nbf
from nbclient import execute
from pathlib import Path

from sphinx.util import logging
from sphinx.util.osutil import ensuredir

from jupyter_cache import get_cache
from jupyter_cache.executors import load_executor

from .converter import path_to_notebook, is_myst_file

LOGGER = logging.getLogger(__name__)


def is_valid_exec_file(env, docname):
    """Check if the docname refers to a file that should be executed."""
    doc_path = env.doc2path(docname)
    if doc_path in env.excluded_nb_exec_paths:
        return False
    extension = os.path.splitext(doc_path)[1]
    if extension not in env.allowed_nb_exec_suffixes:
        return False
    return True


def execution_cache(app, builder, added, changed, removed):
    """
    If caching is required, stages and executes the added or modified notebooks,
    and caches them for further use.
    """
    jupyter_cache = False

    # all the added and changed notebooks should be operated on.
    # note docnames are paths relative to the sphinx root folder, with no extensions
    altered_docnames = added.union(changed)
    if app.config["jupyter_execute_notebooks"] not in ["force", "auto", "cache", "off"]:
        LOGGER.error(
            "Conf jupyter_execute_notebooks can either be `force`, `auto`, `cache` or `off`"  # noqa: E501
        )
        exit(1)

    jupyter_cache = app.config["jupyter_cache"]

    exec_docnames = [
        docname for docname in altered_docnames if is_valid_exec_file(app.env, docname)
    ]
    LOGGER.verbose("MyST-NB: Potential docnames to execute: %s", exec_docnames)

    if "cache" in app.config["jupyter_execute_notebooks"]:
        if jupyter_cache:
            if os.path.isdir(jupyter_cache):
                path_cache = jupyter_cache
            else:
                LOGGER.error(
                    f"Path to jupyter_cache is not a directory: {jupyter_cache}"
                )
                exit(1)
        else:
            path_cache = Path(app.outdir).parent.joinpath(".jupyter_cache")

        app.env.path_cache = str(
            path_cache
        )  # TODO: is there a better way to make it accessible?

        cache_base = get_cache(path_cache)
        for path in removed:
            docpath = app.env.doc2path(path)
            # there is an issue in sphinx doc2path, whereby if the path does not
            # exist then it will be assigned the default source_suffix (usually .rst)
            # therefore, to be safe here, we run through all possible suffixes
            for suffix in app.env.allowed_nb_exec_suffixes:
                docpath = os.path.splitext(docpath)[0] + suffix
                if not os.path.exists(docpath):
                    cache_base.discard_staged_notebook(docpath)

        _stage_and_execute(
            app.env, exec_docnames, path_cache, app.config["execution_timeout"]
        )

    elif jupyter_cache:
        LOGGER.error(
            "If using conf jupyter_cache, please set jupyter_execute_notebooks"  # noqa: E501
            " to `cache`"
        )
        exit(1)

    return altered_docnames


def _stage_and_execute(env, exec_docnames, path_cache, timeout):
    pk_list = []
    cache_base = get_cache(path_cache)

    for nb in exec_docnames:
        source_path = env.doc2path(nb)
        if is_myst_file(source_path):
            stage_record = cache_base.stage_notebook_file(source_path)
            pk_list.append(stage_record.pk)

    # can leverage parallel execution implemented in jupyter-cache here
    try:
        execute_staged_nb(cache_base, pk_list or None, timeout)
    except OSError as err:
        # This is a 'fix' for obscure cases, such as if you
        # remove name.ipynb and add name.md (i.e. same name, different extension)
        # and then name.ipynb isn't flagged for removal.
        # Normally we want to keep the stage records available, so that we can retrieve
        # execution tracebacks at the `add_notebook_outputs` stage,
        # but we need to flush if it becomes 'corrupted'
        LOGGER.error(
            "Execution failed in an unexpected way, clearing staged notebooks: %s", err
        )
        for record in cache_base.list_staged_records():
            cache_base.discard_staged_notebook(record.pk)


def add_notebook_outputs(env, ntbk, file_path=None, show_traceback=False):
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

    if not is_valid_exec_file(env, env.docname):
        return ntbk

    if "cache" in env.config["jupyter_execute_notebooks"]:
        path_cache = env.path_cache

    if not path_cache:
        if "off" not in env.config["jupyter_execute_notebooks"]:
            has_outputs = _read_nb_output_cells(
                file_path, env.config["jupyter_execute_notebooks"]
            )
            if not has_outputs:
                LOGGER.info("Executing: {}".format(env.docname))
                ntbk = execute(ntbk, cwd=Path(file_path).parent)
            else:
                LOGGER.info(
                    "Did not execute {}. "
                    "Set jupyter_execute_notebooks to `force` to execute".format(
                        env.docname
                    )
                )
        return ntbk

    cache_base = get_cache(path_cache)
    # Use relpath here in case Sphinx is building from a non-parent folder
    r_file_path = Path(os.path.relpath(file_path, Path().resolve()))

    try:
        _, ntbk = cache_base.merge_match_into_notebook(ntbk)
    except KeyError:
        message = (
            f"Couldn't find cache key for notebook file {str(r_file_path)}. "
            "Outputs will not be inserted."
        )
        try:
            stage_record = cache_base.get_staged_record(file_path)
        except KeyError:
            stage_record = None
        if stage_record and stage_record.traceback:
            # save the traceback to a log file
            ensuredir(reports_dir)
            file_name = os.path.splitext(r_file_path.name)[0]
            full_path = reports_dir + "/{}.log".format(file_name)
            with open(full_path, "w", encoding="utf8") as log_file:
                log_file.write(stage_record.traceback)
            message += "\n  Last execution failed with traceback saved in {}".format(
                full_path
            )
            if show_traceback:
                message += "\n" + stage_record.traceback

        LOGGER.error(message)

        # This is a 'fix' for jupyter_sphinx, which requires this value for dumping the
        # script file, to stop it from raising an exception if not found:
        # Normally it would be added from the executed notebook but,
        # since we are already logging an error, we don't want to block the whole build.
        # So here we just add a dummy .txt extension
        if "language_info" not in ntbk.metadata:
            ntbk.metadata["language_info"] = nbf.from_dict({"file_extension": ".txt"})
    else:
        LOGGER.verbose("Merged cached outputs into %s", str(r_file_path))

    return ntbk


def execute_staged_nb(cache_base, pk_list, timeout):
    """
    executing the staged notebook
    """
    try:
        executor = load_executor("basic", cache_base, logger=LOGGER)
    except ImportError as error:
        LOGGER.error(str(error))
        return 1
    result = executor.run_and_cache(
        filter_pks=pk_list or None, converter=path_to_notebook, timeout=timeout
    )
    return result


def _read_nb_output_cells(source_path, jupyter_execute_notebooks):
    has_outputs = False
    ext = os.path.splitext(source_path)[1]

    if (
        jupyter_execute_notebooks
        and jupyter_execute_notebooks == "auto"
        and "ipynb" in ext
    ):
        with open(source_path, "r", encoding="utf8") as f:
            ntbk = nbf.read(f, as_version=4)
            has_outputs = all(
                len(cell.outputs) != 0
                for cell in ntbk.cells
                if cell["cell_type"] == "code"
            )
    return has_outputs

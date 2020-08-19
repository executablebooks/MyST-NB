"""Control notebook outputs generation, caching and retrieval

The primary methods in this module are:

- ``update_execution_cache``, which is called when sphinx detects outdated files.
  When caching is enabled, this will execute the files if necessary and update the cache
- ``generate_notebook_outputs`` which is called during the parsing of each notebook.
  If caching is enabled, this will attempt to pull the outputs from the cache,
  or if 'auto' / 'force' is set, will execute the notebook.

"""
import os
from typing import List, Optional, Set

import nbformat as nbf
from nbclient import execute
from pathlib import Path

from sphinx.application import Sphinx
from sphinx.builders import Builder
from sphinx.environment import BuildEnvironment
from sphinx.util import logging
from sphinx.util.osutil import ensuredir

from jupyter_cache import get_cache
from jupyter_cache.executors import load_executor

from myst_parser.main import MdParserConfig

from .converter import path_to_notebook, is_myst_file

LOGGER = logging.getLogger(__name__)


def update_execution_cache(
    app: Sphinx, builder: Builder, added: Set[str], changed: Set[str], removed: Set[str]
) -> Set[str]:
    """If caching is required, stage and execute the added or modified notebooks,
    and cache them for later retrieval.
    """
    # all the added and changed notebooks should be operated on.
    # note docnames are paths relative to the sphinx root folder, with no extensions
    altered_docnames = added.union(changed)

    exec_docnames = [
        docname for docname in altered_docnames if is_valid_exec_file(app.env, docname)
    ]
    LOGGER.verbose("MyST-NB: Potential docnames to execute: %s", exec_docnames)

    if app.config["jupyter_execute_notebooks"] == "cache":

        app.env.nb_path_to_cache = str(
            app.config["jupyter_cache"]
            or Path(app.outdir).parent.joinpath(".jupyter_cache")
        )

        cache_base = get_cache(app.env.nb_path_to_cache)
        for path in removed:
            docpath = app.env.doc2path(path)
            # there is an issue in sphinx doc2path, whereby if the path does not
            # exist then it will be assigned the default source_suffix (usually .rst)
            # therefore, to be safe here, we run through all possible suffixes
            for suffix in app.env.nb_allowed_exec_suffixes:
                docpath = os.path.splitext(docpath)[0] + suffix
                if not os.path.exists(docpath):
                    cache_base.discard_staged_notebook(docpath)

        _stage_and_execute(
            app.env,
            exec_docnames,
            app.env.nb_path_to_cache,
            app.config["execution_timeout"],
        )

    return altered_docnames


def generate_notebook_outputs(
    env: BuildEnvironment,
    ntbk: nbf.NotebookNode,
    file_path: Optional[str] = None,
    show_traceback: bool = False,
) -> nbf.NotebookNode:
    """
    Add outputs to a NotebookNode by pulling from cache.

    Function to get the database instance. Get the cached output of the notebook
    and merge it with the original notebook. If there is no cached output,
    checks if there was error during execution, then saves the traceback to a log file.
    """

    # check if the file is of a format that may be associated with outputs
    if not is_valid_exec_file(env, env.docname):
        return ntbk

    # If we have a jupyter_cache, see if there's a cache for this notebook
    file_path = file_path or env.doc2path(env.docname)
    dest_path = Path(env.app.outdir)
    reports_dir = str(dest_path) + "/reports"

    execution_method = env.config["jupyter_execute_notebooks"]  # type: str

    path_to_cache = env.nb_path_to_cache if "cache" in execution_method else None

    if not path_to_cache and "off" in execution_method:
        return ntbk

    if not path_to_cache:

        if execution_method == "auto" and is_nb_with_outputs(file_path):
            LOGGER.info(
                "Did not execute {}. "
                "Set jupyter_execute_notebooks to `force` to execute".format(
                    env.docname
                )
            )
        else:
            LOGGER.info("Executing: {}".format(env.docname))
            ntbk = execute(ntbk, cwd=Path(file_path).parent)

        return ntbk

    cache_base = get_cache(path_to_cache)
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


def is_valid_exec_file(env: BuildEnvironment, docname: str) -> bool:
    """Check if the docname refers to a file that should be executed."""
    doc_path = env.doc2path(docname)
    if doc_path in env.nb_excluded_exec_paths:
        return False
    extension = os.path.splitext(doc_path)[1]
    if extension not in env.nb_allowed_exec_suffixes:
        return False
    return True


def _stage_and_execute(
    env: BuildEnvironment,
    exec_docnames: List[str],
    path_to_cache: str,
    timeout: Optional[int],
):
    pk_list = []
    cache_base = get_cache(path_to_cache)

    for nb in exec_docnames:
        source_path = env.doc2path(nb)
        if is_myst_file(source_path):
            stage_record = cache_base.stage_notebook_file(source_path)
            pk_list.append(stage_record.pk)

    # can leverage parallel execution implemented in jupyter-cache here
    try:
        execute_staged_nb(cache_base, pk_list or None, timeout, env.myst_config)
    except OSError as err:
        # This is a 'fix' for obscure cases, such as if you
        # remove name.ipynb and add name.md (i.e. same name, different extension)
        # and then name.ipynb isn't flagged for removal.
        # Normally we want to keep the stage records available, so that we can retrieve
        # execution tracebacks at the `generate_notebook_outputs` stage,
        # but we need to flush if it becomes 'corrupted'
        LOGGER.error(
            "Execution failed in an unexpected way, clearing staged notebooks: %s", err
        )
        for record in cache_base.list_staged_records():
            cache_base.discard_staged_notebook(record.pk)


def execute_staged_nb(
    cache_base, pk_list, timeout: Optional[int], config: MdParserConfig
):
    """Executing the staged notebook."""
    try:
        executor = load_executor("basic", cache_base, logger=LOGGER)
    except ImportError as error:
        LOGGER.error(str(error))
        return 1
    result = executor.run_and_cache(
        filter_pks=pk_list or None,
        converter=lambda p: path_to_notebook(p, config),
        timeout=timeout,
    )
    return result


def is_nb_with_outputs(source_path: str, nb_extensions: List[str] = ["ipynb"]) -> bool:
    """Determine if the path contains a notebook with outputs."""
    has_outputs = False
    ext = os.path.splitext(source_path)[1]

    if ext in nb_extensions:
        with open(source_path, "r", encoding="utf8") as f:
            ntbk = nbf.read(f, as_version=4)
            has_outputs = all(
                len(cell.outputs) != 0
                for cell in ntbk.cells
                if cell["cell_type"] == "code"
            )
    return has_outputs

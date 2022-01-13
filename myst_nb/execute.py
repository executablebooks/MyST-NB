"""Module for executing notebooks."""
import asyncio
from contextlib import nullcontext, suppress
from datetime import datetime
from functools import lru_cache
from logging import Logger
import os
from pathlib import Path, PurePosixPath
import re
from tempfile import TemporaryDirectory
from typing import List, Optional, Tuple

from jupyter_cache import get_cache
from jupyter_cache.base import NbBundleIn
from jupyter_cache.cache.db import NbStageRecord
from jupyter_cache.executors.utils import single_nb_execution
from nbclient.client import (
    CellControlSignal,
    DeadKernelError,
    NotebookClient,
    ensure_async,
    run_sync,
)
import nbformat
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
    error: Optional[str]
    """error type if the notebook failed to execute"""
    traceback: Optional[str]
    """traceback if the notebook failed"""


def execute_notebook(
    notebook: NotebookNode,
    source: str,
    nb_config: NbParserConfig,
    logger: Logger,
) -> Tuple[NotebookNode, Optional[ExecutionResult]]:
    """Update a notebook's outputs using the given configuration.

    This function may execute the notebook if necessary, to update its outputs,
    or populate from a cache.

    :param notebook: The notebook to update.
    :param source: Path to or description of the input source being processed.
    :param nb_config: The configuration for the notebook parser.
    :param logger: The logger to use.

    :returns: The updated notebook, and the (optional) execution metadata.
    """
    # TODO should any of the logging messages be debug instead of info?

    # path should only be None when using docutils programmatically,
    # e.g. source="<string>"
    try:
        path = Path(source) if Path(source).is_file() else None
    except OSError:
        path = None  # occurs on Windows for `source="<string>"`

    exec_metadata: Optional[ExecutionResult] = None

    # check if the notebook is excluded from execution by pattern
    if path is not None and nb_config.execution_excludepatterns:
        posix_path = PurePosixPath(path.as_posix())
        for pattern in nb_config.execution_excludepatterns:
            if posix_path.match(pattern):
                logger.info(f"Excluded from execution by pattern: {pattern!r}")
                return notebook, exec_metadata

    # 'auto' mode only executes the notebook if it is missing at least one output
    missing_outputs = (
        len(cell.outputs) == 0 for cell in notebook.cells if cell["cell_type"] == "code"
    )
    if nb_config.execution_mode == "auto" and not any(missing_outputs):
        logger.info("Skipped execution in 'auto' mode (all outputs present)")
        return notebook, exec_metadata

    if nb_config.execution_mode in ("auto", "force"):

        # setup the execution current working directory
        if nb_config.execution_in_temp:
            cwd_context = TemporaryDirectory()
        else:
            if path is None:
                raise ValueError(
                    f"source must exist as file, if execution_in_temp=False: {source}"
                )
            cwd_context = nullcontext(str(path.parent))

        # execute in the context of the current working directory
        with cwd_context as cwd:
            cwd = os.path.abspath(cwd)
            logger.info(
                "Executing notebook using "
                + ("temporary" if nb_config.execution_in_temp else "local")
                + " CWD"
            )
            result = single_nb_execution(
                notebook,
                cwd=cwd,
                allow_errors=nb_config.execution_allow_errors,
                timeout=nb_config.execution_timeout,
                meta_override=True,  # TODO still support this?
            )

        if result.err is not None:
            msg = f"Executing notebook failed: {result.err.__class__.__name__}"
            if nb_config.execution_show_tb:
                msg += f"\n{result.exc_string}"
            logger.warning(msg, subtype="exec")
        else:
            logger.info(f"Executed notebook in {result.time:.2f} seconds")

        exec_metadata = {
            "mtime": datetime.now().timestamp(),
            "runtime": result.time,
            "method": nb_config.execution_mode,
            "succeeded": False if result.err else True,
            "error": f"{result.err.__class__.__name__}" if result.err else None,
            "traceback": result.exc_string if result.err else None,
        }

    elif nb_config.execution_mode == "cache":

        # setup the cache
        cache = get_cache(nb_config.execution_cache_path or ".jupyter_cache")
        # TODO config on what notebook/cell metadata to hash/merge

        # attempt to match the notebook to one in the cache
        cache_record = None
        with suppress(KeyError):
            cache_record = cache.match_cache_notebook(notebook)

        # use the cached notebook if it exists
        if cache_record is not None:
            logger.info(f"Using cached notebook: ID={cache_record.pk}")
            _, notebook = cache.merge_match_into_notebook(notebook)
            exec_metadata = {
                "mtime": cache_record.created.timestamp(),
                "runtime": cache_record.data.get("execution_seconds", None),
                "method": nb_config.execution_mode,
                "succeeded": True,
                "error": None,
                "traceback": None,
            }
            return notebook, exec_metadata

        if path is None:
            raise ValueError(
                f"source must exist as file, if execution_mode is 'cache': {source}"
            )

        # attempt to execute the notebook
        stage_record = cache.stage_notebook_file(str(path))  # TODO record nb reader
        # TODO do in try/except, in case of db write errors
        NbStageRecord.remove_tracebacks([stage_record.pk], cache.db)
        cwd_context = (
            TemporaryDirectory()
            if nb_config.execution_in_temp
            else nullcontext(str(path.parent))
        )
        with cwd_context as cwd:
            cwd = os.path.abspath(cwd)
            logger.info(
                "Executing notebook using "
                + ("temporary" if nb_config.execution_in_temp else "local")
                + " CWD"
            )
            result = single_nb_execution(
                notebook,
                cwd=cwd,
                allow_errors=nb_config.execution_allow_errors,
                timeout=nb_config.execution_timeout,
                meta_override=True,  # TODO still support this?
            )

        # handle success / failure cases
        # TODO do in try/except to be careful (in case of database write errors?
        if result.err is not None:
            msg = f"Executing notebook failed: {result.err.__class__.__name__}"
            if nb_config.execution_show_tb:
                msg += f"\n{result.exc_string}"
            logger.warning(msg, subtype="exec")
            NbStageRecord.set_traceback(stage_record.uri, result.exc_string, cache.db)
        else:
            logger.info(f"Executed notebook in {result.time:.2f} seconds")
            cache_record = cache.cache_notebook_bundle(
                NbBundleIn(
                    notebook, stage_record.uri, data={"execution_seconds": result.time}
                ),
                check_validity=False,
                overwrite=True,
            )
            logger.info(f"Cached executed notebook: ID={cache_record.pk}")

        exec_metadata = {
            "mtime": datetime.now().timestamp(),
            "runtime": result.time,
            "method": nb_config.execution_mode,
            "succeeded": False if result.err else True,
            "error": f"{result.err.__class__.__name__}" if result.err else None,
            "traceback": result.exc_string if result.err else None,
        }

    return notebook, exec_metadata


class NotebookRunnerBase:
    """A client for interacting with a notebook server.

    The runner should be initialised with a notebook as a context manager,
    and all code cells executed, then the final notebook returned::

        with NotebookRunner(nb) as runner:
            for i, cell in enumerate(runner.cells):
                if cell.cell_type == "code":
                    exec_count, outputs = runner.execute_next_cell(i)
            final_nb = runner.get_final_notebook()
    """

    def __init__(self, notebook: NotebookNode, cwd: Optional[str]):
        """Initialise the client."""
        self._notebook = notebook
        self._cwd = cwd
        self._in_context = False

    @property
    def notebook(self) -> NotebookNode:
        """Return the input notebook."""
        if not self._in_context:
            raise ValueError("not in context")
        return self._notebook

    def __enter__(self):
        """Open the client."""
        self._current_index = 0
        self._in_context = True
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Close the client."""
        self._in_context = False

    def get_source_code_lexer(self) -> Optional[str]:
        """Return the lexer name for code cell sources, if available"""
        raise NotImplementedError

    def get_next_code_cell(
        self, expected_index: Optional[int] = None
    ) -> Tuple[int, NotebookNode]:
        """Return the next code cell (index, cell), if available.

        We check against an expected index,
        to ensure that we are receiving the outputs for the cell we expected.
        """
        for i, cell in enumerate(self.notebook.cells[self._current_index :]):
            if cell.cell_type == "code":
                assert (expected_index is None) or (
                    self._current_index + i == expected_index
                ), f"{i} != {expected_index}"
                self._current_index += i + 1
                return cell
        raise StopIteration("No more code cells")

    def get_final_notebook(self) -> NotebookNode:
        """Return the final notebook."""
        try:
            self.get_next_code_cell()
        except StopIteration:
            pass
        else:
            raise ValueError("Un-executed code cell(s)")
        return self.notebook

    def execute_next_cell(
        self, cell_index: int
    ) -> Tuple[Optional[int], List[NotebookNode]]:
        """Execute the next code cell.

        :param cell_index: the index of the cell we expect to execute
        :returns: (execution count, list of outputs)
        """
        raise NotImplementedError

    def get_variable(self, name: str):
        """Return the value of a variable, if available."""
        raise NotImplementedError


class PreExecutedNbRunner(NotebookRunnerBase):
    """Works on pre-executed notebooks."""

    @lru_cache(maxsize=1)
    def get_source_code_lexer(self) -> Optional[str]:
        metadata = self.notebook["metadata"]
        # attempt to get language lexer name
        langinfo = metadata.get("language_info") or {}
        lexer = langinfo.get("pygments_lexer") or langinfo.get("name", None)
        if lexer is None:
            lexer = (metadata.get("kernelspec") or {}).get("language", None)
        return lexer

    def execute_next_cell(
        self, cell_index: int
    ) -> Tuple[Optional[int], List[NotebookNode]]:
        next_cell = self.get_next_code_cell(cell_index)
        return next_cell.get("execution_count", None), next_cell.get("outputs", [])


class NbClientRunner(NotebookRunnerBase):
    def __init__(self, notebook: NotebookNode, cwd: Optional[str]):
        super().__init__(notebook, cwd)
        resources = {"metadata": {"path": cwd}} if cwd else {}
        self._client = ModifiedNotebookClient(
            notebook, record_timing=False, resources=resources
        )
        self._lexer = None

    def __enter__(self):
        super().__enter__()
        self._client.reset_execution_trackers()
        if self._client.km is None:
            self._client.km = self._client.create_kernel_manager()

        if not self._client.km.has_kernel:
            self._client.start_new_kernel()
            self._client.start_new_kernel_client()
        msg_id = self._client.kc.kernel_info()
        info_msg = self._client.wait_for_reply(msg_id)
        if info_msg is not None:
            if "language_info" in info_msg["content"]:
                language_info = info_msg["content"]["language_info"]
                self.notebook.metadata["language_info"] = language_info
        lexer = language_info.get("pygments_lexer") or language_info.get("name", None)
        if lexer is None:
            lexer = (self.notebook.metadata.get("kernelspec") or {}).get(
                "language", None
            )
        self._lexer = lexer
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            # TODO because we set the widget state at the end,
            # it won't be output by the renderer at present
            self._client.set_widgets_metadata()
        except Exception:
            pass
        if self._client.owns_km:
            self._client._cleanup_kernel()
        return super().__exit__(exc_type, exc_val, exc_tb)

    def get_source_code_lexer(self) -> Optional[str]:
        return self._lexer

    def execute_next_cell(
        self, cell_index: int
    ) -> Tuple[Optional[int], List[NotebookNode]]:
        next_cell = self.get_next_code_cell(cell_index)
        self._client.execute_cell(
            next_cell, cell_index, execution_count=self._client.code_cells_executed + 1
        )
        return next_cell.get("execution_count", None), next_cell.get("outputs", [])

    def get_variable(self, name: str):
        # this MUST NOT change the state of the jupyter kernel
        # so we allow execution of variable names
        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", name):
            raise ValueError(f"Invalid variable name: {name}")
        return self._client.user_expression(name)


class ModifiedNotebookClient(NotebookClient):
    async def async_user_expression(self, name: str) -> NotebookNode:
        """ """
        assert self.kc is not None
        self.log.debug(f"Executing user_expression: {name}")
        parent_msg_id = await ensure_async(
            self.kc.execute(
                str(name),
                store_history=False,
                stop_on_error=False,
                # user_expressions={"name": name},
            )
        )
        # We launched a code cell to execute
        exec_timeout = 10

        cell = nbformat.v4.new_code_cell(source=f"{name}")
        cell_index = -1
        self.clear_before_next_output = False

        task_poll_kernel_alive = asyncio.ensure_future(self._async_poll_kernel_alive())
        task_poll_output_msg = asyncio.ensure_future(
            self._async_poll_output_msg(parent_msg_id, cell, cell_index)
        )
        self.task_poll_for_reply = asyncio.ensure_future(
            self._async_poll_for_reply(
                parent_msg_id,
                cell,
                exec_timeout,
                task_poll_output_msg,
                task_poll_kernel_alive,
            )
        )
        try:
            await self.task_poll_for_reply
        except asyncio.CancelledError:
            # can only be cancelled by task_poll_kernel_alive when the kernel is dead
            task_poll_output_msg.cancel()
            raise DeadKernelError("Kernel died")
        except Exception as e:
            # Best effort to cancel request if it hasn't been resolved
            try:
                # Check if the task_poll_output is doing the raising for us
                if not isinstance(e, CellControlSignal):
                    task_poll_output_msg.cancel()
            finally:
                raise

        return cell.outputs[0]

    user_expression = run_sync(async_user_expression)

"""Execute a notebook inline."""
from __future__ import annotations

from datetime import datetime
import shutil
from tempfile import mkdtemp
import time
import traceback

from nbclient.client import CellExecutionError, CellTimeoutError, NotebookClient
from nbformat import NotebookNode

from myst_nb.glue import extract_glue_data_cell

from .base import ExecutionError, NotebookClientBase


class NotebookClientInline(NotebookClientBase):
    """A notebook client that executes the notebook inline,
    i.e. during the render.

    This allows for the client to be called in-between code cell executions,
    in order to extract variable state.
    """

    def start_client(self):

        self._tmp_path = None
        if self.nb_config.execution_in_temp:
            self._tmp_path = mkdtemp()
            resources = {"metadata": {"path": self._tmp_path}}
        else:
            if self.path is None:
                raise ValueError(
                    "Input source must exist as file, if execution_in_temp=False"
                )
            resources = {"metadata": {"path": str(self.path.parent)}}

        self.logger.info("Starting inline execution client")

        self._time_start = time.perf_counter()
        self._client = NotebookClient(
            self.notebook,
            record_timing=False,
            resources=resources,
            allow_errors=self.nb_config.execution_allow_errors,
            timeout=self.nb_config.execution_timeout,
        )
        self._client.reset_execution_trackers()
        if self._client.km is None:
            self._client.km = self._client.create_kernel_manager()
        if not self._client.km.has_kernel:
            self._client.start_new_kernel()
            self._client.start_new_kernel_client()

        # retrieve the the language_info from the kernel
        assert self._client.kc is not None
        msg_id = self._client.kc.kernel_info()
        info_msg = self._client.wait_for_reply(msg_id)
        if info_msg is not None and "language_info" in info_msg["content"]:
            self.notebook.metadata["language_info"] = info_msg["content"][
                "language_info"
            ]
        else:
            self.logger.warning("Failed to retrieve language info from kernel")

        self._last_cell_executed: int = -1
        self._cell_error: None | Exception = None
        self._exc_string: None | str = None

    def finalise_client(self):
        try:
            self._client.set_widgets_metadata()
        except Exception as exc:
            self.logger.warning(f"Failed to set widgets metadata: {exc}")

    def close_client(self, exc_type, exc_val, exc_tb):
        self.logger.info("Stopping inline execution client")
        if self._client.owns_km:
            self._client._cleanup_kernel()
        del self._client

        _exec_time = time.perf_counter() - self._time_start
        self.exec_metadata = {
            "mtime": datetime.now().timestamp(),
            "runtime": _exec_time,
            "method": self.nb_config.execution_mode,
            "succeeded": False if self._cell_error else True,
            "error": f"{self._cell_error.__class__.__name__}"
            if self._cell_error
            else None,
            "traceback": self._exc_string,
        }
        if not self._cell_error:
            self.logger.info(f"Executed notebook in {_exec_time:.2f} seconds")
        else:
            msg = f"Executing notebook failed: {self._cell_error.__class__.__name__}"
            if self.nb_config.execution_show_tb:
                msg += f"\n{self._exc_string}"
            self.logger.warning(msg, subtype="exec")
        if self._tmp_path:
            shutil.rmtree(self._tmp_path, ignore_errors=True)

    def code_cell_outputs(
        self, cell_index: int
    ) -> tuple[int | None, list[NotebookNode]]:

        cells = self.notebook.get("cells", [])

        # ensure all cells up to and including the requested cell have been executed
        while (not self._cell_error) and cell_index > self._last_cell_executed:

            self._last_cell_executed += 1
            try:
                next_cell = cells[self._last_cell_executed]
            except IndexError:
                break

            try:
                self._client.execute_cell(
                    next_cell,
                    self._last_cell_executed,
                    execution_count=self._client.code_cells_executed + 1,
                )
            except (CellExecutionError, CellTimeoutError) as err:
                if self.nb_config.execution_raise_on_error:
                    raise ExecutionError(str(self.path)) from err
                self._cell_error = err
                self._exc_string = "".join(traceback.format_exc())

            for key, cell_data in extract_glue_data_cell(next_cell):
                if key in self._glue_data:
                    self.logger.warning(
                        f"glue key {key!r} duplicate",
                        subtype="glue",
                        line=self.cell_line(self._last_cell_executed),
                    )
                self._glue_data[key] = cell_data

        cell = cells[cell_index]
        return cell.get("execution_count", None), cell.get("outputs", [])

from __future__ import annotations

import gc
import warnings
from typing import TYPE_CHECKING

import nbformat
import pytest
from jupyter_client import AsyncKernelManager

from myst_nb.core.config import NbParserConfig
from myst_nb.core.execute import create_client

if TYPE_CHECKING:
    from pathlib import Path


class _FakeLogger:
    def info(self, *args, **kwargs):
        pass

    def warning(self, *args, **kwargs):
        pass

    def debug(self, *args, **kwargs):
        pass


def _notebook():
    return nbformat.v4.new_notebook(
        metadata=nbformat.NotebookNode(
            kernelspec=dict(name="python3", display_name="", language="python")
        ),
        cells=[nbformat.v4.new_code_cell("1 + 1")],
    )


@pytest.mark.parametrize("execution_mode", ["force", "cache", "inline"])
def test_external_kernel_manager_client_is_closed(tmp_path: Path, execution_mode):
    nb_path = tmp_path / "nb.ipynb"
    nbformat.write(_notebook(), nb_path)
    nb_config = NbParserConfig(
        execution_mode=execution_mode,
        execution_in_temp=True,
        execution_cache_path=str(tmp_path / ".jupyter_cache"),
    )

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        with create_client(
            _notebook(),
            str(nb_path),
            nb_config,
            _FakeLogger(),
            kernel_manager_class=AsyncKernelManager,
        ) as client:
            if execution_mode == "inline":
                # inline mode executes lazily, on request for a cell's outputs
                client.code_cell_outputs(0)
        assert client.exec_metadata["succeeded"]
        gc.collect()

    unclosed = [
        w
        for w in caught
        if issubclass(w.category, ResourceWarning) and "Unclosed" in str(w.message)
    ]
    assert not unclosed, [str(w.message) for w in unclosed]

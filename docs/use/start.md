# Get started

This section covers how to get started with the `MyST-NB` Sphinx extension.
The Sphinx extension allows you to read markdown (`.md`) and Jupyter Notebook (`.ipynb`)
files into your Sphinx site. It also enables you to write [MyST Markdown](myst.md)
in your pages.

## Install and activate

To install `myst-nb`, do the following:

* **Install** `myst-nb` with the following command:

  ```bash
  pip install myst-nb
  ```

* **Activate** the `myst_nb` extension in your Sphinx site by adding it to your list of
  Sphinx extensions in `conf.py`:

  ```python
  extensions = [
      ...,
      "myst_nb"
  ]
  ```

Once you do this, MyST-NB will now parse both markdown (`.md`) and
Jupyter notebooks (`.ipynb`) into your Sphinx site.

(start/config-options)=

## MyST-NB configuration options

The MyST-NB parser derives from {ref}`the base MyST-Parser <myst:intro/get-started>`, and so all the same configuration options are available.
See the {ref}`MyST configuration options <myst:intro/config-options>` for the full set of options.

MyST-NB then adds some additional configuration, specific to notebooks:

`````{list-table}
:header-rows: 1

* - Option
  - Default
  - Description
* - `jupyter_cache`
  - ""
  - Path to jupyter_cache, [see here](execute/cache) for details.
* - `execution_excludepatterns`
  - ()
  - Exclude certain file patterns from execution, [see here](execute/config) for details.
* - `jupyter_execute_notebooks`
  - "auto"
  - The logic for executing notebooks, [see here](execute/config) for details.
* - `execution_in_temp`
  - `False`
  - If `True`, then a temporary directory will be created and used as the command working directory (cwd), if `False` then the notebook's parent directory will be the cwd.
* - `execution_allow_errors`
  - `False`
  - If `False`, when a code cell raises an error the execution is stopped, if `True` then all cells are always run.
    This can also be overridden by metadata in a notebook, [see here](execute/allow_errors) for details.
* - `execution_timeout`
  - 30
  - The maximum time (in seconds) each notebook cell is allowed to run.
    This can also be overridden by metadata in a notebook, [see here](execute/timeout) for details.
* - `execution_show_tb`
  - `False`
  - Show failed notebook tracebacks in stdout (in addition to writing to file).
`````

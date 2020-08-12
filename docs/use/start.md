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

The MyST-NB parser derives from {doc}`the base MyST-Parser <myst:using/intro>`, and so all the same configuration options are available. MyST-NB then adds some additional configuration, specific to notebooks:

`````{list-table}
:header-rows: 1

* - Option
  - Default
  - Description
* - `myst_disable_syntax`
  - ()
  - List of markdown syntax elements to disable, see the {doc}`markdown-it parser guide <markdown_it:using>`.
* - `myst_math_delimiters`
  - "dollars"
  - Delimiters for parsing math, see the [Math syntax](myst:syntax/math) for details
* - `myst_amsmath_enable`
  - `False`
  - Enable direct parsing of [amsmath LaTeX environments](https://ctan.org/pkg/amsmath), [see here](myst:syntax/amsmath)  for details.
* - `myst_admonition_enable`
  - `False`
  - Enable admonition style directives, [see here](myst:syntax/admonitions) for details.
* - `jupyter_cache`
  - ""
  - Path to jupyter_cache, [see here](execute/cache) for details.
* - `execution_excludepatterns`
  - ()
  - Exclude certain file patterns from execution, [see here](execute/config) for details.
* - `jupyter_execute_notebooks`
  - "auto"
  - The logic for executing notebooks, [see here](execute/config) for details.
* - `execution_timeout`
  - 30
  - The maximum time (in seconds) each notebook cell is allowed to run.
    This can be overridden by metadata in a notebook, [see here](execute/timeout) for detail.
* - `execution_show_tb`
  - `False`
  - Show failed notebook tracebacks in stdout (in addition to writing to file).
`````

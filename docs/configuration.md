
(config/reference)=
# Configuration

% TODO highlight how can be global (+prefix), notebook, cell level

This page lists the configuration options that are available to control MyST-NB.
For more detailed explanation of when to use each option, see the other sections in the documentation.

## MyST Parser configuration

The MyST-NB parser derives from {ref}`the base MyST-Parser <myst:intro/get-started>`, and so all the same configuration options are available.
See the {ref}`MyST configuration options <myst:sphinx/config-options>` for the full set of options.

## Notebook execution configuration

This configuration is used to control how Jupyter Notebooks are executed at build-time.

`````{list-table}
:header-rows: 1

* - Option
  - Default
  - Description
* - `nb_execution_cache_path`
  - ""
  - Path to jupyter_cache, [see here](execute/cache) for details.
* - `nb_execution_excludepatterns`
  - ()
  - Exclude certain file patterns from execution, [see here](execute/config) for details.
* - `nb_execution_mode`
  - "auto"
  - The logic for executing notebooks, [see here](execute/config) for details.
* - `nb_execution_in_temp`
  - `False`
  - If `True`, then a temporary directory will be created and used as the command working directory (cwd), if `False` then the notebook's parent directory will be the cwd.
* - `nb_execution_allow_errors`
  - `False`
  - If `False`, when a code cell raises an error the execution is stopped, if `True` then all cells are always run.
    This can also be overridden by metadata in a notebook, [see here](execute/allow_errors) for details.
* - `nb_execution_timeout`
  - 30
  - The maximum time (in seconds) each notebook cell is allowed to run.
    This can also be overridden by metadata in a notebook, [see here](execute/timeout) for details.
* - `nb_execution_show_tb`
  - `False`
  - Show failed notebook tracebacks in stdout (in addition to writing to file).
`````

## Notebook parsing and output rendering

These configuration options affect the look and feel of notebook parsing and output rendering.

`````{list-table}
:header-rows: 1

* - Option
  - Default
  - Description
* - `nb_custom_formats`
  - `{}`
  - Define custom functions for conversion of files to notebooks, [see here](write/custom_formats) for details.
* - `nb_mime_priority_overrides`
  - `()`
  - Dict override for MIME type render priority, [see here](render/output/priority) for details.
* - `nb_render_plugin`
  - `default`
  - Entry point pointing toward a code cell output renderer, [see here](render/output/cutomise) for details.
* - `nb_render_text_lexer`
  - `myst-ansi`
  - pygments lexer for rendering text outputs, [see here](render/output/ansi) for details.
* - `nb_render_key`
  - `render`
  - The top-level cell metadata key, to store render control data, [see here](render/output/images) for examples.
* - `nb_output_stderr`
  - `show`
  - One of 'show', 'remove', 'warn', 'error' or 'severe', [see here](render/output/stderr) for details.
* - `nb_merge_streams`
  - `False`
  - If `True`, ensure all stdout / stderr output streams are merged into single outputs. This ensures deterministic outputs.
`````


## Auto-generated config

```{mystnb-config}
:sphinx:
```

(myst/error-reporting)=

## Error reporting in Sphinx

When Sphinx encounters and error or raises a warning, it will print the location and source file of the text that generated that error.
This works slightly differently depending on whether you use markdown files or Jupyter Notebook files.

For markdown (`.md`) files, Sphinx will correctly report the line number that the error or warning is associated with:

```
source/path:4: (WARNING/2) Duplicate reference definition: abc
```

For Jupyter Notebook (`.ipynb`) files, these errors also correspond to a cell index.
To allow for this, we use a special format of line number corresponding to: `<CELL_INDEX> * 10000 + LINE_NUMBER`.

For example, the following error corresponds to **Cell 1, line 4**:

```
source/path:10004: (WARNING/2) Duplicate reference definition: abc
```

% TODO talk about suppress_warnings

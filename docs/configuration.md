
(config/intro)=
# Configuration

MyST-NB can be configured at three levels of specificity; globally, per file, and per notebook cell, with the most specific configuration taking precedence.

## Global configuration

Overriding the default configuration at the global level is achieved by specifying variables in the Sphinx `conf.py` file.
All `myst_nb` configuration variables are prefixed with `nb_`, e.g.

```python
nb_execution_timeout = 60
```

### Reading

Control how files are read.

```{mystnb-config} global_lvl
:sphinx:
:section: read
```

### Execution

This configuration is used to control how Jupyter Notebooks are executed at build-time.

```{mystnb-config} global_lvl
:sphinx:
:section: execute
```

### Rendering

These configuration options affect the look and feel of notebook parsing and output rendering.

```{mystnb-config} global_lvl
:sphinx:
:section: render
```

## File level configuration

Overriding the default configuration at a per-file level is achieved by specifying variables in the files metadata, under the `mystnb` key.

In Jupyter notebooks, this is added in the notebook-level metadata, e.g.

```json
{
  "metadata": {
    "mystnb": {
      "execution_timeout": 60
    }
  }
}
```

In text-based notebooks, this is added in the YAML top-matter, e.g.

```yaml
---
file_format: mystnb
mystnb:
  execution_timeout: 60
---
```

### Execution

This configuration is used to control how Jupyter Notebooks are executed at build-time.

```{mystnb-config} file_lvl
:sphinx:
:section: execute
```

### Rendering

These configuration options affect the look and feel of notebook parsing and output rendering.

```{mystnb-config} file_lvl
:sphinx:
:section: render
```

## Cell level configuration

Overriding the default configuration at a per-cell level is achieved by specifying variables in the cell metadata, under the `mystnb` key.

In Jupyter notebooks, this is added in the cell-level metadata, e.g.

```json
{
  "cell_type": "code",
  "source": ["print('hello world')"],
  "metadata": {
    "mystnb": {
      "number_source_lines": true
    }
  }
}
```

In text-based notebooks, this is added in the code cell YAML, e.g.

````markdown
```{code-cell} ipython3
---
mystnb:
  number_source_lines: true
---
print('hello world')
```
````

```{mystnb-config} cell_lvl
:sphinx:
```

### Cell tags

As a convenience for users in Jupyter interfaces, some cell level configuration can be achieved by specifying tags in the cell metadata.

Tags are a list of strings under the `tags` key in the cell metadata, e.g.

```json
{
  "cell_type": "code",
  "source": ["print('hello world')"],
  "metadata": {
    "tags": ["my-tag1", "my-tag2"]
  }
}
```

Tag             | Description
--------------- | ---
`remove-cell`   | Remove the cell from the rendered output.
`remove-input`  | Remove the code cell input/source from the rendered output.
`remove-output` | Remove the code cell output from the rendered output.
`remove-stderr` | Remove the code cell output stderr from the rendered output.

Additionally, for code execution, these tags are provided (via `nbclient`):

Tag                | Description
------------------ | ---
`skip-execution`   | Skip this cell, when executing the notebook
`raises-exception` | Expect the code cell to raise an Exception (and continue execution)

## Markdown parsing configuration

The MyST-NB parser derives from {ref}`the base MyST-Parser <myst:intro/get-started>`, and so all the same configuration options are available.
As referenced in {ref}`MyST configuration options <myst:sphinx/config-options>`, the full set of global options are:

```{myst-config}
:sphinx:
```

(myst/error-reporting)=
## Warning suppression

When Sphinx encounters and error or raises a warning, it will print the location and source file of the text that generated that error.
This works slightly differently depending on whether you use markdown files or Jupyter Notebook files.

For markdown (`.md`) files, Sphinx will correctly report the line number that the error or warning is associated with:

```
source/path:4: (WARNING/2) Unknown mime type: 'xyz' [mystnb.unknown_mime_type]
```

For Jupyter Notebook (`.ipynb`) files, these errors also correspond to a cell index.
To allow for this, we use a special format of line number corresponding to: `<CELL_INDEX> * 10000 + LINE_NUMBER`.

For example, the following error corresponds to **Cell 1, line 4**:

```
source/path:10004: (WARNING/2) Unknown mime type: 'xyz' [mystnb.unknown_mime_type]
```

In general, if your build logs any warnings, you should either fix them or raise an Issue if you think the warning is erroneous. However, in some circumstances if you wish to suppress the warning you can use the Sphinx [`suppress_warnings`](https://www.sphinx-doc.org/en/master/usage/configuration.html#confval-suppress_warnings) configuration option.
All myst-nb warnings are prepended by their type, and can be suppressed by e.g.

```python
suppress_warnings = ["mystnb.unknown_mime_type"]
```

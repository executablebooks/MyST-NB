---
jupytext:
  cell_metadata_filter: -all
  formats: md:myst
  text_representation:
    extension: .md
    format_name: myst
    format_version: '0.8'
    jupytext_version: 1.4.2
kernelspec:
  display_name: Python 3
  language: python
  name: python3
---

# Executing and cacheing your content

MyST-NB can automatically run and cache notebooks contained in your project using [jupyter-cache].
Notebooks can either be run each time the documentation is built, or cached
locally so that re-runs occur only when code cells have changed.

Cacheing behavior is controlled with configuration in your `conf.py` file. See
the sections below for each configuration option and its effect.

## Triggering notebook execution

To trigger the execution of notebook pages, use the following configuration in `conf.py`

```
jupyter_execute_notebooks = "auto"
```

By default, this will only execute notebooks that are missing at least one output. If
a notebook has *all* of its outputs populated, then it will not be executed.

**To force the execution of all notebooks, regardless of their outputs**, change the
above configuration value to:

```
jupyter_execute_notebooks = "force"
```

**To cache execution outputs with [jupyter-cache]**, change the above configuration
value to:

```
jupyter_execute_notebooks = "cache"
```

See {ref}`execute/cache` for more information.

**To turn off notebook execution**, change the
above configuration value to:

```
jupyter_execute_notebooks = "off"
```

**To exclude certain file patterns from execution**, use the following
configuration:

```
execution_excludepatterns = ['list', 'of', '*patterns']
```

Any file that matches one of the items in `execution_excludepatterns` will not be
executed.

(execute/cache)=
## Cacheing the notebook execution

As mentioned above, you can **cache the results of executing a notebook page** by setting

```
jupyter_execute_notebooks = "cache"
```

in your conf.py file.   In this case, when a page is executed, its outputs
will be stored in a local database.  This allows you to be sure that the
outputs in your documentation are up-to-date, while saving time avoiding
unnecessary re-execution. It also allows you to store your `.ipynb` files in
your `git` repository *without their outputs*, but still leverage a cache to
save time when building your site.

When you re-build your site, the following will happen:

* Notebooks that have not seen changes to their **code cells** since the last build
  will not be re-executed. Instead, their outputs will be pulled from the cache
  and inserted into your site.
* Notebooks that **have any change to their code cells** will be re-executed, and the
  cache will be updated with the new outputs.

By default, the cache will be placed in the parent of your build folder. Generally,
this is in `_build/.jupyter_cache`.

You may also specify a path to the location of a jupyter cache you'd like to use:

```
jupyter_cache = path/to/mycache
```

The path should point to an **empty folder**, or a folder where a
**jupyter cache already exists**.

[jupyter-cache]: https://github.com/executablebooks/jupyter-cache "the Jupyter Cache Project"

## Execution FAQs

### How can I include code that raises errors?

In some cases, you may want to intentionally show code that doesn't work (e.g., to show
the error message). To do this, add a `raises-exception` tag to your code cell. This
can be done via a Jupyter interface, or via the `{code-cell}` directive like so:

````
```{code-cell}
---
tags: [raises-exception]
---
print(thisvariabledoesntexist)
```
````

Which produces:

```{code-cell}
---
tags: [raises-exception]
---
print(thisvariabledoesntexist)
```

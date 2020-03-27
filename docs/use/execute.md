# Executing and cacheing your content

MyST-NB can automatically run and cache any notebook pages. Notebooks can either
be run each time the documentation is build, or cached locally so that notebooks
will only be re-run when the code cells in a notebook have changed.

Cacheing behavior is controlled with configuration in your `conf.py` file. See
the sections below for each configuration option and its effect.

## Triggering notebook execution

To trigger the execution of notebook pages, use the following configuration in `conf.py`

```
jupyter_execute_notebooks = "auto"
```

By default, this will only execute notebooks that are missing at least one output. If
the notebook has *all* of its outputs populated, then it will not be executed.

**To force the execution of all notebooks, regardless of their outputs**, change the
above configuration value to:

```
jupyter_execute_notebooks = "force"
```

**To turn off notebook execution**,change the
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

## Cacheing the notebook execution

You may also **cache the results of executing a notebook page** using the
[Jupyter Cache project](https://github.com/executablebookproject/jupyter-cache). In
this case, when a page is executed, its outputs will be stored in a local database.
This allows you to be sure that the outputs in your documentation are up-to-date,
while saving time avoiding unnecessary re-execution. It also allows you to store your
`.ipynb` files in your `git` repository *without their outputs*, but still leverage
a cache to save time when building your site.

When you re-build your site, the following will happen:

* Notebooks that have not seen changes to their **code cells** since the last build
  will not be re-executed. Instead, their outputs will be pulled from the cache
  and inserted into your site.
* Notebooks that **have any change to their code cells** will be re-executed, and the
  cache will be updated with the new outputs.

To enable cacheing of notebook outputs, use the following configuration:

```
jupyter_execute_notebooks = "cache"
```

By default, the cache will be placed in the parent of your build folder. Generally,
this is in `_build/.jupyter_cache`.

You may also specify a path to the location of a jupyter cache you'd like to use:

```
jupyter_cache = path/to/mycache
```

The path should point to an **empty folder**, or a folder where a
**jupyter cache already exists**.

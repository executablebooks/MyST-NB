# Writing MyST Markdown

MyST Markdown is a flavor of markdown that gives you full access to all of the
functionality provided by Sphinx (such as roles and directives). In MyST-NB, this
is provided by the [MyST Parser](https://myst-parser.readthedocs.io/en/latest/), another
Sphinx extension that MyST-NB depends on.

You can write your MyST markdown in either regular markdown files (`.md`) or in
the markdown cells of Jupyter Notebooks (`.ipynb`).

```{warning}
If you are using MyST-NB in your documentation, do not activate `myst-parser`. It will
be automatically activated by `myst-nb`.
```

## Writing MyST Markdown

For more information about what you can write with MyST Markdown, see the
[MyST Parser syntax guide](https://myst-parser.readthedocs.io/en/latest/using/syntax.html).

## Parse extensions other than `.md` and `.ipynb`

You can change which files are parsed by MyST-NB using
the [source_suffix](https://www.sphinx-doc.org/en/master/usage/configuration.html#confval-source_suffix)
option in your `conf.py`, e.g.:

```python
extensions = ["myst_nb"]
source_suffix = {
    '.rst': 'restructuredtext',
    '.ipynb': 'myst-nb',
    '.myst': 'myst-nb',
}
```

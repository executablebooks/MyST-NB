# Write your notebook content

Once activated, the MyST-NB Sphinx extension will automatically parse both
markdown (`.md`) and Jupyter notebooks (`.ipynb`) into your Sphinx site. If your
markdown files have [Jupytext metadata for MyST Notebooks](myst-nb/sphinx),
they will be converted to notebooks and optionally executed.

In any of these files, you may write [MyST Markdown](https://myst-parser.readthedocs.io).
This is an extension of CommonMark markdown that provides extra syntax for common
workflows in publishing, and extension points for extra functionality.

## Writing MyST Markdown

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

For more information about what you can write with MyST Markdown, see the
[MyST Parser syntax guide](https://myst-parser.readthedocs.io/en/latest/using/syntax.html).

## Write notebooks in pure markdown

In addition to supporting MyST Markdown inside of `.md` and `.ipynb` files, you can
also write Jupyter Notebooks entirelly with markdown by using
[MyST Markdown Notebooks](markdown.md). MyST Notebooks have a similar structure
to Jupyter Notebooks (`.ipynb`), but they are written with MyST Markdown syntax to
be easier to use with text editors.

To use MyST Notebooks with `myst_nb`, you'll need to add Jupytext metadata to your
MyST Notebooks. See [](myst-nb/sphinx) for more details.

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

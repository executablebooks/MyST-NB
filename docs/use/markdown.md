---
jupytext:
  text_representation:
    extension: .md
    format_name: myst
    format_version: '0.8'
    jupytext_version: '1.4.1'
kernelspec:
  display_name: Python 3
  language: python
  name: python3
---
# Notebooks as Markdown

MyST-NB also provides functionality for writing notebooks in a text-based format,
utilising the [MyST Markdown format](https://jupytext.readthedocs.io/en/latest/formats.html#myst-markdown) outlined in [jupytext](https://jupytext.readthedocs.io).[^download]
These files have a 1-to-1 mapping with the notebook, so can be opened as notebooks
in Jupyter Notebook and Jupyter Lab (with jupytext installed), and are also integrated
directly into the {ref}`Execution and Caching <execute/cache>` machinery!

[^download]: This notebook can be downloaded as
            **{jupyter-download:notebook}`markdown`** and {download}`markdown.md`


(myst-nb/jupytext-metadata)
## Jupytext metadata

In order to signal MyST-NB that it should treat your markdown file as a notebook,
add the following Jupytext front-matter to the beginnign of the markdown file.

```md
---
jupytext:
  text_representation:
    format_name: myst
kernelspec:
  display_name: Python 3
  name: python3
---
```

Note that `kernelspec:` should map on to the kernel you wish to use to run your
notebook's code. It must be installed on the machine and registered with Jupyter to
be used.

```{tip}
Jupytext allows you to convert back-and-forth between `.ipynb` and MyST-markdown
notebooks.

* To convert `.ipynb` to MyST-markdown, run: `jupytext notebook.ipynb --to myst`
* To convert MyST-markdown to `.ipynb`, run: `jupytext mystfile.md --to ipynb`
```

## Supported source files

By default the `myst_nb` extension will look for both `.ipynb` and `.md` file extensions,
treating markdown files with the above front matter as notebooks, and as standard
markdown files otherwise. You can also change which files are parsed by MyST-NB using
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

## Syntax for code cells

When writing notebooks in pure-markdown, use the following syntax to define a code cell:

````md
```{code-cell} ipython3
a = "This is some"
b = "Python code!"
print(f"{a} {b}")
```
````

The argument after `{code-cell}` (above, `ipython3`) is optional, and is used for
readability purposes. The content inside `{code-cell}` makes up the content of the cell,
and will be executed at build time.

This will result in the following output after building your site:

```{code-cell} ipython3
a = "This is some"
b = "Python code!"
print(f"{a} {b}")
```

## Parameterizing your code cell

You can begin your `code-cell` block with front-matter metadata. These will be used
as **cell-level metadata** in the resulting notebook cell.
The same metadata tags can be used as you would in a normal notebook,
for example those discussed in {ref}`use/hiding/code`:

````md
```{code-cell} ipython3
:tags: [hide-output]

for i in range(20):
    print("Millhouse did not test cootie positive")
```
````

Yields the following:

```{code-cell} ipython3
:tags: [hide-output]

for i in range(20):
    print("Millhouse did not test cootie positive")
```

and `raises-exception` means our code will execute without halting the kernel:

````md
```{code-cell} ipython3
:tags: [raises-exception]

raise ValueError("oopsie!")
```
````

```{code-cell} ipython3
:tags: [raises-exception]

raise ValueError("oopsie!")
```

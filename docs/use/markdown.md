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

They are distinguished from standard Markdown files by adding this top matter to the first line of you file (or the relevant `kernelspec` for your code):

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

```{tip}
You can also create the file from an existing notebook: `jupytext notebook.ipynb --to myst`
```

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

The following syntax can then be used to define a code cell:

````md
```{code-cell} ipython3
a = "This is some"
b = "Python code!"
print(f"{a} {b}")
```
````

Yielding the following:

```{code-cell} ipython3
a = "This is some"
b = "Python code!"
print(f"{a} {b}")
```

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

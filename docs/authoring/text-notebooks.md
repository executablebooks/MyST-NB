---
file_format: mystnb
kernelspec:
  name: python3
---

(authoring/text-notebooks)=
# Text-based Notebooks

MyST Markdown notebooks allow you to write your Jupyter Notebook entirely in markdown, utilising the MyST Markdown notebook format.
This allows you to store notebook metadata, Markdown, and cell inputs in a text-based format that is easy to read and use with text-based tools.

MyST notebooks have a 1-to-1 mapping with Jupyter notebook,
so can be [converted to `.ipynb` files](converting-ipynb) and [opened as notebooks in Jupyter interfaces](myst-nb/jupyter-interfaces) (with jupytext installed).
When used with `myst_nb`, MyST notebooks are also integrated directly into the {ref}`Execution and Caching <execute/cache>` machinery.[^download]

[^download]: This notebook can be downloaded as **{nb-download}`text-notebooks.ipynb`** and {download}`text-notebooks.md`

## The MyST notebook Structure

MyST Markdown Notebooks (or MyST notebooks for short) have four main types of content:

- **cell/notebook level metadata** that are written as YAML wrapped in `---`
- **markdown cells** that can be written as CommonMark or MyST Markdown
- **code cells** that are written with the MyST Markdown `code-cell` directive syntax
- **raw cells** that are written with the MyST Markdown `raw-cell` directive syntax

### Notebook-level metadata

Begin a MyST notebook file with YAML top-matter metadata, containing at least the `file_format: mystnb` signifier.
This will be used as **notebook-level metadata** for the resulting Jupyter Notebook.
This metadata takes the following form:

```yaml
---
file_format: mystnb
kernelspec:
  name: python3
otherkey1: val1
otherkey2: val2
---
# Notebook title
...
```

The kernel that your code cells use is determined by the `kernelspec.name` field, and  should relate to a [Jupyter kernel](https://github.com/jupyter/jupyter/wiki/Jupyter-kernels) installed in your environment and registered with Jupyter.
If no kernel is given, then the default kernel will be used.

### Syntax for Markdown

Anything in-between code cells will be treated as Markdown.
You can use any Markdown that is valid MyST.
If you are using MyST notebooks with the `myst_nb` Sphinx extension, you can write Sphinx directives and roles.
However, note that most Jupyter notebook environments may not be able to render MyST Markdown syntax.

**To denote a break between two markdown cells**, use the following syntax:

```
Some markdown
+++ {"optionalkey": "val"}
More markdown
```

This will result in two markdown cells in the resulting notebook. The key:val pairs
specified in the `{}` brackets will be cell-level metadata in the second markdown cell.

### Syntax for code cells

When writing MyST notebooks, use the following syntax to define a code cell:

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

### Cell-level metadata

You can begin `code-cell` blocks with top-matter metadata. These will be used
as **cell-level metadata** in the resulting notebook cell.
The same metadata tags can be used as you would in a normal notebook,
for example those discussed in {ref}`use/hiding/code`:

````md
```{code-cell} ipython3
---
tags: [hide-output]
---
for i in range(20):
    print("Millhouse did not test cootie positive")
```
````

Yields the following:

```{code-cell} ipython3
---
tags: [hide-output]
---
for i in range(20):
    print("Millhouse did not test cootie positive")
```

There is also an **alternative short-hand syntax** for cell-level metadata. This takes
the following form:

````md
```{code-cell}
:key: val
print("hi")
```
````

For example, the following syntax adds a `raises-exception` tag to the cell, which
means our code will execute without halting the kernel:

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

(converting-ipynb)=
## Convert between MyST notebooks and `.ipynb`

MyST notebooks can be converted to Jupyter notebooks using the `mystnb-to-jupyter` CLI command.

```console
$ mystnb-to-jupyter path/to/text-notebook.md
Wrote notebook to: path/to/text-notebook.ipynb
```

MyST notebooks can also be converted back-and-forth from `ipynb` files using [jupytext](https://jupytext.readthedocs.io),
a Python library for two-way conversion of `ipynb` files with many text-based formats.

To let jupytext know the format of the notebook, add the notebook top-matter similar to:

```yaml
---
kernelspec:
  name: python3
  display_name: python3
jupytext:
  text_representation:
    extension: .md
    format_name: myst
    format_version: '0.13'
    jupytext_version: 1.13.8
---
```

Then you can run:

- To convert `.ipynb` to a MyST notebook, run: `jupytext notebook.ipynb --to myst`
- To convert a MyST notebook to `.ipynb`, run: `jupytext mystfile.md --to ipynb`

:::{seealso}
For more information, see the [Jupytext Documentation](https://jupytext.readthedocs.io),
and specifically the [MyST Markdown format](https://jupytext.readthedocs.io/en/latest/formats.html#myst-markdown).
:::

(myst-nb/jupyter-interfaces)=
## MyST notebooks in Jupyter interfaces

You can use MyST notebooks in Jupyter interfaces by using Jupytext extensions. This
allows you to open a MyST Markdown Notebook as a "regular" Jupyter Notebook in
Jupyter Lab and the Classic Notebook interface. For more information, see
[the Jupytext documentation](https://jupytext.readthedocs.io).

(myst-nb/jupyter-book)=
## MyST notebooks in Jupyter Book

In addition to using MyST notebooks with Sphinx, you may also use them with the
Jupyter Book project. See {doc}`jb:file-types/myst-notebooks`.

## Code from Files

```{warning}
This is an experimental feature that is **not** part of the core `MyST` markup specification, and may be removed in the future. Using `:load:` will also overwrite any code written into the directive.
```

`myst_nb` provides a convenience feature for importing executable code into a `{code-cell}`
from a file. This can be useful when you want to share code between documents. To do this
you specify a `load` metadata attribute such as:

````md
```{code-cell} ipython3
:load: <path>
```
````


(authoring/intro)=
# The basics

## Default file formats

As well as writing in the Sphinx default format, [RestructuredText](https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html) (`.rst`), loading `myst_nb` will also parse:

- Markdown files (`.md`)
- Jupyter notebooks (`.ipynb`)
- MyST-NB text-based notebooks (`.md` + top-matter)

## Custom file extensions

You can change which file extensions are parsed by MyST-NB using
the [source_suffix](https://www.sphinx-doc.org/en/master/usage/configuration.html#confval-source_suffix) option in your `conf.py`, e.g.:

```python
extensions = ["myst_nb"]
source_suffix = {
    '.rst': 'restructuredtext',
    '.ipynb': 'myst-nb',
    '.myst': 'myst-nb',
}
```

## Other notebook formats

See the [](write/custom_formats) section, for how to integrate other Notebook formats into your build, and integration with [jupytext](https://github.com/mwouts/jupytext).

## MyST Markdown

For all file formats, Markdown authoring is the backbone of MyST-NB.
By default, the MyST flavour of Markdown is enabled,
which extends [CommonMark](https://commonmark.org/) with RST inspired syntaxes to provide the additional functionality required for technical writing.

In particular MyST adds targets, roles and directives syntax, allowing you to utilise all available Docutils/Sphinx features:

::::{grid} 2
:gutter: 1

:::{grid-item-card} RestructuredText

```
.. _target:
Header
------

:role-name:`content`

.. directive-name:: argument
   :parameter: value

   content
```
:::

:::{grid-item-card} MyST Markdown

````
(target)=
# Header

{role-name}`content`

```{directive-name} argument
:parameter: value

content
```
````
:::
::::

:::{seealso}
See the [](authoring/jupyter-notebooks) section, for more details on how to author Jupyter notebooks.
:::

## Text-based notebooks

MyST-NB text-based notebooks are a special format for storing Jupyter notebooks in a text file.
They map directly to a Notebook file, without directly storing the code execution outputs.

To designate a Markdown file as a text-based notebook, add the following top-matter to the start of the file:

```yaml
---
file_format: mystnb
kernelspec:
  name: python3
---
```

The `kernelspec.name` should relate to a [Jupyter kernel](https://github.com/jupyter/jupyter/wiki/Jupyter-kernels) installed in your environment.

MyST-NB will also recognise [jupytext](https://jupytext.readthedocs.io) top-matter, such as:

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

Code cells are then designated by the `code-cell` directive:

````markdown
```{code-cell}
:tags: [my-tag]

print("Hello world!")
```
````

and Markdown can be split into cells by the `+++` break syntax:

```markdown
Markdown cell 1

+++ {"tags": ["my-tag"]}

Markdown cell 2, with metadata tags
```

:::{seealso}
See the [](authoring/text-notebooks) section, for more details on text-based notebooks, and integration with [jupytext](https://jupytext.readthedocs.io).
:::

## Configuration

MyST-NB parsing, execution and rendering can be configured at three levels of specificity; globally, per file, and per notebook cell, with the most specific configuration taking precedence.

See the [](config/intro) section, for more details on how to configure MyST-NB.

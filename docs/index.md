---
sd_hide_title: true
---

# Overview

::::{grid}
:reverse:
:gutter: 3 4 4 4
:margin: 1 2 1 2

:::{grid-item}
:columns: 12 4 4 4

```{image} _static/logo-square.svg
:width: 200px
:class: sd-m-auto
```

:::

:::{grid-item}
:columns: 12 8 8 8
:child-align: justify
:class: sd-fs-5

```{rubric} Jupyter Notebook Publishing
```

A Docutils and Sphinx extension for compiling Jupyter Notebooks into high quality documentation formats.

```{button-ref} quickstart
:ref-type: doc
:color: primary
:class: sd-rounded-pill

Get Started
```

:::

::::

----------------

::::{grid} 1 3 3 3
:gutter: 1 1 1 2

:::{grid-item-card} {material-regular}`edit_note;2em` Write
:link: authoring/index
:link-type: doc

Mix Jupyter notebooks with text-based notebooks, Markdown and RST documents.\
Use MyST Markdown syntax to support technical authoring features such as cross-referencing, figures, and admonitions.

+++
[Learn more »](authoring/index)
:::

:::{grid-item-card} {material-regular}`published_with_changes;2em` Compute
:link: computation/index
:link-type: doc

Generate dynamic outputs using Jupyter kernels, with configurable execution handling.\
Cache execution outputs, for fast re-builds.

+++
[Learn more »](computation/index)
:::

:::{grid-item-card} {material-regular}`preview;2em` Render
:link: render/index
:link-type: doc

Convert Jupyter execution outputs to embedded content.\
Insert outputs as variables into your documents.\
Build single or collections of documents into multiple formats, including HTML websites and PDF books.

+++
[Learn more »](render/index)
:::

::::

----------------

<!-- Add external links about EBP, Jupyter Book, VS Code, Jupyter Lab extensions
also gallery -->

```{toctree}
:hidden:
:maxdepth: 2

quickstart
```

```{toctree}
:caption: Guides
:hidden:
:maxdepth: 2

authoring/index
computation/index
render/index
configuration
```

```{toctree}
:caption: Reference
:hidden:
:titlesonly:
:maxdepth: 1

reference/api
reference/contributing
reference/changelog
```

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

Hiding cell contents
====================

You can use Jupyter Notebook **cell tags** to control some of the behavior of
the rendered notebook. This uses the [**`sphinx-togglebutton`**](https://sphinx-togglebutton.readthedocs.io/en/latest/)
package to add a little button that toggles the visibility of content.[^download]

[^download]: This notebook can be downloaded as
            **{jupyter-download:notebook}`hiding`** and {download}`hiding.md`

(use/hiding/code)=

# Hiding code cells

You can **cell tags** to control the content hidden with code cells.
Add the following tags to a cell's metadata to control
what to hide in code cells:

* **`hide_input`** tag to hide the cell inputs
* **`hide_output`** to hide the cell outputs
* **`hide_cell`** to hide the entire cell

For example, we'll show cells with each below.

```{code-cell} ipython3
:tags: [remove_cell]

import matplotlib.pyplot as plt
import numpy as np
data = np.random.rand(2, 100) * 100
```

Here is a cell with a `hide_input` tag. Click the "toggle" button to the
right to show it.

```{code-cell} ipython3
:tags: [hide_input]

# This cell has a hide_input tag
fig, ax = plt.subplots()
ax.scatter(*data, c=data[0], s=data[0])
```

Here's a cell with a `hide_output` tag:

```{code-cell} ipython3
:tags: [hide_output]

# This cell has a hide_output tag
fig, ax = plt.subplots()
ax.scatter(*data, c=data[0], s=data[0])
```

And the following cell has a `hide_cell` tag:

```{code-cell} ipython3
:tags: [hide_cell]

# This cell has a hide_cell tag
fig, ax = plt.subplots()
ax.scatter(*data, c=data[0], s=data[0])
```

(use/hiding/markdown)=

# Hiding markdown cells

There are two ways to hide markdown cells. First, **you can add the `hide_input`**
cell metadata. This triggers the same hiding behavior described above for
code cells.

+++ {"tags": ["hide_input"]}

```{note}
This cell was hidden by adding a `hide_input` tag to it!
```

+++

You may also **use a Sphinx directive** to hide specific markdown content. This
is possible by adding the **`.toggle`** class to any block-level directive
that will allow for classes. For example, to the `container`, `note`, or `admonition`
directives.

For example, the hidden block below

```{admonition} This cell was hidden with the toggle class
:class: toggle
Wow, a hidden block! ✨✨
```

Is generated with the following code:

````
```{admonition} This cell was hidden with the toggle class
:class: toggle
Wow, a hidden block! ✨✨
```
````


`````{admonition} Don't add headings to toggle-able sections

Note that containers for markdown (like notes, or this `container`
directive) cannot have their own headings (ie, lines that start
with `#`. If you'd like to use headings, do one of the following:

* Use **bolded text** if you want to highlight sections of a
  toggle-able section.
* Use an **admonition** directive to control the title of the
  message box (that's what this message box uses). Like so:
  ````
  ```{admonition} my admonition title
  My admonition content
  ```
  ````
`````

+++

(use/removing)=

# Removing parts of cells

Sometimes, you want to entirely remove parts of a cell so that it doesn't make it
into the output at all. To do this, you can use the same tag pattern described above,
but with the word `remove_` instead of `hide_`. Use the following tags:

* **`remove_input`** tag to remove the cell inputs
* **`remove_output`** to remove the cell outputs
* **`remove_cell`** to remove the entire cell

+++

Here is a cell with a `remove_input` tag. The inputs will not make it into
the page at all.

```{code-cell} ipython3
:tags: [remove_input]

# This cell has a remove_input tag
fig, ax = plt.subplots()
ax.scatter(*data, c=data[0], s=data[0])
```

Here's a cell with a `remove_output` tag:

```{code-cell} ipython3
:tags: [remove_output]

# This cell has a remove_output tag
fig, ax = plt.subplots()
points = ax.scatter(*data, c=data[0], s=data[0])
```

And the following cell has a `remove_cell` tag (there should be nothing
below, since the cell will be gone).

```{code-cell} ipython3
:tags: [remove_cell]

# This cell has a remove_cell tag
fig, ax = plt.subplots()
points = ax.scatter(*data, c=data[0], s=data[0])
```

---
file_format: mystnb
kernelspec:
  name: python3
---

(authoring/jupyter-notebooks)=
# Jupyter Notebooks

This notebook is a demonstration of directly-parsing Jupyter Notebooks into
Sphinx using the MyST parser.[^download]

[^download]: This notebook can be downloaded as **{nb-download}`jupyter-notebooks.ipynb`** and {download}`jupyter-notebooks.md`

## Markdown

:::{seealso}
For more information about what you can write with MyST Markdown, see the
[MyST Parser documentation](inv:myst#intro/get-started).
:::

### Configuration

The MyST-NB parser derives from [the base MyST-Parser](inv:myst#intro/get-started), and so all the same configuration options are available.
See the [MyST configuration options](inv:myst#sphinx/config-options) for the full set of options, and [MyST syntax guide](inv:myst#syntax/core) for all the syntax options.

To build documentation from this notebook, the following options are set:

```python
myst_enable_extensions = [
    "amsmath",
    "colon_fence",
    "deflist",
    "dollarmath",
    "html_image",
]
myst_url_schemes = ("http", "https", "mailto")
```

:::{note}
Loading the `myst_nb` extension also activates the [`myst_parser`](inv:myst#index) extension, for enabling the MyST flavour of Markdown.
It is not required to add this explicitly in the list of `extensions`.
:::

### Syntax

As you can see, markdown is parsed as expected. Embedding images should work as expected.
For example, here's the MyST-NB logo:

```md
![myst-nb logo](../_static/logo-wide.svg)
```

![myst-nb logo](../_static/logo-wide.svg)

By adding `"html_image"` to the `myst_enable_extensions` list in the sphinx configuration ([see here](inv:myst#syntax/images)), you can even add HTML `img` tags with attributes:

```html
<img src="../_static/logo-wide.svg" alt="logo" width="200px" class="shadow mb-2">
```

<img src="../_static/logo-wide.svg" alt="logo" width="200px"  class="shadow mb-2">

Because MyST-NB is using the MyST-markdown parser, you can include rich markdown with Sphinx in your notebook.
For example, here's a note admonition block:

:::::{note}
**Wow**, a note!
It was generated with this code ([as explained here](inv:myst:std:label#syntax/admonitions)):

````md
:::{note}
**Wow**, a note!
:::
````

:::::

If you wish to use "bare" LaTeX equations, then you should add `"amsmath"` to the `myst_enable_extensions` list in the sphinx configuration.
This is [explained here](inv:myst:std:label#syntax/amsmath), and works as such:

```latex
\begin{equation}
\frac {\partial u}{\partial x} + \frac{\partial v}{\partial y} = - \, \frac{\partial w}{\partial z}
\end{equation}

\begin{align*}
2x - 5y &=  8 \\
3x + 9y &=  -12
\end{align*}
```

\begin{equation}
\frac {\partial u}{\partial x} + \frac{\partial v}{\partial y} = - \, \frac{\partial w}{\partial z}
\end{equation}

\begin{align*}
2x - 5y &=  8 \\
3x + 9y &=  -12
\end{align*}

Also you can use features like **equation numbering** and referencing in the notebooks:

```md
$$e^{i\pi} + 1 = 0$$ (euler)
```

$$e^{i\pi} + 1 = 0$$ (euler)

Euler's identity, equation {math:numref}`euler`, was elected one of the
most beautiful mathematical formulas.

You can see the syntax used for this example [here in the MyST documentation](inv:myst:std:label#syntax/math).

## Code cells and outputs

You can run cells, and the cell outputs will be captured and inserted into
the resulting Sphinx site.

### `__repr__` and HTML outputs

For example, here's some simple Python:

```{code-cell} ipython3
import matplotlib.pyplot as plt
import numpy as np
data = np.random.rand(3, 100) * 100
data[:, :10]
```

This will also work with HTML outputs

```{code-cell} ipython3
import pandas as pd
df = pd.DataFrame(data.T, columns=['a', 'b', 'c'])
df.head()
```

as well as math outputs

```{code-cell} ipython3
from IPython.display import Math
Math(r"\sum_{i=0}^n i^2 = \frac{(n^2+n)(2n+1)}{6}")
```

This works for error messages as well:

```{code-cell} ipython3
:tags: [raises-exception]

print("This will be properly printed...")
print(thiswont)
```

### Images

Images that are generated from your code (e.g., with Matplotlib) will also
be embedded.

```{code-cell} ipython3
fig, ax = plt.subplots()
ax.scatter(*data, c=data[2])
```

## Raw cells

The [raw cell type](https://nbformat.readthedocs.io/en/latest/format_description.html#raw-nbconvert-cells) can be used to specifically render the content as a specific [MIME media type](https://developer.mozilla.org/en-US/docs/Web/HTTP/Basics_of_HTTP/MIME_types).

````markdown
```{raw-cell}
:format: text/html

<p>My cat is <strong>very</strong> grumpy.</p>
```
````

```{raw-cell}
:format: text/html

<p>My cat is <strong>very</strong> grumpy.</p>
```

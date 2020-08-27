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

# An example Jupyter Notebook

This notebook is a demonstration of directly-parsing Jupyter Notebooks into
Sphinx using the MyST parser.[^download]

[^download]: This notebook can be downloaded as
            **{nb-download}`basic.ipynb`** and {download}`basic.md`

## Markdown


### Configuration

The MyST-NB parser derives from [the base MyST-Parser](myst:intro/get-started>, and so all the same configuration options are available.
See the [MyST configuration options](myst:intro/config-options) for the full set of options, and [MyST syntax guide](myst:example_syntax) for all the syntax options.

To build documentation from this notebook, the following options are set:

```python
myst_admonition_enable = True
myst_amsmath_enable = True
myst_html_img_enable = True
myst_url_schemes = ("http", "https", "mailto")
```

### Syntax

As you can see, markdown is parsed as expected. Embedding images should work as expected.
For example, here's the MyST-NB logo:

```md
![myst-nb logo](../_static/logo.png)
```

![myst-nb logo](../_static/logo.png)

With the `myst_html_img_enable=True` ([see here](myst:syntax/images)), you can even add HTML img tags with attributes:

```html
<img src="../_static/logo.png" alt="logo" width="200px" class="shadow mb-2">
```

<img src="../_static/logo.png" alt="logo" width="200px"  class="shadow mb-2">

Because MyST-NB is using the MyST-markdown parser, you can include rich markdown with Sphinx in your notebook.
For example, here's a note admonition block:

:::::{note}
**Wow**, a note!
It was generated with this code ([as explained here](myst:syntax/admonitions)):

````md
:::{note}
**Wow**, a note!
:::
````

:::::

If you wish to use "bare" LaTeX equations, then you should set `myst_amsmath_enable = True` in the sphinx configuration.
This is [explained here](myst:syntax/amsmath), and works as such:

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

You can see the syntax used for this example [here in the MyST documentation](myst:syntax/math).

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

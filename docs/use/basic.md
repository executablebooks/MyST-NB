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
            **{jupyter-download:notebook}`basic`** and {download}`basic.md`

## Markdown

As you can see, markdown is parsed as expected. Embedding images should work as expected.
For example, here's the MyST-nb logo:

![](../_static/logo.png)

because MyST-NB is using the MyST-markdown parser, you can include rich markdown with Sphinx
in your notebook. For example, here's a note block:

`````{note}
Wow, a note! It was generated with this code:

````
```{note}
Wow, a note!
```
````
`````

Equations work as expected:

\begin{equation}
\frac {\partial u}{\partial x} + \frac{\partial v}{\partial y} = - \, \frac{\partial w}{\partial z}
\end{equation}

And some MyST-specific features like **equation numbering** can be used in notebooks:

$$e^{i\pi} + 1 = 0$$ (euler)

Euler's identity, equation {math:numref}`euler`, was elected one of the
most beautiful mathematical formulas.

You can see the syntax used for this example [here](https://myst-parser.readthedocs.io/en/latest/using/syntax.html#roles-an-in-line-extension-point).

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
Math("\sum_{i=0}^n i^2 = \frac{(n^2+n)(2n+1)}{6}")
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

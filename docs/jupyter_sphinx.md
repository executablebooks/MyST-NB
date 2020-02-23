# A Jupyter Sphinx example

```{toctree}
:maxdepth: 2
:caption: "Contents:"
```

Jupyter-sphinx is a Sphinx extension that executes embedded code in a Jupyter
kernel, and embeds outputs of that code in the document. It has support
for rich output such as images, Latex math and even javascript widgets, and
it allows to enable [thebelab](https://thebelab.readthedocs.io/) for live
code execution with minimal effort.


## Basic Usage

You can use the `jupyter-execute` directive to embed code into the document

````
```{jupyter-execute}
name = 'world'
print('hello ' + name + '!')
```
````

The above is rendered as follows:

```{jupyter-execute}
name = 'world'
print('hello ' + name + '!')
```

Note that the code produces *output* (printing the string 'hello world!'), and the output
is rendered directly after the code snippet.

Because all code cells in a document are run in the same kernel, cells later in the document
can use variables and functions defined in cells earlier in the document:

```{jupyter-execute}
a = 1
print('first cell: a = {}'.format(a))
```
```{jupyter-execute}
a += 1
print('second cell: a = {}'.format(a))
```

Because jupyter-sphinx uses the machinery of `nbconvert`, it is capable of rendering
any rich output, for example plots:

```{jupyter-execute}

import numpy as np
from matplotlib import pyplot
%matplotlib inline

x = np.linspace(1E-3, 2 * np.pi)

pyplot.plot(x, np.sin(x) / x)
pyplot.plot(x, np.cos(x))
pyplot.grid()
```

LaTeX output:

```{jupyter-execute}

  from IPython.display import Latex
  Latex('∫_{-∞}^∞ e^{-x²}dx = \sqrt{π}')
```
or even full-blown javascript widgets:

```{jupyter-execute}

import ipywidgets as w
from IPython.display import display

a = w.IntSlider()
b = w.IntText()
w.jslink((a, 'value'), (b, 'value'))
display(a, b)

```

## Directive options

You may choose to hide the code of a cell, but keep its output visible using `:hide-code:`

````
```{jupyter-execute}
:hide-code:

print('this code is invisible')
```
````

produces:

```{jupyter-execute}
:hide-code:

print('this code is invisible')
```

or vice versa with ``:hide-output:``::

````
```{jupyter-execute}
:hide-output:

print('this output is invisible')
```
````

```{jupyter-execute}
:hide-output:

print('this output is invisible')
```

You may also display the code *below* the output with ``:code-below:``::

```{jupyter-execute}
:code-below:
print('this output is above the code')
```

You may also add *line numbers* to the source code with ``:linenos:``::

```{jupyter-execute}
:linenos:

print('A')
print('B')
print('C')

```

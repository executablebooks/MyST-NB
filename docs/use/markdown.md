# Notebooks in markdown

MyST-NB also provides functionality for notebooks within markdown. This lets you
include and control notebook-like behavior from with your markdown content.

The primary way to accomplish this is with the `{execute}` directive. The content
of this directive should be runnable code in Jupyter. For example, the following
code:

````
```{execute}
a = "This is some"
b = "Python code!"
print(f"{a} {b}")
```
````

Yields the following:

```{execute}
a = "This is some"
b = "Python code!"
print(f"{a} {b}")
```

Currently, this uses [Jupyter-Sphinx](https://jupyter-sphinx.readthedocs.io/)
under the hood for execution and rendering.

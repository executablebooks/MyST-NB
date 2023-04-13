# Get Started

`myst-nb` is distributed as a Python package and requires no non-Python dependencies.

Use pip to install `myst-nb`:

```bash
pip install myst-nb
```

You can use the `mystnb-quickstart` CLI to quickly create an example Sphinx + MyST-NB project:

```bash
mystnb-quickstart my_project/docs/
```

or simply add `myst_nb` to your existing Sphinx configuration:

```python
extensions = [
    ...,
    "myst_nb"
]
```

By default, MyST-NB will now parse both markdown (`.md`) and notebooks (`.ipynb`).

```{button-ref} authoring/intro
:ref-type: myst
:color: primary

Begin authoring your content {material-regular}`navigate_next;2em`
```

Once you have finished authoring your content, you can now use the [sphinx-build CLI](https://www.sphinx-doc.org/en/master/man/sphinx-build.html) to build your documentation, e.g.

```bash
sphinx-build -nW --keep-going -b html docs/ docs/_build/html
```

:::{tip}
MyST-NB is parallel-friendly, so you can also distribute the build (and execution of notebooks) over *N* processes with: `sphinx-build -j 4`
:::

:::{seealso}
Check out [Read the Docs](https://docs.readthedocs.io) for hosting and *continuous deployment* of documentation
:::

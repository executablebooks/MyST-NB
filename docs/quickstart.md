# Get Started

`myst-nb` is distributed as a Python package and requires no non-Python dependencies.

Use pip to install `myst-nb`:

```bash
pip install myst-nb
```

You can use the `mystnb-quickstart` CLI to quickly create an example Sphinx + MyST-NB project:

```bash
mystnb-quickstart my_project/
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

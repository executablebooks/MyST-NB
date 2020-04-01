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
orphan: true
---

(orphaned-nb)=

# An orphaned notebook

This defines a variable that we'll re-use in another notebook.

```{code-cell} ipython3
from myst_nb import glue
my_var = "My orphaned variable!"
glue("orphaned_var", my_var)
```

---
jupytext:
  text_representation:
    extension: .md
    format_name: myst
    format_version: '0.8'
    jupytext_version: 1.4.1+dev
kernelspec:
  display_name: Python 3
  language: python
  name: python3
author: Chris
---

# Test the `nb-exec-table` directive

```{code-cell} ipython3
print("hi")
```

This directive should generate a table of executed notebook statistics.

```{nb-exec-table}
```

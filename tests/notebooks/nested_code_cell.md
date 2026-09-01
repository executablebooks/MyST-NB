---
file_format: mystnb
kernelspec:
  display_name: Python 3
  language: python
  name: python3
---

# Nested code cells

## Control: standalone code cell (should render)

```{code-cell} python
print("hello from standalone cell")
```

## Reproducer: code cell nested in another directive (should still render source)

````{note}
```{code-cell} python
print("hello from nested cell")
```
````

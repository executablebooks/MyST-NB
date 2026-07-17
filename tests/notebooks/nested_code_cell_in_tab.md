---
file_format: mystnb
kernelspec:
  display_name: Python 3
  language: python
  name: python3
---

# Code cells in tab groups

## Control: standalone code cell

```{code-cell} python
print("hello from standalone cell")
```

## Reproducer: code cells inside tab-set

`````{tab-set}

````{tab-item} Tab 1
```{code-cell} python
print("hello from tab 1")
```
````

````{tab-item} Tab 2
```{code-cell} python
print("hello from tab 2")
```
````

`````

---
jupytext:
  text_representation:
    extension: .md
    format_name: myst
    format_version: '0.12'
    jupytext_version: 1.5.2
kernelspec:
  display_name: Coconut
  language: coconut
  name: coconut
---

# Notebooks in other languages

<http://coconut-lang.org/>

```{code-cell} coconut
def factorial(n):
    """Compute n! where n is an integer >= 0."""
    if n `isinstance` int and n >= 0:
        acc = 1
        for x in range(1, n+1):
            acc *= x
        return acc
    else:
        raise TypeError("the argument to factorial must be an integer >= 0")

3 |> factorial |> print
```

```{code-cell} coconut
def quick_sort(l):
    """Sort the input iterator using the quick sort algorithm."""
    match [head] :: tail in l:
        tail = reiterable(tail)
        yield from quick_sort(left) :: [head] :: quick_sort(right) where:
            left = (x for x in tail if x < head)
            right = (x for x in tail if x >= head)
    # By yielding nothing if the match falls through, we implicitly return an empty iterator.

[3,0,4,2,1] |> quick_sort |> list |> print
```

```{code-cell} coconut
:tags: [raises-exception]
x
```

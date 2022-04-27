---
file_format: mystnb
kernelspec:
  name: coconut
---

# Jupyter kernels

A Jupyter Notebook can utilise any program kernel that implements the [Jupyter messaging protocol](http://jupyter-client.readthedocs.io/en/latest/messaging.html) for executing code.
There are kernels available for [Python](http://ipython.org/notebook.html), [Julia](https://github.com/JuliaLang/IJulia.jl), [Ruby](https://github.com/minad/iruby), [Haskell](https://github.com/gibiansky/IHaskell) and [many other languages](https://github.com/jupyter/jupyter/wiki/Jupyter-kernels).

In this notebook we demonstrate executing code with the [Coconut Programming Language](http://coconut-lang.org), a variant of Python built for *simple, elegant, Pythonic functional programming*.

In the first example we will define a recursive `factorial` function, a fundamentally functional approach that doesn’t involve any state changes or loops:

```{code-cell} coconut
def factorial(n):
    """Compute n! where n is an integer >= 0."""
    case n:
        match 0:
            return 1
        match x is int if x > 0:
            return x * factorial(x-1)
    else:
        raise TypeError("the argument to factorial must be an integer >= 0")

3 |> factorial |> print
```

Although this example is very basic, pattern-matching is both one of Coconut’s most powerful and most complicated features.

In the second example, we implement the quick sort algorithm.
This quick_sort algorithm works using a bunch of new constructs:

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

Finally, we see that exceptions are raised as one would expect:

```{code-cell} coconut
:tags: [raises-exception]
x
```

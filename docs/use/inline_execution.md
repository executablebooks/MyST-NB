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
mystnb:
    execution_mode: inline
---

# Inline execution mode and Markdown variables

This is a Proof of Concept notebook for inline variables.

This notebook is executed using top-matter:

```md

---
mystnb:
    execution_mode: inline
---
```

which turns on the experimental inline execution mode.

Inline execution starts the Jupyter kernel, then executes code cells as they are visited during the conversion to docutils AST.

When an `eval` role or directive is encountered, the name is evaluated by the kernel and the result is inserted into the document.

You can see here that the variable `a`, which is inserted by the `eval` role, will change based on the order of execution (relative to the code cells).

```{code-cell} ipython3
a=1
```

First call to `` {eval}`a` `` gives us: {eval}`a`

```{code-cell} ipython3
a=2
```

Second call to `` {eval}`a` `` gives us: {eval}`a`

```{note}
The evaluation works in any nested environment: {eval}`a`
```

```{code-cell} ipython3
from IPython.display import Image
image = Image("images/fun-fish.png")
```

You can also evaluate any type of variable:

````md
```{eval} image
```
````

```{eval} image
```

```{code-cell} ipython3
from IPython.display import Markdown
markdown = Markdown("""
This can have **nested syntax**.
""")
```

````md
```{eval} markdown
```
````

```{eval} markdown
```

This will work for any Jupyter kernel, independent of language!

Incorrect variables will currently like `` {eval}`b` ``, will currently log warnings:

> `/docs/use/inline_execution.md:88: WARNING: NameError: name 'b' is not defined [mystnb.eval]`

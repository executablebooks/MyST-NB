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
---

# Formatting Code Outputs

## ANSI Outputs


```{code-cell} ipython3
print("\u001b[44;1m A \u001b[45;1m B \u001b[46;1m C \u001b[47;1m D \u001b[0m ")
```


```{code-cell} ipython3
print("\u001b[36mres3\u001b[39m: \u001b[32mInt\u001b[39m = \u001b[32m1\u001b[39m")
```

To turn off: `nb_render_text_lexer="none"`

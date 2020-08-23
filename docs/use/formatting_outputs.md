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

(use/format)=
# Formatting code outputs

(use/format/priority)=
## Render priority

When Jupyter executes a code cell it can produce multiple outputs, and each of these outputs can contain multiple [MIME media types](https://developer.mozilla.org/en-US/docs/Web/HTTP/Basics_of_HTTP/MIME_types), for use by different output formats (like HTML or LaTeX).

MyST-NB stores a default priority dictionary for most of the common [Sphinx builders](https://www.sphinx-doc.org/en/master/usage/builders/index.html), which you can be also update in your `conf.py`.
For example, this is the default priority list for HTML:

```python
nb_render_priority = {
  "html": (
            "application/vnd.jupyter.widget-view+json",
            "application/javascript",
            "text/html",
            "image/svg+xml",
            "image/png",
            "image/jpeg",
            "text/markdown",
            "text/latex",
            "text/plain",
        )
}
```

:::{seealso}
[](use/format/cutomise), for a more advanced means of customisation.
:::

## Removing stdout and stderr

In some cases you may not wish to display stdout/stderr outputs in your final documentation,
for example, if they are only for debugging purposes.
You can tell MyST-NB to remove these outputs using the `remove-stdout` and `remove-stderr` [cell tags](https://jupyter-notebook.readthedocs.io/en/stable/changelog.html#cell-tags), like so:

````md
```{code-cell} ipython3
:tags: [remove-input,remove-stdout,remove-stderr]

import pandas, sys
print("this is some stdout")
print("this is some stderr", file=sys.stderr)
# but what I really want to show is:
pandas.DataFrame({"column 1": [1, 2, 3]})
```
````

```{code-cell} ipython3
:tags: [remove-input,remove-stdout,remove-stderr]

import pandas, sys
print("this is some stdout")
print("this is some stderr", file=sys.stderr)
# but what I really want to show is:
pandas.DataFrame({"column 1": [1, 2, 3]})
```

(use/format/markdown)=
## Markdown

Markdown output is parsed by MyST-Parser, currently with the configuration set to `myst_commonmark_only=True` (see [MyST configuration options](myst:intro/config-options)).

The parsed Markdown is integrated into the wider documentation, and so it is possible, for example, to include internal references:

```{code-cell} ipython3
from IPython.display import display, Markdown
display(Markdown('**_some_ markdown** and an [internal reference](use/format/markdown)!'))
```

and even internal images can be rendered!

```{code-cell} ipython3
display(Markdown('![figure](../_static/logo.png)'))
```

(use/format/ansi)=
## ANSI Outputs

By default, the standard output/error streams and text/plain MIME outputs may contain ANSI escape sequences to change the text and background colors.

```{code-cell} ipython3
import sys
print("BEWARE: \x1b[1;33;41mugly colors\x1b[m!", file=sys.stderr)
print("AB\x1b[43mCD\x1b[35mEF\x1b[1mGH\x1b[4mIJ\x1b[7m"
      "KL\x1b[49mMN\x1b[39mOP\x1b[22mQR\x1b[24mST\x1b[27mUV")
```

This uses the built-in `AnsiColorLexer` [pygments](https://pygments.org/) lexer.
You can change the lexer used in the `conf.py`, for example to turn off lexing:

```python
nb_render_text_lexer = "none"
```

The following code[^acknowledge] shows the 8 basic ANSI colors it is based on.
Each of the 8 colors has an “intense” variation, which is used for bold text.

[^acknowledge]: Borrowed from [nbsphinx](https://nbsphinx.readthedocs.io/en/0.7.1/code-cells.html#ANSI-Colors)!

```{code-cell} ipython3
text = " XYZ "
formatstring = "\x1b[{}m" + text + "\x1b[m"

print(
    " " * 6
    + " " * len(text)
    + "".join("{:^{}}".format(bg, len(text)) for bg in range(40, 48))
)
for fg in range(30, 38):
    for bold in False, True:
        fg_code = ("1;" if bold else "") + str(fg)
        print(
            " {:>4} ".format(fg_code)
            + formatstring.format(fg_code)
            + "".join(
                formatstring.format(fg_code + ";" + str(bg)) for bg in range(40, 48)
            )
        )
```

:::{note}
ANSI also supports a set of 256 indexed colors.
This is currently not supported, but we hope to introduce it at a later date
(raise an issue on the repository if you require it!).
:::

(use/format/cutomise)=
## Customising the rendering process

TODO

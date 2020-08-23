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

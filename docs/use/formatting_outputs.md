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

(use/format/stderr)=
## Removing stdout and stderr

In some cases you may not wish to display stdout/stderr outputs in your final documentation,
for example, if they are only for debugging purposes.

You can tell MyST-NB to remove these outputs, per cell, using the `remove-stdout` and `remove-stderr` [cell tags](https://jupyter-notebook.readthedocs.io/en/stable/changelog.html#cell-tags), like so:

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

Alternatively, you can configure how stdout is dealt with at a global configuration level, using the `nb_output_stderr` configuration value.
This can be set to:

- `"show"` (default): show all stderr (unless a `remove-stderr` tag is present)
- `"remove"`: remove all stderr
- `"remove-warn"`: remove all stderr, but log a warning to sphinx if any found
- `"warn"`, `"error"` or `"severe"`: log to sphinx, at a certain level, if any found.

(use/format/images)=
## Images

With the default renderer, for any image types output by the code, we can apply formatting *via* cell metadata.
The top-level metadata key can be set using `nb_render_key` in your `conf.py`, and is set to `render` by default.
Then for the image we can apply all the variables of the standard [image directive](https://docutils.sourceforge.io/docs/ref/rst/directives.html#image):

- **width**: length or percentage (%) of the current line width
- **height**: length
- **scale**: integer percentage (the "%" symbol is optional)
- **align**: "top", "middle", "bottom", "left", "center", or "right"
- **classes**: space separated strings
- **alt**: string

Units of length are: 'em', 'ex', 'px', 'in', 'cm', 'mm', 'pt', 'pc'

We can also set a caption (which is rendered as [CommonMark](https://commonmark.org/)) and name, by which to reference the figure:

````md
```{code-cell} ipython3
---
render:
  image:
    width: 200px
    alt: fun-fish
    classes: shadow bg-primary
  figure:
    caption: |
      Hey everyone its **party** time!
    name: fun-fish
---
from IPython.display import Image
Image("images/fun-fish.png")
```
````

```{code-cell} ipython3
---
render:
  image:
    width: 300px
    alt: fun-fish
    classes: shadow bg-primary
  figure:
    caption: |
      Hey everyone its **party** time!
    name: fun-fish
---
from IPython.display import Image
Image("images/fun-fish.png")
```

Now we can link to the image from anywhere in our documentation: [swim to the fish](fun-fish)

(use/format/markdown)=
## Markdown

Markdown output is parsed by MyST-Parser, currently with the configuration set to `myst_commonmark_only=True` (see [MyST configuration options](myst:sphinx/config-options)).

The parsed Markdown is integrated into the wider documentation, and so it is possible, for example, to include internal references:

```{code-cell} ipython3
from IPython.display import display, Markdown
display(Markdown('**_some_ markdown** and an [internal reference](use/format/markdown)!'))
```

and even internal images can be rendered!

```{code-cell} ipython3
display(Markdown('![figure](../_static/logo-wide.svg)'))
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

This uses the built-in {py:class}`~myst_nb.ansi_lexer.AnsiColorLexer` [pygments lexer](https://pygments.org/).
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
## Customise the render process

The render process is goverened by subclasses of {py:class}`myst_nb.render_outputs.CellOutputRendererBase`, which dictate how to create the `docutils` AST nodes for a particular MIME type. the default implementation is {py:class}`~myst_nb.render_outputs.CellOutputRenderer`.

Implementations are loaded *via* Python [entry points](https://packaging.python.org/guides/distributing-packages-using-setuptools/#entry-points), in the `myst_nb.mime_render` group.
So it is possible to inject your own subclass to handle rendering.

For example, the renderers loaded in this package are:

```python
entry_points={
    "myst_nb.mime_render": [
        "default = myst_nb.render_outputs:CellOutputRenderer",
        "inline = myst_nb.render_outputs:CellOutputRendererInline",
    ],
}
```

You can then select the renderer plugin in your `conf.py`:

```python
nb_render_plugin = "default"
```

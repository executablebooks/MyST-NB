(render/single-page)=
# Single page builds

```{versionadded} 0.14.0
```

Sphinx, and thus MyST-NB, is built on top of the [Docutils](https://docutils.sourceforge.io/docs/) package.
MyST-NB offers a renderer, parser and CLI-interface for working directly with Docutils, independent of Sphinx, as described below.

:::{note}
Since these tools are independent of Sphinx, this means they cannot parse any Sphinx or Sphinx extensions specific roles or directives.
:::

On installing MyST-NB, the following CLI-commands are made available:

- `mystnb-docutils-html`: converts notebooks to HTML
- `mystnb-docutils-html5`: converts notebooks to HTML5
- `mystnb-docutils-latex`: converts notebooks to LaTeX
- `mystnb-docutils-xml`: converts notebooks to docutils-native XML
- `mystnb-docutils-pseudoxml`: converts notebooks to pseudo-XML (to visualise the AST structure)

Each command can be piped stdin or take a file path as an argument:

```console
$ mystnb-docutils-html --help
$ mystnb-docutils-html --nb-execution-mode="off" hello-world.ipynb
$ mystnb-docutils-html --nb-read-as-md="yes" hello-world.md
```

The commands are based on the [Docutils Front-End Tools](https://docutils.sourceforge.io/docs/user/tools.html), and so follow the same argument and options structure, included many of the MyST NB specific options detailed in the [](config/intro) section.

:::{dropdown}  Shared Docutils CLI Options
```{docutils-cli-help}
```
:::

The CLI commands can also utilise the [`docutils.conf` configuration file](https://docutils.sourceforge.io/docs/user/config.html) to configure the behaviour of the CLI commands. For example:

```ini
# These entries affect all processing:
[general]
nb_execution_mode: off

# These entries affect specific HTML output:
[html writers]
embed-stylesheet: no

[html5 writer]
stylesheet-dirs: path/to/html5_polyglot/
stylesheet-path: minimal.css, responsive.css
```

You can also use the {py:class}`myst_nb.docutils_.Parser` class programmatically with the [Docutils publisher API](https://docutils.sourceforge.io/docs/api/publisher.html):

```python
from docutils.core import publish_string
from nbformat import writes
from nbformat.v4 import new_notebook
from myst_nb.docutils_ import Parser

source = writes(new_notebook())
output = publish_string(
    source=source,
    writer_name="html5",
    settings_overrides={
        "nb_execution_mode": "off",
        "embed_stylesheet": False,
    },
    parser=Parser(),
)
```

Finally, you can include MyST Markdown files within a RestructuredText file, using the [`include` directive](https://docutils.sourceforge.io/docs/ref/rst/directives.html#include):

```rst
.. include:: include.ipynb
   :parser: myst_nb.docutils_
```

```{important}
The `parser` option requires `docutils>=0.17`
```

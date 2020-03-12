# MyST-NB

A collection of tools for working with Jupyter Notebooks in Sphinx, using the
Markedly Structured Text markdown language.

The primary tool this package provides is a Sphinx parser for `ipynb` files.
This allows you to directly convert Jupyter Notebooks into Sphinx documents.
It relies heavily on the [`MyST` parser](https://github.com/ExecutableBookProject/myst_parser).

```{warning}
This project is in an alpha state. It may evolve rapidly and/or make breaking changes!
Comments, requests, or bugreports are welcome and recommended! Please
[open an issue here](https://github.com/ExecutableBookProject/myst-nb/issues)
```

## Installation

To install `myst-nb`, do the following:

* Install `myst-nb` with the following command:

  ```bash
  pip install myst-nb
  ```

  Or for package development:

  ```bash
  git clone https://github.com/ExecutableBookProject/MyST-NB
  cd MyST-NB
  git checkout master
  pip install -e .[code_style,testing,rtd]
  pip install git+https://github.com/pandas-dev/pandas-sphinx-theme.git@master
  ```

* Enable the `myst_nb` extension in your Sphinx repository's extensions:

  ```python
  extensions = [
      ...,
      "myst_nb"
  ]
  ```

  ```{note}
  If you'd like to use MyST to parse markdown files as well, then you can enable it by
  adding `myst_parser` to your list of extensions as well.
  ```
* Write Jupyter Notebooks with your built documentation, and remember to include them
  in your `toctree`, and that's it!

## How the Jupyter Notebook parser works

MyST-NB is built on top of the MyST markdown parser. This is a flavor of markdown
designed to work with the Sphinx ecosystem. It is a combination of CommonMark markdown,
with a few extra syntax pieces added for use in Sphinx (for example, roles and
directives).

```{note}
For more about MyST markdown, see
[the MyST markdown documentation](https://myst-parser.readthedocs.io/en/latest/)
```

MyST-NB will do the following:

* Check for any pages in your documentation folder that end in `.ipynb`. For each one:
* Loop through the notebook's cells, converting cell contents into the Sphinx AST.
  * If it finds executable code cells, include their outputs in-line with the code.
  * If it finds markdown cells, use the MyST parser to convert them into Sphinx.

Eventually, it will also provide support for writing pure-markdown versions of notebooks
that can be executed and read into Sphinx.

## Use and configure

For information on using and configuring MyST-NB, as well as some examples of notebook
outputs, see the pages below:

```{toctree}
use/index.ipynb
```

In addition, here is a reference page that uses the `jupyter-sphinx` package to create
outputs, to compare how these outputs look relative to the MyST-NB style.

```{toctree}
examples/jupyter_sphinx.md
```

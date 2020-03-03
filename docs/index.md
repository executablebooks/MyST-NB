# MyST-NB

A collection of tools for working with Jupyter Notebooks in Sphinx.

The primary tool this package provides is a Sphinx parser for `ipynb` files.
This allows you to directly convert Jupyter Notebooks into Sphinx documents.
It relies heavily on the [`MyST` parser](https://github.com/ExecutableBookProject/myst_parser).

```{warn}
This project is in an alpha state. It may evolve rapidly and/or make breaking changes!
It currently depends on a fork of the Mistletoe library, so keep that in mind as you
use it!
```

## Installation

To install `myst-nb`, do the following:

* Ensure that `myst_parser` and `myst-nb` are installed with the following
  commands:

  `myst_parser`:
  ```
  pip install -e "git+https://github.com/ExecutableBookProject/myst_parser.git#egg=myst_parser[sphinx]"
  ```

  `myst-nb`:
  ```
  pip install -e "git+https://github.com/executablebookproject/sphinx-notebook.git#egg=sphinx-notebook[sphinx]"
  ```
* Enable both the `myst_parser` and `sphinx-notebook` in your Sphinx repository's
  extensions:

  ```python
  extensions = [
      ...,
      "myst_parser",
      "myst_nb"
  ]
  ```
* Include Jupyter Notebooks with your built documentation, and remember to include them
  in your `toctree`, and that's it!

## An example

To see an example of reading in notebooks directly into Sphinx, see the page below.

```{toctree}
notebooks.ipynb
```

And here is a reference Jupyter Sphinx demo page to see how things look in raw text

```{toctree}
jupyter_sphinx.md
```

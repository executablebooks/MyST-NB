# MyST-NB

[![Github-CI][github-badge]][github-link]
[![Github-CI][github-ci]][github-link]
[![Coverage Status][codecov-badge]][codecov-link]
[![Documentation Status][rtd-badge]][rtd-link]
[![PyPI][pypi-badge]][pypi-link]

**Read, write, and execute Jupyter Notebooks in Sphinx**

`MyST-NB` is a reference implementation of MyST Markdown Notebooks, and
an open source tool for working with Jupyter Notebooks in the
Sphinx ecosystem. It provides the following primary features:

* **{ref}`Parse ipynb files in Sphinx<installation>`**. Directly convert Jupyter
  Notebooks into Sphinx documents.
* [**Execute and Cache your notebook content**](use/execute.md).
  Save time building your documentation without needing to commit your notebook outputs
  directly into `git`.
* **{doc}`Write MyST Markdown<use/myst>`**. MyST Markdown
  allows you to write Sphinx roles and directives in markdown.
* **{doc}`Insert notebook outputs into your content <use/glue>`**. Generate outputs
  as you build your documentation, and insert them across pages.
* **{doc}`Write Jupyter Notebooks entirely with Markdown <use/markdown>`**. You can
  define the structure of a notebook *in pure-text* making it more diff-able.

In addition, there are several options for controlling the look and feel of how your
notebooks are used in your documentation. See the documentation pages to the left for
more information.

:::{note}
This project is in a beta state. Comments, requests, or bugreports are welcome and
recommended! Please [open an issue here](https://github.com/executablebooks/myst-nb/issues)
:::

(installation)=
## Installation and basic usage

To install `myst-nb`, do the following:

* Install `myst-nb` with the following command:

  ```bash
  pip install myst-nb
  ```

* Enable the `myst_nb` extension in your Sphinx repository's extensions:

  ```python
  extensions = [
      ...,
      "myst_nb"
  ]
  ```

  By default, MyST-NB will parse both markdown (`.md`) and notebooks (`.ipynb`).

* Write Jupyter Notebooks with your built documentation, and remember to include them
  in your `toctree`, and that's it!

## Customize and configure

For information on using and configuring MyST-NB, as well as some examples of notebook
outputs, see the pages below:

```{toctree}
:maxdepth: 2
use/index
use/markdown
```

In addition, here is a reference page that uses the `jupyter-sphinx` package to create
outputs, to compare how these outputs look relative to the MyST-NB style.

```{toctree}
:maxdepth: 2
examples/index
```

Finally, here is documentation on contributing to the development of MySt-NB

```{toctree}
:titlesonly:
:maxdepth: 1
changelog
develop/contributing
api/index
GitHub Repo <https://github.com/executablebooks/myst-nb>
```

[github-ci]: https://github.com/executablebooks/MyST-NB/workflows/continuous-integration/badge.svg?branch=master
[github-link]: https://github.com/executablebooks/MyST-NB
[rtd-badge]: https://readthedocs.org/projects/myst-nb/badge/?version=latest
[rtd-link]: https://myst-nb.readthedocs.io/en/latest/?badge=latest
[codecov-badge]: https://codecov.io/gh/executablebooks/MyST-NB/branch/master/graph/badge.svg
[codecov-link]: https://codecov.io/gh/executablebooks/MyST-NB
[pypi-badge]: https://img.shields.io/pypi/v/myst-nb.svg
[pypi-link]: https://pypi.org/project/myst-nb
[github-badge]: https://img.shields.io/github/stars/executablebooks/myst-nb?label=github

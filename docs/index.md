# MyST-NB

**Read, write, and execute Jupyter Notebooks in Docutils and Sphinx**

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

# MyST-NB

Tools for working with Jupyter Notebooks in Sphinx, using the
Markedly Structured Text markdown language. `MyST-NB` provides the following main
features:

* **{ref}`Parse ipynb files in Sphinx<installation>`**. Directly convert Jupyter
  Notebooks into Sphinx documents.
* **{doc}`Execute and Cache your notebook content <use/execute>`**.
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

```{warning}
This project is in an alpha state. It may evolve rapidly and/or make breaking changes!
Comments, requests, or bugreports are welcome and recommended! Please
[open an issue here](https://github.com/ExecutableBookProject/myst-nb/issues)
```

(installation)=
## Installation and basic usage

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
use/index.ipynb
```

In addition, here is a reference page that uses the `jupyter-sphinx` package to create
outputs, to compare how these outputs look relative to the MyST-NB style.

```{toctree}
examples/index.md
```

Finally, here is documentation on contributing to the development of MySt-NB

```{toctree}
develop/index.md
```

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

# Contribute to MyST-NB

This section covers documentation relevant to developing and maintaining the MyST-NB
codebase, and some guidelines for how you can contribute.

## Installation

To install `MyST-NB` for package development:

```bash
git clone https://github.com/executablebooks/MyST-NB
cd MyST-NB
git checkout master
pip install -e .[code_style,testing,rtd]
```

See below for the contributing guidelines, practices, and code structure.

```{toctree}
contributing
```

## How the Jupyter Notebook parser works

MyST-NB is built on top of the MyST markdown parser. This is a flavor of markdown
designed to work with the Sphinx ecosystem. It is a combination of CommonMark markdown,
with a few extra syntax pieces added for use in Sphinx (for example, roles and
directives).

MyST-NB will do the following:

* Check for any pages in your documentation folder that end in `.ipynb`. For each one:
* Loop through the notebook's cells, converting cell contents into the Sphinx AST.
  * If it finds executable code cells, include their outputs in-line with the code.
  * If it finds markdown cells, use the MyST parser to convert them into Sphinx.

Eventually, it will also provide support for writing pure-markdown versions of notebooks
that can be executed and read into Sphinx.

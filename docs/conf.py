# Configuration file for the Sphinx documentation builder.
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os

# -- Project information -----------------------------------------------------

project = "MyST-NB"
copyright = "2022, Executable Book Project"
author = "Executable Book Project"

master_doc = "index"

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "myst_nb",
    "sphinx_togglebutton",
    "sphinx_copybutton",
    "sphinx.ext.intersphinx",
    "sphinx.ext.autodoc",
    "sphinx.ext.viewcode",
]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store", "**.ipynb_checkpoints"]

myst_enable_extensions = [
    "amsmath",
    "colon_fence",
    "deflist",
    "dollarmath",
    "html_image",
]

nb_custom_formats = {".Rmd": ["jupytext.reads", {"fmt": "Rmd"}]}
nb_execution_mode = "cache"
nb_execution_show_tb = "READTHEDOCS" in os.environ
nb_execution_timeout = 60  # Note: 30 was timing out on RTD

intersphinx_mapping = {
    "python": ("https://docs.python.org/3.8", None),
    "jb": ("https://jupyterbook.org/", None),
    "myst": ("https://myst-parser.readthedocs.io/en/latest/", None),
    "markdown_it": ("https://markdown-it-py.readthedocs.io/en/latest", None),
    "nbclient": ("https://nbclient.readthedocs.io/en/latest", None),
    "nbformat": ("https://nbformat.readthedocs.io/en/latest", None),
    "sphinx": ("https://www.sphinx-doc.org/en/master", None),
}
intersphinx_cache_limit = 5

nitpick_ignore = [
    ("py:class", "docutils.nodes.document"),
    ("py:class", "docutils.nodes.Node"),
    ("py:class", "docutils.nodes.container"),
    ("py:class", "docutils.nodes.system_message"),
    ("py:class", "nbformat.notebooknode.NotebookNode"),
    ("py:class", "pygments.lexer.RegexLexer"),
]

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_title = ""
html_theme = "sphinx_book_theme"
html_logo = "_static/logo-wide.svg"
html_favicon = "_static/logo-square.svg"
html_theme_options = {
    "github_url": "https://github.com/executablebooks/myst-nb",
    "repository_url": "https://github.com/executablebooks/myst-nb",
    "repository_branch": "master",
    "use_edit_page_button": True,
    "path_to_docs": "docs/",
    "show_navbar_depth": 2,
}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]

copybutton_selector = "div:not(.output) > div.highlight pre"

panels_add_bootstrap_css = False


def setup(_):
    import subprocess

    # this is required to register the coconut kernel with Jupyter,
    # to execute docs/examples/coconut-lang.md
    subprocess.check_call(["coconut", "--jupyter"])

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
    "sphinx_copybutton",
    "sphinx_book_theme",
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
# nb_render_image_options = {"width": "200px"}
# application/vnd.plotly.v1+json and application/vnd.bokehjs_load.v0+json
suppress_warnings = ["mystnb.unknown_mime_type"]

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

# ignore these type annotations
nitpick_ignore = [
    ("py:class", klass)
    for klass in [
        "attr._make.Attribute",
        "docutils.nodes.document",
        "docutils.nodes.Node",
        "docutils.nodes.Element",
        "docutils.nodes.container",
        "docutils.nodes.system_message",
        "DocutilsNbRenderer",
        "myst_parser.main.MdParserConfig",
        "nbformat.notebooknode.NotebookNode",
        "pygments.lexer.RegexLexer",
        # Literal values are not supported
        "typing_extensions.Literal",
        "typing_extensions.Literal[show, remove, remove - warn, warn, error, severe]",
        "off",
        "force",
        "auto",
        "cache",
        "commonmark",
        "gfm",
        "myst",
    ]
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
    "path_to_docs": "docs",
    "show_navbar_depth": 2,
    "use_edit_page_button": True,
    "use_repository_button": True,
    "use_download_button": True,
    "launch_buttons": {
        "binderhub_url": "https://mybinder.org",
        "notebook_interface": "classic",
    },
}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]

copybutton_selector = "div:not(.output) > div.highlight pre"

panels_add_bootstrap_css = False


def setup(app):
    """Add functions to the Sphinx setup."""
    import subprocess
    from typing import cast

    from docutils import nodes
    from docutils.parsers.rst import directives
    from sphinx.application import Sphinx
    from sphinx.util.docutils import SphinxDirective

    app = cast(Sphinx, app)

    # this is required to register the coconut kernel with Jupyter,
    # to execute docs/examples/coconut-lang.md
    subprocess.check_call(["coconut", "--jupyter"])

    class MystNbConfigDirective(SphinxDirective):
        """Directive to automate printing of the configuration."""

        option_spec = {"sphinx": directives.flag}

        def run(self):
            """Run the directive."""
            from myst_nb.configuration import NbParserConfig

            config = NbParserConfig()
            text = [
                "```````{list-table}",
                ":header-rows: 1",
                "",
                "* - Name",
                "  - Type",
                "  - Default",
                "  - Description",
            ]
            for name, value, field in config.as_triple():
                if "sphinx" in self.options and field.metadata.get("sphinx_exclude"):
                    continue
                description = " ".join(field.metadata.get("help", "").splitlines())
                default = " ".join(f"{value!r}".splitlines())
                if len(default) > 20:
                    default = default[:20] + "..."
                ctype = " ".join(str(field.type).splitlines())
                ctype = ctype.replace("typing.", "")
                ctype = ctype.replace("typing_extensions.", "")
                for tname in ("str", "int", "float", "bool"):
                    ctype = ctype.replace(f"<class '{tname}'>", tname)
                text.extend(
                    [
                        f"* - `{name}`",
                        f"  - `{ctype}`",
                        f"  - `{default}`",
                        f"  - {description}",
                    ]
                )
            text.append("```````")
            node = nodes.Element()
            self.state.nested_parse(text, 0, node)
            return node.children

    app.add_directive("mystnb-config", MystNbConfigDirective)

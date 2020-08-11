__version__ = "0.8.5"

from pathlib import Path

from docutils import nodes
from sphinx.application import Sphinx
from sphinx.util.docutils import SphinxDirective
from sphinx.util import logging

from myst_parser.myst_refs import MystReferenceResolver

from jupyter_sphinx.ast import (  # noqa: F401
    JupyterWidgetStateNode,
    JupyterWidgetViewNode,
    JupyterCell,
)

from .cache import execution_cache
from .parser import (
    NotebookParser,
    CellNode,
    CellInputNode,
    CellOutputNode,
    CellOutputBundleNode,
)
from .transform import CellOutputsToNodes
from .nb_glue import glue  # noqa: F401

from .nb_glue.domain import (
    NbGlueDomain,
    PasteMathNode,
    PasteNode,
    PasteTextNode,
    PasteInlineNode,
)
from .nb_glue.transform import PasteNodesToDocutils

LOGGER = logging.getLogger(__name__)


def static_path(app):
    static_path = Path(__file__).absolute().with_name("_static")
    app.config.html_static_path.append(str(static_path))


def set_valid_execution_paths(app):
    """Set files excluded from execution, and valid file suffixes

    Patterns given in execution_excludepatterns conf variable from executing.
    """
    app.env.excluded_nb_exec_paths = {
        str(path)
        for pat in app.config["execution_excludepatterns"]
        for path in Path().cwd().rglob(pat)
    }
    LOGGER.verbose("MyST-NB: Excluded Paths: %s", app.env.excluded_nb_exec_paths)
    app.env.allowed_nb_exec_suffixes = {
        suffix
        for suffix, parser_type in app.config["source_suffix"].items()
        if parser_type in ("myst-nb",)
    }


def add_exclude_patterns(app, config):
    """Add default exclude patterns (if not already present)."""
    if "**.ipynb_checkpoints" not in config.exclude_patterns:
        config.exclude_patterns.append("**.ipynb_checkpoints")


def update_togglebutton_classes(app, config):
    to_add = [
        ".tag_hide_input div.cell_input",
        ".tag_hide-input div.cell_input",
        ".tag_hide_output div.cell_output",
        ".tag_hide-output div.cell_output",
        ".tag_hide_cell.cell",
        ".tag_hide-cell.cell",
    ]
    for selector in to_add:
        config.togglebutton_selector += f", {selector}"


def save_glue_cache(app, env):
    NbGlueDomain.from_env(env).write_cache()


class CodeCell(SphinxDirective):
    """Raises a warning if it is triggered, it should not make it to the doctree."""

    optional_arguments = 1
    final_argument_whitespace = True
    has_content = True

    def run(self):
        LOGGER.warning(
            (
                "Found a `code-cell` directive. To execute the `code-cell`, you must "
                "add Jupytext header content to the page. See "
                "https://myst-nb.readthedocs.io/en/latest/use/markdown.html "
                "for more information."
            ),
            location=(self.env.docname, self.lineno),
        )
        return []


def setup(app: Sphinx):
    """Initialize Sphinx extension."""
    # Allow parsing ipynb files
    app.add_source_suffix(".md", "myst-nb")
    app.add_source_suffix(".ipynb", "myst-nb")
    app.add_source_parser(NotebookParser)
    app.setup_extension("sphinx_togglebutton")

    # Helper functions for the registry, pulled from jupyter-sphinx
    def skip(self, node):
        raise nodes.SkipNode

    # Used to render an element node as HTML
    def visit_element_html(self, node):
        self.body.append(node.html())
        raise nodes.SkipNode

    # Shortcut for registering our container nodes
    render_container = (
        lambda self, node: self.visit_container(node),
        lambda self, node: self.depart_container(node),
    )

    # Register our container nodes, these should behave just like a regular container
    for node in [CellNode, CellInputNode, CellOutputNode]:
        app.add_node(
            node,
            override=True,
            html=(render_container),
            latex=(render_container),
            textinfo=(render_container),
            text=(render_container),
            man=(render_container),
        )

    # Register the output bundle node.
    # No translators should touch this node because we'll replace it in a post-transform
    app.add_node(
        CellOutputBundleNode,
        override=True,
        html=(skip, None),
        latex=(skip, None),
        textinfo=(skip, None),
        text=(skip, None),
        man=(skip, None),
    )

    # Register our inline nodes so they can be parsed as a part of titles
    # No translators should touch these nodes because we'll replace them in a transform
    for node in [PasteMathNode, PasteNode, PasteTextNode, PasteInlineNode]:
        app.add_node(
            node,
            override=True,
            html=(skip, None),
            latex=(skip, None),
            textinfo=(skip, None),
            text=(skip, None),
            man=(skip, None),
        )

    # Add configuration for the cache
    app.add_config_value("jupyter_cache", "", "env")
    app.add_config_value("execution_excludepatterns", [], "env")
    app.add_config_value("jupyter_execute_notebooks", "auto", "env")
    app.add_config_value("execution_timeout", 30, "env")
    # show traceback in stdout (in addition to writing to file)
    # this is useful in e.g. RTD where one cannot inspect a file
    app.add_config_value("execution_show_tb", False, "")

    # Register our post-transform which will convert output bundles to nodes
    app.add_post_transform(PasteNodesToDocutils)
    app.add_post_transform(CellOutputsToNodes)

    # Myst transforms
    app.add_post_transform(MystReferenceResolver)

    # Events
    app.connect("builder-inited", static_path)
    app.connect("builder-inited", set_valid_execution_paths)
    app.connect("env-get-outdated", execution_cache)
    app.connect("config-inited", add_exclude_patterns)
    app.connect("config-inited", update_togglebutton_classes)
    app.connect("env-updated", save_glue_cache)

    # Misc
    app.add_css_file("mystnb.css")
    app.add_js_file("mystnb.js")
    app.setup_extension("jupyter_sphinx")
    app.add_domain(NbGlueDomain)
    app.add_directive("code-cell", CodeCell)

    # TODO need to deal with key clashes in NbGlueDomain.merge_domaindata
    # before this is parallel_read_safe
    return {"version": __version__, "parallel_read_safe": False}

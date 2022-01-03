"""An extension for sphinx"""
import logging
from pathlib import Path
from typing import Any, Dict

from docutils import nodes
from myst_parser import setup_sphinx as setup_myst_parser
from myst_parser.main import MdParserConfig, create_md_parser
from myst_parser.sphinx_parser import MystParser
from sphinx.application import Sphinx
from sphinx.util import logging as sphinx_logging

from myst_nb import __version__
from myst_nb.configuration import NbParserConfig
from myst_nb.docutils_ import DocutilsNbRenderer
from myst_nb.new.execute import update_notebook
from myst_nb.new.parse import notebook_to_tokens
from myst_nb.new.read import create_nb_reader


def setup(app):
    return sphinx_setup(app)


def sphinx_setup(app: Sphinx):
    """Initialize Sphinx extension."""
    # TODO perhaps there should be a way to turn this off,
    # app.add_source_suffix(".md", "myst-nb")
    app.add_source_suffix(".ipynb", "myst-nb")
    app.add_source_parser(MystNbParser)

    # Add myst-parser transforms and configuration
    setup_myst_parser(app)

    for name, default, field in NbParserConfig().as_triple():
        if not field.metadata.get("docutils_only", False):
            # TODO add types?
            app.add_config_value(f"nb_{name}", default, "env")
            # TODO add deprecated names

    # generate notebook configuration from Sphinx configuration
    app.connect("builder-inited", create_mystnb_config)

    # ensure notebook checkpoints are excluded
    app.connect("config-inited", add_exclude_patterns)
    # add HTML resources
    app.connect("builder-inited", add_static_path)
    app.add_css_file("mystnb.css")

    # TODO do we need to add lexers, if they are anyhow added via entry-points?

    return {"version": __version__, "parallel_read_safe": True}


def create_mystnb_config(app):
    """Generate notebook configuration from Sphinx configuration"""

    # Ignore type checkers because the attribute is dynamically assigned
    from sphinx.util.console import bold  # type: ignore[attr-defined]

    logger = sphinx_logging.getLogger(__name__)

    # TODO deal with deprecated names
    values = {
        name: app.config[f"nb_{name}"]
        for name, _, field in NbParserConfig().as_triple()
        if not field.metadata.get("docutils_only", False)
    }

    try:
        app.env.mystnb_config = NbParserConfig(**values)
        logger.info(bold("myst-nb v%s:") + " %s", __version__, app.env.mystnb_config)
    except (TypeError, ValueError) as error:
        logger.error("myst-nb configuration invalid: %s", error.args[0])
        app.env.mystnb_config = NbParserConfig()


def add_exclude_patterns(app: Sphinx, config):
    """Add default exclude patterns (if not already present)."""
    if "**.ipynb_checkpoints" not in config.exclude_patterns:
        config.exclude_patterns.append("**.ipynb_checkpoints")


def add_static_path(app: Sphinx):
    """Add static path for myst-nb."""
    static_path = Path(__file__).absolute().with_name("_static")
    app.config.html_static_path.append(str(static_path))


class MystNbParser(MystParser):
    """Sphinx parser for Jupyter Notebook formats, containing MyST Markdown."""

    supported = ("myst-nb",)
    translate_section_name = None

    config_section = "myst-nb parser"
    config_section_dependencies = ("parsers",)

    @staticmethod
    def get_logger(document: nodes.document) -> logging.Logger:
        """Get or create a logger for a docutils document."""
        # TODO load with document
        return sphinx_logging.getLogger(__name__)

    def parse(self, inputstring: str, document: nodes.document) -> None:
        """Parse source text.

        :param inputstring: The source string to parse
        :param document: The root docutils node to add AST elements to
        """
        # create a logger for this document
        logger = self.get_logger(document)

        # get markdown parsing configuration
        md_config: MdParserConfig = document.settings.env.myst_config
        # get notebook rendering configuration
        nb_config: NbParserConfig = document.settings.env.mystnb_config

        # convert inputstring to notebook
        nb_reader, md_config = create_nb_reader(
            inputstring, document["source"], md_config, nb_config
        )
        notebook = nb_reader(inputstring)

        # TODO update nb_config from notebook metadata

        # potentially execute notebook and/or populate outputs from cache
        notebook, exec_data = update_notebook(
            notebook, document["source"], nb_config, logger
        )
        if exec_data:
            document["nb_exec_data"] = exec_data
        # TODO store/print error traceback?

        # TODO write executed notebook to output folder
        # always for sphinx, but maybe docutils option on whether to do this?
        # only on successful parse?

        # Setup parser
        mdit_parser = create_md_parser(md_config, DocutilsNbRenderer)
        mdit_parser.options["document"] = document
        mdit_parser.options["notebook"] = notebook
        mdit_parser.options["nb_config"] = nb_config.as_dict()
        mdit_env: Dict[str, Any] = {}
        # parse to tokens
        mdit_tokens = notebook_to_tokens(notebook, mdit_parser, mdit_env)
        # convert to docutils AST, which is added to the document
        mdit_parser.renderer.render(mdit_tokens, mdit_parser.options, mdit_env)

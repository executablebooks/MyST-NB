from docutils import nodes
import nbformat as nbf
from pathlib import Path
from sphinx.util import logging

from myst_parser.docutils_renderer import SphinxRenderer, dict_to_docinfo
from myst_parser.block_tokens import Document
from myst_parser.sphinx_parser import MystParser
from jupyter_sphinx.ast import get_widgets, JupyterWidgetStateNode
from jupyter_sphinx.execute import contains_widgets
from myst_nb.cache import add_notebook_outputs

logger = logging.getLogger(__name__)


class NotebookParser(MystParser):
    """Docutils parser for IPynb + CommonMark + Math + Tables + RST Extensions """

    supported = ("ipynb",)
    translate_section_name = None

    default_config = {"known_url_schemes": None}

    config_section = "ipynb parser"
    config_section_dependencies = ("parsers",)

    def parse(self, inputstring, document):
        self.reporter = document.reporter
        self.config = self.default_config.copy()
        try:
            source_path = document.settings.env.doc2path(document.settings.env.docname)
            new_cfg = document.settings.env.config.myst_config
            self.config.update(new_cfg)
        except AttributeError:
            pass

        ntbk = nbf.reads(inputstring, nbf.NO_CONVERT)

        # Populate the outputs either with nbclient or a cache
        path_cache = document.settings.env.config['jupyter_cache']
        if path_cache is True:
            path_cache = Path(document.settings.env.srcdir).joinpath('.jupyter_cache')

        # If outputs are in the notebook, assume we just use those outputs
        do_run = document.settings.env.config['jupyter_notebook_force_run']
        has_outputs = all(len(cell.outputs) == 0 for cell in ntbk.cells if cell['cell_type'] == "code")
        if do_run or not has_outputs:
            ntbk = add_notebook_outputs(source_path, ntbk, path_cache)
        else:
            logger.error(f"Did not run notebook with pre-populated outputs: {source_path}")

        # Parse notebook-level metadata as front-matter
        # For now, only keep key/val pairs that point to int/float/string
        metadata = ntbk.metadata
        docinfo = dict_to_docinfo(metadata)
        document += docinfo

        # If there are widgets, this will embed the state of all widgets in a script
        if contains_widgets(ntbk):
            document.append(JupyterWidgetStateNode(state=get_widgets(ntbk)))
        renderer = SphinxRenderer(document=document, current_node=None)
        with renderer:
            # Loop through cells and render them
            for ii, cell in enumerate(ntbk.cells):
                # Skip empty cells
                if len(cell["source"]) == 0:
                    continue
                try:
                    _render_cell(cell, renderer)
                except Exception as exc:
                    source = cell["source"][:50]
                    if len(cell["source"]) > 50:
                        source = source + "..."
                    msg_node = self.reporter.error(
                        (
                            f"\nError parsing notebook cell #{ii+1}: {exc}\n"
                            f"Type: {cell['cell_type']}\n"
                            f"Source:\n{source}\n\n"
                        )
                    )
                    msg_node += nodes.literal_block(cell["source"], cell["source"])
                    renderer.current_node += [msg_node]
                    continue


def _render_cell(cell, renderer):
    """Render a cell with a SphinxRenderer instance.

    Returns nothing because the renderer updates itself.
    """
    tags = cell.metadata.get("tags", [])
    if "remove_cell" in tags:
        return

    # If a markdown cell, simply call the Myst parser and append children
    if cell["cell_type"] == "markdown":
        document = Document.read(cell["source"], front_matter=False)
        # Check for tag-specific behavior because markdown isn't wrapped in a cell
        if "hide_input" in tags:
            container = nodes.container()
            container["classes"].extend(["toggle"])
            with renderer.current_node_context(container, append=True):
                renderer.render(document)
        else:
            renderer.render(document)

    # If a code cell, convert the code + outputs
    elif cell["cell_type"] == "code":
        # Cell container will wrap whatever is in the cell
        classes = ["cell"]
        for tag in tags:
            classes.append(f"tag_{tag}")
        sphinx_cell = CellNode(classes=classes, cell_type=cell["cell_type"])
        renderer.current_node += sphinx_cell
        if "remove_input" not in tags:
            cell_input = CellInputNode(classes=["cell_input"])
            sphinx_cell += cell_input

            # Input block
            code_block = nodes.literal_block(text=cell["source"])
            cell_input += code_block

        # ==================
        # Cell output
        # ==================
        if "remove_output" not in tags:
            cell_output = CellOutputNode(classes=["cell_output"])
            sphinx_cell += cell_output

            outputs = CellOutputBundleNode(cell["outputs"])
            cell_output += outputs


class CellNode(nodes.container):
    """Represent a cell in the Sphinx AST."""

    def __init__(self, rawsource="", *children, **attributes):
        super().__init__("", **attributes)


class CellInputNode(nodes.container):
    """Represent an input cell in the Sphinx AST."""

    def __init__(self, rawsource="", *children, **attributes):
        super().__init__("", **attributes)


class CellOutputNode(nodes.container):
    """Represent an output cell in the Sphinx AST."""

    def __init__(self, rawsource="", *children, **attributes):
        super().__init__("", **attributes)


class CellOutputBundleNode(nodes.container):
    """Represent a MimeBundle in the Sphinx AST, to be transformed later."""

    def __init__(self, outputs, rawsource="", *children, **attributes):
        self.outputs = outputs
        super().__init__("", **attributes)


class CellImageNode(nodes.image):
    """An inline image that will output to an inline HTML image."""

    def __init__(self, rawsource="", *children, **attributes):
        super().__init__("", **attributes)

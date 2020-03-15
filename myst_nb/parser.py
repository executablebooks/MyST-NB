from docutils import nodes
import nbformat as nbf
from pathlib import Path
from sphinx.util import logging

from myst_parser.docutils_renderer import SphinxRenderer
from myst_parser.sphinx_parser import MystParser

from mistletoe.base_elements import BlockToken, Position, SourceLines
from mistletoe.parse_context import ParseContext, get_parse_context, set_parse_context
from mistletoe.block_tokenizer import tokenize_block
from mistletoe.block_tokens import Document, FrontMatter

from jupyter_sphinx.ast import get_widgets, JupyterWidgetStateNode
from jupyter_sphinx.execute import contains_widgets, write_notebook_output

from myst_nb.nb_glue import GLUE_PREFIX
from myst_nb.nb_glue.domain import NbGlueDomain


SPHINX_LOGGER = logging.getLogger(__name__)


class NotebookParser(MystParser):
    """Docutils parser for IPynb + CommonMark + Math + Tables + RST Extensions """

    supported = ("ipynb",)
    translate_section_name = None

    default_config = {"known_url_schemes": None}

    config_section = "ipynb parser"
    config_section_dependencies = ("parsers",)

    def parse(self, inputstring, document):

        # de-serialize the notebook
        ntbk = nbf.reads(inputstring, nbf.NO_CONVERT)

        # This is a contaner for top level markdown tokens
        # which we will add to as we walk the document
        mkdown_tokens = []  # type: list[BlockToken]

        # First we ensure that we are using a 'clean' global context
        # for parsing, which is setup with the MyST parsing tokens
        # the logger will report on duplicate link/footnote definitions, etc
        parse_context = ParseContext(
            find_blocks=SphinxNBRenderer.default_block_tokens,
            find_spans=SphinxNBRenderer.default_span_tokens,
            logger=SPHINX_LOGGER,
        )
        set_parse_context(parse_context)

        for cell_index, nb_cell in enumerate(ntbk.cells):

            # Skip empty cells
            if len(nb_cell["source"].strip()) == 0:
                continue

            # skip cells tagged for removal
            tags = nb_cell.metadata.get("tags", [])
            if "remove_cell" in tags:
                continue

            if nb_cell["cell_type"] == "markdown":

                # we add the document path and cell index
                # to the source lines, so they can be included in the error logging
                # NOTE: currently the logic to report metadata is not written
                # into SphinxRenderer, but this will be introduced in a later update
                lines = SourceLines(
                    nb_cell["source"],
                    uri=document["source"],
                    metadata={"cell_index": cell_index},
                    standardize_ends=True,
                )

                # parse the source markdown text;
                # at this point span/inline level tokens are not yet processed, but
                # link/footnote definitions are collected/stored in the global context
                mkdown_tokens.extend(tokenize_block(lines))

                # TODO for md cells, think of a way to implement the previous
                # `if "hide_input" in tags:` logic

            elif nb_cell["cell_type"] == "code":
                # here we do nothing but store the cell as a custom token
                mkdown_tokens.append(
                    NbCodeCell(
                        cell=nb_cell,
                        position=Position(
                            line_start=0,
                            uri=document["source"],
                            data={"cell_index": cell_index},
                        ),
                    )
                )

        # Now all definitions have been gathered, we walk the tokens and
        # process any inline text
        for token in mkdown_tokens + list(
            get_parse_context().foot_definitions.values()
        ):
            token.expand_spans()

        # If there are widgets, this will embed the state of all widgets in a script
        if contains_widgets(ntbk):
            mkdown_tokens.insert(0, JupyterWidgetState(state=get_widgets(ntbk)))

        # create the front matter token
        front_matter = FrontMatter(content=ntbk.metadata, position=None)

        # Finally, we create the top-level markdown document
        markdown_doc = Document(
            children=mkdown_tokens,
            front_matter=front_matter,
            link_definitions=parse_context.link_definitions,
            footnotes=parse_context.foot_definitions,
            footref_order=parse_context.foot_references,
        )

        self.reporter = document.reporter
        self.config = self.default_config.copy()
        try:
            new_cfg = document.settings.env.config.myst_config
            self.config.update(new_cfg)
        except AttributeError:
            pass

        # Remove all the mime prefixes from "glue" step.
        # This way, writing properly captures the glued images
        replace_mime = []
        for cell in ntbk.cells:
            if hasattr(cell, "outputs"):
                for out in cell.outputs:
                    if "data" in out:
                        # Only do the mimebundle replacing for the scrapbook outputs
                        mime_prefix = (
                            out.get("metadata", {})
                            .get("scrapbook", {})
                            .get("mime_prefix")
                        )
                        if mime_prefix:
                            out["data"] = {
                                key.replace(mime_prefix, ""): val
                                for key, val in out["data"].items()
                            }
                            replace_mime.append(out)

        # Write the notebook's output to disk. This changes metadata in notebook cells
        path_doc = Path(document.settings.env.docname)
        doc_relpath = path_doc.parent
        doc_filename = path_doc.name
        build_dir = Path(document.settings.env.app.outdir).parent
        output_dir = build_dir.joinpath("jupyter_execute", doc_relpath)
        write_notebook_output(ntbk, str(output_dir), doc_filename)

        # Now add back the mime prefixes to the right outputs so they aren't rendered
        # until called from the role/directive
        for out in replace_mime:
            out["data"] = {
                f"{GLUE_PREFIX}{key}": val for key, val in out["data"].items()
            }

        # Update our glue key list with new ones defined in this page
        glue_domain = NbGlueDomain.from_env(document.settings.env)
        glue_domain.add_notebook(ntbk, path_doc)

        # render the Markdown AST to docutils AST
        renderer = SphinxNBRenderer(
            parse_context=parse_context, document=document, current_node=None
        )
        renderer.render(markdown_doc)


class JupyterWidgetState(BlockToken):
    def __init__(self, state):
        self.state = state


class NbCodeCell(BlockToken):
    def __init__(self, cell, position):
        self.cell = cell
        self.position = position


class SphinxNBRenderer(SphinxRenderer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.render_map["NbCodeCell"] = self.render_nb_code_cell
        self.render_map["JupyterWidgetState"] = self.render_jupyter_widget_state

    def render_jupyter_widget_state(self, token):
        self.document.append(JupyterWidgetStateNode(state=token.state))

    def render_nb_code_cell(self, token: NbCodeCell):
        """Render a Jupyter notebook cell."""
        cell = token.cell
        tags = cell.metadata.get("tags", [])

        # Cell container will wrap whatever is in the cell
        classes = ["cell"]
        for tag in tags:
            classes.append(f"tag_{tag}")
        sphinx_cell = CellNode(classes=classes, cell_type=cell["cell_type"])
        self.current_node += sphinx_cell
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

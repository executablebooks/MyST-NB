from docutils import nodes
import nbformat as nbf
from pathlib import Path
import yaml

from myst_parser.docutils_renderer import SphinxRenderer
from myst_parser.sphinx_parser import MystParser

from mistletoe.base_elements import SpanContainer, BlockToken
from mistletoe.parse_context import ParseContext, get_parse_context, set_parse_context
from mistletoe.block_tokenizer import tokenize_block
from mistletoe.block_tokens import Document, FrontMatter

from jupyter_sphinx.ast import get_widgets, JupyterWidgetStateNode
from jupyter_sphinx.execute import contains_widgets, write_notebook_output


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
        mkdown_tokens = []

        # first we ensure that we are using a 'clean' global context
        # for parsing, which is setup with the MyST parsing tokens
        parse_context = ParseContext(
            find_blocks=SphinxNBRenderer.default_block_tokens,
            find_spans=SphinxNBRenderer.default_span_tokens,
        )
        # TODO hook in the document.reporter here,
        # to e.g. report on duplicate link/footnote definitions
        set_parse_context(parse_context)

        for cell_index, nb_cell in enumerate(ntbk.cells):

            # Skip empty cells
            if len(nb_cell["source"]) == 0:
                continue

            # skip cells tagged for removal
            tags = nb_cell.metadata.get("tags", [])
            if "remove_cell" in tags:
                continue

            if nb_cell["cell_type"] == "markdown":
                lines = nb_cell["source"]

                # ensure all lines end with a new line
                # TODO this is going to be changed in mistletoe, to just be
                # lines = SourceLines(lines)
                if isinstance(lines, str):
                    lines = lines.splitlines(keepends=True)
                lines = [
                    line if line.endswith("\n") else "{}\n".format(line)
                    for line in lines
                ]

                # parse the source markdown text;
                # at this point span/inline level tokens are not yet processed, but
                # link/footnote definitions are collected/stored in the global context
                mkdown_tokens.extend(tokenize_block(lines))

                # TODO here it would be ideal to somehow include the cell index
                # in the `position` attribute of each token
                # and utilise in within the document.reporter

                # thinking about this now, I could make an upstream change to mistletoe
                # so that you could do:
                # >> lines = SourceLines(lines, metadata={"cell_index": cell_index})
                # >> mkdown_tokens.extend(tokenize_block(lines))
                # then the metadata would propogate to the `position`
                # attribute of the token

                # TODO think of a way to implement the previous
                # `if "hide_input" in tags:` logic

            elif nb_cell["cell_type"] == "code":
                # here we do nothing but store the cell as a custom token
                # TODO here index would instead be part of the position attribute
                mkdown_tokens.append(NbCodeCell(cell=nb_cell, index=cell_index))

        # Now all definitions have been gathered, we walk the tokens and
        # process any inline text
        # TODO maybe make this a small function in mistletoe/myst_parser
        for token in mkdown_tokens + list(
            get_parse_context().foot_definitions.values()
        ):
            for result in list(token.walk(include_self=True)):
                if isinstance(result.node.children, SpanContainer):
                    result.node.children = result.node.children.expand()

        # create the front matter token
        # TODO at present the front matter must be stored in its serialized form
        # but ideally we would also allow it to be a dict,
        # so we don't have this redundant round-trip conversion
        yaml.add_representer(
            nbf.NotebookNode,
            lambda d, node: d.represent_dict(dict(node)),
            yaml.SafeDumper,
        )
        front_matter = FrontMatter(content=yaml.safe_dump(ntbk.metadata), position=None)

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

        # Write the notebook's output to disk
        path_doc = Path(document.settings.env.docname)
        doc_relpath = path_doc.parent
        doc_filename = path_doc.name
        build_dir = Path(document.settings.env.app.outdir).parent
        output_dir = build_dir.joinpath("jupyter_execute", doc_relpath)
        write_notebook_output(ntbk, str(output_dir), doc_filename)

        # If there are widgets, this will embed the state of all widgets in a script
        if contains_widgets(ntbk):
            document.append(JupyterWidgetStateNode(state=get_widgets(ntbk)))

        # render the Markdown AST to docutils AST
        renderer = SphinxNBRenderer(
            parse_context=parse_context, document=document, current_node=None
        )
        renderer.render(markdown_doc)


class NbCodeCell(BlockToken):
    def __init__(self, cell, index):
        self.cell = cell
        self.index = index


class SphinxNBRenderer(SphinxRenderer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.render_map["NbCodeCell"] = self.render_nb_code_cell

    def render_nb_code_cell(self, token):
        """Render a cell with a SphinxRenderer instance.

        Returns nothing because the renderer updates itself.
        """
        cell = token.cell
        # index = token.index
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

import json
from pathlib import Path

from docutils import nodes
import nbformat as nbf
from sphinx.util import logging

from jupyter_sphinx.ast import get_widgets, JupyterWidgetStateNode
from jupyter_sphinx.execute import contains_widgets, write_notebook_output

from markdown_it.token import Token
from markdown_it.rules_core import StateCore
from markdown_it.utils import AttrDict

from myst_parser.main import default_parser
from myst_parser.sphinx_renderer import SphinxRenderer
from myst_parser.sphinx_parser import MystParser

from myst_nb.nb_glue import GLUE_PREFIX
from myst_nb.nb_glue.domain import NbGlueDomain

from myst_nb.cache import add_notebook_outputs


SPHINX_LOGGER = logging.getLogger(__name__)


class NotebookParser(MystParser):
    """Docutils parser for IPynb + CommonMark + Math + Tables + RST Extensions """

    supported = ("ipynb",)
    translate_section_name = None

    default_config = {"known_url_schemes": None}

    config_section = "ipynb parser"
    config_section_dependencies = ("parsers",)

    def parse(self, inputstring, document, source_path=None):

        # de-serialize the notebook
        ntbk = nbf.reads(inputstring, nbf.NO_CONVERT)
        self.reporter = document.reporter
        self.config = self.default_config.copy()

        try:
            new_cfg = document.settings.env.config.myst_config
            self.config.update(new_cfg)
        except AttributeError:
            pass
        # add outputs to notebook from the cache
        if document.settings.env.config["jupyter_execute_notebooks"] != "off":
            ntbk = add_notebook_outputs(document.settings.env, ntbk, source_path)

        # parse the notebook content to a list of syntax tokens and an env
        # containing global data like reference definitions
        md, env, tokens = nb_to_tokens(ntbk)

        # Write the notebook's output to disk
        path_doc = nb_output_to_disc(ntbk, document)

        # Update our glue key list with new ones defined in this page
        glue_domain = NbGlueDomain.from_env(document.settings.env)
        glue_domain.add_notebook(ntbk, path_doc)

        # render the Markdown AST to docutils AST
        md.options["document"] = document
        md.renderer.render(tokens, md.options, env)


def nb_to_tokens(ntbk):
    # setup a markdown parser
    md = default_parser().disable("front_matter", ignoreInvalid=True)
    md.renderer = SphinxNBRenderer(md)
    # make a sandbox where all the parsing global data,
    # like reference definitions will be stored
    env = AttrDict()
    rules = md.core.ruler.get_active_rules()

    # First only run pre-inline chains
    # so we can collect all reference definitions, etc, before assessing references
    def parse_block(src, meta=None):
        with md.reset_rules():
            # enable only rules up to block
            md.core.ruler.enableOnly(rules[: rules.index("inline")])
            tokens = md.parse(src, env)
        for token in tokens:
            token.meta = token.meta or {}
            token.meta["doc"] = meta
        return tokens

    block_tokens = []

    for cell_index, nb_cell in enumerate(ntbk.cells):

        # Skip empty cells
        if len(nb_cell["source"].strip()) == 0:
            continue

        # skip cells tagged for removal
        # TODO this logic should be deferred to a transform
        tags = nb_cell.metadata.get("tags", [])
        if "remove_cell" in tags:
            continue

        if nb_cell["cell_type"] == "markdown":

            # we add the cell index to tokens,
            # so they can be included in the error logging,
            # although note this logic isn't currently implemented in SphinxRenderer
            block_tokens.extend(parse_block(nb_cell["source"], {"index": cell_index}))

        elif nb_cell["cell_type"] == "code":
            # here we do nothing but store the cell as a custom token
            block_tokens.append(
                Token(
                    "nb_code_cell", "", 0, meta={"index": cell_index, "cell": nb_cell}
                )
            )

    # Now all definitions have been gathered,
    # we run inline and post-inline chains, to expand the text
    # Note we assume here that these rules never require the actual source text,
    # only acting on the existing tokens
    state = StateCore(None, md, env, block_tokens)
    with md.reset_rules():
        md.core.ruler.enableOnly(rules[rules.index("inline") :])
        md.core.process(state)

    # Add the front matter.
    # Note that myst_parser now serialises dict/list like keys, when rendering to
    # docutils docinfo,
    # so to stay consistent with the previous code (for now) we strip this data
    state.tokens = [
        Token(
            "front_matter",
            "",
            0,
            content=json.dumps(
                {
                    k: v
                    for k, v in ntbk.metadata.items()
                    if isinstance(v, (str, int, float))
                }
            ),
        )
    ] + state.tokens

    # If there are widgets, this will embed the state of all widgets in a script
    if contains_widgets(ntbk):
        state.tokens = [
            Token("jupyter_widget_state", "", 0, meta={"state": get_widgets(ntbk)})
        ] + state.tokens

    return md, env, state.tokens


class SphinxNBRenderer(SphinxRenderer):
    """A markdown-it token renderer,
    which includes special methods for notebook cells.
    """

    def render_jupyter_widget_state(self, token: Token):
        node = JupyterWidgetStateNode(state=token.meta["state"])
        self.add_line_and_source_path(node, token)
        self.document.append(node)

    def render_nb_code_cell(self, token: Token):
        """Render a Jupyter notebook cell."""
        cell = token.meta["cell"]
        # TODO logic involving tags should be deferred to a transform
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


def nb_output_to_disc(ntbk, document):
    """Write the notebook's output to disk

    We remove all the mime prefixes from "glue" step.
    This way, writing properly captures the glued images
    """
    replace_mime = []
    for cell in ntbk.cells:
        if hasattr(cell, "outputs"):
            for out in cell.outputs:
                if "data" in out:
                    # Only do the mimebundle replacing for the scrapbook outputs
                    mime_prefix = (
                        out.get("metadata", {}).get("scrapbook", {}).get("mime_prefix")
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
        out["data"] = {f"{GLUE_PREFIX}{key}": val for key, val in out["data"].items()}

    return path_doc

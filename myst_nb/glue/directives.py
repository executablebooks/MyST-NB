"""Directives which can be used by both docutils and sphinx.

We intentionally do no import sphinx in this module,
in order to allow docutils-only use without sphinx installed.
"""
from typing import List, Optional, Tuple

from docutils import nodes
from docutils.parsers.rst import Directive, directives

from myst_nb.core.render import MimeData, strip_latex_delimiters

from .utils import (
    RetrievalError,
    is_sphinx,
    render_glue_output,
    retrieve_glue_data,
    set_source_info,
    warning,
)


def _shared_option_spec(spec: Optional[dict] = None) -> dict:
    """Return an option spec with shared options for all directives."""
    spec = spec or {}
    # spec.update({"doc": directives.unchanged})
    return spec


class _PasteDirectiveBase(Directive):

    required_arguments = 1  # the key
    final_argument_whitespace = True
    has_content = False

    option_spec = _shared_option_spec()

    @property
    def document(self) -> nodes.document:
        return self.state.document

    def get_source_info(self) -> Tuple[str, int]:
        """Get source and line number."""
        return self.state_machine.get_source_and_line(self.lineno)

    def set_source_info(self, node: nodes.Node) -> None:
        """Set source and line number to the node and its descendants."""
        source, line = self.get_source_info()
        set_source_info(node, source, line)


class PasteAnyDirective(_PasteDirectiveBase):
    """A directive for pasting code outputs from notebooks,
    using render priority to decide the output mime type.
    """

    def run(self) -> List[nodes.Node]:
        """Run the directive."""
        line, source = self.get_source_info()
        try:
            data = retrieve_glue_data(self.document, self.arguments[0])
        except RetrievalError as exc:
            return [warning(str(exc), self.document, self.lineno)]
        return render_glue_output(data, self.document, line, source)


class PasteMarkdownDirective(_PasteDirectiveBase):
    """A directive for pasting markdown outputs from notebooks as MyST Markdown."""

    def fmt(argument):
        return directives.choice(argument, ("commonmark", "gfm", "myst"))

    option_spec = _shared_option_spec(
        {
            "format": fmt,
        }
    )

    def run(self) -> List[nodes.Node]:
        """Run the directive."""
        key = self.arguments[0]
        try:
            result = retrieve_glue_data(self.document, key)
        except RetrievalError as exc:
            return [warning(str(exc), self.document, self.lineno)]
        if "text/markdown" not in result.data:
            return [
                warning(
                    f"No text/markdown found in {key!r} data",
                    self.document,
                    self.lineno,
                )
            ]

        # TODO this "override" feels a bit hacky
        cell_key = result.nb_renderer.renderer.nb_config.cell_render_key
        mime = MimeData(
            "text/markdown",
            result.data["text/markdown"],
            cell_metadata={
                cell_key: {"markdown_format": self.options.get("format", "commonmark")},
            },
            output_metadata=result.metadata,
            line=self.lineno,
            md_headings=True,
        )
        _nodes = result.nb_renderer.render_markdown(mime)
        for node in _nodes:
            self.set_source_info(node)
        return _nodes


class PasteFigureDirective(_PasteDirectiveBase):
    """A directive for pasting code outputs from notebooks, wrapped in a figure."""

    def align(argument):
        return directives.choice(argument, ("left", "center", "right"))

    def figwidth_value(argument):
        return directives.length_or_percentage_or_unitless(argument, "px")

    option_spec = _shared_option_spec(
        {
            "figwidth": figwidth_value,
            "figclass": directives.class_option,
            "align": align,
            "name": directives.unchanged,
        }
    )
    has_content = True

    def run(self):
        line, source = self.get_source_info()
        try:
            data = retrieve_glue_data(self.document, self.arguments[0])
        except RetrievalError as exc:
            return [warning(str(exc), self.document, self.lineno)]
        paste_nodes = render_glue_output(data, self.document, line, source)

        # note: most of this is copied directly from sphinx.Figure

        # create figure node
        figure_node = nodes.figure("", *paste_nodes)
        self.set_source_info(figure_node)

        # add attributes
        figwidth = self.options.pop("figwidth", None)
        figclasses = self.options.pop("figclass", None)
        align = self.options.pop("align", None)
        if figwidth is not None:
            figure_node["width"] = figwidth
        if figclasses:
            figure_node["classes"] += figclasses
        if align:
            figure_node["align"] = align

        # add target
        self.add_name(figure_node)

        # create the caption and legend
        if self.content:
            node = nodes.Element()  # anonymous container for parsing
            self.state.nested_parse(self.content, self.content_offset, node)
            first_node = node[0]
            if isinstance(first_node, nodes.paragraph):
                caption = nodes.caption(first_node.rawsource, "", *first_node.children)
                caption.source = first_node.source
                caption.line = first_node.line
                figure_node += caption
            elif not (isinstance(first_node, nodes.comment) and len(first_node) == 0):
                error = warning(
                    "Figure caption must be a paragraph or empty comment.",
                    self.document,
                    self.lineno,
                )
                return [figure_node, error]
            if len(node) > 1:
                figure_node += nodes.legend("", *node[1:])

        return [figure_node]


class PasteMathDirective(_PasteDirectiveBase):
    """A directive for pasting latex outputs from notebooks as math."""

    option_spec = _shared_option_spec(
        {
            "label": directives.unchanged,
            "name": directives.unchanged,
            "class": directives.class_option,
            "nowrap": directives.flag,
        }
    )

    def run(self) -> List[nodes.Node]:
        """Run the directive."""
        key = self.arguments[0]
        try:
            result = retrieve_glue_data(self.document, key)
        except RetrievalError as exc:
            return [warning(str(exc), self.document, self.lineno)]
        if "text/latex" not in result.data:
            return [
                warning(
                    f"No text/latex found in {key!r} data",
                    self.document,
                    self.lineno,
                )
            ]

        latex = strip_latex_delimiters(str(result.data["text/latex"]))
        label = self.options.get("label", self.options.get("name"))
        node = nodes.math_block(
            latex,
            latex,
            nowrap="nowrap" in self.options,
            label=label,
            number=None,
            classes=["pasted-math"] + (self.options.get("class") or []),
        )
        self.add_name(node)
        self.set_source_info(node)
        if is_sphinx(self.document):
            return self.add_target(node)
        return [node]

    def add_target(self, node: nodes.math_block) -> List[nodes.Node]:
        """Add target to the node."""
        # adapted from sphinx.directives.patches.MathDirective

        env = self.state.document.settings.env

        node["docname"] = env.docname

        # assign label automatically if math_number_all enabled
        if node["label"] == "" or (env.config.math_number_all and not node["label"]):
            seq = env.new_serialno("sphinx.ext.math#equations")
            node["label"] = "%s:%d" % (env.docname, seq)

        # no targets and numbers are needed
        if not node["label"]:
            return [node]

        # register label to domain
        domain = env.get_domain("math")
        domain.note_equation(env.docname, node["label"], location=node)
        node["number"] = domain.get_equation_number_for(node["label"])

        # add target node
        node_id = nodes.make_id("equation-%s" % node["label"])
        target = nodes.target("", "", ids=[node_id])
        self.document.note_explicit_target(target)

        return [target, node]

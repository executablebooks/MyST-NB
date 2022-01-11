"""Directives and roles which can be used by both docutils and sphinx.

We intentionally do no import sphinx in this module,
in order to allow docutils-only use without sphinx installed.
"""
from typing import Any, Dict, List, Optional, Tuple, Union

import attr
from docutils import nodes
from docutils.parsers.rst import Directive, directives
from docutils.parsers.rst.states import Inliner
from docutils.utils import unescape

from myst_nb.loggers import DocutilsDocLogger, SphinxDocLogger
from myst_nb.render import MimeData, NbElementRenderer, strip_latex_delimiters


def is_sphinx(document) -> bool:
    """Return True if we are in sphinx, otherwise docutils."""
    return hasattr(document.settings, "env")


def warning(message: str, document: nodes.document, line: int) -> nodes.system_message:
    """Create a warning."""
    if is_sphinx(document):
        logger = SphinxDocLogger(document)
    else:
        logger = DocutilsDocLogger(document)
    logger.warning(message, subtype="glue")
    return nodes.system_message(
        message,
        type="WARNING",
        level=2,
        line=line,
        source=document["source"],
    )


def set_source_info(node: nodes.Node, source: str, line: int) -> None:
    """Set the source info for a node and its descendants."""
    iterator = getattr(node, "findall", node.traverse)  # findall for docutils 0.18
    for _node in iterator(include_self=True):
        _node.source = source
        _node.line = line


@attr.s
class RetrievedData:
    """A class to store retrieved mime data."""

    found: bool = attr.ib()
    data: Union[None, str, bytes] = attr.ib(default=None)
    metadata: Dict[str, Any] = attr.ib(factory=dict)
    nb_renderer: Optional[NbElementRenderer] = attr.ib(default=None)
    warning: Optional[str] = attr.ib(default=None)


def retrieve_glue_data(document: nodes.document, key: str) -> RetrievedData:
    """Retrieve the glue data from a specific document."""
    if "nb_renderer" not in document:
        return RetrievedData(False, warning="No 'nb_renderer' found on the document.")
    nb_renderer: NbElementRenderer = document["nb_renderer"]
    resources = nb_renderer.get_resources()
    if "glue" not in resources:
        return RetrievedData(False, warning=f"No key {key!r} found in glue data.")

    if key not in resources["glue"]:
        return RetrievedData(False, warning=f"No key {key!r} found in glue data.")

    return RetrievedData(
        True,
        data=resources["glue"][key]["data"],
        metadata=resources["glue"][key].get("metadata", {}),
        nb_renderer=nb_renderer,
    )


def render_glue_output(
    key: str,
    document: nodes.document,
    line: int,
    source: str,
    inline=False,
) -> Tuple[bool, List[nodes.Node]]:
    """Retrive the notebook output data for this glue key,
    then return the docutils/sphinx nodes relevant to this data.

    :param key: The glue key to retrieve.
    :param document: The current docutils document.
    :param line: The current source line number of the directive or role.
    :param source: The current source path or description.
    :param inline: Whether to render the output as inline (or block).

    :returns: A tuple of (was the key found, the docutils/sphinx nodes).
    """
    data = retrieve_glue_data(document, key)
    if not data.found:
        return (False, [warning(data.warning, document, line)])
    if is_sphinx(document):
        _nodes = render_output_sphinx(
            data.nb_renderer, data.data, data.metadata, source, line, inline
        )
    else:
        _nodes = render_output_docutils(
            data.nb_renderer, data.data, data.metadata, document, line, inline
        )
    # TODO rendering should perhaps return if it succeeded explicitly
    if _nodes and isinstance(_nodes[0], nodes.system_message):
        return False, _nodes
    return True, _nodes


def render_output_docutils(
    nb_renderer: NbElementRenderer,
    data: Dict[str, Any],
    metadata: Dict[str, Any],
    document: nodes.document,
    line: int,
    inline=False,
) -> List[nodes.Node]:
    """Render the output in docutils (select mime priority directly)."""
    mime_priority = nb_renderer.renderer.nb_config.mime_priority
    try:
        mime_type = next(x for x in mime_priority if x in data)
    except StopIteration:
        return [
            warning(
                "No output mime type found from render_priority",
                document,
                line,
            )
        ]
    else:
        data = MimeData(
            mime_type,
            data[mime_type],
            output_metadata=metadata,
            line=line,
        )
        if inline:
            return nb_renderer.render_mime_type_inline(data)
        return nb_renderer.render_mime_type(data)


def render_output_sphinx(
    nb_renderer: NbElementRenderer,
    data: Dict[str, Any],
    metadata: Dict[str, Any],
    source: str,
    line: int,
    inline=False,
) -> List[nodes.Node]:
    """Render the output in sphinx (defer mime priority selection)."""
    mime_bundle = nodes.container(nb_element="mime_bundle")
    set_source_info(mime_bundle, source, line)
    for mime_type, data in data.items():
        mime_container = nodes.container(mime_type=mime_type)
        set_source_info(mime_container, source, line)
        data = MimeData(mime_type, data, output_metadata=metadata, line=line)
        if inline:
            nds = nb_renderer.render_mime_type_inline(data)
        else:
            nds = nb_renderer.render_mime_type(data)
        if nds:
            mime_container.extend(nds)
            mime_bundle.append(mime_container)
    return [mime_bundle]


class _PasteRoleBase:
    """A role for pasting inline code outputs from notebooks."""

    def get_source_info(self, lineno: int = None) -> Tuple[str, int]:
        """Get source and line number."""
        if lineno is None:
            lineno = self.lineno
        return self.inliner.reporter.get_source_and_line(lineno)  # type: ignore

    def set_source_info(self, node: nodes.Node, lineno: int = None) -> None:
        """Set the source info for a node and its descendants."""
        source, line = self.get_source_info(lineno)
        set_source_info(node, source, line)

    def __call__(
        self,
        name: str,
        rawtext: str,
        text: str,
        lineno: int,
        inliner: Inliner,
        options=None,
        content=(),
    ) -> Tuple[List[nodes.Node], List[nodes.system_message]]:
        self.text = unescape(text)
        self.lineno = lineno
        self.inliner = inliner
        self.rawtext = rawtext
        return self.run()

    def run(self) -> Tuple[List[nodes.Node], List[nodes.system_message]]:
        """Run the role."""
        raise NotImplementedError


class PasteRoleAny(_PasteRoleBase):
    """A role for pasting inline code outputs from notebooks,
    using render priority to decide the output mime type.
    """

    def run(self) -> Tuple[List[nodes.Node], List[nodes.system_message]]:
        line, source = self.get_source_info()
        found, paste_nodes = render_glue_output(
            self.text,
            self.inliner.document,
            line,
            source,
            inline=True,
        )
        if not found:
            return [], paste_nodes
        return paste_nodes, []


class PasteTextRole(_PasteRoleBase):
    """A role for pasting text outputs from notebooks."""

    def run(self) -> Tuple[List[nodes.Node], List[nodes.system_message]]:
        # check if we have both key:format in the key
        parts = self.text.rsplit(":", 1)
        if len(parts) == 2:
            key, formatting = parts
        else:
            key = parts[0]
            formatting = None

        # now retrieve the data
        document = self.inliner.document

        result = retrieve_glue_data(document, key)
        if not result.found:
            return [], [warning(result.warning, document, self.lineno)]
        if "text/plain" not in result.data:
            return [], [
                warning(f"No text/plain found in {key!r} data", document, self.lineno)
            ]

        text = str(result.data["text/plain"]).strip("'")

        # If formatting is specified, see if we have a number of some kind
        if formatting:
            try:
                newtext = float(text)
                text = f"{newtext:>{formatting}}"
            except ValueError:
                pass

        node = nodes.inline(text, text, classes=["pasted-text"])
        self.set_source_info(node)
        return [node], []


class PasteMarkdownRole(_PasteRoleBase):
    """A role for pasting markdown outputs from notebooks as inline MyST Markdown."""

    def run(self) -> Tuple[List[nodes.Node], List[nodes.system_message]]:
        # check if we have both key:format in the key
        parts = self.text.rsplit(":", 1)
        if len(parts) == 2:
            key, fmt = parts
        else:
            key = parts[0]
            fmt = "commonmark"
        # TODO - check fmt is valid
        # retrieve the data
        document = self.inliner.document

        result = retrieve_glue_data(document, key)
        if not result.found:
            return [], [warning(result.warning, document, self.lineno)]
        if "text/markdown" not in result.data:
            return [], [
                warning(
                    f"No text/markdown found in {key!r} data", document, self.lineno
                )
            ]

        # TODO this feels a bit hacky
        cell_key = result.nb_renderer.renderer.nb_config.cell_render_key
        mime = MimeData(
            "text/markdown",
            result.data["text/markdown"],
            cell_metadata={
                cell_key: {"markdown_format": fmt},
            },
            output_metadata=result.metadata,
            line=self.lineno,
        )
        _nodes = result.nb_renderer.render_markdown_inline(mime)
        for node in _nodes:
            self.set_source_info(node)
        return _nodes, []


class _PasteDirectiveBase(Directive):

    required_arguments = 1  # the key
    final_argument_whitespace = True
    has_content = False

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
        _, paste_nodes = render_glue_output(
            self.arguments[0], self.document, line, source
        )
        return paste_nodes


class PasteMarkdownDirective(_PasteDirectiveBase):
    """A directive for pasting markdown outputs from notebooks as MyST Markdown."""

    def fmt(argument):
        return directives.choice(argument, ("commonmark", "gfm", "myst"))

    option_spec = {
        "format": fmt,
    }

    def run(self) -> List[nodes.Node]:
        """Run the directive."""
        key = self.arguments[0]
        result = retrieve_glue_data(self.document, key)
        if not result.found:
            return [warning(result.warning, self.document, self.lineno)]
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

    option_spec = {
        "figwidth": figwidth_value,
        "figclass": directives.class_option,
        "align": align,
        "name": directives.unchanged,
    }
    has_content = True

    def run(self):
        line, source = self.get_source_info()
        found, paste_nodes = render_glue_output(
            self.arguments[0], self.document, line, source
        )
        if not found:
            return paste_nodes

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

    option_spec = {
        "label": directives.unchanged,
        "name": directives.unchanged,
        "class": directives.class_option,
        "nowrap": directives.flag,
    }

    def run(self) -> List[nodes.Node]:
        """Run the directive."""
        key = self.arguments[0]
        result = retrieve_glue_data(self.document, key)
        if not result.found:
            return [warning(result.warning, self.document, self.lineno)]
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

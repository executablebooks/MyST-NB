"""Directives and roles which can be used by both docutils and sphinx."""
from typing import Any, Dict, List, Tuple

from docutils import nodes
from docutils.parsers.rst import Directive, directives
from docutils.parsers.rst.states import Inliner
from docutils.utils import unescape

from myst_nb.loggers import DocutilsDocLogger, SphinxDocLogger
from myst_nb.render import MimeData, NbElementRenderer


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


def render_output_docutils(
    document, line, nb_renderer: NbElementRenderer, output: Dict[str, Any], inline=False
) -> List[nodes.Node]:
    """Render the output in docutils (select mime priority directly)."""
    mime_priority = nb_renderer.renderer.get_nb_config("mime_priority")
    try:
        mime_type = next(x for x in mime_priority if x in output["data"])
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
            output["data"][mime_type],
            output_metadata=output.get("metadata", {}),
            line=line,
        )
        if inline:
            return nb_renderer.render_mime_type_inline(data)
        return nb_renderer.render_mime_type(data)


def render_output_sphinx(
    document,
    line,
    nb_renderer: NbElementRenderer,
    output: Dict[str, Any],
    set_source_info,
    inline=False,
) -> List[nodes.Node]:
    """Render the output in sphinx (defer mime priority selection)."""
    mime_bundle = nodes.container(nb_element="mime_bundle")
    set_source_info(mime_bundle)
    for mime_type, data in output["data"].items():
        mime_container = nodes.container(mime_type=mime_type)
        set_source_info(mime_container)
        data = MimeData(
            mime_type, data, output_metadata=output.get("metadata", {}), line=line
        )
        if inline:
            nds = nb_renderer.render_mime_type_inline(data)
        else:
            nds = nb_renderer.render_mime_type(data)
        if nds:
            mime_container.extend(nds)
            mime_bundle.append(mime_container)
    return [mime_bundle]


def render_glue_output(
    key: str, document: nodes.document, line: int, set_source_info, inline=False
) -> List[nodes.Node]:
    if "nb_renderer" not in document:
        return [warning("No 'nb_renderer' found on the document.", document, line)]
    nb_renderer: NbElementRenderer = document["nb_renderer"]
    resources = nb_renderer.get_resources()
    if "glue" not in resources:
        return [
            warning("No glue data found in the notebook resources.", document, line)
        ]
    if key not in resources["glue"]:
        return [warning(f"No key {key!r} found in glue data.", document, line)]
    if not resources["glue"][key].get("data"):
        return [warning(f"{key!r} does not contain any data.", document, line)]
    if is_sphinx(document):
        return render_output_sphinx(
            document, line, nb_renderer, resources["glue"][key], set_source_info, inline
        )
    else:
        return render_output_docutils(
            document, line, nb_renderer, resources["glue"][key], inline
        )


class PasteRole:
    """A role for pasting inline code outputs from notebooks."""

    def get_source_info(self, lineno: int = None) -> Tuple[str, int]:
        if lineno is None:
            lineno = self.lineno
        return self.inliner.reporter.get_source_and_line(lineno)  # type: ignore

    def set_source_info(self, node: nodes.Node, lineno: int = None) -> None:
        node.source, node.line = self.get_source_info(lineno)

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
        paste_nodes = render_glue_output(
            self.text,
            self.inliner.document,
            self.lineno,
            self.set_source_info,
            inline=True,
        )
        if not paste_nodes and isinstance(paste_nodes[0], nodes.system_message):
            return [], paste_nodes
        return paste_nodes, []


class PasteTextRole(PasteRole):
    """A role for pasting text outputs from notebooks."""

    def run(self) -> Tuple[List[nodes.Node], List[nodes.system_message]]:
        # now check if we have both key:format in the key
        parts = self.text.rsplit(":", 1)
        if len(parts) == 2:
            key, formatting = parts
        else:
            key = parts[0]
            formatting = None

        # now retrieve the data
        document = self.inliner.document
        if "nb_renderer" not in document:
            return [], [
                warning(
                    "No 'nb_renderer' found on the document.", document, self.lineno
                )
            ]
        nb_renderer: NbElementRenderer = document["nb_renderer"]
        resources = nb_renderer.get_resources()
        if "glue" not in resources:
            return [], [
                warning(
                    "No glue data found in the notebook resources.",
                    document,
                    self.lineno,
                )
            ]
        if key not in resources["glue"]:
            return [], [
                warning(f"No key {key!r} found in glue data.", document, self.lineno)
            ]
        if "text/plain" not in resources["glue"][key].get("data", {}):
            return [], [
                warning(
                    f"{key!r} does not contain 'text/plain' data.",
                    document,
                    self.lineno,
                )
            ]
        text = resources["glue"][key]["data"]["text/plain"].strip("'")
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


class PasteDirective(Directive):
    """A directive for pasting code outputs from notebooks."""

    required_arguments = 1  # the key
    final_argument_whitespace = True
    has_content = False

    def get_source_info(self) -> Tuple[str, int]:
        """Get source and line number."""
        return self.state_machine.get_source_and_line(self.lineno)

    def set_source_info(self, node: nodes.Node) -> None:
        """Set source and line number to the node."""
        node.source, node.line = self.get_source_info()

    def run(self) -> List[nodes.Node]:
        """Run the directive."""
        return render_glue_output(
            self.arguments[0], self.state.document, self.lineno, self.set_source_info
        )


class PasteFigureDirective(PasteDirective):
    """A directive for pasting code outputs from notebooks, wrapped in a figure."""

    def align(argument):
        return directives.choice(argument, ("left", "center", "right"))

    def figwidth_value(argument):
        return directives.length_or_percentage_or_unitless(argument, "px")

    option_spec = (PasteDirective.option_spec or {}).copy()
    option_spec["figwidth"] = figwidth_value
    option_spec["figclass"] = directives.class_option
    option_spec["align"] = align
    option_spec["name"] = directives.unchanged
    has_content = True

    def run(self):
        paste_nodes = super().run()
        if not paste_nodes or isinstance(paste_nodes[0], nodes.system_message):
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
                    self.state.document,
                    self.lineno,
                )
                return [figure_node, error]
            if len(node) > 1:
                figure_node += nodes.legend("", *node[1:])

        return [figure_node]

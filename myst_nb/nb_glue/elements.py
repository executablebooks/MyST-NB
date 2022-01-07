"""Directives and roles which can be used by both docutils and sphinx."""
from typing import Any, Dict, List

from docutils import nodes
from docutils.parsers.rst import Directive, directives

from myst_nb.loggers import DocutilsDocLogger, SphinxDocLogger
from myst_nb.render import NbElementRenderer


class PasteDirective(Directive):
    """A directive for pasting code outputs from notebooks."""

    required_arguments = 1  # the key
    final_argument_whitespace = True
    has_content = False

    @property
    def is_sphinx(self) -> bool:
        """Return True if we are in sphinx, otherwise docutils."""
        return hasattr(self.state.document.settings, "env")

    def warning(self, message: str) -> nodes.system_message:
        if self.is_sphinx:
            logger = SphinxDocLogger(self.state.document)
        else:
            logger = DocutilsDocLogger(self.state.document)
        logger.warning(message, subtype="glue")
        return nodes.system_message(
            message,
            type="WARNING",
            level=2,
            line=self.lineno,
            source=self.state.document["source"],
        )

    def set_source_info(self, node: nodes.Node) -> None:
        """Set source and line number to the node."""
        node.source, node.line = self.state_machine.get_source_and_line(self.lineno)

    def run(self) -> List[nodes.Node]:
        """Run the directive."""
        key = self.arguments[0]
        if "nb_renderer" not in self.state.document:
            return self.warning("No 'nb_renderer' found on the document.")
        nb_renderer: NbElementRenderer = self.state.document["nb_renderer"]
        resources = nb_renderer.get_resources()
        if "glue" not in resources:
            return self.warning("No glue data found in the notebook resources.")
        if key not in resources["glue"]:
            return self.warning(f"No key {key!r} found in glue data.")
        if not resources["glue"][key].get("data"):
            return self.warning(f"{key!r} does not contain any data.")
        if self.is_sphinx:
            return self.render_output_sphinx(nb_renderer, resources["glue"][key])
        else:
            return self.render_output_docutils(nb_renderer, resources["glue"][key])

    def render_output_docutils(
        self, nb_renderer: NbElementRenderer, output: Dict[str, Any]
    ) -> List[nodes.Node]:
        mime_priority = nb_renderer.renderer.get_nb_config("mime_priority")
        try:
            mime_type = next(x for x in mime_priority if x in output["data"])
        except StopIteration:
            return self.warning("No output mime type found from render_priority")
        else:
            cell_index = 0  # TODO make this optional, and actually just pass metadata?
            return nb_renderer.render_mime_type(
                mime_type, output["data"][mime_type], cell_index, self.lineno
            )

    def render_output_sphinx(
        self, nb_renderer: NbElementRenderer, output: Dict[str, Any]
    ) -> List[nodes.Node]:
        mime_bundle = nodes.container(nb_element="mime_bundle")
        self.set_source_info(mime_bundle)
        for mime_type, data in output["data"].items():
            mime_container = nodes.container(mime_type=mime_type)
            self.set_source_info(mime_container)
            cell_index = 0  # TODO make this optional, and actually just pass metadata?
            nds = nb_renderer.render_mime_type(mime_type, data, cell_index, self.lineno)
            if nds:
                mime_container.extend(nds)
                mime_bundle.append(mime_container)
        return [mime_bundle]


class PasteFigureDirective(PasteDirective):
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
                error = self.warning(
                    "Figure caption must be a paragraph or empty comment."
                )
                return [figure_node, error]
            if len(node) > 1:
                figure_node += nodes.legend("", *node[1:])

        return [figure_node]

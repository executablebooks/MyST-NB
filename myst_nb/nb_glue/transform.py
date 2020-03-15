from sphinx.transforms import SphinxTransform
from sphinx.util import logging

from myst_nb.nb_glue.domain import PasteNode, NbGlueDomain


SPHINX_LOGGER = logging.getLogger(__name__)


class PasteNodesToDocutils(SphinxTransform):
    """Use the builder context to transform a CellOutputNode into Sphinx nodes."""

    default_priority = 699  # must be applied before CellOutputsToNodes

    def apply(self):
        glue_domain = NbGlueDomain.from_env(self.app.env)  # type: NbGlueDomain
        for paste_node in self.document.traverse(PasteNode):

            if paste_node.key not in glue_domain:
                SPHINX_LOGGER.warning(
                    (
                        f"Couldn't find key `{paste_node.key}` "
                        "in keys defined across all pages."
                    ),
                    location=paste_node.location,
                )
                continue

            # Grab the output for this key
            output = glue_domain.get(paste_node.key)

            out_node = paste_node.create_node(
                output=output, document=self.document, env=self.app.env
            )
            if out_node is None:
                SPHINX_LOGGER.warning(
                    (
                        "Couldn't find compatible output format for key "
                        f"`{paste_node.key}`"
                    ),
                    location=paste_node.location,
                )
            else:
                paste_node.replace_self(out_node)

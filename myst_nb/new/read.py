"""Module for reading notebooks from a string input."""
from typing import Callable, Tuple

from myst_parser.main import MdParserConfig
from nbformat import NotebookNode
from nbformat import reads as read_ipynb

from myst_nb.configuration import NbParserConfig

NOTEBOOK_VERSION = 4


def create_nb_reader(
    string: str, source: str, md_config: MdParserConfig, nb_config: NbParserConfig
) -> Tuple[Callable[[str], NotebookNode], MdParserConfig]:
    """Create a notebook reader, given a string, source and configuration.

    Note, we do not directly parse to a notebook, since jupyter-cache functionality
    requires the reader.

    :param string: The input string.
    :param source: Path to or description of the input source being processed.

    :returns: the notebook reader, and the (potentially modified) MdParserConfig.
    """
    # TODO handle converters
    return lambda text: read_ipynb(text, as_version=NOTEBOOK_VERSION), md_config

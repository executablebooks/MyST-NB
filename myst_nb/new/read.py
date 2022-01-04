"""Module for reading notebook formats from a string input."""
import json
from functools import partial
from pathlib import Path
from typing import Callable, Iterator, Optional, Union

import attr
import nbformat as nbf
import yaml
from markdown_it.renderer import RendererHTML
from myst_parser.main import MdParserConfig, create_md_parser

from myst_nb.configuration import NbParserConfig

NOTEBOOK_VERSION = 4
"""The notebook version that readers should return."""


@attr.s
class NbReader:
    """A data class for reading a notebook format."""

    read: Callable[[str], nbf.NotebookNode] = attr.ib()
    """The function to read a notebook from a string."""
    md_config: MdParserConfig = attr.ib()
    """The configuration for parsing markdown cells."""


def standard_nb_read(text: str) -> nbf.NotebookNode:
    """Read a standard .ipynb notebook from a string."""
    return nbf.reads(text, as_version=NOTEBOOK_VERSION)


def create_nb_reader(
    path: str,
    md_config: MdParserConfig,
    nb_config: NbParserConfig,
    content: Union[None, str, Iterator[str]],
) -> Optional[NbReader]:
    """Create a notebook reader, given a string, source path and configuration.

    Note, we do not directly parse to a notebook, since jupyter-cache functionality
    requires the reader.

    :param path: Path to the input source being processed.
    :param nb_config: The  configuration for parsing Notebooks.
    :param md_config: The default configuration for parsing Markown.
    :param content: The input string (optionally used to check for text-based notebooks)

    :returns: the notebook reader, and the (potentially modified) MdParserConfig,
        or None if the input cannot be read as a notebook.
    """
    # the import is here so this module can be loaded without sphinx
    from sphinx.util import import_object

    # get all possible readers
    readers = nb_config.custom_formats.copy()
    # add the default reader
    readers.setdefault(".ipynb", (standard_nb_read, {}, False))

    # we check suffixes ordered by longest first, to ensure we get the "closest" match
    iterator = sorted(readers.items(), key=lambda x: len(x[0]), reverse=True)
    for suffix, (reader, reader_kwargs, commonmark_only) in iterator:
        if path.endswith(suffix):
            if isinstance(reader, str):
                # attempt to load the reader as an object path
                reader = import_object(reader)
            if commonmark_only:
                # Markdown cells should be read as Markdown only
                md_config = attr.evolve(md_config, commonmark_only=True)
            return NbReader(partial(reader, **(reader_kwargs or {})), md_config)

    # a Markdown file is a special case, since we only treat it as a notebook,
    # if it starts with certain "top-matter"
    if content is not None and is_myst_markdown_notebook(content):
        return NbReader(
            partial(
                read_myst_markdown_notebook,
                config=md_config,
                add_source_map=True,
                path=path,
            ),
            md_config,
        )

    # if we get here, we did not find a reader
    return None


def is_myst_markdown_notebook(text: Union[str, Iterator[str]]) -> bool:
    """Check if the input is a MyST Markdown notebook.

    This is identified by the presence of a top-matter section, containing::

        ---
        jupytext:
            text_representation:
                format_name: myst
        ---

    :param text: The input text.
    :returns: True if the input is a markdown notebook.
    """
    if isinstance(text, str):
        if not text.startswith("---"):  # skip creating the line list in memory
            return False
        text = (line for line in text.splitlines())
    try:
        if not next(text).startswith("---"):
            return False
    except StopIteration:
        return False
    top_matter = []
    for line in text:
        if line.startswith("---") or line.startswith("..."):
            break
        top_matter.append(line.rstrip() + "\n")
    try:
        metadata = yaml.safe_load("".join(top_matter))
        assert isinstance(metadata, dict)
    except Exception:
        return False
    if (
        metadata.get("jupytext", {})
        .get("text_representation", {})
        .get("format_name", None)
        != "myst"
    ):
        return False

    return True

    # TODO move this to reader, since not strictly part of function objective
    # or just allow nbformat/nbclient to handle the failure
    # if "name" not in metadata.get("kernelspec", {}):
    #     raise IOError(
    #         "A myst notebook text-representation requires " "kernelspec/name metadata"
    #     )
    # if "display_name" not in metadata.get("kernelspec", {}):
    #     raise IOError(
    #         "A myst notebook text-representation requires "
    #         "kernelspec/display_name metadata"
    #     )


def read_myst_markdown_notebook(
    text,
    config: MdParserConfig,
    code_directive="{code-cell}",
    raw_directive="{raw-cell}",
    add_source_map=False,
    path: Optional[str] = None,
) -> nbf.NotebookNode:
    """Convert text written in the myst format to a notebook.

    :param text: the file text
    :param code_directive: the name of the directive to search for containing code cells
    :param raw_directive: the name of the directive to search for containing raw cells
    :param add_source_map: add a `source_map` key to the notebook metadata,
        which is a list of the starting source line number for each cell.
    :param path: path to notebook (required for :load:)

    :raises _MystMetadataParsingError if the metadata block is not valid JSON/YAML

    NOTE: we assume here that all of these directives are at the top-level,
    i.e. not nested in other directives.
    """
    # parse markdown file up to the block level (i.e. don't worry about inline text)
    inline_config = attr.evolve(
        config, disable_syntax=(config.disable_syntax + ["inline"])
    )
    parser = create_md_parser(inline_config, RendererHTML)
    tokens = parser.parse(text + "\n")
    lines = text.splitlines()
    md_start_line = 0

    # get the document metadata
    metadata_nb = {}
    if tokens[0].type == "front_matter":
        metadata = tokens.pop(0)
        md_start_line = metadata.map[1]
        try:
            metadata_nb = yaml.safe_load(metadata.content)
        except (yaml.parser.ParserError, yaml.scanner.ScannerError) as error:
            raise _MystMetadataParsingError("Notebook metadata: {}".format(error))

    # create an empty notebook
    nbf_version = nbf.v4
    kwargs = {"metadata": nbf.from_dict(metadata_nb)}
    notebook = nbf_version.new_notebook(**kwargs)
    source_map = []  # this is a list of the starting line number for each cell

    def _flush_markdown(start_line, token, md_metadata):
        """When we find a cell we check if there is preceding text.o"""
        endline = token.map[0] if token else len(lines)
        md_source = _strip_blank_lines("\n".join(lines[start_line:endline]))
        meta = nbf.from_dict(md_metadata)
        if md_source:
            source_map.append(start_line)
            notebook.cells.append(
                nbf_version.new_markdown_cell(source=md_source, metadata=meta)
            )

    # iterate through the tokens to identify notebook cells
    nesting_level = 0
    md_metadata = {}

    for token in tokens:

        nesting_level += token.nesting

        if nesting_level != 0:
            # we ignore fenced block that are nested, e.g. as part of lists, etc
            continue

        if token.type == "fence" and token.info.startswith(code_directive):
            _flush_markdown(md_start_line, token, md_metadata)
            options, body_lines = _read_fenced_cell(token, len(notebook.cells), "Code")
            # Parse :load: or load: tags and populate body with contents of file
            if "load" in options:
                body_lines = _load_code_from_file(
                    path, options["load"], token, body_lines
                )
            meta = nbf.from_dict(options)
            source_map.append(token.map[0] + 1)
            notebook.cells.append(
                nbf_version.new_code_cell(source="\n".join(body_lines), metadata=meta)
            )
            md_metadata = {}
            md_start_line = token.map[1]

        elif token.type == "fence" and token.info.startswith(raw_directive):
            _flush_markdown(md_start_line, token, md_metadata)
            options, body_lines = _read_fenced_cell(token, len(notebook.cells), "Raw")
            meta = nbf.from_dict(options)
            source_map.append(token.map[0] + 1)
            notebook.cells.append(
                nbf_version.new_raw_cell(source="\n".join(body_lines), metadata=meta)
            )
            md_metadata = {}
            md_start_line = token.map[1]

        elif token.type == "myst_block_break":
            _flush_markdown(md_start_line, token, md_metadata)
            md_metadata = _read_cell_metadata(token, len(notebook.cells))
            md_start_line = token.map[1]

    _flush_markdown(md_start_line, None, md_metadata)

    if add_source_map:
        notebook.metadata["source_map"] = source_map
    return notebook


class _MystMetadataParsingError(Exception):
    """Error when parsing metadata from myst formatted text"""


class _LoadFileParsingError(Exception):
    """Error when parsing files for code-blocks/code-cells"""


def _strip_blank_lines(text):
    text = text.rstrip()
    while text and text.startswith("\n"):
        text = text[1:]
    return text


class _MockDirective:
    option_spec = {"options": True}
    required_arguments = 0
    optional_arguments = 1
    has_content = True


def _read_fenced_cell(token, cell_index, cell_type):
    from myst_parser.parse_directives import DirectiveParsingError, parse_directive_text

    try:
        _, options, body_lines = parse_directive_text(
            directive_class=_MockDirective,
            first_line="",
            content=token.content,
            validate_options=False,
        )
    except DirectiveParsingError as err:
        raise _MystMetadataParsingError(
            "{0} cell {1} at line {2} could not be read: {3}".format(
                cell_type, cell_index, token.map[0] + 1, err
            )
        )
    return options, body_lines


def _read_cell_metadata(token, cell_index):
    metadata = {}
    if token.content:
        try:
            metadata = json.loads(token.content.strip())
        except Exception as err:
            raise _MystMetadataParsingError(
                "Markdown cell {0} at line {1} could not be read: {2}".format(
                    cell_index, token.map[0] + 1, err
                )
            )
        if not isinstance(metadata, dict):
            raise _MystMetadataParsingError(
                "Markdown cell {0} at line {1} is not a dict".format(
                    cell_index, token.map[0] + 1
                )
            )

    return metadata


def _load_code_from_file(nb_path, file_name, token, body_lines):
    """load source code from a file."""
    if nb_path is None:
        raise _LoadFileParsingError("path to notebook not supplied for :load:")
    file_path = Path(nb_path).parent.joinpath(file_name).resolve()
    if len(body_lines):
        pass  # TODO this would make the reader dependent on sphinx
        # line = token.map[0] if token.map else 0
        # msg = (
        #     f"{nb_path}:{line} content of code-cell is being overwritten by "
        #     f":load: {file_name}"
        # )
        # LOGGER.warning(msg)
    try:
        body_lines = file_path.read_text().split("\n")
    except Exception:
        raise _LoadFileParsingError("Can't read file from :load: {}".format(file_path))
    return body_lines

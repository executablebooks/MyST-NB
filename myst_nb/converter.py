import json
from typing import Callable, Iterable, Optional

import attr

import nbformat as nbf
from sphinx.environment import BuildEnvironment
from sphinx.util import import_object
import yaml

from myst_parser.main import MdParserConfig

NOTEBOOK_VERSION = 4
CODE_DIRECTIVE = "{code-cell}"
RAW_DIRECTIVE = "{raw-cell}"


@attr.s
class NbConverter:
    func: Callable[[str], nbf.NotebookNode] = attr.ib()
    config: MdParserConfig = attr.ib()


def get_nb_converter(
    path: str,
    env: BuildEnvironment,
    source_iter: Optional[Iterable[str]] = None,
) -> Optional[NbConverter]:
    """Get function, to convert a source string to a Notebook."""

    # Standard notebooks take priority
    if path.endswith(".ipynb"):
        return NbConverter(
            lambda text: nbf.reads(text, as_version=NOTEBOOK_VERSION), env.myst_config
        )

    # we check suffixes ordered by longest first, to ensure we get the "closest" match
    for source_suffix in sorted(
        env.config.nb_custom_formats.keys(), key=len, reverse=True
    ):
        if path.endswith(source_suffix):
            (
                converter,
                converter_kwargs,
                commonmark_only,
            ) = env.config.nb_custom_formats[source_suffix]
            converter = import_object(converter)
            a = NbConverter(
                lambda text: converter(text, **(converter_kwargs or {})),
                env.myst_config
                if commonmark_only is None
                else attr.evolve(env.myst_config, commonmark_only=commonmark_only),
            )
            return a

    # If there is no source text then we assume a MyST Notebook
    if source_iter is None:
        return NbConverter(
            lambda text: myst_to_notebook(
                text, config=env.myst_config, add_source_map=True
            ),
            env.myst_config,
        )

    # Given the source lines, we check it can be recognised as a MyST Notebook
    if is_myst_notebook(source_iter):
        return NbConverter(
            lambda text: myst_to_notebook(
                text, config=env.myst_config, add_source_map=True
            ),
            env.myst_config,
        )

    # Otherwise, we return None,
    # to imply that it should be parsed as as standard Markdown file
    return None


def is_myst_notebook(line_iter: Iterable[str]) -> bool:
    """Is the text file a MyST based notebook representation?"""
    # we need to distinguish between markdown representing notebooks
    # and standard notebooks.
    # Therefore, for now we require that, at a mimimum we can find some top matter
    # containing the jupytext format_name
    yaml_lines = []
    for i, line in enumerate(line_iter):
        if i == 0 and not line.startswith("---"):
            return False
        if i != 0 and (line.startswith("---") or line.startswith("...")):
            break
        yaml_lines.append(line.rstrip() + "\n")

    try:
        front_matter = yaml.safe_load("".join(yaml_lines))
    except Exception:
        return False
    if front_matter is None:  # this can occur for empty files
        return False
    if (
        front_matter.get("jupytext", {})
        .get("text_representation", {})
        .get("format_name", None)
        != "myst"
    ):
        return False

    if "name" not in front_matter.get("kernelspec", {}):
        raise IOError(
            "A myst notebook text-representation requires " "kernelspec/name metadata"
        )
    if "display_name" not in front_matter.get("kernelspec", {}):
        raise IOError(
            "A myst notebook text-representation requires "
            "kernelspec/display_name metadata"
        )
    return True


class MystMetadataParsingError(Exception):
    """Error when parsing metadata from myst formatted text"""


def strip_blank_lines(text):
    text = text.rstrip()
    while text and text.startswith("\n"):
        text = text[1:]
    return text


class MockDirective:
    option_spec = {"options": True}
    required_arguments = 0
    optional_arguments = 1
    has_content = True


def read_fenced_cell(token, cell_index, cell_type):
    from myst_parser.parse_directives import DirectiveParsingError, parse_directive_text

    try:
        _, options, body_lines = parse_directive_text(
            directive_class=MockDirective,
            argument_str="",
            content=token.content,
            validate_options=False,
        )
    except DirectiveParsingError as err:
        raise MystMetadataParsingError(
            "{0} cell {1} at line {2} could not be read: {3}".format(
                cell_type, cell_index, token.map[0] + 1, err
            )
        )
    return options, body_lines


def read_cell_metadata(token, cell_index):
    metadata = {}
    if token.content:
        try:
            metadata = json.loads(token.content.strip())
        except Exception as err:
            raise MystMetadataParsingError(
                "Markdown cell {0} at line {1} could not be read: {2}".format(
                    cell_index, token.map[0] + 1, err
                )
            )
        if not isinstance(metadata, dict):
            raise MystMetadataParsingError(
                "Markdown cell {0} at line {1} is not a dict".format(
                    cell_index, token.map[0] + 1
                )
            )

    return metadata


def myst_to_notebook(
    text,
    config: MdParserConfig,
    code_directive=CODE_DIRECTIVE,
    raw_directive=RAW_DIRECTIVE,
    add_source_map=False,
):
    """Convert text written in the myst format to a notebook.

    :param text: the file text
    :param code_directive: the name of the directive to search for containing code cells
    :param raw_directive: the name of the directive to search for containing raw cells
    :param add_source_map: add a `source_map` key to the notebook metadata,
        which is a list of the starting source line number for each cell.

    :raises MystMetadataParsingError if the metadata block is not valid JSON/YAML

    NOTE: we assume here that all of these directives are at the top-level,
    i.e. not nested in other directives.
    """
    # TODO warn about nested code-cells
    from myst_parser.main import default_parser

    # parse markdown file up to the block level (i.e. don't worry about inline text)
    inline_config = attr.evolve(
        config, renderer="html", disable_syntax=(config.disable_syntax + ["inline"])
    )
    parser = default_parser(inline_config)
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
            raise MystMetadataParsingError("Notebook metadata: {}".format(error))

    # create an empty notebook
    nbf_version = nbf.v4
    kwargs = {"metadata": nbf.from_dict(metadata_nb)}
    notebook = nbf_version.new_notebook(**kwargs)
    source_map = []  # this is a list of the starting line number for each cell

    def _flush_markdown(start_line, token, md_metadata):
        """When we find a cell we check if there is preceding text.o"""
        endline = token.map[0] if token else len(lines)
        md_source = strip_blank_lines("\n".join(lines[start_line:endline]))
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
            options, body_lines = read_fenced_cell(token, len(notebook.cells), "Code")
            meta = nbf.from_dict(options)
            source_map.append(token.map[0] + 1)
            notebook.cells.append(
                nbf_version.new_code_cell(source="\n".join(body_lines), metadata=meta)
            )
            md_metadata = {}
            md_start_line = token.map[1]

        elif token.type == "fence" and token.info.startswith(raw_directive):
            _flush_markdown(md_start_line, token, md_metadata)
            options, body_lines = read_fenced_cell(token, len(notebook.cells), "Raw")
            meta = nbf.from_dict(options)
            source_map.append(token.map[0] + 1)
            notebook.cells.append(
                nbf_version.new_raw_cell(source="\n".join(body_lines), metadata=meta)
            )
            md_metadata = {}
            md_start_line = token.map[1]

        elif token.type == "myst_block_break":
            _flush_markdown(md_start_line, token, md_metadata)
            md_metadata = read_cell_metadata(token, len(notebook.cells))
            md_start_line = token.map[1]

    _flush_markdown(md_start_line, None, md_metadata)

    if add_source_map:
        notebook.metadata["source_map"] = source_map
    return notebook

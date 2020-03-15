import json
from typing import List, Union

from docutils.parsers.rst.directives.misc import TestDirective
import nbformat as nbf

from mistletoe.base_elements import SourceLines
from mistletoe.parse_context import ParseContext, get_parse_context, set_parse_context
from mistletoe.block_tokens import Document, CodeFence

from myst_parser.block_tokens import BlockBreak
from myst_parser.parse_directives import parse_directive_text


def myst_to_nb(
    text: Union[str, List[str], SourceLines], directive: str = "nb-cell"
) -> nbf.NotebookNode:
    """Convert text written in the myst format to a notebook.

    :param text: the file text
    :directive: the name of the directive to search for.

    NOTE: we assume here that all of these directives are at the top-level,
    i.e. not nested in other directives.
    """
    from myst_nb.parser import SphinxNBRenderer

    original_context = get_parse_context()
    parse_context = ParseContext(
        find_blocks=SphinxNBRenderer.default_block_tokens,
        find_spans=SphinxNBRenderer.default_span_tokens,
    )

    if isinstance(text, SourceLines):
        lines = text
    else:
        lines = SourceLines(text, standardize_ends=True)

    try:
        set_parse_context(parse_context)
        doc = Document.read(lines, front_matter=True)

        metadata = doc.front_matter.get_data() if doc.front_matter else {}
        nbformat = metadata.pop("nbformat", None)
        nbformat_minor = metadata.pop("nbformat_minor", None)
        kwargs = {"metadata": nbf.from_dict(metadata)}
        if nbformat is not None:
            kwargs["nbformat"] = nbformat
        if nbformat_minor is not None:
            kwargs["nbformat_minor"] = nbformat_minor

        notebook = nbf.v4.new_notebook(**kwargs)

        current_line = 0 if not doc.front_matter else doc.front_matter.position.line_end
        md_metadata = {}

        for item in doc.walk(["CodeFence", "BlockBreak"]):
            if isinstance(item.node, BlockBreak):
                token = item.node  # type: BlockBreak
                notebook.cells.append(
                    nbf.v4.new_markdown_cell(
                        source="".join(
                            lines.lines[current_line : token.position.line_start - 1]
                        ).rstrip(),
                        metadata=nbf.from_dict(md_metadata),
                    )
                )
                if token.content:
                    try:
                        md_metadata = json.loads(token.content.strip())
                    except Exception:
                        # TODO log warning if content can't be parsed as json
                        md_metadata = {}
                    if not isinstance(md_metadata, dict):
                        # TODO log warning if content isn't a dict
                        md_metadata = {}
                else:
                    md_metadata = {}
                current_line = token.position.line_start
            if isinstance(
                item.node, CodeFence
            ) and item.node.language == "{{{0}}}".format(directive):
                token = item.node  # type: CodeFence

                # Note: we ignore anything after the directive on the first line
                # TODO: could log warning about this: ``if token.arguments != ""```

                # we use the TestDirective here, since `parse_directive_text`
                # is setup to skip any option validation for this class
                _, options, body_lines = parse_directive_text(
                    directive_class=TestDirective,
                    argument_str="",
                    content=token.children[0].content,
                )

                notebook.cells.append(
                    nbf.v4.new_markdown_cell(
                        source="".join(
                            lines.lines[current_line : token.position.line_start - 1]
                        ).rstrip(),
                        metadata=nbf.from_dict(md_metadata),
                    )
                )
                current_line = token.position.line_end
                md_metadata = {}

                notebook.cells.append(
                    nbf.v4.new_code_cell(
                        source="\n".join(body_lines), metadata=nbf.from_dict(options)
                    )
                )

        # add the final markdown cell (if present)
        if lines.lines[current_line:]:
            notebook.cells.append(
                nbf.v4.new_markdown_cell(
                    source="".join(lines.lines[current_line:]).rstrip(),
                    metadata=nbf.from_dict(md_metadata),
                )
            )

    finally:
        set_parse_context(original_context)

    return notebook

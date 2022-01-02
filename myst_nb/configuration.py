"""Configuration for myst-nb."""
from typing import Any, Dict, Iterable, Sequence, Tuple

import attr
from attr.validators import deep_iterable, in_, instance_of, optional
from typing_extensions import Literal


def custom_formats_converter(value: dict) -> dict:
    """Convert the custom format dict."""
    if not isinstance(value, dict):
        raise TypeError(f"`nb_custom_formats` must be a dict: {value}")
    output = {}
    for suffix, reader in value.items():
        if not isinstance(suffix, str):
            raise TypeError(f"`nb_custom_formats` keys must be a string: {suffix}")
        if isinstance(reader, str):
            output[suffix] = (reader, {}, False)
        elif not isinstance(reader, Sequence):
            raise TypeError(
                f"`nb_custom_formats` values must be a string or sequence: {reader}"
            )
        elif len(reader) == 2:
            output[suffix] = (reader[0], reader[1], False)
        elif len(reader) == 3:
            output[suffix] = (reader[0], reader[1], reader[2])
        else:
            raise TypeError(
                f"`nb_custom_formats` values must be a string, of sequence of length "
                f"2 or 3: {reader}"
            )
        if not isinstance(output[suffix][0], str):
            raise TypeError(
                f"`nb_custom_formats` values[0] must be a string: {output[suffix][0]}"
            )
        if not isinstance(output[suffix][1], dict):
            raise TypeError(
                f"`nb_custom_formats` values[1] must be a dict: {output[suffix][1]}"
            )
        if not isinstance(output[suffix][2], bool):
            raise TypeError(
                f"`nb_custom_formats` values[2] must be a bool: {output[suffix][2]}"
            )
    return output


@attr.s()
class NbParserConfig:
    """Global configuration options for the MyST-NB parser.

    Note: in the sphinx configuration these option names are prepended with ``nb_``
    """

    # TODO: nb_render_key, execution_show_tb,
    # execution_excludepatterns, jupyter_cache
    # jupyter_sphinx_require_url, jupyter_sphinx_embed_url

    # TODO handle old names; put in metadata, then auto generate warnings

    # file read options

    custom_formats: Dict[str, Tuple[str, dict, bool]] = attr.ib(
        factory=dict,
        converter=custom_formats_converter,
        # TODO check can be loaded from string?
        metadata={"help": "Custom formats for reading notebook; suffix -> reader"},
    )

    # notebook execution options

    execution_mode: Literal["off", "force", "cache"] = attr.ib(
        default="off",  # TODO different default for docutils (off) and sphinx (cache)?
        validator=in_(
            [
                "off",
                "force",
                "cache",
            ]
        ),
        metadata={"help": "Execution mode for notebooks"},
    )
    execution_cache_path: str = attr.ib(
        default="",
        validator=instance_of(str),
        metadata={"help": "Path to folder for caching notebooks"},
    )
    execution_timeout: int = attr.ib(
        default=30,
        validator=instance_of(int),
        metadata={"help": "Execution timeout (seconds)"},
    )
    execution_in_temp: bool = attr.ib(
        default=False,
        validator=instance_of(bool),
        metadata={
            "help": "Use a temporary folder for the execution current working directory"
        },
    )
    execution_allow_errors: bool = attr.ib(
        default=False,
        validator=instance_of(bool),
        metadata={"help": "Allow errors during execution"},
    )

    # render options

    output_folder: str = attr.ib(
        default="build",
        validator=instance_of(str),
        metadata={
            "help": "Output folder for external outputs",
            "docutils_only": True,  # in sphinx we output to the build folder
        },
    )
    remove_code_source: bool = attr.ib(
        default=False,
        validator=instance_of(bool),
        metadata={"help": "Remove code cell source"},
    )
    remove_code_outputs: bool = attr.ib(
        default=False,
        validator=instance_of(bool),
        metadata={"help": "Remove code cell outputs"},
    )
    number_source_lines: bool = attr.ib(
        default=False,
        validator=instance_of(bool),
        metadata={"help": "Number code cell source lines"},
    )
    merge_streams: bool = attr.ib(
        default=False,
        validator=instance_of(bool),
        metadata={"help": "Merge stdout/stderr execution output streams"},
    )
    output_stderr: Literal[
        "show", "remove", "remove-warn", "warn", "error", "severe"
    ] = attr.ib(
        default="show",
        validator=in_(
            [
                "show",
                "remove",
                "remove-warn",
                "warn",
                "error",
                "severe",
            ]
        ),
        metadata={"help": "Behaviour for stderr output"},
    )
    embed_markdown_outputs: bool = attr.ib(
        default=False,
        validator=instance_of(bool),
        metadata={"help": "Embed markdown outputs"},  # TODO better help text
    )
    # TODO this would be for docutils but not for sphinx
    render_priority: Iterable[str] = attr.ib(
        default=(
            "application/vnd.jupyter.widget-view+json",
            "application/javascript",
            "text/html",
            "image/svg+xml",
            "image/png",
            "image/jpeg",
            "text/markdown",
            "text/latex",
            "text/plain",
        ),
        validator=deep_iterable(instance_of(str)),
        metadata={"help": "Render priority for mime types"},
    )
    render_text_lexer: str = attr.ib(
        default="myst-ansi",
        # TODO allow None -> "none"?
        validator=optional(instance_of(str)),  # TODO check it can be loaded?
        metadata={
            "help": "Pygments lexer applied to stdout/stderr and text/plain outputs"
        },
    )
    render_error_lexer: str = attr.ib(
        default="ipythontb",
        # TODO allow None -> "none"?
        validator=optional(instance_of(str)),  # TODO check it can be loaded?
        metadata={"help": "Pygments lexer applied to error/traceback outputs"},
    )
    render_plugin: str = attr.ib(
        default="default",
        validator=instance_of(str),  # TODO check it can be loaded?
        metadata={
            "help": "The entry point for the execution output render class "
            "(in group `myst_nb.output_renderer`)"
        },
    )

    @classmethod
    def get_fields(cls) -> Tuple[attr.Attribute, ...]:
        return attr.fields(cls)

    def as_dict(self, dict_factory=dict) -> dict:
        return attr.asdict(self, dict_factory=dict_factory)

    def as_triple(self) -> Iterable[Tuple[str, Any, attr.Attribute]]:
        """Yield triples of (name, value, field)."""
        fields = attr.fields_dict(self.__class__)
        for name, value in attr.asdict(self).items():
            yield name, value, fields[name]

"""Configuration for myst-nb."""
from typing import Any, Dict, Iterable, Sequence, Tuple

import attr
from attr.validators import deep_iterable, deep_mapping, in_, instance_of, optional
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
            # TODO check can be loaded as a python object?
        if not isinstance(output[suffix][1], dict):
            raise TypeError(
                f"`nb_custom_formats` values[1] must be a dict: {output[suffix][1]}"
            )
        if not isinstance(output[suffix][2], bool):
            raise TypeError(
                f"`nb_custom_formats` values[2] must be a bool: {output[suffix][2]}"
            )
    return output


def render_priority_factory() -> Dict[str, Sequence[str]]:
    """Create a default render priority dict: name -> priority list."""
    # See formats at https://www.sphinx-doc.org/en/master/usage/builders/index.html
    # generated with:
    # [(b.name, b.format, b.supported_image_types)
    # for b in app.registry.builders.values()]
    # TODO potentially could auto-generate
    html_builders = [
        ("epub", "html", ["image/svg+xml", "image/png", "image/gif", "image/jpeg"]),
        ("html", "html", ["image/svg+xml", "image/png", "image/gif", "image/jpeg"]),
        ("dirhtml", "html", ["image/svg+xml", "image/png", "image/gif", "image/jpeg"]),
        (
            "singlehtml",
            "html",
            ["image/svg+xml", "image/png", "image/gif", "image/jpeg"],
        ),
        (
            "applehelp",
            "html",
            [
                "image/png",
                "image/gif",
                "image/jpeg",
                "image/tiff",
                "image/jp2",
                "image/svg+xml",
            ],
        ),
        ("devhelp", "html", ["image/png", "image/gif", "image/jpeg"]),
        ("htmlhelp", "html", ["image/png", "image/gif", "image/jpeg"]),
        ("json", "html", ["image/svg+xml", "image/png", "image/gif", "image/jpeg"]),
        ("pickle", "html", ["image/svg+xml", "image/png", "image/gif", "image/jpeg"]),
        ("qthelp", "html", ["image/svg+xml", "image/png", "image/gif", "image/jpeg"]),
        # deprecated RTD builders
        # https://github.com/readthedocs/readthedocs-sphinx-ext/blob/master/readthedocs_ext/readthedocs.py
        (
            "readthedocs",
            "html",
            ["image/svg+xml", "image/png", "image/gif", "image/jpeg"],
        ),
        (
            "readthedocsdirhtml",
            "html",
            ["image/svg+xml", "image/png", "image/gif", "image/jpeg"],
        ),
        (
            "readthedocssinglehtml",
            "html",
            ["image/svg+xml", "image/png", "image/gif", "image/jpeg"],
        ),
        (
            "readthedocssinglehtmllocalmedia",
            "html",
            ["image/svg+xml", "image/png", "image/gif", "image/jpeg"],
        ),
    ]
    other_builders = [
        ("changes", "", []),
        ("dummy", "", []),
        ("gettext", "", []),
        ("latex", "latex", ["application/pdf", "image/png", "image/jpeg"]),
        ("linkcheck", "", []),
        ("man", "man", []),
        ("texinfo", "texinfo", ["image/png", "image/jpeg", "image/gif"]),
        ("text", "text", []),
        ("xml", "xml", []),
        ("pseudoxml", "pseudoxml", []),
    ]
    output = {}
    for name, _, supported_images in html_builders:
        output[name] = (
            "application/vnd.jupyter.widget-view+json",
            "application/javascript",
            "text/html",
            *supported_images,
            "text/markdown",
            "text/latex",
            "text/plain",
        )
    for name, _, supported_images in other_builders:
        output[name] = (
            *supported_images,
            "text/latex",
            "text/markdown",
            "text/plain",
        )
    return output


@attr.s()
class NbParserConfig:
    """Global configuration options for the MyST-NB parser.

    Note: in the docutils/sphinx configuration,
    these option names are prepended with ``nb_``
    """

    # TODO: nb_render_key, execution_show_tb, execution_excludepatterns
    # jupyter_sphinx_require_url, jupyter_sphinx_embed_url

    # TODO mark which config are allowed per notebook/cell

    # file read options

    custom_formats: Dict[str, Tuple[str, dict, bool]] = attr.ib(
        factory=dict,
        converter=custom_formats_converter,
        metadata={
            "help": "Custom formats for reading notebook; suffix -> reader",
            "docutils_exclude": True,
        },
    )
    # docutils does not support directly the custom format mechanism
    read_as_md: bool = attr.ib(
        default=False,
        validator=instance_of(bool),
        metadata={
            "help": "Read as the MyST Markdown format",
            "sphinx_exclude": True,
        },
        repr=False,
    )

    # notebook execution options

    execution_mode: Literal["off", "force", "cache"] = attr.ib(
        # TODO different default for docutils (off) and sphinx (cache)?
        # TODO deprecate auto
        default="off",
        validator=in_(
            [
                "off",
                "force",
                "cache",
            ]
        ),
        metadata={
            "help": "Execution mode for notebooks",
            "legacy_name": "jupyter_execute_notebooks",
        },
    )
    execution_cache_path: str = attr.ib(
        default="",  # No default, so that sphinx can set it inside outdir, if empty
        validator=instance_of(str),
        metadata={
            "help": "Path to folder for caching notebooks",
            "legacy_name": "jupyter_cache",
        },
    )
    execution_timeout: int = attr.ib(
        default=30,
        validator=instance_of(int),
        metadata={
            "help": "Execution timeout (seconds)",
            "legacy_name": "execution_timeout",
        },
    )
    execution_in_temp: bool = attr.ib(
        default=False,
        validator=instance_of(bool),
        metadata={
            "help": "Use temporary folder for the execution current working directory",
            "legacy_name": "execution_in_temp",
        },
    )
    execution_allow_errors: bool = attr.ib(
        default=False,
        validator=instance_of(bool),
        metadata={
            "help": "Allow errors during execution",
            "legacy_name": "execution_allow_errors",
        },
    )
    execution_show_tb: bool = attr.ib(  # TODO implement
        default=False,
        validator=instance_of(bool),
        metadata={
            "help": "Print traceback to stderr on execution error",
            "legacy_name": "execution_show_tb",
        },
    )

    # render options

    output_folder: str = attr.ib(
        default="build",
        validator=instance_of(str),
        metadata={
            "help": "Output folder for external outputs",
            "sphinx_exclude": True,  # in sphinx we always output to the build folder
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
    # docutils does not allow for the dictionaries in its configuration,
    # and also there is no API for the parser to know the output format, so
    # we use two different options for docutils(mime_priority)/sphinx(render_priority)
    mime_priority: Sequence[str] = attr.ib(
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
        metadata={"help": "Render priority for mime types", "sphinx_exclude": True},
        repr=False,
    )
    render_priority: Dict[str, Sequence[str]] = attr.ib(
        factory=render_priority_factory,
        validator=deep_mapping(instance_of(str), deep_iterable(instance_of(str))),
        metadata={
            "help": "Render priority for mime types, by builder name",
            "docutils_exclude": True,
        },
        repr=False,
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

    def copy(self, **changes) -> "NbParserConfig":
        """Return a copy of the configuration with optional changes applied."""
        return attr.evolve(self, **changes)

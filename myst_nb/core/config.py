"""Configuration for myst-nb."""
import dataclasses as dc
from typing import Any, Dict, Iterable, Optional, Sequence, Tuple

from myst_parser.dc_validators import (
    deep_iterable,
    deep_mapping,
    in_,
    instance_of,
    optional,
    validate_fields,
)
from typing_extensions import Literal


def custom_formats_converter(value: dict) -> Dict[str, Tuple[str, dict, bool]]:
    """Convert the custom format dict."""
    if not isinstance(value, dict):
        raise TypeError(f"`nb_custom_formats` must be a dict: {value}")
    output: Dict[str, Tuple[str, dict, bool]] = {}
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


def ipywidgets_js_factory() -> Dict[str, Dict[str, str]]:
    """Create a default ipywidgets js dict."""
    # see: https://ipywidgets.readthedocs.io/en/7.6.5/embedding.html
    return {
        # Load RequireJS, used by the IPywidgets for dependency management
        "https://cdnjs.cloudflare.com/ajax/libs/require.js/2.3.4/require.min.js": {
            "integrity": "sha256-Ae2Vz/4ePdIu6ZyI/5ZGsYnb+m0JlOmKPjt6XZ9JJkA=",
            "crossorigin": "anonymous",
        },
        # Load IPywidgets bundle for embedding.
        "https://unpkg.com/@jupyter-widgets/html-manager@^0.20.0/dist/embed-amd.js": {
            "data-jupyter-widgets-cdn": "https://cdn.jsdelivr.net/npm/",
            "crossorigin": "anonymous",
        },
    }


@dc.dataclass()
class NbParserConfig:
    """Global configuration options for the MyST-NB parser.

    Note: in the docutils/sphinx configuration,
    these option names are prepended with ``nb_``
    """

    def __post_init__(self):
        self.custom_formats = custom_formats_converter(self.custom_formats)
        validate_fields(self)

    # file read options

    custom_formats: Dict[str, Tuple[str, dict, bool]] = dc.field(
        default_factory=dict,
        metadata={
            "help": "Custom formats for reading notebook; suffix -> reader",
            "docutils_exclude": True,
        },
    )
    # docutils does not support the custom formats mechanism
    read_as_md: bool = dc.field(
        default=False,
        metadata={
            "validator": instance_of(bool),
            "help": "Read as the MyST Markdown format",
            "sphinx_exclude": True,
        },
        repr=False,
    )

    # configuration override keys (applied after file read)

    # TODO previously we had `nb_render_key` (default: "render"),
    # for cell.metadata.render.image and cell.metadata.render.figure`,
    # and also `timeout`/`allow_errors` in notebook.metadata.execution
    # do we still support these or deprecate?
    # (plus also cell.metadata.tags:
    #   nbclient: `skip-execution` and `raises-exception`,
    #   myst_nb: `remove_cell`, `remove-cell`, `remove_input`, `remove-input`,
    #            `remove_output`, `remove-output`, `remove-stderr`
    # )
    # see also:
    # https://nbformat.readthedocs.io/en/latest/format_description.html#cell-metadata
    metadata_key: str = dc.field(
        default="mystnb",  # TODO agree this as the default
        metadata={
            "validator": instance_of(str),
            "help": "Notebook level metadata key for config overrides",
        },
    )

    # notebook execution options

    execution_mode: Literal["off", "force", "auto", "cache"] = dc.field(
        default="auto",
        metadata={
            "validator": in_(
                [
                    "off",
                    "auto",
                    "force",
                    "cache",
                ]
            ),
            "help": "Execution mode for notebooks",
            "legacy_name": "jupyter_execute_notebooks",
        },
    )
    execution_cache_path: str = dc.field(
        default="",  # No default, so that sphinx can set it inside outdir, if empty
        metadata={
            "validator": instance_of(str),
            "help": "Path to folder for caching notebooks",
            "legacy_name": "jupyter_cache",
        },
    )
    execution_excludepatterns: Sequence[str] = dc.field(
        default=(),
        metadata={
            "validator": deep_iterable(instance_of(str)),
            "help": "Exclude (POSIX) glob patterns for notebooks",
            "legacy_name": "execution_excludepatterns",
            "docutils_exclude": True,
        },
    )
    execution_timeout: int = dc.field(
        default=30,
        metadata={
            "validator": instance_of(int),
            "help": "Execution timeout (seconds)",
            "legacy_name": "execution_timeout",
        },
    )
    execution_in_temp: bool = dc.field(
        default=False,
        metadata={
            "validator": instance_of(bool),
            "help": "Use temporary folder for the execution current working directory",
            "legacy_name": "execution_in_temp",
        },
    )
    execution_allow_errors: bool = dc.field(
        default=False,
        metadata={
            "validator": instance_of(bool),
            "help": "Allow errors during execution",
            "legacy_name": "execution_allow_errors",
        },
    )
    execution_show_tb: bool = dc.field(  # TODO implement
        default=False,
        metadata={
            "validator": instance_of(bool),
            "help": "Print traceback to stderr on execution error",
            "legacy_name": "execution_show_tb",
        },
    )

    # pre-processing options

    merge_streams: bool = dc.field(
        default=False,
        metadata={
            "validator": instance_of(bool),
            "help": "Merge stdout/stderr execution output streams",
            "cell_metadata": True,
        },
    )

    # render options

    render_plugin: str = dc.field(
        default="default",
        metadata={
            "validator": instance_of(str),
            "help": "The entry point for the execution output render class "
            "(in group `myst_nb.output_renderer`)",
        },
    )
    cell_render_key: str = dc.field(
        default="render",
        metadata={
            "validator": instance_of(str),
            "help": "Cell level metadata key to use for render config",
            "legacy_name": "nb_render_key",
        },
    )
    remove_code_source: bool = dc.field(
        default=False,
        metadata={
            "validator": instance_of(bool),
            "help": "Remove code cell source",
            "cell_metadata": True,
        },
    )
    remove_code_outputs: bool = dc.field(
        default=False,
        metadata={
            "validator": instance_of(bool),
            "help": "Remove code cell outputs",
            "cell_metadata": True,
        },
    )
    number_source_lines: bool = dc.field(
        default=False,
        metadata={
            "validator": instance_of(bool),
            "help": "Number code cell source lines",
            "cell_metadata": True,
        },
    )
    # we cannot directly obtain a sphinx builder name from docutils,
    # so must set it manually
    builder_name: str = dc.field(
        default="html",
        metadata={
            "validator": instance_of(str),
            "help": "Builder name, to select render priority for mime types",
            "sphinx_exclude": True,
        },
        repr=False,
    )
    mime_priority_overrides: Sequence[Tuple[str, str, Optional[int]]] = dc.field(
        default=(),
        metadata={
            "validator": deep_iterable(instance_of(tuple)),  # TODO better validation
            "help": "Overrides for the base render priority of mime types: "
            "list of (builder name, mime type, priority)",
            # TODO how to allow this in docutils?
            "docutils_exclude": True,
        },
        repr=False,
    )
    output_stderr: Literal[
        "show", "remove", "remove-warn", "warn", "error", "severe"
    ] = dc.field(
        default="show",
        metadata={
            "validator": in_(
                [
                    "show",
                    "remove",
                    "remove-warn",
                    "warn",
                    "error",
                    "severe",
                ]
            ),
            "help": "Behaviour for stderr output",
            "cell_metadata": True,
        },
    )
    render_text_lexer: str = dc.field(
        default="myst-ansi",
        # TODO allow None -> "none"?
        # TODO check it can be loaded?
        metadata={
            "validator": optional(instance_of(str)),
            "help": "Pygments lexer applied to stdout/stderr and text/plain outputs",
            "cell_metadata": "text_lexer",
        },
    )
    render_error_lexer: str = dc.field(
        default="ipythontb",
        # TODO allow None -> "none"?
        # TODO check it can be loaded?
        metadata={
            "validator": optional(instance_of(str)),
            "help": "Pygments lexer applied to error/traceback outputs",
            "cell_metadata": "error_lexer",
        },
    )
    render_image_options: Dict[str, str] = dc.field(
        default_factory=dict,
        # see https://docutils.sourceforge.io/docs/ref/rst/directives.html#image
        metadata={
            "validator": deep_mapping(instance_of(str), instance_of((str, int))),
            "help": "Options for image outputs (class|alt|height|width|scale|align)",
            "docutils_exclude": True,
            # TODO backward-compatible change to "image_options"?
            "cell_metadata": "image",
        },
    )
    render_markdown_format: Literal["commonmark", "gfm", "myst"] = dc.field(
        default="commonmark",
        metadata={
            "validator": in_(["commonmark", "gfm", "myst"]),
            "help": "The format to use for text/markdown rendering",
            "cell_metadata": "markdown_format",
        },
    )
    # TODO jupyter_sphinx_require_url and jupyter_sphinx_embed_url (undocumented),
    # are no longer used by this package, replaced by ipywidgets_js
    # do we add any deprecation warnings?
    ipywidgets_js: Dict[str, Dict[str, str]] = dc.field(
        default_factory=ipywidgets_js_factory,
        metadata={
            "validator": deep_mapping(
                instance_of(str), deep_mapping(instance_of(str), instance_of(str))
            ),
            "help": "Javascript to be loaded on pages containing ipywidgets",
            "docutils_exclude": True,
        },
        repr=False,
    )

    # write options for docutils
    output_folder: str = dc.field(
        default="build",
        metadata={
            "validator": instance_of(str),
            "help": "Folder for external outputs (like images), skipped if empty",
            "sphinx_exclude": True,  # in sphinx we always output to the build folder
        },
    )
    append_css: bool = dc.field(
        default=True,
        metadata={
            "validator": instance_of(bool),
            "help": "Add default MyST-NB CSS to HTML outputs",
            "sphinx_exclude": True,
        },
    )
    metadata_to_fm: bool = dc.field(
        default=False,
        metadata={
            "validator": instance_of(bool),
            "help": "Convert unhandled metadata to frontmatter",
            "sphinx_exclude": True,
        },
    )

    @classmethod
    def get_fields(cls) -> Tuple[dc.Field, ...]:
        return dc.fields(cls)

    def as_dict(self, dict_factory=dict) -> dict:
        return dc.asdict(self, dict_factory=dict_factory)

    def as_triple(self) -> Iterable[Tuple[str, Any, dc.Field]]:
        """Yield triples of (name, value, field)."""
        fields = {f.name: f for f in dc.fields(self.__class__)}
        for name, value in dc.asdict(self).items():
            yield name, value, fields[name]

    def copy(self, **changes) -> "NbParserConfig":
        """Return a copy of the configuration with optional changes applied."""
        return dc.replace(self, **changes)

    def __getitem__(self, field: str) -> Any:
        """Get a field value by name."""
        if field in ("get_fields", "as_dict", "as_triple", "copy"):
            raise KeyError(field)
        try:
            return getattr(self, field)
        except AttributeError:
            raise KeyError(field)

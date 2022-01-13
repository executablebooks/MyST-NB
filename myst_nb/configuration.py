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


@attr.s()
class NbParserConfig:
    """Global configuration options for the MyST-NB parser.

    Note: in the docutils/sphinx configuration,
    these option names are prepended with ``nb_``
    """

    # file read options

    custom_formats: Dict[str, Tuple[str, dict, bool]] = attr.ib(
        factory=dict,
        converter=custom_formats_converter,
        metadata={
            "help": "Custom formats for reading notebook; suffix -> reader",
            "docutils_exclude": True,
        },
    )
    # docutils does not support the custom formats mechanism
    read_as_md: bool = attr.ib(
        default=False,
        validator=instance_of(bool),
        metadata={
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
    metadata_key: str = attr.ib(
        default="mystnb",  # TODO agree this as the default
        validator=instance_of(str),
        metadata={"help": "Notebook level metadata key for config overrides"},
    )

    # notebook execution options

    execution_mode: Literal["off", "force", "auto", "cache", "inline"] = attr.ib(
        default="auto",
        validator=in_(
            [
                "off",
                "auto",
                "force",
                "cache",
                "inline",
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
    execution_excludepatterns: Sequence[str] = attr.ib(
        default=(),
        validator=deep_iterable(instance_of(str)),
        metadata={
            "help": "Exclude (POSIX) glob patterns for notebooks",
            "legacy_name": "execution_excludepatterns",
            "docutils_exclude": True,
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

    # pre-processing options

    merge_streams: bool = attr.ib(
        default=False,
        validator=instance_of(bool),
        metadata={
            "help": "Merge stdout/stderr execution output streams",
            "cell_metadata": True,
        },
    )

    # render options

    render_plugin: str = attr.ib(
        default="default",
        validator=instance_of(str),  # TODO check it can be loaded?
        metadata={
            "help": "The entry point for the execution output render class "
            "(in group `myst_nb.output_renderer`)"
        },
    )
    cell_render_key: str = attr.ib(
        default="render",
        validator=instance_of(str),
        metadata={
            "help": "Cell level metadata key to use for render config",
            "legacy_name": "nb_render_key",
        },
    )
    remove_code_source: bool = attr.ib(
        default=False,
        validator=instance_of(bool),
        metadata={"help": "Remove code cell source", "cell_metadata": True},
    )
    remove_code_outputs: bool = attr.ib(
        default=False,
        validator=instance_of(bool),
        metadata={"help": "Remove code cell outputs", "cell_metadata": True},
    )
    number_source_lines: bool = attr.ib(
        default=False,
        validator=instance_of(bool),
        metadata={"help": "Number code cell source lines", "cell_metadata": True},
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
        metadata={
            "help": "Render priority for mime types",
            "sphinx_exclude": True,
            "cell_metadata": True,
        },
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
        metadata={"help": "Behaviour for stderr output", "cell_metadata": True},
    )
    render_text_lexer: str = attr.ib(
        default="myst-ansi",
        # TODO allow None -> "none"?
        validator=optional(instance_of(str)),  # TODO check it can be loaded?
        metadata={
            "help": "Pygments lexer applied to stdout/stderr and text/plain outputs",
            "cell_metadata": "text_lexer",
        },
    )
    render_error_lexer: str = attr.ib(
        default="ipythontb",
        # TODO allow None -> "none"?
        validator=optional(instance_of(str)),  # TODO check it can be loaded?
        metadata={
            "help": "Pygments lexer applied to error/traceback outputs",
            "cell_metadata": "error_lexer",
        },
    )
    render_image_options: Dict[str, str] = attr.ib(
        factory=dict,
        validator=deep_mapping(instance_of(str), instance_of((str, int))),
        # see https://docutils.sourceforge.io/docs/ref/rst/directives.html#image
        metadata={
            "help": "Options for image outputs (class|alt|height|width|scale|align)",
            "docutils_exclude": True,
            # TODO backward-compatible change to "image_options"?
            "cell_metadata": "image",
        },
    )
    render_markdown_format: Literal["commonmark", "gfm", "myst"] = attr.ib(
        default="commonmark",
        validator=in_(["commonmark", "gfm", "myst"]),
        metadata={
            "help": "The format to use for text/markdown rendering",
            "cell_metadata": "markdown_format",
        },
    )
    # TODO jupyter_sphinx_require_url and jupyter_sphinx_embed_url (undocumented),
    # are no longer used by this package, replaced by ipywidgets_js
    # do we add any deprecation warnings?
    ipywidgets_js: Dict[str, Dict[str, str]] = attr.ib(
        factory=ipywidgets_js_factory,
        validator=deep_mapping(
            instance_of(str), deep_mapping(instance_of(str), instance_of(str))
        ),
        metadata={
            "help": "Javascript to be loaded on pages containing ipywidgets",
            "docutils_exclude": True,
        },
        repr=False,
    )

    # write options for docutils
    output_folder: str = attr.ib(
        default="build",
        validator=instance_of(str),
        metadata={
            "help": "Folder for external outputs (like images), skipped if empty",
            "sphinx_exclude": True,  # in sphinx we always output to the build folder
        },
    )
    append_css: bool = attr.ib(
        default=True,
        validator=instance_of(bool),
        metadata={
            "help": "Add default MyST-NB CSS to HTML outputs",
            "sphinx_exclude": True,
        },
    )
    metadata_to_fm: bool = attr.ib(
        default=False,
        validator=instance_of(bool),
        metadata={
            "help": "Convert unhandled metadata to frontmatter",
            "sphinx_exclude": True,
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

    def __getitem__(self, field: str) -> Any:
        """Get a field value by name."""
        if field in ("get_fields", "as_dict", "as_triple", "copy"):
            raise KeyError(field)
        try:
            return getattr(self, field)
        except AttributeError:
            raise KeyError(field)

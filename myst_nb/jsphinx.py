"""Replacements for jupyter-sphinx"""
import os
import warnings
from pathlib import Path

# TODO pin nbconvert version?
import nbconvert
import nbformat
from nbconvert.preprocessors import ExtractOutputPreprocessor
from nbconvert.writers import FilesWriter

# from ipywidgets (7.6.5)
_HTML_MANGER_URL = "https://unpkg.com/@jupyter-widgets/html-manager@^0.20.0"
DEFAULT_EMBED_SCRIPT_URL = f"{_HTML_MANGER_URL}/dist/embed.js"
DEFAULT_EMBED_REQUIREJS_URL = f"{_HTML_MANGER_URL}/dist/embed-amd.js"
snippet_template = """
{load}
<script type="application/vnd.jupyter.widget-state+json">
{json_data}
</script>
{widget_views}
"""
widget_view_template = """<script type="application/vnd.jupyter.widget-view+json">
{view_spec}
</script>"""

# from jupyter-sphinx (0.3.2)
REQUIRE_URL_DEFAULT = (
    "https://cdnjs.cloudflare.com/ajax/libs/require.js/2.3.4/require.min.js"
)

WIDGET_STATE_MIMETYPE = "application/vnd.jupyter.widget-state+json"
WIDGET_VIEW_MIMETYPE = "application/vnd.jupyter.widget-view+json"


def sphinx_abs_dir(env, *paths):
    # We write the output files into
    # output_directory / jupyter_execute / path relative to source directory
    # Sphinx expects download links relative to source file or relative to
    # source dir and prepended with '/'. We use the latter option.
    out_path = (
        output_directory(env) / Path(env.docname).parent / Path(*paths)
    ).resolve()

    if os.name == "nt":
        # Can't get relative path between drives on Windows
        return out_path.as_posix()

    # Path().relative_to() doesn't work when not a direct subpath
    return "/" + os.path.relpath(out_path, env.app.srcdir)


def output_directory(env):
    # Put output images inside the sphinx build directory to avoid
    # polluting the current working directory. We don't use a
    # temporary directory, as sphinx may cache the doctree with
    # references to the images that we write

    # Note: we are using an implicit fact that sphinx output directories are
    # direct subfolders of the build directory.
    # TODO change this?
    return (Path(env.app.outdir) / os.path.pardir / "jupyter_execute").resolve()


def strip_latex_delimiters(source):
    r"""Remove LaTeX math delimiters that would be rendered by the math block.

    These are: ``\(…\)``, ``\[…\]``, ``$…$``, and ``$$…$$``.
    This is necessary because sphinx does not have a dedicated role for
    generic LaTeX, while Jupyter only defines generic LaTeX output, see
    https://github.com/jupyter/jupyter-sphinx/issues/90 for discussion.
    """
    source = source.strip()
    delimiter_pairs = (pair.split() for pair in r"\( \),\[ \],$$ $$,$ $".split(","))
    for start, end in delimiter_pairs:
        if source.startswith(start) and source.endswith(end):
            return source[len(start) : -len(end)]

    return source


def get_widgets(notebook):
    try:
        return notebook.metadata.widgets[WIDGET_STATE_MIMETYPE]
    except AttributeError:
        # Don't catch KeyError, as it's a bug if 'widgets' does
        # not contain 'WIDGET_STATE_MIMETYPE'
        return None


def contains_widgets(notebook):
    widgets = get_widgets(notebook)
    return widgets and widgets["state"]


def write_notebook_output(notebook, output_dir, notebook_name, location=None):
    """Extract output from notebook cells and write to files in output_dir.

    This also modifies 'notebook' in-place, adding metadata to each cell that
    maps output mime-types to the filenames the output was saved under.
    """
    resources = dict(unique_key=os.path.join(output_dir, notebook_name), outputs={})

    # Modifies 'resources' in-place
    ExtractOutputPreprocessor().preprocess(notebook, resources)
    # Write the cell outputs to files where we can (images and PDFs),
    # as well as the notebook file.
    FilesWriter(build_directory=output_dir).write(
        nbformat.writes(notebook),
        resources,
        os.path.join(output_dir, notebook_name + ".ipynb"),
    )

    exporter = nbconvert.exporters.ScriptExporter(
        #  TODO:log=LoggerAdapterWrapper(js.logger)
    )
    with warnings.catch_warnings():
        # See https://github.com/jupyter/nbconvert/issues/1388
        warnings.simplefilter("ignore", DeprecationWarning)
        contents, resources = exporter.from_notebook_node(notebook)

    notebook_file = notebook_name + resources["output_extension"]
    output_dir = Path(output_dir)
    # utf-8 is the de-facto standard encoding for notebooks.
    (output_dir / notebook_file).write_text(contents, encoding="utf8")

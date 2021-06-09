import IPython
from IPython.display import display as ipy_display

GLUE_PREFIX = "application/papermill.record/"


def glue(name, variable, display=True):
    """Glue an variable into the notebook's cell metadata.

    Parameters
    ----------
    name: string
        A unique name for the variable. You can use this name to refer to the variable
        later on.
    variable: python object
        A variable in Python for which you'd like to store its display value. This is
        not quite the same as storing the object itself - the stored information is
        what is *displayed* when you print or show the object in a Jupyter Notebook.
    display: bool
        Display the object you are gluing. This is helpful in sanity-checking the
        state of the object at glue-time.
    """
    mime_prefix = "" if display else GLUE_PREFIX
    metadata = {"scrapbook": dict(name=name, mime_prefix=mime_prefix)}
    if "bokeh" in type(variable).__module__:
        # import here to avoid a hard dependency on bokeh
        from bokeh.embed import json_item
        import json

        bokeh_json = json_item(variable, name)
        bokeh_version = bokeh_json.get("doc", {}).get("version", None)
        metadata["scrapbook"]["bokeh_version"] = bokeh_version
        ipy_display(
            {
                mime_prefix
                + "application/jupyter-book-bokeh-json": json.dumps(
                    bokeh_json, separators=(",", ":")
                )
            },
            raw=True,
            metadata=metadata,
        )

    else:
        mimebundle, meta = IPython.core.formatters.format_display_data(variable)
        metadata.update(meta)
        ipy_display(
            {mime_prefix + k: v for k, v in mimebundle.items()},
            raw=True,
            metadata=metadata,
        )

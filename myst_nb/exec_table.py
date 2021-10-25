"""A directive to create a table of executed notebooks, and related statistics.

This directive utilises the
``env.nb_execution_data`` and ``env.nb_execution_data_changed`` variables,
set by myst-nb, to produce a table of statistics,
which will be updated when any notebooks are modified/removed.
"""
from datetime import datetime

from docutils import nodes
from sphinx.transforms import SphinxTransform
from sphinx.transforms.post_transforms import SphinxPostTransform
from sphinx.util import logging
from sphinx.util.docutils import SphinxDirective

LOGGER = logging.getLogger(__name__)


def setup_exec_table(app):
    """execution statistics table."""
    app.add_node(ExecutionStatsNode)
    app.add_directive("nb-exec-table", ExecutionStatsTable)
    app.add_transform(ExecutionStatsTransform)
    app.add_post_transform(ExecutionStatsPostTransform)
    app.connect("builder-inited", add_doc_tracker)
    app.connect("env-purge-doc", remove_doc)
    app.connect("env-updated", update_exec_tables)


def add_doc_tracker(app):
    """This variable keeps track of want documents contain
    an `nb-exec-table` directive.
    """
    if not hasattr(app.env, "docs_with_exec_table"):
        app.env.docs_with_exec_table = set()


def remove_doc(app, env, docname):
    env.docs_with_exec_table.discard(docname)


def update_exec_tables(app, env):
    """If the execution data has changed,
    this callback adds the list of documents containing an `nb-exec-table` directive
    to the list of document that are outdated.
    """
    if not (env.nb_execution_data_changed and env.docs_with_exec_table):
        return None
    if env.docs_with_exec_table:
        LOGGER.info("Updating `nb-exec-table`s in: %s", env.docs_with_exec_table)
    return list(env.docs_with_exec_table)


class ExecutionStatsNode(nodes.General, nodes.Element):
    """A placeholder node, for adding a notebook execution statistics table."""


class ExecutionStatsTable(SphinxDirective):
    """Add a notebook execution statistics table."""

    has_content = True
    final_argument_whitespace = True

    def run(self):

        return [ExecutionStatsNode()]


class ExecutionStatsTransform(SphinxTransform):
    """Updates the list of documents containing an `nb-exec-table` directive."""

    default_priority = 400

    def apply(self):
        self.env.docs_with_exec_table.discard(self.env.docname)
        for _ in self.document.traverse(ExecutionStatsNode):
            self.env.docs_with_exec_table.add(self.env.docname)
            break


class ExecutionStatsPostTransform(SphinxPostTransform):
    """Replace the placeholder node with the final table nodes."""

    default_priority = 400

    def run(self, **kwargs) -> None:
        for node in self.document.traverse(ExecutionStatsNode):
            node.replace_self(make_stat_table(self.env.nb_execution_data))


def make_stat_table(nb_execution_data):

    key2header = {
        "mtime": "Modified",
        "method": "Method",
        "runtime": "Run Time (s)",
        "succeeded": "Status",
    }

    key2transform = {
        "mtime": lambda x: datetime.fromtimestamp(x).strftime("%Y-%m-%d %H:%M")
        if x
        else "",
        "method": str,
        "runtime": lambda x: "-" if x is None else str(round(x, 2)),
        "succeeded": lambda x: "✅" if x is True else "❌",
    }

    # top-level element
    table = nodes.table()
    table["classes"] += ["colwidths-auto"]
    # self.set_source_info(table)

    # column settings element
    ncols = len(key2header) + 1
    tgroup = nodes.tgroup(cols=ncols)
    table += tgroup
    colwidths = [round(100 / ncols, 2)] * ncols
    for colwidth in colwidths:
        colspec = nodes.colspec(colwidth=colwidth)
        tgroup += colspec

    # header
    thead = nodes.thead()
    tgroup += thead
    row = nodes.row()
    thead += row

    for name in ["Document"] + list(key2header.values()):
        row.append(nodes.entry("", nodes.paragraph(text=name)))

    # body
    tbody = nodes.tbody()
    tgroup += tbody

    for docname in sorted(nb_execution_data.keys()):
        data = nb_execution_data[docname]
        row = nodes.row()
        tbody += row
        row.append(nodes.entry("", nodes.paragraph(text=docname)))
        for name in key2header.keys():
            text = key2transform[name](data[name])
            row.append(nodes.entry("", nodes.paragraph(text=text)))

    return table

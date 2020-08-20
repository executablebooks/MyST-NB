"""A directive to create a table of executed notebooks, and related statistics."""
from datetime import datetime

from docutils import nodes
from sphinx.transforms.post_transforms import SphinxPostTransform
from sphinx.util.docutils import SphinxDirective


def setup_exec_table(app):
    """execution statistics table."""
    app.add_node(ExecutionStatsNode)
    app.add_directive("nb-exec-table", ExecutionStatsTable)
    app.add_post_transform(ExecutionStatsPostTransform)


class ExecutionStatsNode(nodes.General, nodes.Element):
    """A placeholder node, for adding a notebook execution statistics table."""


class ExecutionStatsTable(SphinxDirective):
    """Add a notebook execution statistics table."""

    has_content = True
    final_argument_whitespace = True

    def run(self):

        return [ExecutionStatsNode()]


class ExecutionStatsPostTransform(SphinxPostTransform):
    """Replace the placeholder node with the final table."""

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
        "mtime": lambda x: datetime.fromtimestamp(x).strftime("%Y-%m-%d %H:%M"),
        "method": str,
        "runtime": lambda x: str(round(x, 2)),
        "succeeded": lambda x: "✅" if x else "❌",
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

    for doc, data in nb_execution_data.items():
        row = nodes.row()
        tbody += row
        row.append(nodes.entry("", nodes.paragraph(text=doc)))
        for name in key2header.keys():
            row.append(
                nodes.entry("", nodes.paragraph(text=key2transform[name](data[name])))
            )

    return table

from textwrap import dedent
import nbformat
from myst_nb.convert import myst_to_nb


def test_basic(file_regression):
    text = dedent(
        """\
        ---
        orphan: true
        ---

        a

        b
        c
        ```{nb-cell}
        a = 1
        print(a)
        ```

        c

        +++ {"tags": ["hide-cell"]}

        d

        """
    )
    notebook = myst_to_nb(text, directive="nb-cell")
    file_regression.check(nbformat.writes(notebook), extension=".ipynb")

from pathlib import Path

import nbformat
from myst_nb.convert import myst_to_nb, nb_to_myst

SOURCEDIR = Path(__file__).parent.joinpath("roundtrip")


def test_myst_to_nb(file_regression):
    text = SOURCEDIR.joinpath("basic.mystnb").read_text()
    notebook = myst_to_nb(text, directive="nb-code")
    file_regression.check(
        nbformat.writes(notebook), fullpath=SOURCEDIR.joinpath("basic.ipynb")
    )


def test_nb_to_myst(file_regression):
    text = SOURCEDIR.joinpath("basic.ipynb").read_text()
    output = nb_to_myst(nbformat.reads(text, 4), directive="nb-code")
    file_regression.check(output, fullpath=SOURCEDIR.joinpath("basic.mystnb"))

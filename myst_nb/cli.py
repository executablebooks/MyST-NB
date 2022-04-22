"""A basic CLI for quickstart of a myst_nb project."""
from __future__ import annotations

import argparse
from pathlib import Path
from textwrap import indent

import nbformat

from .core.config import NbParserConfig


def quickstart(args: list[str] | None = None):
    """Quickstart myst_nb project."""
    namespace = create_quickstart_cli().parse_args(args)
    path = Path(namespace.path).resolve()
    verbose: bool = namespace.verbose
    overwrite: bool = namespace.overwrite
    if path.exists():
        if not overwrite:
            raise FileExistsError(f"{path} already exists.")
        if verbose:
            print(f"Overwriting existing files in: {path}")
    # create directory
    path.mkdir(parents=True, exist_ok=True)
    # write .gitignore
    (path / ".gitignore").write_text(".ipynb_checkpoints\n_build\n", encoding="utf-8")
    # write conf.py
    (path / "conf.py").write_text(generate_conf_py(), encoding="utf-8")
    # write index.md
    (path / "index.md").write_text(
        generate_index(["notebook1", "notebook2"]), encoding="utf-8"
    )
    # write notebook1.ipynb
    (path / "notebook1.ipynb").write_text(generate_jupyter_notebook(), encoding="utf-8")
    # write notebook2.md
    (path / "notebook2.md").write_text(generate_text_notebook(), encoding="utf-8")

    print(f"Created myst_nb project at: {path}")


def create_quickstart_cli():
    cli = argparse.ArgumentParser(description="Create a basic myst_nb project.")
    cli.add_argument(
        "path", metavar="PATH", type=str, help="Directory to output the project."
    )
    cli.add_argument(
        "-o", "--overwrite", action="store_true", help="Overwrite existing files."
    )
    cli.add_argument("-v", "--verbose", action="store_true", help="Increase verbosity.")
    return cli


def generate_conf_py() -> str:
    """Generate `conf.py` content."""
    content = (
        """\
# outline for a myst_nb project with sphinx
# build with: sphinx-build -nW --keep-going -b html . ./_build/html

# load extensions
extensions = ["myst_nb"]

# specify project details
master_doc = "index"
project = "MyST-NB Quickstart"

# basic build settings
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store", "**.ipynb_checkpoints"]
nitpicky = True

## myst_nb default settings
    """.rstrip()
        + "\n"
    )

    settings = ""
    config = NbParserConfig()
    for name, value, field in config.as_triple():
        if field.metadata.get("sphinx_exclude"):
            continue
        if field.metadata.get("help"):
            settings += f'{field.metadata.get("help")}\n'
        settings += f"nb_{name} = {value!r}\n\n"
    content += "\n" + indent(settings, "# ").rstrip() + "\n"

    return content


def generate_index(children: list[str]) -> str:
    """Generate `index.md` content."""
    children_str = "\n".join(children)
    content = (
        f"""\
# MyST-NB Quickstart

```{{toctree}}
{children_str}
```
    """.rstrip()
        + "\n"
    )
    return content


def generate_jupyter_notebook() -> str:
    """Generate `notebook.ipynb` content."""
    nb = nbformat.v4.new_notebook()
    nb["metadata"] = {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3",
        },
    }
    nb["cells"] = [
        nbformat.v4.new_markdown_cell("# Jupyter Notebook"),
        nbformat.v4.new_code_cell("print('Hello, World!')"),
    ]
    return nbformat.writes(nb)


def generate_text_notebook() -> str:
    """Generate `notebook.md` content."""
    content = (
        """\
---
file_format: mystnb
kernelspec:
  name: python3
  language: python
  display_name: Python 3
---

# Text-based Notebook

```{code-cell}
print("Hello, World!")
```
    """.rstrip()
        + "\n"
    )
    return content

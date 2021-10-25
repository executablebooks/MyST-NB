# Get started

This section covers how to get started with the `MyST-NB` Sphinx extension.
The Sphinx extension allows you to read markdown (`.md`) and Jupyter Notebook (`.ipynb`) files into your Sphinx site.
It also enables you to write [MyST Markdown](myst.md) in your pages.

To get started with the extension, follow these steps.

* **Install** `myst-nb` with the following command:

  ```console
  $ pip install myst-nb
  ```

* **Activate** the `myst_nb` extension in your Sphinx site by adding it to your list of
  Sphinx extensions in `conf.py`:

  ```python
  extensions = [
      ...,
      "myst_nb"
  ]
  ```

* **Add MyST and notebook content** to your documentation's source files.
  Sphinx will now be able to parse **markdown files** written in [MyST Markdown](https://myst-parser.readthedocs.io), Jupyter Notebooks (ending in `.ipynb`), and [Jupyter Notebooks written in plain-text with MyST markdown](markdown.md).
  Make sure to include paths to your content in a Sphinx `toctree` directive!

* **Build your documentation**. MyST-NB will now parse any markdown (`.md`), Jupyter notebooks (`.ipynb`), and [text-based Notebooks](markdown.md) (`.md`) into your Sphinx site, and include them in the outputs.

## Next steps

There is a lot more that you can do with MyST-NB.
For example, you can define [custom text-based notebook formats](examples/custom_formats), [execute and cache notebook content](execute.md), and [format cell outputs](formatting_outputs.md).

Check out the sections to the left under [Using with Sphinx](index.md) for more information.

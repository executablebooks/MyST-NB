# Get started

This section covers how to get started with the `MyST-NB` Sphinx extension.
The Sphinx extension allows you to read markdown (`.md`) and Jupyter Notebook (`.ipynb`)
files into your Sphinx site. It also enables you to write [MyST Markdown](myst.md)
in your pages.

## Install and activate

To install `myst-nb`, do the following:

* **Install** `myst-nb` with the following command:

  ```bash
  pip install myst-nb
  ```

* **Activate** the `myst_nb` extension in your Sphinx site by adding it to your list of
  Sphinx extensions in `conf.py`:

  ```python
  extensions = [
      ...,
      "myst_nb"
  ]
  ```

Once you do this, MyST-NB will now parse both markdown (`.md`) and
Jupyter notebooks (`.ipynb`) into your Sphinx site.

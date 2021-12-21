"""A docutils/sphinx parser for Jupyter Notebooks."""
__version__ = "0.13.1"


def setup(app):
    """Sphinx extension setup."""
    # we import this locally, so sphinx is not automatically imported
    from .extension import sphinx_setup

    return sphinx_setup(app)

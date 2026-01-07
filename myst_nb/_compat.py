from typing import Any

from docutils.nodes import Element


def findall(node: Element):
    # findall replaces traverse in docutils v0.18
    # note a difference is that findall is an iterator
    return getattr(node, "findall", node.traverse)


def get_env_app(env: Any):
    """Return the Sphinx app without triggering deprecated accessors."""
    # This is the new Sphinx app behavior
    app = getattr(env, "_app", None)
    if app is None:
        # This was removed in Sphinx 9
        app = env.app
    return app

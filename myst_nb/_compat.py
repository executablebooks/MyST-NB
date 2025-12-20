from typing import Any

from docutils.nodes import Element


def findall(node: Element):
    # findall replaces traverse in docutils v0.18
    # note a difference is that findall is an iterator
    return getattr(node, "findall", node.traverse)


def get_env_app(env: Any):
    """Return the Sphinx app without triggering deprecated accessors."""
    app = getattr(env, "_app", None)
    if app is None:
        app = env.app
    return app

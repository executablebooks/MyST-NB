.. _api/main:

Python API
==========

The parsing of a notebook consists of a number of stages, with each stage separated into a separate module:

1. The configuration is set (from a file or CLI)
2. The parser is called with an input string and source
3. The parser reads the input string to a notebook node
4. The notebook code outputs are potentially updated, via execution or from a cache
5. The notebook is "pre-processed" in-place (e.g. to coalesce output streams and extract glue outputs)
6. The notebook is converted to a Markdown-It tokens syntax tree
7. The syntax tree is transformed to a docutils document AST (calling the renderer plugin)
8. The docutils document is processed by docutils/sphinx, to create the desired output format(s)

Configuration
-------------

.. autoclass:: myst_nb.core.config.NbParserConfig
    :members:

Parsers
-------

.. autoclass:: myst_nb.docutils_.Parser
    :members:

.. autoclass:: myst_nb.sphinx_.Parser
    :members:

Read
----

.. autoclass:: myst_nb.core.read.NbReader
    :members:

.. autofunction:: myst_nb.core.read.create_nb_reader

.. autofunction:: myst_nb.core.read.is_myst_markdown_notebook

.. autofunction:: myst_nb.core.read.read_myst_markdown_notebook

Execute
-------

.. autoclass:: myst_nb.core.execute.ExecutionResult
    :members:

.. autofunction:: myst_nb.core.execute.execute_notebook

Pre-process
-----------

.. autofunction:: myst_nb.core.preprocess.preprocess_notebook

Render plugin
-------------

.. autoclass:: myst_nb.core.render.MimeData
    :members:

.. autoclass:: myst_nb.core.render.NbElementRenderer
    :members:

.. autoclass:: myst_nb.core.render.MimeRenderPlugin
    :members:
    :undoc-members:

.. autoclass:: myst_nb.core.render.ExampleMimeRenderPlugin
    :members:
    :undoc-members:

Lexers
------

.. autoclass:: myst_nb.core.lexers.AnsiColorLexer
    :members:
    :undoc-members:
    :show-inheritance:

Loggers
-------

.. autoclass:: myst_nb.core.loggers.DocutilsDocLogger
    :members:
    :undoc-members:
    :show-inheritance:


.. autoclass:: myst_nb.core.loggers.SphinxDocLogger
    :members:
    :undoc-members:
    :show-inheritance:

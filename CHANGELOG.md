# Change Log

## v0.15.0 - 2022-05-05

[Full changelog](https://github.com/executablebooks/MyST-NB/compare/v0.14.0...v0.15.0)

✨ NEW: Add `inline` execution mode and `eval` role/directive, for inserting code variables directly into the text flow of your documentation!
See [Inline variable evaluation](docs/render/inline.md) for more information.

## v0.14.0 - 2022-04-27

[Full changelog](https://github.com/executablebooks/MyST-NB/compare/v0.13.2...v0.14.0)

This release encompasses a **major** rewrite of the entire library and its documentation, primarily in [#380](https://github.com/executablebooks/MyST-NB/pull/380) and [#405](https://github.com/executablebooks/MyST-NB/pull/405).

### Breaking Changes ‼️

#### Configuration

A number of configuration option names have been changed, such that they now share the `nb_` prefix.
Most of the deprecated names will be auto-converted at the start of the build, emitting a warning such as:

```
WARNING: 'jupyter_execute_notebooks' is deprecated for 'nb_execution_mode' [mystnb.config]
```

`nb_render_priority` has been removed and replaced by `nb_mime_priority_overrides`, which has a different format and is more flexible. See [Outputs MIME priority](docs/render/format_code_cells.md) for more information.

As per the changes in [`myst_parser`](myst:develop/_changelog), the `dollarmath` syntax extension is no longer included by default.
To re-add this extension, ensure that it is specified in your `conf.py`: `myst_enable_extensions = ["dollarmath"]`.

For cell-level configuration the top-level key `render` has now been deprecated for `mystnb`.
For example, replace:

````markdown
```{code-cell}
---
render:
  image:
    width: 200px
---
...
```
````

with:

````markdown
```{code-cell}
---
mystnb:
  image:
    width: 200px
---
...
```
````

`render` will currently still be read, if present, and will issue a `[mystnb.cell_metadata_key]` warning.

The `jupyter_sphinx_require_url` and `jupyter_sphinx_embed_url` configuration options are no longer used by this package, and are replaced by `nb_ipywidgets_js`.

See the [configuration section](docs/configuration.md) for more details.

#### Dependencies

The [ipywidgets](https://ipywidgets.readthedocs.io) package has been removed from the requirements.
If required, please install it specifically.

#### AST structure and rendering plugins

The structure of the docutils AST and nodes produced by MyST-NB has been fully changed, for compatibility with the new [docutils only functionality](docs/docutils.md).
See [the API documentation](docs/reference/api.rst) for more details.

The renderer plugin system (used by the `myst_nb.renderers` entry point) has also been completely rewritten,
so any current existing renderers will no longer work.
There is also now a new `myst_nb.mime_renderers` entry point, to allow for targeted rendering of specific code-cell output MIME types.
See [Customise the render process](docs/render/format_code_cells.md) for more information.

#### Glue functionality

By default, `glue` roles and directives now only work for keys within the same document.
To reference glued content in a different document, the `glue:any` directive allows for a `doc` option and `glue:any`/`glue:text` roles allow the (relative) doc path to be added, for example:

````markdown
```{glue:any} var_text
:doc: other.ipynb
```

{glue:text}`other.ipynb::var_float:.2E`
````

This cross-document functionality is currently restricted to only `text/plain` and `text/html` output MIME types, not images.

See [Embedding outputs as variables](docs/render/glue.md) for more details.

### Dependency changes ⬆️

- Removed:
  - `ipywidgets`
  - `jupyter_sphinx`
  - `nbconvert`
- Updated:
  - `Python`: `3.6+ -> 3.7+`
  - `myst_parser`: [`0.15 -> 0.17`](myst:develop/_changelog)
  - `jupyter-cache`: [`0.4 -> 0.5`](https://github.com/executablebooks/jupyter-cache/blob/master/CHANGELOG.md)
  - `sphinx-togglebutton`: [`0.1 -> 0.3`](https://sphinx-togglebutton.readthedocs.io/en/latest/changelog.html)

### New and improved ✨

The following is a non-exhaustive list of new features and improvements, see the rest of the documentation for all the changes.

- Multi-level configuration (global (`conf.py`) < notebook level metadata < cell level metadata)
  - Plus new config options including: `nb_number_source_lines`, `nb_remove_code_source`, `nb_remove_code_outputs`, `nb_render_error_lexer`, `nb_execution_raise_on_error`, `nb_kernel_rgx_aliases`
  - See the [configuration section](docs/configuration.md) for more details.

- Added `mystnb-quickstart` and `mystnb-to-jupyter` CLI commands.

- MyST text-based notebooks can now be specified by just:

  ```yaml
  ---
  file_format: mystnb
  kernelspec:
    name: python3
  ---
  ```

  as opposed to the alternative jupytext top-matter.
  See [Text-based Notebooks](docs/authoring/text-notebooks.md) for more details.

- docutils API/CLI with command line tools, e.g. `mystnb-docutils-html`
  - Includes `glue` roles and directives
  - See [single page builds](docs/docutils.md) for more details.

- Parallel friendly (e.g. `sphinx-build -j 4` can execute four notebooks in parallel)

- Page specific loading of ipywidgets JavaScript, i.e. only when ipywidgets are present in the notebook.

- Added raw cell rendering, with the `raw-cell` directive.
  See [Raw cells authoring](docs/authoring/jupyter-notebooks.md) for more details.

- Added MIME render plugins. See [Customise the render process](docs/render/format_code_cells.md) for more details.

- Better log info/warnings, with `type.subtype` specifiers for warning suppression.
  See [Warning suppression](docs/configuration.md) for more details.

- Reworked jupyter-cache integration to be easier to use (including parallel execution)

- Added image options to `glue:figure`

- New `glue:md` role/directive includes nested parsing of MyST Markdown.
  See [Embedding outputs as variables](docs/render/glue.md) for more details.

- Improved `nb-exec-table` directive (includes links to documents, etc)

### Additional Pull Requests

- 👌 IMPROVE: Update ANSI CSS colors by @saulshanabrook in [#384](https://github.com/executablebooks/MyST-NB/pull/384)
- ✨ NEW: Add `nb_execution_raise_on_error` config by @chrisjsewell in [#404](https://github.com/executablebooks/MyST-NB/pull/404)
- 👌 IMPROVE: Add image options to `glue:figure` by @chrisjsewell in [#403](https://github.com/executablebooks/MyST-NB/pull/403)

## v0.13.2 - 2022-02-10

This release improves for cell outputs and brings UI improvements for toggling cell inputs and outputs.
It also includes several bugfixes.

- Add CSS support for 8-bit ANSI colours [#379](https://github.com/executablebooks/MyST-NB/pull/379) ([@thiippal](https://github.com/thiippal))
- Use configured `nb_render_plugin` for glue nodes [#337](https://github.com/executablebooks/MyST-NB/pull/337) ([@bryanwweber](https://github.com/bryanwweber))
- UPGRADE: sphinx-togglebutton v0.3.0 [#390](https://github.com/executablebooks/MyST-NB/pull/390) ([@choldgraf](https://github.com/choldgraf))

## 0.13.1 - 2021-10-04

✨ NEW: `nb_merge_streams` configuration  [[PR #364](https://github.com/executablebooks/MyST-NB/pull/364)]

If `nb_merge_streams=True`, all stdout / stderr output streams are merged into single outputs. This ensures deterministic outputs.

## 0.13.0 - 2021-09-02

### Upgraded to `sphinx` v4 ⬆️

The primary change in this release is to update the requirements of myst-nb from `sphinx>=2,<4` to `sphinx>=3,<5` to
support `sphinx>=4` [[PR #356](https://github.com/executablebooks/MyST-NB/pull/356)].

- 👌 IMPROVE: Allows more complex suffixes in notebooks [[PR #328](https://github.com/executablebooks/MyST-NB/pull/328)]
- ⬆️ UPDATE: myst-parser to `0.15.2` [[PR #353](https://github.com/executablebooks/MyST-NB/pull/353)]
- ⬆️ UPGRADE: nbconvert 6 support [[PR #326](https://github.com/executablebooks/MyST-NB/pull/326)]
- ⬆️ UPGRADE: markdown-it-py v1.0 [[PR #320](https://github.com/executablebooks/MyST-NB/pull/320)]
- 🔧 MAINT: Pin ipykernel to ~v5.5 [[PR #347](https://github.com/executablebooks/MyST-NB/pull/347)]
- 🔧 MAINT: Make a more specific selector for no-border [[PR #344](https://github.com/executablebooks/MyST-NB/pull/344)]

Many thanks to @akhmerov, @bollwyvl, @choldgraf, @chrisjsewell, @juhuebner, @mmcky

## 0.12.1 - 2021-04-25

- ⬆️ UPDATE: jupyter_sphinx to `0.3.2`: fixes `Notebook code has no file extension metadata` warning)
- ⬆️ UPDATE: importlib_metadata to `3.6`: to use new entry point loading interface
- Official support for Python 3.9

(`0.12.2` and `0.12.3` fix a regression, when working with the entry point loading interface)

## 0.12.0 - 2021-02-23

This release adds an experimental MyST-NB feature to enable loading of code from a file
for `code-cell` directives using a `:load: <file>` option.

Usage information is available in the [docs](https://myst-nb.readthedocs.io/en/latest/use/markdown.html#syntax-for-code-cells)

## 0.11.1 - 2021-01-20

Minor update to handle MyST-Parser `v0.13.3` and `v4.5` notebooks.

## 0.11.0 - 2021-01-12

This release updates MyST-Parser to `v0.13`,
which is detailed in the [myst-parser changelog](https://myst-parser.readthedocs.io/en/latest/develop/_changelog.html).

The primary change is to the extension system, with extensions now all loaded *via* `myst_enable_extensions = ["dollarmath", ...]`,
and a number of extensions added or improved.

## 0.10.2 - 2021-01-12

Minor fixes:

- 🐛 FIX: empty myst file read
- 🐛 FIX: remove cell background-color CSS for cells
- 🔧 MAINTAIN: Pin jupyter-sphinx version

## 0.10.1 - 2020-09-08

⬆️ UPGRADE: myst-parser v0.12.9

: Minor bug fixes and enhancements / new features

## 0.10.0 - 2020-08-28

⬆️ UPGRADE: jupyter-sphinx v0.3, jupyter-cache v0.4.1 and nbclient v0.5.

: These upgrades allow for full Windows OS compatibility, and improve the stability of notebook execution on small machines.

👌 IMPROVE: Formatting of stderr is now similar to stdout, but with a slight red background.

🧪 TESTS: Add Windows CI

## 0.9.2 - 2020-08-27

⬆️ UPGRADE: myst-parser patch version

: to ensure a few new features and bug fixes are incorporated (see its [CHANGELOG.md](https://github.com/executablebooks/MyST-Parser/blob/master/CHANGELOG.md))

## 0.9.1 - 2020-08-24

More configuration!

- ✨ NEW: Add stderr global configuration: `nb_output_stderr`
  (see [removing stderr](https://myst-nb.readthedocs.io/en/latest/use/formatting_outputs.html#removing-stdout-and-stderr))
- ✨ NEW: Add `nb_render_key` configuration
  (see [formatting outputs](https://myst-nb.readthedocs.io/en/latest/use/formatting_outputs.html#images))
- 🐛 FIX: `auto` execution not recognising (and skipping) notebooks with existing outputs

## 0.9.0 - 2020-08-24

This versions see's many great changes; utilising the ⬆️ upgrade to `myst-parser=v0.12`
and accompanying ⬆️ upgrade to `sphinx=v3`,
as well as major refactors to the execution ([#236](https://github.com/executablebooks/MyST-NB/commit/2bc0c11cedbad6206f70546819fad85d779ce449)) and code output rendering ([#243](https://github.com/executablebooks/MyST-NB/commit/04f3bbb928cf1794e140de6a919fb58578753300)).
Plus much more configuration options, to allow for a more configurable workflow (the defaults work great as well!).

Below is a summary of the changes, and you can also check out many examples in the documentation, <https://myst-nb.readthedocs.io/>,
and the MyST-Parser Changelog for all the new Markdown parsing features available: <https://github.com/executablebooks/MyST-Parser>.

### New ✨

- Custom notebook formats:

  Configuration and logic has been added for designating additional file types to be converted to Notebooks, which are then executed & parsed in the same manner as regular Notebooks.
  See [Custom Notebook Formats](https://myst-nb.readthedocs.io/en/latest/examples/custom-formats.html) for details.

- Allow for configuration of render priority (per output format) with `nb_render_priority`.

- The code cell output renderer class is now loaded from an entry-point, with a configurable name,
  meaning that anyone can provide their own renderer subclass.
  See [Customise the render process](https://myst-nb.readthedocs.io/en/latest/use/formatting_outputs.html#customise-the-render-process) for details.

- Assignment of metadata tags `remove-stdout` and `remove-stderr` for removal of the relevant outputs ([see here](https://myst-nb.readthedocs.io/en/latest/use/formatting_outputs.html#removing-stdout-and-stderr))

- Render `text/markdown` MIME types with an integrated CommonMark parser ([see here](https://myst-nb.readthedocs.io/en/latest/use/formatting_outputs.html#markdown)).

- Add code output image formatting, *via* cell metadata, including size, captions and labelling ([see here](https://myst-nb.readthedocs.io/en/latest/use/formatting_outputs.html#images)).

- Notebook outputs ANSI lexer which is applied to stdout/stderr and text/plain outputs, and is configurable *via* `nb_render_text_lexer` ([see here](https://myst-nb.readthedocs.io/en/latest/use/formatting_outputs.html#ansi-outputs)).

- Capture execution data in sphinx env, which can be output into the documentation, with the `nb-exec-table` directive. See [Execution statistics](https://myst-nb.readthedocs.io/en/latest/use/execute.html#execution-statistics) for details.

### Improved 👌

- Standardise auto/cache execution

    Both now call the same underlying function (from `jupyter-cache`) and act the same.
    This improves `auto`, by making it output error reports and not raising an exception on an error.
    Additional config has also been added: `execution_allow_errors` and `execution_in_temp`.
    As for for `timeout`, `allow_errors` can also be set in the notebook `metadata.execution.allow_errors`
    This presents one breaking change, in that `cache` will now by default execute in a the local folder as the CWD (not a temporary one).

### Fixed 🐛

- Code cell source code is now assigned the correct lexer when using custom kernels ([39c1bb9](https://github.com/executablebooks/MyST-NB/commit/39c1bb99e73b35812474366f2f1760850fe40a57))

### Documented 📚

- Add example of using kernels other than Python ([676eb2c](https://github.com/executablebooks/MyST-NB/commit/676eb2c46b1ca605980180479c845b43ec64c5fb))

### Refactored ♻️

- Add more signature typing and docstrings
- Move config value validation to separate function
- Rename functions in cache.py and improve their logical flow
- Rename variable stored in sphinx environment, to share same suffix:
  - `path_to_cache` -> `nb_path_to_cache`
  - `allowed_nb_exec_suffixes` -> `nb_allowed_exec_suffixes`
  - `excluded_nb_exec_paths` -> `nb_excluded_exec_paths`
- Initial Nb output rendering:
  - Ensure source (path, lineno) are correctly propagated to `CellOutputBundleNode`
  - Capture cell level metadata in `CellOutputBundleNode`
  - New `CellOutputRenderer` class to contain render methods
  - Simplify test code, using sphinx `get_doctree` and `get_and_resolve_doctree` methods

## 0.8.5 - 2020-08-11

### Improved 👌

- Add configuration for traceback in stderr (#218)

### Fixed 🐛

- MIME render priority lookup

### Upgrades ⬆️

- myst-parser -> 0.9
- jupyter-cache to v0.3.0

### Documented 📚

- More explanation of myst notebooks (#213)
- Update contributing guide

## Contributors for previously releases

Thanks to all these contributors 🙏:

[@AakashGfude](https://github.com/search?q=repo%3Aexecutablebooks%2FMyST-NB+involves%3AAakashGfude+updated%3A2020-03-28..2020-08-11&type=Issues) | [@akhmerov](https://github.com/search?q=repo%3Aexecutablebooks%2FMyST-NB+involves%3Aakhmerov+updated%3A2020-03-28..2020-08-11&type=Issues) | [@amueller](https://github.com/search?q=repo%3Aexecutablebooks%2FMyST-NB+involves%3Aamueller+updated%3A2020-03-28..2020-08-11&type=Issues) | [@choldgraf](https://github.com/search?q=repo%3Aexecutablebooks%2FMyST-NB+involves%3Acholdgraf+updated%3A2020-03-28..2020-08-11&type=Issues) | [@chrisjsewell](https://github.com/search?q=repo%3Aexecutablebooks%2FMyST-NB+involves%3Achrisjsewell+updated%3A2020-03-28..2020-08-11&type=Issues) | [@codecov](https://github.com/search?q=repo%3Aexecutablebooks%2FMyST-NB+involves%3Acodecov+updated%3A2020-03-28..2020-08-11&type=Issues) | [@consideRatio](https://github.com/search?q=repo%3Aexecutablebooks%2FMyST-NB+involves%3AconsideRatio+updated%3A2020-03-28..2020-08-11&type=Issues) | [@jstac](https://github.com/search?q=repo%3Aexecutablebooks%2FMyST-NB+involves%3Ajstac+updated%3A2020-03-28..2020-08-11&type=Issues) | [@matthew-brett](https://github.com/search?q=repo%3Aexecutablebooks%2FMyST-NB+involves%3Amatthew-brett+updated%3A2020-03-28..2020-08-11&type=Issues) | [@mmcky](https://github.com/search?q=repo%3Aexecutablebooks%2FMyST-NB+involves%3Ammcky+updated%3A2020-03-28..2020-08-11&type=Issues) | [@phaustin](https://github.com/search?q=repo%3Aexecutablebooks%2FMyST-NB+involves%3Aphaustin+updated%3A2020-03-28..2020-08-11&type=Issues) | [@rossbar](https://github.com/search?q=repo%3Aexecutablebooks%2FMyST-NB+involves%3Arossbar+updated%3A2020-03-28..2020-08-11&type=Issues) | [@rowanc1](https://github.com/search?q=repo%3Aexecutablebooks%2FMyST-NB+involves%3Arowanc1+updated%3A2020-03-28..2020-08-11&type=Issues) | [@seanpue](https://github.com/search?q=repo%3Aexecutablebooks%2FMyST-NB+involves%3Aseanpue+updated%3A2020-03-28..2020-08-11&type=Issues) | [@stefanv](https://github.com/search?q=repo%3Aexecutablebooks%2FMyST-NB+involves%3Astefanv+updated%3A2020-03-28..2020-08-11&type=Issues) | [@TomDonoghue](https://github.com/search?q=repo%3Aexecutablebooks%2FMyST-NB+involves%3ATomDonoghue+updated%3A2020-03-28..2020-08-11&type=Issues) | [@tonyfast](https://github.com/search?q=repo%3Aexecutablebooks%2FMyST-NB+involves%3Atonyfast+updated%3A2020-03-28..2020-08-11&type=Issues) | [@welcome](https://github.com/search?q=repo%3Aexecutablebooks%2FMyST-NB+involves%3Awelcome+updated%3A2020-03-28..2020-08-11&type=Issues)

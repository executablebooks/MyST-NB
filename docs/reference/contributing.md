# Contribute to MyST-NB

[![Github-CI][github-ci]][github-link]
[![Coverage Status][codecov-badge]][codecov-link]
[![Documentation Status][rtd-badge]][rtd-link]
[![Code style: black][black-badge]][black-link]

We welcome all contributions!
See the [EBP Contributing Guide](https://executablebooks.org/en/latest/contributing.html) for general details, and below for guidance specific to MyST-NB.

## Installation

To install `MyST-NB` for package development (you will need a recent version of pip (>=22.0)):

```bash
git clone https://github.com/executablebooks/MyST-NB
cd MyST-NB
git checkout master
pip install -e .[code_style,testing,rtd]
```

## How the Jupyter Notebook parser works

MyST-NB is built on top of the MyST markdown parser. This is a flavor of markdown
designed to work with the Sphinx ecosystem. It is a combination of CommonMark markdown,
with a few extra syntax pieces added for use in Sphinx (for example, roles and
directives).

MyST-NB will do the following:

* Check for any pages in your documentation folder that end in `.ipynb`. For each one:
* Loop through the notebook's cells, converting cell contents into the Sphinx AST.
  * If it finds executable code cells, include their outputs in-line with the code.
  * If it finds markdown cells, use the MyST parser to convert them into Sphinx.

Eventually, it will also provide support for writing pure-markdown versions of notebooks
that can be executed and read into Sphinx.

## Code Style

Code style is tested using [ruff](https://docs.astral.sh/ruff),
with the configuration set in `pyproject.toml`,
and code formatted with [black](https://github.com/ambv/black).

Installing with `myst-nb[code_style]` makes the [pre-commit](https://pre-commit.com/)
package available, which will ensure this style is met before commits are submitted, by reformatting the code
and testing for lint errors.
It can be setup by:

```shell
>> cd MyST-NB
>> pre-commit install
```

Optionally you can run `black` and `ruff` separately:

```shell
>> black .
>> ruff .
```

Editors like VS Code also have automatic code reformat utilities, which can adhere to this standard.

All functions and class methods should be annotated with types and include a docstring. The preferred docstring format is outlined in `MyST-NB/docstring.fmt.mustache` and can be used automatically with the
[autodocstring](https://marketplace.visualstudio.com/items?itemName=njpwerner.autodocstring) VS Code extension.

## Testing

For code tests, MyST-NB uses [pytest](https://docs.pytest.org)):

```shell
>> cd MyST-NB
>> pytest
```

You can also use [tox](https://tox.readthedocs.io), to run the tests in multiple isolated environments (see the `tox.ini` file for available test environments):

```shell
>> cd MyST-NB
>> tox
```

For documentation build tests:

```shell
>> cd MyST-NB
>> tox
```

or

```shell
>> cd MyST-NB/docs
>> make clean
>> make html-strict
```

## Unit Testing

Testing is one of the most important aspects of your PR. You should write test cases and verify your implementation by following the testing guide above. If you modify code related to existing unit tests, you must run appropriate commands and confirm that the tests still pass.

Note that we are using [pytest](https://docs.pytest.org/en/latest/) for testing, [pytest-regression](https://pytest-regressions.readthedocs.io/en/latest/) to self-generate/re-generate expected outcomes of test and [pytest-cov](https://pytest-cov.readthedocs.io/en/latest/) for checking coverage.

To run tests along with coverage:

```
pytest -v --cov=myst_nb
```

To run tests along with generation of an html coverage report:

```
pytest -v --cov=myst_nb --cov-report=html
```


### Test File and Directory Naming Conventions

Tests are found in the [tests](https://github.com/executablebooks/MyST-NB/tree/master/tests) directory. In order for `pytest` to find the test scripts correctly, the name of each test script should start with `test_` prefix.

### How to Write Tests

There are many examples of unit tests under the [tests](https://github.com/executablebooks/MyST-NB/tree/master/tests) directory, so reading some of them is a good and recommended way. Prefer using the `fixtures` and the classes defined in [conftest.py](https://github.com/executablebooks/MyST-NB/blob/master/tests/conftest.py) as much as possible.

If using [pytest-regression](https://pytest-regressions.readthedocs.io/en/latest/), a new directory with `test_` prefix is expected to be created in the first test run. This will store your expected output against which subsequent test outputs will be compared.

### Code Coverage report

[pytest-cov](https://pytest-cov.readthedocs.io/en/latest/) is used to generate code coverage report. Make sure that your test cases cover most of the code written by you.

[github-ci]: https://github.com/executablebooks/MyST-NB/workflows/continuous-integration/badge.svg?branch=master
[github-link]: https://github.com/executablebooks/MyST-NB
[codecov-badge]: https://codecov.io/gh/executablebooks/MyST-NB/branch/master/graph/badge.svg
[codecov-link]: https://codecov.io/gh/executablebooks/MyST-NB
[rtd-badge]: https://readthedocs.org/projects/myst-nb/badge/?version=latest
[rtd-link]: https://myst-nb.readthedocs.io/en/latest/?badge=latest
[black-badge]: https://img.shields.io/badge/code%20style-black-000000.svg
[black-link]: https://github.com/ambv/black

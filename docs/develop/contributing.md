# Contributing

[![Github-CI][github-ci]][github-link]
[![Coverage Status][codecov-badge]][codecov-link]
[![CircleCI][circleci-badge]][circleci-link]
[![Documentation Status][rtd-badge]][rtd-link]
[![Code style: black][black-badge]][black-link]

## Code Style

Code style is tested using [flake8](http://flake8.pycqa.org),
with the configuration set in `.flake8`,
and code formatted with [black](https://github.com/ambv/black).

Installing with `myst-nb[code_style]` makes the [pre-commit](https://pre-commit.com/)
package available, which will ensure this style is met before commits are submitted, by reformatting the code
and testing for lint errors.
It can be setup by:

```shell
>> cd MyST-NB
>> pre-commit install
```

Optionally you can run `black` and `flake8` separately:

```shell
>> black .
>> flake8 .
```

Editors like VS Code also have automatic code reformat utilities, which can adhere to this standard.

All functions and class methods should be annotated with types and include a docstring. The prefered docstring format is outlined in `MyST-NB/docstring.fmt.mustache` and can be used automatically with the
[autodocstring](https://marketplace.visualstudio.com/items?itemName=njpwerner.autodocstring) VS Code extension.

## Testing

For code tests:

```shell
>> cd MyST-NB
>> pytest
```

For documentation build tests:

```shell
>> cd MyST-NB/docs
>> make clean
>> make html-strict
```

## Pull Requests

To contribute, make Pull Requests to the `master` branch (this is the default branch). A PR can consist of one or multiple commits. Before you open a PR, make sure to clean up your commit history and create the commits that you think best divide up the total work as outlined above (use `git rebase` and `git commit --amend`). Ensure all commit messages clearly summarise the changes in the header and the problem that this commit is solving in the body.

Merging pull requests: There are three ways of 'merging' pull requests on GitHub:

- Squash and merge: take all commits, squash them into a single one and put it on top of the base branch.
    Choose this for pull requests that address a single issue and are well represented by a single commit.
    Make sure to clean the commit message (title & body)
- Rebase and merge: take all commits and 'recreate' them on top of the base branch. All commits will be recreated with new hashes.
    Choose this for pull requests that require more than a single commit.
    Examples: PRs that contain multiple commits with individually significant changes; PRs that have commits from different authors (squashing commits would remove attribution)
- Merge with merge commit: put all commits as they are on the base branch, with a merge commit on top
    Choose for collaborative PRs with many commits. Here, the merge commit provides actual benefits.

[github-ci]: https://github.com/ExecutableBookProject/MyST-NB/workflows/continuous-integration/badge.svg?branch=master
[github-link]: https://github.com/ExecutableBookProject/MyST-NB
[codecov-badge]: https://codecov.io/gh/ExecutableBookProject/MyST-NB/branch/master/graph/badge.svg
[codecov-link]: https://codecov.io/gh/ExecutableBookProject/MyST-NB
[circleci-badge]: https://circleci.com/gh/ExecutableBookProject/MyST-NB.svg?style=shield
[circleci-link]: https://circleci.com/gh/ExecutableBookProject/MyST-NB
[rtd-badge]: https://readthedocs.org/projects/myst-nb/badge/?version=latest
[rtd-link]: https://myst-nb.readthedocs.io/en/latest/?badge=latest
[black-badge]: https://img.shields.io/badge/code%20style-black-000000.svg
[black-link]: https://github.com/ambv/black

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

Tests are found in the [tests](https://github.com/ExecutableBookProject/MyST-NB/tree/master/tests) directory. In order for `pytest` to find the test scripts correctly, the name of each test script should start with `test_` prefix.

### How to Write Tests

There are many examples of unit tests under the [tests](https://github.com/ExecutableBookProject/MyST-NB/tree/master/tests) directory, so reading some of them is a good and recommended way. Prefer using the `fixtures` and the classes defined in [conftest.py](https://github.com/ExecutableBookProject/MyST-NB/blob/master/tests/conftest.py) as much as possible.

If using [pytest-regression](https://pytest-regressions.readthedocs.io/en/latest/), a new directory with `test_` prefix is expected to be created in the first test run. This will store your expected output against which subsequent test outputs will be compared.

### Code Coverage report

[pytest-cov](https://pytest-cov.readthedocs.io/en/latest/) is used to generate code coverage report. Make sure that your test cases cover most of the code written by you. Expect the coverage build in Travis CI to fail if the overall coverage of the repository decreases.

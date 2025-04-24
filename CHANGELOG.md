# Change Log

## v1.2.0 - 2025-02-07

([full changelog](https://github.com/executablebooks/MyST-NB/compare/v1.1.2...v1.2.0))

### Enhancements made

- ENH: Support translated notebooks by @OriolAbril in https://github.com/executablebooks/MyST-NB/pull/600

### Bugs Fixed

- BUG: using rstrip to preserve indents by @bsipocz in https://github.com/executablebooks/MyST-NB/pull/637
- FIX: fix path suffix condition in core/read.py by @je-cook in https://github.com/executablebooks/MyST-NB/pull/641

### Maintenance and upkeep improvements

- DOCS: adding changelog for 1.1.2 by @bsipocz in https://github.com/executablebooks/MyST-NB/pull/638
- MAINT: adding python 3.13 to CI and classifiers by @bsipocz in https://github.com/executablebooks/MyST-NB/pull/635
- CI: adding devdeps testing and cron and workflow dispatch by @bsipocz in https://github.com/executablebooks/MyST-NB/pull/639
- TST: fail on warnings by @bsipocz in https://github.com/executablebooks/MyST-NB/pull/647
- add `configuration` key to readthedocs.yml by @sneakers-the-rat in https://github.com/executablebooks/MyST-NB/pull/657
- MAINT: fix CI in prep for release by @bsipocz in https://github.com/executablebooks/MyST-NB/pull/659

### Other merged PRs

- [pre-commit.ci] pre-commit autoupdate by @pre-commit-ci in https://github.com/executablebooks/MyST-NB/pull/569
- Revert "[pre-commit.ci] pre-commit autoupdate" by @agoose77 in https://github.com/executablebooks/MyST-NB/pull/642

### New Contributors
- @sneakers-the-rat made their first contribution in https://github.com/executablebooks/MyST-NB/pull/657

([GitHub contributors page for this release](https://github.com/executablebooks/MyST-NB/graphs/contributors?from=2024-09-24&to=2025-02-07&type=c))


## v1.1.2 - 2024-09-24

([full changelog](https://github.com/executablebooks/MyST-NB/compare/v1.1.1...c6a2d4b61205c2b20943391a656f01a4cc446076))

### Bugs fixed

- Fix incorrect output from prints originating from different processes [#604](https://github.com/executablebooks/MyST-NB/pull/604) ([@basnijholt](https://github.com/basnijholt))

### Maintenance and upkeep improvements

- MAINT: removing version pinnings for testing and rtd [#634](https://github.com/executablebooks/MyST-NB/pull/634) ([@bsipocz](https://github.com/bsipocz))
- MAINT: only doing monthly pre-commit update [#627](https://github.com/executablebooks/MyST-NB/pull/627) ([@bsipocz](https://github.com/bsipocz))
- MAINT: no need for weekly dependabot [#626](https://github.com/executablebooks/MyST-NB/pull/626) ([@bsipocz](https://github.com/bsipocz))
- MAINT: fix sphinx 8.0 compatibility [#620](https://github.com/executablebooks/MyST-NB/pull/620) ([@bsipocz](https://github.com/bsipocz))
- MAINT: bump version [#614](https://github.com/executablebooks/MyST-NB/pull/614) ([@agoose77](https://github.com/agoose77))

### Documentation improvements

- DOC: adding changelog for 1.1.0 and 1.1.1 [#625](https://github.com/executablebooks/MyST-NB/pull/625) ([@bsipocz](https://github.com/bsipocz))
- Update glueing docs for NumPy >=2.0 [#615](https://github.com/executablebooks/MyST-NB/pull/615) ([@bryanwweber](https://github.com/bryanwweber))

### Other merged PRs

- build(deps): bump codecov/codecov-action from 3.1.4 to 4.5.0 in the actions group [#630](https://github.com/executablebooks/MyST-NB/pull/630) ([@dependabot](https://github.com/dependabot))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/executablebooks/MyST-NB/graphs/contributors?from=2024-06-27&to=2024-09-24&type=c))

[@agoose77](https://github.com/search?q=repo%3Aexecutablebooks%2FMyST-NB+involves%3Aagoose77+updated%3A2024-06-27..2024-09-24&type=Issues) | [@basnijholt](https://github.com/search?q=repo%3Aexecutablebooks%2FMyST-NB+involves%3Abasnijholt+updated%3A2024-06-27..2024-09-24&type=Issues) | [@bryanwweber](https://github.com/search?q=repo%3Aexecutablebooks%2FMyST-NB+involves%3Abryanwweber+updated%3A2024-06-27..2024-09-24&type=Issues) | [@bsipocz](https://github.com/search?q=repo%3Aexecutablebooks%2FMyST-NB+involves%3Absipocz+updated%4A2024-06-27..2024-09-24&type=Issues) | [@choldgraf](https://github.com/search?q=repo%3Aexecutablebooks%2FMyST-NB+involves%3Acholdgraf+updated%3A2024-06-27..2024-09-24&type=Issues) | [@chrisjsewell](https://github.com/search?q=repo%3Aexecutablebooks%2FMyST-NB+involves%3Achrisjsewell+updated%3A2024-06-27..2024-09-24&type=Issues) | [@dependabot](https://github.com/search?q=repo%3Aexecutablebooks%2FMyST-NB+involves%3Adependabot+updated%3A2024-06-27..2024-09-24&type=Issues) | [@LecrisUT](https://github.com/search?q=repo%3Aexecutablebooks%2FMyST-NB+involves%3ALecrisUT+updated%3A2024-06-27..2024-09-24&type=Issues) | [@OriolAbril](https://github.com/search?q=repo%3Aexecutablebooks%2FMyST-NB+involves%3AOriolAbril+updated%3A2024-06-27..2024-09-24&type=Issues) | [@tupui](https://github.com/search?q=repo%3Aexecutablebooks%2FMyST-NB+involves%3Atupui+updated%3A2024-06-27..2024-09-24&type=Issues) | [@welcome](https://github.com/search?q=repo%3Aexecutablebooks%2FMyST-NB+involves%3Awelcome+updated%3A2024-06-27..2024-09-24&type=Issues)

## v1.1.1 - 2024-06-27

([full changelog](https://github.com/executablebooks/MyST-NB/compare/v1.1.0...6ce30cd41fa82543e0f315ac8bbee82669b0cc82))

### Bugs fixed

- FIX: output metadata overwrites image size for all following images [#609](https://github.com/executablebooks/MyST-NB/pull/609) ([@aeisenbarth](https://github.com/aeisenbarth))

- FIX: remove incorrect license classifier [#603](https://github.com/executablebooks/MyST-NB/pull/603) ([@agoose77](https://github.com/agoose77))

### Maintenance and upkeep improvements

- MAINT: bump version [#614](https://github.com/executablebooks/MyST-NB/pull/614) ([@agoose77](https://github.com/agoose77))

- MAINT: appease mypy [#612](https://github.com/executablebooks/MyST-NB/pull/612) ([@agoose77](https://github.com/agoose77))

- MAINT: fix specs for CI matrix [#611](https://github.com/executablebooks/MyST-NB/pull/611) ([@agoose77](https://github.com/agoose77))

- MAINT: bump version [#592](https://github.com/executablebooks/MyST-NB/pull/592) ([@agoose77](https://github.com/agoose77))

### Documentation improvements

- DOCS: set printoptions to disable modern scalar printing [#613](https://github.com/executablebooks/MyST-NB/pull/613) ([@agoose77](https://github.com/agoose77))

- DOCS: extra comma forgotten [#606](https://github.com/executablebooks/MyST-NB/pull/606) ([@jeertmans](https://github.com/jeertmans))

- DOCS: update shown code to match source [#598](https://github.com/executablebooks/MyST-NB/pull/598) ([@OriolAbril](https://github.com/OriolAbril))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/executablebooks/MyST-NB/graphs/contributors?from=2024-04-12&to=2024-06-27&type=c))

[@aeisenbarth](https://github.com/search?q=repo%3Aexecutablebooks%2FMyST-NB+involves%3Aaeisenbarth+updated%3A2024-04-12..2024-06-27&type=Issues) | [@agoose77](https://github.com/search?q=repo%3Aexecutablebooks%2FMyST-NB+involves%3Aagoose77+updated%3A2024-04-12..2024-06-27&type=Issues) | [@jeertmans](https://github.com/search?q=repo%3Aexecutablebooks%2FMyST-NB+involves%3Ajeertmans+updated%3A2024-04-12..2024-06-27&type=Issues) | [@OriolAbril](https://github.com/search?q=repo%3Aexecutablebooks%2FMyST-NB+involves%3AOriolAbril+updated%3A2024-04-12..2024-06-27&type=Issues) | [@sstroemer](https://github.com/search?q=repo%3Aexecutablebooks%2FMyST-NB+involves%3Asstroemer+updated%3A2024-04-12..2024-06-27&type=Issues) | [@welcome](https://github.com/search?q=repo%3Aexecutablebooks%2FMyST-NB+involves%3Awelcome+updated%3A2024-04-12..2024-06-27&type=Issues)


## v1.1.0 - 2024-04-12

([full changelog](https://github.com/executablebooks/MyST-NB/compare/v1.0.0...9943ec214c35844c4535d0184f7840574fc7ab03))

### Enhancements made

- ENH: pass-through image metadata [#588](https://github.com/executablebooks/MyST-NB/pull/588) ([@flying-sheep](https://github.com/flying-sheep))

### Maintenance and upkeep improvements

- MAINT: bump version [#592](https://github.com/executablebooks/MyST-NB/pull/592) ([@agoose77](https://github.com/agoose77))

- MAINT: use `findall` instead of `traverse` [#585](https://github.com/executablebooks/MyST-NB/pull/585) ([@agoose77](https://github.com/agoose77))

- MAINT: restore default line length [#577](https://github.com/executablebooks/MyST-NB/pull/577) ([@agoose77](https://github.com/agoose77))

### Other merged PRs

- build(deps): bump actions/setup-python from 4 to 5 [#576](https://github.com/executablebooks/MyST-NB/pull/576) ([@dependabot](https://github.com/dependabot))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/executablebooks/MyST-NB/graphs/contributors?from=2023-11-08&to=2024-04-12&type=c))

[@agoose77](https://github.com/search?q=repo%3Aexecutablebooks%2FMyST-NB+involves%3Aagoose77+updated%3A2023-11-08..2024-04-12&type=Issues) | [@cisaacstern](https://github.com/search?q=repo%3Aexecutablebooks%2FMyST-NB+involves%3Acisaacstern+updated%3A2023-11-08..2024-04-12&type=Issues) | [@dependabot](https://github.com/search?q=repo%3Aexecutablebooks%2FMyST-NB+involves%3Adependabot+updated%3A2023-11-08..2024-04-12&type=Issues) | [@flying-sheep](https://github.com/search?q=repo%3Aexecutablebooks%2FMyST-NB+involves%3Aflying-sheep+updated%3A2023-11-08..2024-04-12&type=Issues) | [@ma-sadeghi](https://github.com/search?q=repo%3Aexecutablebooks%2FMyST-NB+involves%3Ama-sadeghi+updated%3A2023-11-08..2024-04-12&type=Issues) | [@peytondmurray](https://github.com/search?q=repo%3Aexecutablebooks%2FMyST-NB+involves%3Apeytondmurray+updated%3A2023-11-08..2024-04-12&type=Issues) | [@PhilipVinc](https://github.com/search?q=repo%3Aexecutablebooks%2FMyST-NB+involves%3APhilipVinc+updated%3A2023-11-08..2024-04-12&type=Issues) | [@sphuber](https://github.com/search?q=repo%3Aexecutablebooks%2FMyST-NB+involves%3Asphuber+updated%3A2023-11-08..2024-04-12&type=Issues) | [@welcome](https://github.com/search?q=repo%3Aexecutablebooks%2FMyST-NB+involves%3Awelcome+updated%3A2023-11-08..2024-04-12&type=Issues)


## v1.0.0 - 2023-11-08

([full changelog](https://github.com/executablebooks/MyST-NB/compare/e8fd165...48edb5d852eb73b09eae962c7518045f836633d5))

### New features added

- FEAT: allow any value for expr [#429](https://github.com/executablebooks/MyST-NB/pull/429) ([@agoose77](https://github.com/agoose77))

### Bugs fixed

- FIX: update tests for newer matplotlib [#559](https://github.com/executablebooks/MyST-NB/pull/559) ([@agoose77](https://github.com/agoose77))
- FIX: remove warnings for 3.11+ [#547](https://github.com/executablebooks/MyST-NB/pull/547) ([@agoose77](https://github.com/agoose77))
- FIX: Show traceback before raising ExecutionError [#531](https://github.com/executablebooks/MyST-NB/pull/531) ([@paugier](https://github.com/paugier))

### Maintenance and upkeep improvements

- MAINT: uncap nbformat [#568](https://github.com/executablebooks/MyST-NB/pull/568) ([@agoose77](https://github.com/agoose77))
- MAINT: unpin jupyer-cache [#567](https://github.com/executablebooks/MyST-NB/pull/567) ([@agoose77](https://github.com/agoose77))
- MAINT: bump minimum Python version [#566](https://github.com/executablebooks/MyST-NB/pull/566) ([@agoose77](https://github.com/agoose77))
- MAINT: enable ruff formatter [#565](https://github.com/executablebooks/MyST-NB/pull/565) ([@agoose77](https://github.com/agoose77))
- MAINT: test wider matrix [#552](https://github.com/executablebooks/MyST-NB/pull/552) ([@agoose77](https://github.com/agoose77))
- MAINT: update linting [#551](https://github.com/executablebooks/MyST-NB/pull/551) ([@agoose77](https://github.com/agoose77))
- MAINT: Patch `file_regression` fixture for Sphinx backwards compatibility [#536](https://github.com/executablebooks/MyST-NB/pull/536) ([@je-cook](https://github.com/je-cook))
- MAINT: remove python=3.7 as EOL is June 2023 [#516](https://github.com/executablebooks/MyST-NB/pull/516) ([@mmcky](https://github.com/mmcky))

### Documentation improvements

- DOCS: Fix broken pytest fixture [#546](https://github.com/executablebooks/MyST-NB/pull/546) ([@peytondmurray](https://github.com/peytondmurray))
- 📚 DOCS: Fix typos and add codespell pre-commit hook [#475](https://github.com/executablebooks/MyST-NB/pull/475) ([@kianmeng](https://github.com/kianmeng))

### API and Breaking Changes

- UPGRADE: Support Sphinx 7 [#524](https://github.com/executablebooks/MyST-NB/pull/524) ([@LecrisUT](https://github.com/LecrisUT))
- UPGRADE: myst-parser 1.0 [#479](https://github.com/executablebooks/MyST-NB/pull/479) ([@aleivag](https://github.com/aleivag))

### Other merged PRs

- [pre-commit.ci] pre-commit autoupdate [#564](https://github.com/executablebooks/MyST-NB/pull/564) ([@pre-commit-ci](https://github.com/pre-commit-ci))
- [pre-commit.ci] pre-commit autoupdate [#561](https://github.com/executablebooks/MyST-NB/pull/561) ([@pre-commit-ci](https://github.com/pre-commit-ci))
- [pre-commit.ci] pre-commit autoupdate [#556](https://github.com/executablebooks/MyST-NB/pull/556) ([@pre-commit-ci](https://github.com/pre-commit-ci))
- Update readthedocs Config File to fix Test Error [#554](https://github.com/executablebooks/MyST-NB/pull/554) ([@michaelweinold](https://github.com/michaelweinold))
- [pre-commit.ci] pre-commit autoupdate [#553](https://github.com/executablebooks/MyST-NB/pull/553) ([@pre-commit-ci](https://github.com/pre-commit-ci))
- build(deps): update ipython requirement from <=8.16.0 to <=8.16.1 [#550](https://github.com/executablebooks/MyST-NB/pull/550) ([@dependabot](https://github.com/dependabot))
- [pre-commit.ci] pre-commit autoupdate [#549](https://github.com/executablebooks/MyST-NB/pull/549) ([@pre-commit-ci](https://github.com/pre-commit-ci))
- build(deps): update ipython requirement from !=8.1.0,<8.16 to !=8.1.0,<8.17 [#548](https://github.com/executablebooks/MyST-NB/pull/548) ([@dependabot](https://github.com/dependabot))
- [pre-commit.ci] pre-commit autoupdate [#542](https://github.com/executablebooks/MyST-NB/pull/542) ([@pre-commit-ci](https://github.com/pre-commit-ci))
- build(deps): bump actions/checkout from 3 to 4 [#539](https://github.com/executablebooks/MyST-NB/pull/539) ([@dependabot](https://github.com/dependabot))
- build(deps): update ipython requirement from !=8.1.0,<8.15 to !=8.1.0,<8.16 [#538](https://github.com/executablebooks/MyST-NB/pull/538) ([@dependabot](https://github.com/dependabot))
- Update copyright year to 2023 [#537](https://github.com/executablebooks/MyST-NB/pull/537) ([@GlobalMin](https://github.com/GlobalMin))
- build(deps-dev): update jupytext requirement from <1.15.0,>=1.11.2 to >=1.11.2,<1.16.0 [#534](https://github.com/executablebooks/MyST-NB/pull/534) ([@dependabot](https://github.com/dependabot))
- [pre-commit.ci] pre-commit autoupdate [#529](https://github.com/executablebooks/MyST-NB/pull/529) ([@pre-commit-ci](https://github.com/pre-commit-ci))
- build(deps-dev): update coconut requirement from <2.3.0,>=1.4.3 to >=1.4.3,<3.1.0 [#527](https://github.com/executablebooks/MyST-NB/pull/527) ([@dependabot](https://github.com/dependabot))
- [pre-commit.ci] pre-commit autoupdate [#526](https://github.com/executablebooks/MyST-NB/pull/526) ([@pre-commit-ci](https://github.com/pre-commit-ci))
- Update ipython requirement from !=8.1.0,<8.5 to !=8.1.0,<8.15 [#521](https://github.com/executablebooks/MyST-NB/pull/521) ([@dependabot](https://github.com/dependabot))
- [pre-commit.ci] pre-commit autoupdate [#518](https://github.com/executablebooks/MyST-NB/pull/518) ([@pre-commit-ci](https://github.com/pre-commit-ci))
- Update coconut requirement from <2.3.0,>=1.4.3 to >=1.4.3,<3.1.0 [#517](https://github.com/executablebooks/MyST-NB/pull/517) ([@dependabot](https://github.com/dependabot))
- [pre-commit.ci] pre-commit autoupdate [#515](https://github.com/executablebooks/MyST-NB/pull/515) ([@pre-commit-ci](https://github.com/pre-commit-ci))
- Update ipykernel requirement from ~=5.5 to >=5.5,<7.0 [#512](https://github.com/executablebooks/MyST-NB/pull/512) ([@dependabot](https://github.com/dependabot))
- Update sphinx-book-theme requirement from ~=0.3.0 to >=0.3,<1.1 [#510](https://github.com/executablebooks/MyST-NB/pull/510) ([@dependabot](https://github.com/dependabot))
- Update jupytext requirement from ~=1.11.2 to >=1.11.2,<1.15.0 [#509](https://github.com/executablebooks/MyST-NB/pull/509) ([@dependabot](https://github.com/dependabot))

### Contributors to this release

([GitHub contributors page for this release](https://github.com/executablebooks/MyST-NB/graphs/contributors?from=2023-04-24&to=2023-11-29&type=c))

[@agoose77](https://github.com/search?q=repo%3Aexecutablebooks%2FMyST-NB+involves%3Aagoose77+updated%3A2023-04-24..2023-11-29&type=Issues) | [@aleivag](https://github.com/search?q=repo%3Aexecutablebooks%2FMyST-NB+involves%3Aaleivag+updated%3A2023-04-24..2023-11-29&type=Issues) | [@choldgraf](https://github.com/search?q=repo%3Aexecutablebooks%2FMyST-NB+involves%3Acholdgraf+updated%3A2023-04-24..2023-11-29&type=Issues) | [@chrisjsewell](https://github.com/search?q=repo%3Aexecutablebooks%2FMyST-NB+involves%3Achrisjsewell+updated%3A2023-04-24..2023-11-29&type=Issues) | [@cisaacstern](https://github.com/search?q=repo%3Aexecutablebooks%2FMyST-NB+involves%3Acisaacstern+updated%3A2023-04-24..2023-11-29&type=Issues) | [@codecov](https://github.com/search?q=repo%3Aexecutablebooks%2FMyST-NB+involves%3Acodecov+updated%3A2023-04-24..2023-11-29&type=Issues) | [@dependabot](https://github.com/search?q=repo%3Aexecutablebooks%2FMyST-NB+involves%3Adependabot+updated%3A2023-04-24..2023-11-29&type=Issues) | [@GlobalMin](https://github.com/search?q=repo%3Aexecutablebooks%2FMyST-NB+involves%3AGlobalMin+updated%3A2023-04-24..2023-11-29&type=Issues) | [@je-cook](https://github.com/search?q=repo%3Aexecutablebooks%2FMyST-NB+involves%3Aje-cook+updated%3A2023-04-24..2023-11-29&type=Issues) | [@joeldodson](https://github.com/search?q=repo%3Aexecutablebooks%2FMyST-NB+involves%3Ajoeldodson+updated%3A2023-04-24..2023-11-29&type=Issues) | [@kianmeng](https://github.com/search?q=repo%3Aexecutablebooks%2FMyST-NB+involves%3Akianmeng+updated%3A2023-04-24..2023-11-29&type=Issues) | [@kloczek](https://github.com/search?q=repo%3Aexecutablebooks%2FMyST-NB+involves%3Akloczek+updated%3A2023-04-24..2023-11-29&type=Issues) | [@LecrisUT](https://github.com/search?q=repo%3Aexecutablebooks%2FMyST-NB+involves%3ALecrisUT+updated%3A2023-04-24..2023-11-29&type=Issues) | [@michaelweinold](https://github.com/search?q=repo%3Aexecutablebooks%2FMyST-NB+involves%3Amichaelweinold+updated%3A2023-04-24..2023-11-29&type=Issues) | [@mmcky](https://github.com/search?q=repo%3Aexecutablebooks%2FMyST-NB+involves%3Ammcky+updated%3A2023-04-24..2023-11-29&type=Issues) | [@paugier](https://github.com/search?q=repo%3Aexecutablebooks%2FMyST-NB+involves%3Apaugier+updated%3A2023-04-24..2023-11-29&type=Issues) | [@peytondmurray](https://github.com/search?q=repo%3Aexecutablebooks%2FMyST-NB+involves%3Apeytondmurray+updated%3A2023-04-24..2023-11-29&type=Issues) | [@PhilipVinc](https://github.com/search?q=repo%3Aexecutablebooks%2FMyST-NB+involves%3APhilipVinc+updated%3A2023-04-24..2023-11-29&type=Issues) | [@pre-commit-ci](https://github.com/search?q=repo%3Aexecutablebooks%2FMyST-NB+involves%3Apre-commit-ci+updated%3A2023-04-24..2023-11-29&type=Issues) | [@rowanc1](https://github.com/search?q=repo%3Aexecutablebooks%2FMyST-NB+involves%3Arowanc1+updated%3A2023-04-24..2023-11-29&type=Issues) | [@sphuber](https://github.com/search?q=repo%3Aexecutablebooks%2FMyST-NB+involves%3Asphuber+updated%3A2023-04-24..2023-11-29&type=Issues) | [@tupui](https://github.com/search?q=repo%3Aexecutablebooks%2FMyST-NB+involves%3Atupui+updated%3A2023-04-24..2023-11-29&type=Issues) | [@WarrenWeckesser](https://github.com/search?q=repo%3Aexecutablebooks%2FMyST-NB+involves%3AWarrenWeckesser+updated%3A2023-04-24..2023-11-29&type=Issues) | [@welcome](https://github.com/search?q=repo%3Aexecutablebooks%2FMyST-NB+involves%3Awelcome+updated%3A2023-04-24..2023-11-29&type=Issues) | [@Yoshanuikabundi](https://github.com/search?q=repo%3Aexecutablebooks%2FMyST-NB+involves%3AYoshanuikabundi+updated%3A2023-04-24..2023-11-29&type=Issues)


## v0.17.2 - 2023-04-21

This is primarily a maintenance release to support newer versions of dependencies and fix a few bugs.

### Maintenance and upkeep improvements

- MAINT: Create dependabot.yml [#499](https://github.com/executablebooks/MyST-NB/pull/499) ([@choldgraf](https://github.com/choldgraf))
- MAINT: Fix codecov jobs and update pre-commit [#460](https://github.com/executablebooks/MyST-NB/pull/460) ([@choldgraf](https://github.com/choldgraf))
- UPDATE: jupyter-cache v0.6.0 [#498](https://github.com/executablebooks/MyST-NB/pull/498) ([@choldgraf](https://github.com/choldgraf))

### Documentation improvements

- DOCS: Hint to avoid Extension error in sphinx-build [#494](https://github.com/executablebooks/MyST-NB/pull/494) ([@kolibril13](https://github.com/kolibril13), [@choldgraf](https://github.com/choldgraf))
- DOCS: fix link to gallery [#483](https://github.com/executablebooks/MyST-NB/pull/483) ([@michaelaye](https://github.com/michaelaye), [@choldgraf](https://github.com/choldgraf), [@agoose77](https://github.com/agoose77))
- Add note about how to use cell tags [#490](https://github.com/executablebooks/MyST-NB/pull/490) ([@kolibril13](https://github.com/kolibril13), [@choldgraf](https://github.com/choldgraf))
- Update quickstart.md to include docs folder [#489](https://github.com/executablebooks/MyST-NB/pull/489) ([@kolibril13](https://github.com/kolibril13), [@choldgraf](https://github.com/choldgraf))
- docs: update to latest `sphinx-design` [#486](https://github.com/executablebooks/MyST-NB/pull/486) ([@agoose77](https://github.com/agoose77), [@choldgraf](https://github.com/choldgraf))

### Bug fixes

- fix: use jsdelivr CDN for ipywidgets [#491](https://github.com/executablebooks/MyST-NB/pull/491) ([@agoose77](https://github.com/agoose77), [@choldgraf](https://github.com/choldgraf))
- Add ipywidgets javascript [#469](https://github.com/executablebooks/MyST-NB/pull/469) ([@OriolAbril](https://github.com/OriolAbril), [@agoose77](https://github.com/agoose77))

### Contributors to this release

The following people contributed discussions, new ideas, code and documentation contributions, and review.
See [our definition of contributors](https://github-activity.readthedocs.io/en/latest/#how-does-this-tool-define-contributions-in-the-reports).

([GitHub contributors page for this release](https://github.com/executablebooks/MyST-NB/graphs/contributors?from=2022-09-30&to=2023-04-21&type=c))

@agoose77 ([activity](https://github.com/search?q=repo%3Aexecutablebooks%2FMyST-NB+involves%3Aagoose77+updated%3A2022-09-30..2023-04-21&type=Issues)) | @choldgraf ([activity](https://github.com/search?q=repo%3Aexecutablebooks%2FMyST-NB+involves%3Acholdgraf+updated%3A2022-09-30..2023-04-21&type=Issues)) | @chrisjsewell ([activity](https://github.com/search?q=repo%3Aexecutablebooks%2FMyST-NB+involves%3Achrisjsewell+updated%3A2022-09-30..2023-04-21&type=Issues)) | @dependabot ([activity](https://github.com/search?q=repo%3Aexecutablebooks%2FMyST-NB+involves%3Adependabot+updated%3A2022-09-30..2023-04-21&type=Issues)) | @kolibril13 ([activity](https://github.com/search?q=repo%3Aexecutablebooks%2FMyST-NB+involves%3Akolibril13+updated%3A2022-09-30..2023-04-21&type=Issues)) | @michaelaye ([activity](https://github.com/search?q=repo%3Aexecutablebooks%2FMyST-NB+involves%3Amichaelaye+updated%3A2022-09-30..2023-04-21&type=Issues)) | @OriolAbril ([activity](https://github.com/search?q=repo%3Aexecutablebooks%2FMyST-NB+involves%3AOriolAbril+updated%3A2022-09-30..2023-04-21&type=Issues)) | @pre-commit-ci ([activity](https://github.com/search?q=repo%3Aexecutablebooks%2FMyST-NB+involves%3Apre-commit-ci+updated%3A2022-09-30..2023-04-21&type=Issues))

## v0.17.1 - 2022-30-09

[Full changelog](https://github.com/executablebooks/MyST-NB/compare/v0.17.0...v0.17.1)

- 👌 IMPROVE: `hide-output` button (#450)
  This now uses the same margin color as the cell source and, when the cell source is present, is "connected" to that, to form a single element.
  See [Hide cell contents](docs/render/hiding.md) for more information.

## v0.17.0 - 2022-29-09

[Full changelog](https://github.com/executablebooks/MyST-NB/compare/v0.16.0...v0.17.0)

- 👌 IMPROVE: Replace sphinx-togglebutton with built-in functionality (#446)
  This allows for tighter integration with myst-nb:

  - Nicer rendering of the hidden content buttons
  - Customisation of the hide/show prompts

  See [Hide cell contents](docs/render/hiding.md) for more information.

- 🐛 FIX: Inline exec variables with multiple outputs (#440)
  Previously, it was assumed that a variable evaluation would only ever create 0 or 1 outputs.
  Multiple are now allowed.

- 👌 IMPROVE: cache bust changes to CSS (#447)
- 👌 IMPROVE: Move CSS colors to variables (#448)

## v0.16.0 - 2022-06-13

[Full changelog](https://github.com/executablebooks/MyST-NB/compare/v0.15.0...v0.16.0)

- ⬆️ UPGRADE: Sphinx v5 and drop v3 (see [changelog](https://www.sphinx-doc.org/en/master/changes.html)), myst-parser v0.18 (see [changelog](https://myst-parser.readthedocs.io/en/latest/develop/_changelog.html))
- ⬆️ UPGRADE: Add Python 3.10 support

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

As per the changes in [`myst_parser`](inv:myst#develop/_changelog), the `dollarmath` syntax extension is no longer included by default.
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
  - `myst_parser`: [`0.15 -> 0.17`](inv:myst#develop/_changelog)
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

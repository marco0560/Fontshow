## [0.32.2](https://github.com/marco0560/Fontshow/compare/v0.32.1...v0.32.2) (2026-01-28)

### Bug Fixes

* **cli:** improve parse-inventory warning output with schema-aware font identity ([25180b0](https://github.com/marco0560/Fontshow/commit/25180b071d88ea22350a0b78f1b28ca18f03bfa1))

## [0.32.1](https://github.com/marco0560/Fontshow/compare/v0.32.0...v0.32.1) (2026-01-27)

### Bug Fixes

* **cli:** enforce verbosity semantics for parse-inventory ([1184956](https://github.com/marco0560/Fontshow/commit/1184956f50c53f54860f614976885934b4d8fca2))

## [0.32.0](https://github.com/marco0560/Fontshow/compare/v0.31.2...v0.32.0) (2026-01-26)

### Features

* **parser:** clarify semantic validation scope for language codes ([d385344](https://github.com/marco0560/Fontshow/commit/d385344e5dec7e16a1cf397ef558112e03b43095))
* **parser:** normalize languages and track dropped entries ([322d37e](https://github.com/marco0560/Fontshow/commit/322d37e22977349e03ff0cee09a6c3fc5d318c6c))

### Bug Fixes

* **build:** remove secondary CLI entrypoint ([cf575b0](https://github.com/marco0560/Fontshow/commit/cf575b0a61c290b3551154d97380e35cb9d7408b))
* **cli:** align quiet/verbose behavior and document via tests ([90689f8](https://github.com/marco0560/Fontshow/commit/90689f8d9ee43c1fa988d973682b12d9a79ab3f7))
* **dump:** exclude non-OpenType fonts and normalize style ([b3dfde8](https://github.com/marco0560/Fontshow/commit/b3dfde8ff8d6e2fbb99e55873b58a2ea6fb0381f))
* **dump:** normalize missing style and exclude non-OpenType fonts ([a2b9361](https://github.com/marco0560/Fontshow/commit/a2b93616398493dccefc2afd6069e40417c9d1ae))
* **dump:** skip non-OpenType fonts and improve verbose summary ([748d8ce](https://github.com/marco0560/Fontshow/commit/748d8cef2d8c379c6770929a3488c51bd14f7a44))
* **parser:** align field access with identity-based schema ([53a2b37](https://github.com/marco0560/Fontshow/commit/53a2b37d917e8666ebfb896d6650acfd3746cfae))
* **parser:** clarify validation errors for identity fields ([3b064ba](https://github.com/marco0560/Fontshow/commit/3b064ba780d20568cd41a5fe147bd1fb9c6fbe2b))
* **schema:** add languages_raw field to inventory schema ([0eacff8](https://github.com/marco0560/Fontshow/commit/0eacff88943d5011522e6d5da9f7ef992dcc14a6))
* **schema:** stabilize inventory validation and regression tests ([645d0c3](https://github.com/marco0560/Fontshow/commit/645d0c3b95f7e8c6b00e008c121a07580ee44c02))
* **validation:** enforce correct semantics for identity and base_names ([0e36fd4](https://github.com/marco0560/Fontshow/commit/0e36fd4879b77c7ca78d5e2726077f1f62a7edc9)), closes [#48](https://github.com/marco0560/Fontshow/issues/48)

## [0.31.2](https://github.com/marco0560/Fontshow/compare/v0.31.1...v0.31.2) (2026-01-25)

### Bug Fixes

* **parser:** align field access with identity-based schema ([ca82289](https://github.com/marco0560/Fontshow/commit/ca82289b39ae346a0fe97185fde2f51def4b92bf))
* **parser:** clarify validation errors for identity fields ([82df45e](https://github.com/marco0560/Fontshow/commit/82df45e427afa03d2da620c0b05a95835fda6520))
* **schema:** stabilize inventory schema validation and regression coverage ([6564507](https://github.com/marco0560/Fontshow/commit/656450703d9e02b1dfe89d01e9558a847c918577))
* **schema:** stabilize inventory validation and regression tests ([8e834be](https://github.com/marco0560/Fontshow/commit/8e834bee9b483a2b021f7b53a9c0ca0309738f7b))
* **validation:** enforce correct semantics for identity and base_names ([ac20d8b](https://github.com/marco0560/Fontshow/commit/ac20d8b8d3a573ab122d31db18945a4a32730326)), closes [#48](https://github.com/marco0560/Fontshow/issues/48)

## [0.31.1](https://github.com/marco0560/Fontshow/compare/v0.31.0...v0.31.1) (2026-01-25)

### Bug Fixes

* **cli:** align quiet/verbose behavior and document via tests ([ddbfe1e](https://github.com/marco0560/Fontshow/commit/ddbfe1ef67871c5937f452aa80f452c3c489e0be))

## [0.31.0](https://github.com/marco0560/Fontshow/compare/v0.30.0...v0.31.0) (2026-01-25)

### Features

* **parser:** normalize languages and track dropped entries ([f3398d4](https://github.com/marco0560/Fontshow/commit/f3398d44be1e34db72878c6cbc5335fbe442ffb7))

## [0.30.0](https://github.com/marco0560/Fontshow/compare/v0.29.5...v0.30.0) (2026-01-24)

### Features

* **parser:** clarify semantic validation scope for language codes ([d0496d5](https://github.com/marco0560/Fontshow/commit/d0496d56f93bf64d18d0db5785e279edcc1f30ba))

### Bug Fixes

* **schema:** add languages_raw field to inventory schema ([7a3d70e](https://github.com/marco0560/Fontshow/commit/7a3d70e4319e0818008472aa75235c51cc6ae536))

## [0.29.5](https://github.com/marco0560/Fontshow/compare/v0.29.4...v0.29.5) (2026-01-24)

### Bug Fixes

* **build:** remove secondary CLI entrypoint ([328aaae](https://github.com/marco0560/Fontshow/commit/328aaaeb1c237f3bd3b4e2e0fd7ee57544180e98))
* **ci:** Merge branch 'fix/packaging-entrypoints-37' ([2ee192d](https://github.com/marco0560/Fontshow/commit/2ee192dada37c4cd95172774df7ad24a288c3342)), closes [#37](https://github.com/marco0560/Fontshow/issues/37)

## [0.29.4](https://github.com/marco0560/Fontshow/compare/v0.29.3...v0.29.4) (2026-01-23)

### Bug Fixes

* **cli:** align --quiet semantics with stderr behavior and argparse rules ([8dca108](https://github.com/marco0560/Fontshow/commit/8dca108b37da2964eff5ef6208bb4ecc29ca983a)), closes [#46](https://github.com/marco0560/Fontshow/issues/46)
* **cli:** normalize stdout/stderr and --quiet handling ([138215a](https://github.com/marco0560/Fontshow/commit/138215a4e789f003bfe524d80ed00183b0750a98))
* **cli:** normalize stdout/stderr behavior and align tests ([b2b9d65](https://github.com/marco0560/Fontshow/commit/b2b9d658392aff1447a3a4c609b8dec43615c30d)), closes [#46](https://github.com/marco0560/Fontshow/issues/46)

## [0.29.3](https://github.com/marco0560/Fontshow/compare/v0.29.2...v0.29.3) (2026-01-19)

### Bug Fixes

* **cli:** normalize quiet/verbose behavior across core commands ([b1c927f](https://github.com/marco0560/Fontshow/commit/b1c927f9c959a1cb11507da61c5ff988f2738edf)), closes [#44](https://github.com/marco0560/Fontshow/issues/44)

## [0.29.2](https://github.com/marco0560/Fontshow/compare/v0.29.1...v0.29.2) (2026-01-18)

### Bug Fixes

* **core:** align logging architecture, CLI dispatch and tests ([a33a3d2](https://github.com/marco0560/Fontshow/commit/a33a3d2e666cfb357e7eb3ae0ac47ff3b364bda0)), closes [#43](https://github.com/marco0560/Fontshow/issues/43)

## [0.29.1](https://github.com/marco0560/Fontshow/compare/v0.29.0...v0.29.1) (2026-01-15)

### Bug Fixes

* **core:** normalize error handling across commands ([0d7303a](https://github.com/marco0560/Fontshow/commit/0d7303aa4692eef864146962d0f3d8dde070aa76)), closes [#33](https://github.com/marco0560/Fontshow/issues/33)

## [0.29.0](https://github.com/marco0560/Fontshow/compare/v0.28.9...v0.29.0) (2026-01-15)

### Features

* **output:** improve readability of charset-derived arrays in JSON output ([5213d39](https://github.com/marco0560/Fontshow/commit/5213d39cf095acdc0ba96a0269d2ca4ecf8c463e)), closes [#30](https://github.com/marco0560/Fontshow/issues/30)

## [0.28.9](https://github.com/marco0560/Fontshow/compare/v0.28.8...v0.28.9) (2026-01-14)

### Bug Fixes

* **docs:** add awesome-pages plugin for better page ordering ([cad6975](https://github.com/marco0560/Fontshow/commit/cad6975327c7c9a1151f91e850559e6509357ee3))

## [0.28.8](https://github.com/marco0560/Fontshow/compare/v0.28.7...v0.28.8) (2026-01-14)

### Bug Fixes

* **build:** restrict setuptools package discovery to fontshow ([b02f626](https://github.com/marco0560/Fontshow/commit/b02f626d8095d108a4ca9437d9a7300c8aa36778))

## [0.28.7](https://github.com/marco0560/Fontshow/compare/v0.28.6...v0.28.7) (2026-01-09)

### Bug Fixes

* **parser:** preserve and decode Fontconfig charset raw data ([eac73c0](https://github.com/marco0560/Fontshow/commit/eac73c0d6464706bb170f712102391590722b5da))

## [0.28.6](https://github.com/marco0560/Fontshow/compare/v0.28.5...v0.28.6) (2026-01-09)

### Bug Fixes

* **dump:** correctly extract Fontconfig charset block ([e052f00](https://github.com/marco0560/Fontshow/commit/e052f003aa0e58f3954970951ca47611154027c1))

## [0.28.5](https://github.com/marco0560/Fontshow/compare/v0.28.4...v0.28.5) (2026-01-08)

### Bug Fixes

* **core:** enhance logging format with extra context ([4baf75b](https://github.com/marco0560/Fontshow/commit/4baf75bf19f01fbc24e0e6ce3aeee0cbdf7d229f))

## [0.28.4](https://github.com/marco0560/Fontshow/compare/v0.28.3...v0.28.4) (2026-01-08)

### Bug Fixes

* **core:** make TRACE level deterministic and preserve caller context ([ea91129](https://github.com/marco0560/Fontshow/commit/ea9112981583f2bb124d6741475ea846641798e7))
* **core:** stabilize TRACE semantics and logging tests ([3531dbc](https://github.com/marco0560/Fontshow/commit/3531dbcee5dc0cb569a9a7ca1b5b7049dbedfacf))

## [0.28.3](https://github.com/marco0560/Fontshow/compare/v0.28.2...v0.28.3) (2026-01-08)

### Bug Fixes

* **cli:** normalize main() contract and remove sys.exit from command logic ([9edeceb](https://github.com/marco0560/Fontshow/commit/9edecebcf25dc2d7ce8c4e4fdb2987d970d9e695))

## [0.28.2](https://github.com/marco0560/Fontshow/compare/v0.28.1...v0.28.2) (2026-01-07)

### Bug Fixes

* **cli:** unify CLI syntax across dispatcher and module entrypoint ([b970dd9](https://github.com/marco0560/Fontshow/commit/b970dd95933c9f6ad187481e1aeaec65aa570e2d))

## [0.28.1](https://github.com/marco0560/Fontshow/compare/v0.28.0...v0.28.1) (2026-01-07)

### Bug Fixes

* **cli:** align root fontshow version with package version ([c8fc976](https://github.com/marco0560/Fontshow/commit/c8fc976996a8d26797fc258d5adeb5f99e50445b))

## [0.28.0](https://github.com/marco0560/Fontshow/compare/v0.27.0...v0.28.0) (2026-01-07)

### Features

* **cli:** introduce unified fontshow dispatcher and subcommands ([ba3d522](https://github.com/marco0560/Fontshow/commit/ba3d522d797c2b6aac2c46c3571d00c156cecc64))

## [0.27.0](https://github.com/marco0560/Fontshow/compare/v0.26.0...v0.27.0) (2026-01-07)

### Features

* **parser:** add deterministic normalization of FontConfig charset ranges ([643a00e](https://github.com/marco0560/Fontshow/commit/643a00eb0ce8ea127d262c2c03ce144efe6bd5ef))
* **parser:** derive script coverage from charset-derived unicode blocks ([adc6347](https://github.com/marco0560/Fontshow/commit/adc6347a227416b2f9e6cb834811a8afbb5d0231))

## [0.26.0](https://github.com/marco0560/Fontshow/compare/v0.25.0...v0.26.0) (2026-01-06)

### Features

* **parser:** complete structured logging for inventory parsing ([c0318e5](https://github.com/marco0560/Fontshow/commit/c0318e560b4912372024acec6fad55840e59af1f))

## [0.25.0](https://github.com/marco0560/Fontshow/compare/v0.24.0...v0.25.0) (2026-01-06)

### Features

* **dump:** add file-level DEBUG/TRACE logging to fc_query_extract ([98b064d](https://github.com/marco0560/Fontshow/commit/98b064d628f3131ec1aa1fbc62b426b5e55860f3))

## [0.24.0](https://github.com/marco0560/Fontshow/compare/v0.23.0...v0.24.0) (2026-01-06)

### Features

* **dump:** add per-file DEBUG/TRACE logging to fc_query_extract ([57bd9d0](https://github.com/marco0560/Fontshow/commit/57bd9d06db26d744587bc6589f100198fd068729))

## [0.23.0](https://github.com/marco0560/Fontshow/compare/v0.22.0...v0.23.0) (2026-01-06)

### Features

* **dump:** add DEBUG logging for global flags ([1cc782c](https://github.com/marco0560/Fontshow/commit/1cc782c2aae7875229a364b932e4f10bacafb167))

## [0.22.0](https://github.com/marco0560/Fontshow/compare/v0.21.1...v0.22.0) (2026-01-06)

### Features

* **core:** add structured logging infrastructure and INFO logs ([3b494ad](https://github.com/marco0560/Fontshow/commit/3b494ada2df389bd8a44ff5708c35918ddb39e03))

## [0.21.1](https://github.com/marco0560/Fontshow/compare/v0.21.0...v0.21.1) (2026-01-05)

### Bug Fixes

* **validation:** add module entry point for preflight runner ([ae8f436](https://github.com/marco0560/Fontshow/commit/ae8f436613370b0633f12bb4ea71b120ea973cd3))

## [0.21.0](https://github.com/marco0560/Fontshow/compare/v0.20.1...v0.21.0) (2026-01-05)

### Features

* **validation:** add module entry point for preflight runner ([e877eba](https://github.com/marco0560/Fontshow/commit/e877ebad95206c2b09f66bd45c5224292a1921e3))

## [0.20.1](https://github.com/marco0560/Fontshow/compare/v0.20.0...v0.20.1) (2026-01-05)

### Bug Fixes

* **catalog:** ignore embedded sample text when language-incompatible ([356e618](https://github.com/marco0560/Fontshow/commit/356e6182bec0e82a749378a672a90cea9b5f6f50))

## [0.20.0](https://github.com/marco0560/Fontshow/compare/v0.19.2...v0.20.0) (2026-01-04)

### Features

* **validation:** stabilize class-based checks with BaseCheck and registry ([abf01c8](https://github.com/marco0560/Fontshow/commit/abf01c8cca39590329ddf46e41a3681f7322644b))

## [0.19.2](https://github.com/marco0560/Fontshow/compare/v0.19.1...v0.19.2) (2026-01-04)

### Bug Fixes

* **docs:** correct mkdocs repository metadata ([1425c1c](https://github.com/marco0560/Fontshow/commit/1425c1c152beb788d736c061adc6a994723d3f1f))

## [0.19.1](https://github.com/marco0560/Fontshow/compare/v0.19.0...v0.19.1) (2026-01-04)

### Bug Fixes

* **release:** cancel-in-progress to false in docs.yml ([0a8d566](https://github.com/marco0560/Fontshow/commit/0a8d566e6d5f81fe3712d8813d982b409f35424d))

## [0.19.0](https://github.com/marco0560/Fontshow/compare/v0.18.0...v0.19.0) (2026-01-04)

### Features

* **validation:** stabilize class-based checks and runner API ([79b7183](https://github.com/marco0560/Fontshow/commit/79b7183dd786ce7eaeeecd867ec4f87b814f0283))

### Bug Fixes

* **release:** remove @semantic-release/exec plugin ([af27035](https://github.com/marco0560/Fontshow/commit/af2703551fbe84d006a565636141c422346302d5))

## [0.18.0](https://github.com/marco0560/Fontshow/compare/v0.17.0...v0.18.0) (2026-01-03)

### Features

* **cli:** apply --quiet flag and add preflight summary ([c508003](https://github.com/marco0560/Fontshow/commit/c5080036a259407d3d2c7ebb6e255c41165e2b7d))

## [0.17.0](https://github.com/marco0560/Fontshow/compare/v0.16.0...v0.17.0) (2026-01-03)

### Features

* **cli:** add preflight-only CLI entry point ([f85ef90](https://github.com/marco0560/Fontshow/commit/f85ef90863afb088778ba55eccc7a25db8788e82))
* **core:** add preflight result renderer and exit code helper ([7d4d152](https://github.com/marco0560/Fontshow/commit/7d4d1529965bef09049f033b73a1a455de013dca))

## [0.16.0](https://github.com/marco0560/Fontshow/compare/v0.15.0...v0.16.0) (2026-01-03)

### Features

* **core:** add LuaLaTeX capability detection ([1cd5fae](https://github.com/marco0560/Fontshow/commit/1cd5faee45c719b7c20597bfd46a5f53af20c054))
* **core:** add preflight policy for LuaLaTeX capability ([5e7da46](https://github.com/marco0560/Fontshow/commit/5e7da462226a8378f1720833e02b5a70ee150fb8))

## [0.15.0](https://github.com/marco0560/Fontshow/compare/v0.14.0...v0.15.0) (2026-01-03)

### Features

* **core:** add font discovery capability to preflight check ([9bdf8b8](https://github.com/marco0560/Fontshow/commit/9bdf8b82f77446d675b533f904c9402fee542f19))

## [0.14.0](https://github.com/marco0560/Fontshow/compare/v0.13.0...v0.14.0) (2026-01-02)

### Features

* **core:** add environment and execution mode detection to preflight ([1b35996](https://github.com/marco0560/Fontshow/commit/1b35996d2de6e33580a7219f019633de0810374e))

## [0.13.0](https://github.com/marco0560/Fontshow/compare/v0.12.3...v0.13.0) (2026-01-02)

### Features

* **core:** add preflight scaffolding and result model ([0257da0](https://github.com/marco0560/Fontshow/commit/0257da0f2fbd2dfe9885d818265590b5bfb434b6))

## [0.12.3](https://github.com/marco0560/Fontshow/compare/v0.12.2...v0.12.3) (2026-01-02)

### Bug Fixes

* **git:** update .gitignore to excude .patch files ([14a729c](https://github.com/marco0560/Fontshow/commit/14a729c4409986428881086cefb519505bfd265b))

## [0.12.2](https://github.com/marco0560/Fontshow/compare/v0.12.1...v0.12.2) (2026-01-01)

### Bug Fixes

* **validation:** handle unknown schema versions gracefully ([754cea1](https://github.com/marco0560/Fontshow/commit/754cea184cdbaa1825d62e11c352f282f08349c9))

## [0.12.1](https://github.com/marco0560/Fontshow/compare/v0.12.0...v0.12.1) (2025-12-31)

### Bug Fixes

* **catalog:** escape LaTeX special characters in author and version strings ([acf7528](https://github.com/marco0560/Fontshow/commit/acf7528cd8001ff32b4179d9a73b994580bf1d69))

## [0.12.0](https://github.com/marco0560/Fontshow/compare/v0.11.0...v0.12.0) (2025-12-29)

### Features

* **dev:** add semantic validation for ISO language codes ([5e790be](https://github.com/marco0560/Fontshow/commit/5e790be8c7c283d0dd0c792b390a151778de2063))

## [0.11.0](https://github.com/marco0560/Fontshow/compare/v0.10.1...v0.11.0) (2025-12-29)

### Features

* **parser:** mark enriched inventories as schema version 1.1 ([d425ff1](https://github.com/marco0560/Fontshow/commit/d425ff17b641b9e8a54423d0c70c0708c8eeba40))

## [0.10.1](https://github.com/marco0560/Fontshow/compare/v0.10.0...v0.10.1) (2025-12-29)

### Bug Fixes

* **parser:** allow schema validation of raw inventories without metadata ([2fe9478](https://github.com/marco0560/Fontshow/commit/2fe9478d51ed75c7df3359933cc718d19f9b6bbb))

## [0.10.0](https://github.com/marco0560/Fontshow/compare/v0.9.0...v0.10.0) (2025-12-29)

### Features

* **dev:** add inventory schema validation against JSON Schema v1.1 ([48666ba](https://github.com/marco0560/Fontshow/commit/48666ba1397c165bfec17922bd8a299c9bb69adb))

## [0.9.0](https://github.com/marco0560/Fontshow/compare/v0.8.2...v0.9.0) (2025-12-29)

### Features

* **core:** define JSON Schema v1.1 for enriched inventory ([e205494](https://github.com/marco0560/Fontshow/commit/e20549401c4a5974fba01233e5eacf5bf51d88a1))

### Bug Fixes

* **cli:** add short options for existing arguments ([2aa3218](https://github.com/marco0560/Fontshow/commit/2aa32185d0233434e6a48b91f9fdaa437858540a))

## [0.8.2](https://github.com/marco0560/Fontshow/compare/v0.8.1...v0.8.2) (2025-12-29)

### Bug Fixes

* **build:** add packaging dependency for version tests ([93ff942](https://github.com/marco0560/Fontshow/commit/93ff9425650f80f6ae4f65aa72c1f92e4f96c468))

## [0.8.1](https://github.com/marco0560/Fontshow/compare/v0.8.0...v0.8.1) (2025-12-28)

### Bug Fixes

* **build:** adjust setuptools-scm version scheme ([733f6c7](https://github.com/marco0560/Fontshow/commit/733f6c7eddc58558bf446ca7c3e5b3e68fc2dd21))

## [0.8.0](https://github.com/marco0560/Fontshow/compare/v0.7.3...v0.8.0) (2025-12-28)

### Features

* **parser:** extend inference model with declared languages ([81b6432](https://github.com/marco0560/Fontshow/commit/81b6432d3ab679f8221efb47bf31accbba3079e2))

## [0.7.3](https://github.com/marco0560/Fontshow/compare/v0.7.2...v0.7.3) (2025-12-27)

### Bug Fixes

* **parser:** honor quiet flag in inventory validation output ([a7dc6e0](https://github.com/marco0560/Fontshow/commit/a7dc6e0eb1adabd243ad48da0a61e44f7911900b))

## [0.7.2](https://github.com/marco0560/Fontshow/compare/v0.7.1...v0.7.2) (2025-12-27)

### Bug Fixes

* **dump:** add stable font identity id field and test ([cf849f6](https://github.com/marco0560/Fontshow/commit/cf849f613f123ef825bb957f900a073343fc502e))

## [0.7.1](https://github.com/marco0560/Fontshow/compare/v0.7.0...v0.7.1) (2025-12-27)

### Bug Fixes

* **dump:** defer evaluation of type hints to avoid TTFont NameError ([df61007](https://github.com/marco0560/Fontshow/commit/df61007480d9dba7e740d892594e61e72761cdbb))

## [0.7.0](https://github.com/marco0560/Fontshow/compare/v0.6.1...v0.7.0) (2025-12-26)

### Features

* **parser:** enrich dump phase and strengthen parsing validation ([4976a19](https://github.com/marco0560/Fontshow/commit/4976a19b8e15c06dcd763bd6fe6b5ddf97c41636))

## [0.6.1](https://github.com/marco0560/Fontshow/compare/v0.6.0...v0.6.1) (2025-12-25)

### Bug Fixes

* **core:** improve inventory validation errors and mark fc-charset as experimental ([ce0df0c](https://github.com/marco0560/Fontshow/commit/ce0df0c4c8a199994f23dafa8696ad87a95089c3))

## [0.6.0](https://github.com/marco0560/Fontshow/compare/v0.5.0...v0.6.0) (2025-12-24)

### Features

* **core:** add clean_repo script to remove ignored artifacts ([cef0937](https://github.com/marco0560/Fontshow/commit/cef09376ac141e4d61427ccf861740486c1e250a))

## [0.5.0](https://github.com/marco0560/Fontshow/compare/v0.4.0...v0.5.0) (2025-12-24)

### Features

* **core:** package execution model, inventory validation, and docs update ([3965550](https://github.com/marco0560/Fontshow/commit/3965550574799a1d560b5c30defcebed635e85cf))

## [0.3.2](https://github.com/marco0560/Fontshow/compare/v0.3.1...v0.3.2) (2025-12-20)

### Bug Fixes

* **core:** deduplicate font families during LaTeX generation ([dfe9c71](https://github.com/marco0560/Fontshow/commit/dfe9c7158161913b544f83ca90c610a70ab1273b))

## [0.3.1](https://github.com/marco0560/Fontshow/compare/v0.3.0...v0.3.1) (2025-12-20)

### Bug Fixes

* **output:** group font faces by family to avoid duplicate catalog entries ([44af6f8](https://github.com/marco0560/Fontshow/commit/44af6f8e0a496e8aed74a339da63fc2b829fcaac))

## [0.3.0](https://github.com/marco0560/Fontshow/compare/v0.2.0...v0.3.0) (2025-12-18)

### Features

* **core:** add advanced font inventory with fontTools and caching ([23e6d00](https://github.com/marco0560/Fontshow/commit/23e6d00dffc65e8622a9e159a2215725b40be354))

## [0.2.0](https://github.com/marco0560/Fontshow/compare/v0.1.0...v0.2.0) (2025-12-17)

### Features

* **cli:** add initial changelog support ([a1e6498](https://github.com/marco0560/Fontshow/commit/a1e6498f6a190a5bb0cbc4ca394ca4b18a5576bd))

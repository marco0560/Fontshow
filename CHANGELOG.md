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

# Changelog

This document lists notable changes for each release and follows:

- Keep a Changelog: <https://keepachangelog.com>
- Semantic Versioning: <https://semver.org>

## [0.3.1](https://github.com/amal-khailtash/pyipxact-de/compare/v0.3.0...v0.3.1) (2026-10-20)

### Bug Fixes

- automate verified releases and complete documentation builds
  ([#11](https://github.com/amal-khailtash/pyipxact-de/issues/11))
  ([39da93f](https://github.com/amal-khailtash/pyipxact-de/commit/39da93fa9b0b9fb93b7cca779996ff6d8e61f166))

## [Unreleased]

### CI

- Consolidate numbered PR, CI, release, and publication workflows; reuse validated distributions
  and trigger release docs after PyPI.

### Fixed

- Clear repository registrations and cached entries when search paths are removed.
- Recover from unreadable caches and verify explicit/environment precedence and same-size file edits.
- Verify unsupported discovered documents do not prevent supported sibling registration.
- Reject unsupported catalog target versions and targets with incomplete VLNVs.
- Validate encoded local URI paths and isolate invalid escapes, UTF-8, and NUL paths per entry.
- Verify that vendor-extension lookalikes do not participate in catalog dependency discovery.
- Validate catalog reference VLNVs and diagnose referenced document-category mismatches.
- Recover per entry from invalid URIs and malformed target XML while processing valid siblings.
- Preserve first-record precedence for duplicate VLNVs during cache-only loading.
- Validate individual cache records and invalidate stale registrations using file fingerprints.
- Clear empty cached registries and skip deleted or modified cached files.
- Create cache directories and atomically replace cache files without losing prior data on failure.
- Expand cache recovery tests; focused loader coverage reaches 93%.
- Discover nested catalog dependencies through local URIs, including percent-encoded paths.
- Detect catalog cycles and shared targets; diagnose missing files and VLNV mismatches.
- Recheck unchanged catalogs when dependencies disappear or return; reject unsupported remote URIs.
- Make repository VLNV extraction independent of XML namespace prefixes.
- Discover uppercase XML extensions, retain search-path order, and deduplicate overlapping files.
- Warn on duplicate VLNVs and keep the first match on fresh and cached scans.
- Continue scanning after a discovered file disappears.

- Avoid duplicate API navigation trees and fully expanded sidebars during documentation rendering.
- Match the pysystemc screenshot badge order and labels for release automation, tests, publishing, and documentation.
- Match pysystemc CI/CD badge order and styling, including Documentation and RELEASE_PLEASE badges.
- Keep README badge categories aligned with pysystemc: CI/CD, Project, Docs, Meta, and Standards.
- Remove unsupported setup-uv input; uv selects the interpreter from .python-version.
- Split API documentation into module pages to avoid slow rendering of generated binding packages.

### Added

- Show the Release Please action version in the README Standards badges.
- Exercise verified uv trusted publishing and attestations through the manual TestPyPI workflow;
  confirm successful wheel and source publication.
- Align README badges with pysystemc and link documentation to Read the Docs.
- Add automated release PRs, verified PyPI publishing, PR build/test/documentation
  checks, Codecov reports, and Read the Docs configuration.

## [0.3.0] - 2026-10-19

### Added

- Add structured XML validation, offline local schema support, and detailed
  diagnostics for XML and schema failures.
- Add source-preserving choice enumeration operations and prefix-independent
  document identification across supported SPIRIT/IP-XACT versions.
- Add explicit offline schema validation with local Accellera schemas and detailed
  XSD diagnostics, including source locations and structured schema-load failures.
- Add Markdown lint configuration and normalize repository documentation formatting.
- new persistent xml registration `register` with `scan`, and `list` subcommands.
- add registry loader and scanner for IP-XACT XML files, enhance VLNV management
- Expand the categorized feature checklist to track all planned capabilities and all 2,469 TGI operation entries,
  distinguishing verified work from outstanding work.
- Add the bus-definition extended-VLNV accessor and feature implementation checklist.

### Fixed

- Preserve the QName of empty generic bus-interface choices during XML round trips.
- Update catalog TGI URI construction and test fixtures for regenerated keyword-only models.
- Verify rejection of experimental IPXACT/2.0 files included in upstream examples.
- Return structured validation failures for missing and malformed XML documents.
- Identify SPIRIT/IP-XACT documents from the expanded root namespace, supporting
  default and arbitrary prefixes; reject unsupported versions and allow retry
  after failed identification.
- Repair choice enumeration creation, source-expression access and parent ownership
  for new and parsed children; reject invalid removal handles.
- Align bus capability setters and optional broadcast/extends removers with Annex F argument names; reject non-Boolean
  capability values without changing documents.
- Align bus-definition extends and choice inputs with Annex F; preserve choice enumerations and correct
  choice/system-group ownership during removal.

### Changed

- Regenerate Accellera bindings with keyword-only models and required fields.
- Require Python 3.14 and refresh locked dependencies and CI setup.

## [0.2.0] - 2025-09-01

### Added

- enhance documentation configuration and update project classifiers (bfb3f16)

### Changed

- commented out "illegal" signal directions in XML files to avoid schema violations.

### Build/CI

- validation for `CHANGELOG.md` Unreleased section in manual release workflows (fba4a99)
- update workflow names for consistency and remove obsolete workflows (99f193d)
- update CI workflow name for consistency, enhance README with project badges, and improve documentation styling
  (0e7abfc)

## [0.1.0] - 2024-12-01

- Migration to xsData and repository restructure.
  - Moved to xsData[^1] instead of PyXB[^2] that provides a cleaner Pythong interface using dataclasses.
  - Old PyXB version has been moved to `PyXB` directory.

### Added

- IP-XACT/SPIRIT bindings generated with xsData.
- Missing bindings based on xsData PR tefra/xsdata#1100.
- XSL files for transformations/translations.
- Accellera XML tests.

### Changed

- Regenerated bindings after xsData bugfix tefra/xsdata#1106.
- Fixed Makefile to update binding generation.
- Repository layout updates and file moves.
- Minor updates and root file refresh.

### Docs

- Updated text. (95ae72c)

## [0.0.0] - 2016-11-15

### Added

- Initial commit and Accellera schemas submodule.
- Generated bindings snapshot.

[Unreleased]: https://github.com/amal-khailtash/pyipxact-de/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/amal-khailtash/pyipxact-de/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/amal-khailtash/pyipxact-de/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/amal-khailtash/pyipxact-de/releases/tag/v0.1.0
[0.0.0]: https://github.com/amal-khailtash/pyipxact-de/tree/b55e147

[^1]: [xsData - Naive XML & JSON Bindings for python](https://github.com/tefra/xsdata)
[^2]: [PyXB: Python XML Schema Bindings](https://pyxb.sourceforge.net/)

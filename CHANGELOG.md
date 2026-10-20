# Changelog

This document lists notable changes for each release and follows:

- Keep a Changelog: <https://keepachangelog.com>
- Semantic Versioning: <https://semver.org>

## [0.4.1](https://github.com/amal-khailtash/pyipxact-de/compare/v0.4.0...v0.4.1) (2026-10-20)


### Bug Fixes

* complete abstraction contracts and consolidate depot updates ([#18](https://github.com/amal-khailtash/pyipxact-de/issues/18)) ([7586431](https://github.com/amal-khailtash/pyipxact-de/commit/7586431ab172e014755a1cb6cf9f9e59144a0f3e))
* synchronize and activate Read the Docs release versions ([#16](https://github.com/amal-khailtash/pyipxact-de/issues/16)) ([c5f7821](https://github.com/amal-khailtash/pyipxact-de/commit/c5f7821da356d3bd5ce65260464f9adf37655825))

## [Unreleased]

### Fixed

- Correct logical port qualifiers using selective generated mode handles, ownership, and scoped XML verification.
- Correct mode initiative and property identity using selective generated mode handles, ownership, and scoped XML verification.
- Correct wire mode removers using selective generated mode handles, ownership, and scoped XML verification.
- Correct transactional mode removers using selective generated mode handles, ownership, and scoped XML verification.
- Correct wire mode getters using selective generated mode handles, ownership, and scoped XML verification.
- Correct transactional mode getters using selective generated mode handles, ownership, and scoped XML verification.
- Correct seven wire/transactional property setters to edit the supplied mode handle selectively.
- Validate mode enums, initialize generated protocol types, and preserve property handles during updates.
- Implement logical mode setters and validated system-group editing using generated mode models.
- Preserve mode identity and correct creation ownership for immediate removal without traversal.
- Traverse logical-port system modes for both generated styles and restore parsed mode ownership.
- Implement typed wire/transactional mode removal with selective detachment and handle invalidation.
- Initialize packet-field qualifiers without replacing existing content or handles.
- Remove optional packet-field qualifiers and values with correct ownership and handle invalidation.
- Verify explicit packet/field endianness values and absence through XML round trips.
- Implement packet-field creation and selective packet/field removal with parsed ownership.
- Add validated packet/field endianness editing and expression setters that preserve handles and metadata.
- Validate logical-port packet creation before mutation and restore parsed packet/field ownership.
- Add packet-field value handles and preserve width/value expressions, qualifiers, and child identity.
- Implement standard logical-port mode names and grouped wire/transactional system modes.
- Correct six mode getters to use generated style-choice fields and preserve mode identity and XML values.
- Create logical abstraction ports with generated wire/transactional choice fields and validate inputs before mutation.
- Restore parsed logical-port parent ownership and verify names, styles, match flags, and selective removal.
- Use supplied enumeration arrays for abstraction-definition choices and validate bus/abstraction choice inputs atomically.
- Restore choice parent ownership during root traversal so parsed choices can be removed reliably.
- Implement interface, struct, and union abstractor ports using generated structured choice models.
- Preserve required sub-port names, structured type names, direction values, and parent identity in XML round trips.
- Implement abstractor wire and transactional ports using generated choice fields and validated schema values.
- Validate abstractor view names and repair port/view parent paths for ordered traversal and removal.
- Initialize abstractor generators with generated URI values and choices with standard enumeration arrays.
- Validate generator/choice inputs before mutation and repair parent paths for selective removal.
- Use standard interface handles for abstractor abstraction-type creation and traversal.
- Validate abstraction references and component-instantiation names before mutation.
- Repair abstraction-type and component-instantiation parent paths for removal and verify XML round trips.

- Synchronize Read the Docs release tags, wait for discovery, activate versions, and request builds after publication.
- Validate abstractor mode and bus-reference updates before mutation; preserve mode handles and existing groups.
- Correct abstractor file-set parent paths and verify add/list/remove behavior and XML round trips.
- Implement standard abstraction-definition and abstractor creation contracts with generated models.
- Correct abstraction port-style traversal for generated wire/transactional choice fields.
- Verify related bus references, interface/port traversal, mode handles, input faults, and XML round trips.

## [0.4.0](https://github.com/amal-khailtash/pyipxact-de/compare/v0.3.1...v0.4.0) (2026-10-20)

### Features

- Implement standard root creation and robust repository discovery
  ([#14](https://github.com/amal-khailtash/pyipxact-de/pull/14)).

### CI

- Dispatch production publication directly so PEP 740 identity matches the PyPI trusted publisher.
- Consolidate numbered PR, CI, release, and publication workflows; reuse validated distributions
  and trigger release docs after PyPI.

### Fixed

- Implement bus-definition creation with Boolean capabilities and generator-chain creation with an initial generator.
- Verify strict Boolean bus-capability setters, duplicate creation, parent identity, and XML preservation.
- Implement VLNV-based catalog, component, design, design-configuration, and type-definition creation.
- Return generated roots with registry identity, reject invalid VLNVs, and return null for duplicates.
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

- Record standard-first implementation priorities and defer further caching and GUI work.
- Show the Release Please action version in the README Standards badges.
- Exercise verified uv trusted publishing and attestations through the manual TestPyPI workflow;
  confirm successful wheel and source publication.
- Align README badges with pysystemc and link documentation to Read the Docs.
- Add automated release PRs, verified PyPI publishing, PR build/test/documentation
  checks, Codecov reports, and Read the Docs configuration.

## [0.3.1](https://github.com/amal-khailtash/pyipxact-de/compare/v0.3.0...v0.3.1) (2026-10-20)

### Bug Fixes

- automate verified releases and complete documentation builds
  ([#11](https://github.com/amal-khailtash/pyipxact-de/issues/11))
  ([39da93f](https://github.com/amal-khailtash/pyipxact-de/commit/39da93fa9b0b9fb93b7cca779996ff6d8e61f166))


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

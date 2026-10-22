# Changelog

This document lists notable changes for each release and follows:

- Keep a Changelog: <https://keepachangelog.com>
- Semantic Versioning: <https://semver.org>

## [0.6.0](https://github.com/amal-khailtash/pyipxact-de/compare/v0.5.0...v0.6.0) (2026-10-21)


### Features

* expand TGI BASE access and organize Accellera APIs ([#23](https://github.com/amal-khailtash/pyipxact-de/issues/23)) ([3f2d0ac](https://github.com/amal-khailtash/pyipxact-de/commit/3f2d0ac035d9007420618b1b124bfff380ef0919))

## [0.5.0](https://github.com/amal-khailtash/pyipxact-de/compare/v0.4.2...v0.5.0) (2026-10-21)


### Features

* expand standard validation and generated TGI contracts ([#21](https://github.com/amal-khailtash/pyipxact-de/issues/21)) ([7e35647](https://github.com/amal-khailtash/pyipxact-de/commit/7e35647bced07206e2a69bee62765b334a272f48))

## [0.4.2](https://github.com/amal-khailtash/pyipxact-de/compare/v0.4.1...v0.4.2) (2026-10-20)


### Bug Fixes

* correct generated-model TGI editing and lifecycle contracts ([#19](https://github.com/amal-khailtash/pyipxact-de/issues/19)) ([c5e48af](https://github.com/amal-khailtash/pyipxact-de/commit/c5e48af79eeb3b385147ff6872a5efc1e41259b0))

## [0.4.1](https://github.com/amal-khailtash/pyipxact-de/compare/v0.4.0...v0.4.1) (2026-10-20)


### Bug Fixes

* complete abstraction contracts and consolidate depot updates ([#18](https://github.com/amal-khailtash/pyipxact-de/issues/18)) ([7586431](https://github.com/amal-khailtash/pyipxact-de/commit/7586431ab172e014755a1cb6cf9f9e59144a0f3e))
* synchronize and activate Read the Docs release versions ([#16](https://github.com/amal-khailtash/pyipxact-de/issues/16)) ([c5f7821](https://github.com/amal-khailtash/pyipxact-de/commit/c5f7821da356d3bd5ce65260464f9adf37655825))

## [Unreleased]

### Added

- Complete standard Assertion Boolean/source/handle getters and generated XML creation, expression editing and subtree removal.
- Complete Access policy mode/external-definition references, typed field-data and write-constraint choices, source expressions and owned lifecycle edits.
- Complete Element attribute typed metadata editing, schema-default removal and document-scoped reference resolution.
- Complete File builder language-tool/linker choices, expression children and component-scoped generator references.
- Complete File set file/function/reference editing with schema types, local fileId resolution and parsed ownership.
- Complete Access handle traversal and schema-selected creation, typed path segments/slices, Boolean force and owned removals.
- Complete Generator phase resolution and metadata/group/transport editing with typed ownership and atomic validation.
- Complete Generator chain editing and selector references using generated mixed collections and schema choices.
- Add make coverage HTML/XML reports including generated org bindings; build documentation directly under build/docs.
- Complete Vector traversal and lifecycle with generated endpoints, self-contained SV integer evaluation and parsed ownership.
- Complete Vendor extensions XML fragment retrieval, append, replacement and removal while preserving namespaces and wildcard content.
- Remove owned children by identity to preserve equal-valued siblings.
- Complete Array editing across bounded, register and field arrays with typed ownership and SystemVerilog integer expression evaluation.
- Complete Instantiation reference-node, VLNV and typed target-resolution functions with atomic setters.
- Restore detailed standard-linked module/function docstrings, argument/return documentation and section headings.
- Complete Top element registry enumeration, XML file-location metadata and editing-start contracts.
- Verify all Choice operations with parsed ownership, schema-valid edits and atomic string validation.
- Complete remaining Abstraction definition TGI editing and getters, with slang-backed integer expressions, atomic extends references and schema-valid drive/load constraints.
- Resolve Clearbox references within their owning component and abstractor-instance views through the referenced abstractor VLNV.
- Complete Abstractor interface and file-set-reference-group removal with parsed ownership and descendant invalidation.
- Add pyslang-backed SystemVerilog expression parsing and a highlighted REPL under amal.eda.systemverilog, with a Makefile target.
- Verify BASE unit, units, usageType, type and reset-type reference attributes.
- Verify BASE custom, other, modify, text and flowType attributes.
- Copy Annex E expression reference into documentation and link it from the SV parser guide.
- Verify BASE port, sub-port, field, memory-map and power-domain reference source attributes.
- Verify BASE interface mode, isIO, group selection operator, packed and phantom attributes.
- Implement BASE wildcard attribute lookup/names and verify libext, level and imageType source attributes.
- Verify BASE bus, component-instance, choice, mode and view reference source attributes.
- Verify BASE document-reference vendor, library, name, version and executable image ID attributes.
- Verify BASE address-block, address-space, alternate-register, bank and register reference source attributes.
- Verify BASE help, prompt, prefix, user and hierarchical path attributes with XML reloads.
- Verify BASE force, mandatory, misalignmentAllowed, replicate and unique boolean flags.
- Return BASE configuration groups as XML list text and constrained values as copied string lists; verify index, order and constraint-set ID attributes.
- Verify BASE resolve, scope, sign, test constraint and usage configuration attributes.
- Verify BASE XML identity attributes and share the vector ID getter across category and package exports.
- Verify BASE exact, externalDeclarations, implicit, strict and hidden boolean attributes.
- Read BASE minimum/maximum source, integer and double attributes; reject fractional or non-finite integer conversions.
- Verify BASE data type, delay, direction and driver attributes with generated XML bindings.
- Read BASE array ID, bank alignment, cell strength and clock attributes using generated XML metadata.
- Read BASE boolean XML attributes through generated binding metadata, preserving false values.
- Read register/field array dimensions and strides through BASE getters with typed parent checks and parsed ownership.
- Traverse bounded arrays and retrieve ordered left/right values, source expressions and owned handles through BASE getters.
- Read CPU region offset/range through BASE getters using region handles and owned parsed children.
- Read segment offset/range literals, source expressions and owned child handles through six BASE getters.
- Move TGI to ``amal.eda.accellera.ipxact.v1685_2022.tgi`` and update application and test imports.
- Traverse CPU and generator transport children through standard BASE handles.
- Read CPU source expressions with stable parsed child handles through BASE getters.
- Read catalog file URI and four-part VLNV metadata through BASE handles.
- Traverse catalog file categories using standard BASE handles and parsed ownership.
- Read generated generator-chain group selectors through BASE getters.
- Traverse generated mixed generator-chain collections through BASE getters.
- Read generated generator API/executable metadata with parsed child ownership through BASE getters.
- Read instance-generator groups and scope with stable typed handles through BASE getters.
- Return generated function return/source types and source reference names through BASE getters.
- Traverse executable-image linker choices and restore parsed child ownership through BASE getters.
- Consolidate repeated TGI checklist entries into their canonical category entries.
- BASE function source metadata returns generated strings/enum literals and stable child handles with parsed ownership; effective expression evaluation and file target resolution remain pending.
- BASE file-set collections preserve source order and stable handles, restore parsed ownership and preserve serialized content during traversal.
- BASE file identity/source metadata traversal restores parsed child ownership and preserves optional states, lexical source and schema metadata.
- BASE file collection getters preserve order/source values, return define value text, and restore parsed ownership without changing document content.
- Generated default builders validate standard file types, restore parsed ownership, preserve siblings and enforce typed removal lifetime.
- Generated clearbox type enums and optional Boolean driveable edits validate inputs atomically and survive schema validation/XML reload.
- Generated build-command target and replacement source editing with typed ownership, identity and removal lifetime; effective expression evaluation remains pending.
- Build command/flags source editing preserves generated identity and append/extensions, supports standard buildCommand handles and legacy file handles, and invalidates removed expressions.
- Generated file-builder source edits preserve child identity and metadata; removals invalidate child handles. Expression evaluation remains pending.
- Generated required location/slice/pathSegments preserve HDL source, parsed ownership and descendant invalidation. Clearbox target resolution remains pending.
- Restore parsed reference ownership, validate schema lexical names, preserve siblings and invalidate removed handles. Target existence/configured resolution remain pending.
- Preserve absent/false/true virtual source states, reject non-Boolean edits, restore parsed language ownership and invalidate removed language handles.
- Support selective optional instantiation name removal with parsed XML and lifecycle verification.
- Validate instantiation source name edits while preserving unrestricted XML strings and absent values.
- Preserve generated instantiation language and reference metadata during validated updates.
- Create generated component, design and design-configuration instantiations with required references and ownership.
- Add typed generated viewRef source-name access and editing with stable identity and package exports.
- Traverse and remove typed component instantiations with ownership and descendant invalidation.
- Restore registered parsed view ownership for typed local reference resolution and selective lifecycle operations.
- Resolve view instantiation targets by type and name within the owning component.
- Support component view instantiation source-reference getters, setters and removers for all three reference types.
- Support generated view environment metadata, syntax validation, parsed ownership and selective removal.
- Create generated structured component interface, struct and union ports with standard signatures and type metadata.
- Create generated component wire/transactional ports, views and named clock drivers with standard arguments and ownership.
- Support standard single-child component removers with parsed ownership and descendant handle invalidation.
- Invalidate descendant TGI model handles when their owning subtree is removed or replaced.
- Add component direction and timing-clock semantic validation with named/default clock-driver resolution.
- Expose scoped XML semantic validation in Python and CLI with offline schemas, source diagnostics and failure exit status.
- Add IEEE abstraction constraint semantic checks with rule IDs and XPath diagnostics for direction and clock references.

### Fixed

- Correct logical port style setters to use the generated exclusive choice while preserving port and packet content.
- Implement timing constraint lifecycle with generated models, ownership and scoped validation.
- Implement drive and load constraint traversal with generated models, ownership and scoped validation.
- Implement wire mode constraint containers with generated models, ownership and scoped validation.
- Correct wire driver metadata using selective generated mode handles, ownership, and scoped XML verification.
- Correct wire default expressions using selective generated mode handles, ownership, and scoped XML verification.
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

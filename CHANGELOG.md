# Changelog

This document lists notable changes for each release and follows:

- Keep a Changelog: <https://keepachangelog.com>
- Semantic Versioning: <https://semver.org>

## [Unreleased]

### Fixed

- Complete six Register field type-identifier and volatility operations with validated ordered choices, inline default-false semantics, preserved alias/reference branches and sibling data, and exact setter keywords.
- Complete six Register type-identifier and volatility getters, setters and removals with ordered schema choices, validated names and Boolean values, preserved wrapper identity, and explicit absent-volatility semantics.
- Complete eight Register field offset and width operations with typed expression children, preserved metadata and handles, validated scalar containment, and schema-valid alias/reference replacement.
- Complete eight Register address-offset and size TGI operations using generated models, constant-expression validation, owned handles and metadata-preserving edits. Validate scalar field containment before resizing and support inline definition choice replacement.

## [0.9.0](https://github.com/amal-khailtash/pyipxact-de/compare/v0.8.0...v0.9.0) (2026-10-26)


### Features

* complete driver, slice, design, indirect interface and type definitions TGI ([#30](https://github.com/amal-khailtash/pyipxact-de/issues/30)) ([092859c](https://github.com/amal-khailtash/pyipxact-de/commit/092859c69f6a7fc42ac3000588159791f6fee1a6))

### Fixed

- Complete nine expression-bearing Type definitions and field-enumeration lifecycle operations with shared constant parsing, generated models and typed ownership. Require explicit keyword-only width in addEnumerationDefinition to resolve the Annex signature mismatch with mandatory XML width; retain the published domainTypeDefID argument name for typed field-value removal.

- Implement five external Type definitions and mode/view link lifecycle operations using generated component holders, validated VLNVs and shared reference setters.

- Implement seven generated named Type definitions builders and typed field-access-policy removal using shared collection lifecycle validation.

- Complete Indirect interface bridge creation, traversal and removal, endianness mutation, memory-map choice replacement and alias/broadcast optional-reference removal.

- Implement seven Indirect interface getters with standard defaults, shared constant evaluation, typed required references and scalar memory-map target resolution.

- Implement eight Indirect interface named reference setters using shared Slice wrapper mutation with index and metadata preservation.

- Implement six Indirect interface root-reference setters through shared Slice choice mutation with wrapper preservation and atomic branch validation.

- Implement ten Indirect interface memory-remap getters and map/remap removers using generated choices, map-qualified target resolution and owned handle invalidation.

- Implement nine Type definitions collection removers with shared typed ownership checks, subtree invalidation and optional-holder pruning.

- Implement view and external VLNV reference setters plus mode/reset/view collection removers with generated wrapper preservation, shared validation, typed ownership and empty-holder pruning.
- Implement four mode/reset reference setters and three external-link removers with generated wrapper preservation, known local uniqueness, parsed ownership checks and empty-holder pruning.
- Implement seven Type definitions view/reference lookups with required typed reference handles, validated stored VLNV, registered document resolution and local view target ownership.
- Implement eight Type definitions mode/reset link reference getters using required generated reference handles, correct reference fields and shared XML Name validation with indirect interfaces.
- Implement six Type definitions mode/view/reset and external-link collection getters with typed generated members, ordered handles, preserved tuple storage and restored descendant ownership.
- Implement nine Type definitions collection getters with typed generated members, ordered handles, preserved tuple storage and restored descendant ownership.
- Implement seven Type definitions enumeration traversal/lifecycle operations with generated builders, unique XML names, known value-width checks, preserved width metadata and parsed-owner subtree removal.
- Implement four Type definitions address-unit expression setters and three required enumeration-width getters with native Annex signatures, generated wrapper preservation, shared constant-expression validation and correct decimal boundary values.
- Implement register-file definition address-unit value/expression/ID getters and four typed definition address-unit removers, reusing expression evaluation and invalidating removed child handles while preserving sibling identities.
- Implement nine Type definitions address-unit value, expression and ID getters for address-block, bank and memory-remap definitions using shared SystemVerilog evaluation, schema/TGI numeric bounds and typed child ownership.
- Fix eight Indirect interface address-space/memory-map getters and two address-space removers to use generated reference choices, with shared Slice validation, owned handles and atomic rejection of malformed branches.
- Implement eight Indirect interface bank/register-file path add/remove operations with normalized XML names, atomic typed mutation, strict owner membership and descendant handle invalidation; reuse shared Slice path helpers and guard against foreign-child removal.
- Implement ten Indirect interface ordered bank/register-file reference getters and alternate-register removers with shared validation, preserved metadata, and owned handle lifetimes.
- Implement ten Indirect interface register and alternate-register reference operations with shared typed name/handle access and indexed register subtree removal.
- Implement ten Indirect interface address-block and field-reference operations using shared source/traversal helpers, XML name validation, and indexed subtree removal.
- Complete all 70 Design TGI operations with schema-valid choice and connection builders, guarded owned removal, and scoped current/top generator Design context.
- Implement eight Design power-domain link operations with shared typed traversal, SystemVerilog string expressions, preserved metadata, and registered referencing-component domain resolution.
- Implement seven Design component-instance operations with generated name/reference wrappers, registry target resolution, unique names, shared metadata-preserving VLNV edits and owned subtree removal.
- Implement eight Design monitor-endpoint and interconnection setter operations using shared builders, owned replacement/removal, role-aware handles and schema instance-path validation.
- Implement nine Design active-interface, hierarchical-interface and excluded-port lifecycle operations with generated fields, schema name validation, ordered ownership and strict subtree removal.
- Implement five Design tied-value operations through shared expression and child-lifecycle functions, validating unsigned constants and open/default alternatives while preserving source, bounds and metadata.
- Implement eight Design ad-hoc connection and endpoint lifecycle operations with shared builders, schema name validation, unique connection names, ordered references and owned subtree removal.
- Implement nine Design port-reference traversal operations with generated mixed holders, stored names, shared ordered sub-port validation, and strict owner/list membership on removal.
- Implement six Design internal/external port part-select operations using shared generated models and SV expression validation, preserving metadata and invalidating removed subtree handles.
- Complete all 67 Slice TGI operations with document-local target resolution, selected map/remap context, exact bank/register-file paths, and banked address-block support.
- Validate mode port-builder references with the standard portName restriction and record a deferred ossschem GUI integration investigation.
- Implement nine Slice register-reference and mode-builder operations with complete Annex/WSDL signatures, generated required references, and parsed subtree removal.
- Implement eight FieldSlice bank/register-file reference-path operations with standard name signatures, generated ordered wrappers, and owned subtree removal.
- Implement ten FieldSlice address-space/map/remap reference-choice operations with generated wrappers, atomic choice updates, and removed handle invalidation.
- Implement ten FieldSlice named-reference operations with standard signatures and generated wrappers.
- Normalize referenced XML names while preserving indices, metadata and wrapper identity; remove alternate-register references through their owning slice.
- Implement five FieldSlice range operations for mode and field-map slices using shared generated range helpers.
- Correct FieldSlice range source-array and owner-based mutation signatures while preserving expression metadata and descendant lifetimes.
- Implement eight mode port-slice reference and part-select operations using generated models and shared atomic setters.
- Correct Slice reference signatures and name-return contracts, normalize referenced port names, and preserve wrappers and subtree lifetimes.
- Reject reversed unsigned expression bounds even when constant identifiers remain unresolved.
- Implement five Slice path/location operations with generated path holders, ordered traversal, and parsed ownership recovery.
- Validate HDL path string expressions through SvExpressionParser while preserving source text and required containers on removal.
- Implement six HDL Slice range operations with generated models, preserved expression metadata, and shared Driver range helpers.
- Correct Slice range setter and remover signatures and validate endpoint changes atomically.
- Complete Driver choice builders with standard expression arguments, atomic validation, and shared low-level setters.
- Validate and normalize unique Driver view references using the standard NMTOKEN rules.
- Correct Driver removal handles, invalidate removed subtrees, and recover parsed view-reference ownership.
- Preserve Driver range/default expression metadata and validate mutations before changing generated choice or endpoint values.
- Implement standard string-expression signatures for clock pulse and SingleShotDriver setters, preserving wrapper identity and metadata.
- Validate clock pulse expressions using the shared SystemVerilog one-bit cast and enforce binary SingleShotDriver values.
- Update Codecov main coverage from the immutable release tag after verified PyPI publication.

## [0.8.0](https://github.com/amal-khailtash/pyipxact-de/compare/v0.7.0...v0.8.0) (2026-10-24)


### Features

* complete standard TGI contracts and align verified release automation ([#27](https://github.com/amal-khailtash/pyipxact-de/issues/27)) ([0e040ba](https://github.com/amal-khailtash/pyipxact-de/commit/0e040ba55ef6d3abc854ebb4b7cb001eddb83a1b))

### Fixed

- Preserve design-configuration choice references by refusing to remove a choice while parameters still reference it.
- Defer XML and TGI imports for lightweight CLI commands to reduce startup overhead.
- Make parallel test collection deterministic and protect shared example-cache preparation.
- Include generated `src/org` schema bindings in published Codecov reports.
- Retain owned TGI children to prevent stale ownership links after object identity reuse.
- Exit quietly when a downstream pipe closes during CLI output.
- Check each cached source file once when validating registry metadata.
- Exit quietly with status 130 when Ctrl-C interrupts a CLI command.
- Preserve the saved registry when listing documents or running commands without configured search paths.

### Features

- Align feature CI, metadata-only release PRs, reusable distribution builds, verified PyPI publication and draft release/documentation activation with pysystemc.
- Complete three OtherClockDriver pulse-value getters and six clock timing setters with exact expression-string arguments, shared real validation, atomic edits and preserved metadata/ownership.
- Complete nine SingleShotDriver timing and value getters with shared expression evaluation, declared real bounds, zero-or-one logic values, source and unit preservation and owned handles.
- Complete nine OtherClockDriver timing getters with shared SystemVerilog real evaluation, declared bounds, source and unit preservation, owned handles and distinct driver type validation.
- Complete six Driver range and view-reference getters with shared constant evaluation, unsigned bounds, source preservation, owned handles and document-scoped view resolution.
- Complete eight Driver value and child-handle getters with generated choice routing, SystemVerilog bit casts, shared default-expression evaluation and preserved ownership.
- Complete nine clock-driver timing getters with SystemVerilog real-expression evaluation, declared bounds, exact source text, preserved units and owned element handles.
- Complete the six remaining design-configuration choice and View creation/removal operations with required enumerations, unique XML names, shared setters, parsed ownership recovery and optional-holder cleanup.
- Run tests and combined coverage in parallel, reuse cached Leon2 examples without network checks, and provide an explicit `--refresh-examples` test option.
- Complete seven design-configuration View operations with owned handles, shared override access, unique instance names, NMTOKEN view references and identity-preserving edits.
- Complete six design-configuration interconnection operations with registered target lookup, atomic required abstractor creation, reference validation and owned removal; fix the two underlying Design collection getters to read the generated mixed list.
- Complete nine design-configuration design/generator reference operations with typed registry lookup, identity-preserving edits, unique generator references and owned subtree removal.
- Complete seven design-configuration collection operations with ordered owned handles, scoped endpoint uniqueness, atomic abstractor-group creation and parsed subtree removal.
- Complete nine design-configuration abstractor-instance operations with registry target resolution, schema-valid names, atomic edits, preserved configurable references and owned removal; align creation arguments with Annex F.
- Report registry loading and scan progress, discover XML files progressively and print compact file/edition/type scan results.
- Support `registry list --color=always` for colored pipes, with `auto` and `never` modes.
- List saved registry snapshots without checking or refreshing sources, batch styled output and provide fast plain output with `--plain`; `registry scan` updates the inventory.
- Show each document's schema family and edition in an aligned column beside registry listings in tree and flat formats.
- Register recognized top-level SPIRIT/IP-XACT documents from every available schema edition during scans, catalog discovery and cache restoration; retain IP-XACT 1685-2022 as the supported TGI edition.

## [0.7.0](https://github.com/amal-khailtash/pyipxact-de/compare/v0.6.0...v0.7.0) (2026-10-22)


### Features

* complete standard TGI categories and add SV expression tools ([#25](https://github.com/amal-khailtash/pyipxact-de/issues/25)) ([cc7a6ff](https://github.com/amal-khailtash/pyipxact-de/commit/cc7a6ffd0deb53959cd0b295b6d070d660f08fd3))

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

### Detailed changes

### Added

- Complete Miscellaneous contracts with owned argument/define values, SV expression resolution, typed part selects, filename/catalog registration, validated document persistence and administrative status calls.
- Complete Constraint contracts with typed cell choices, effective count defaults, unsigned SV vector/count expressions, preserved wrappers and owned removal.
- Complete Register file contracts with typed inline/reference choices, scoped external definitions, unsigned expressions, schema-valid factories and owned atomic removal.
- Use native Python 3.14 annotations in handwritten modules, complete function signatures and model helper types, and preserve standard commentary.
- Complete Power contracts with scoped domain references, typed constraints and instance links, preserved expression metadata, uniqueness checks and owned removal.
- Complete Port map contracts with typed logical/physical choices, numeric/source getters, schema-valid combined part selects, preserved metadata and owned atomic edits.
- Complete CPU BASE and EXTENDED contracts with scoped memory-map references, typed regions and executable images, unsigned expressions, atomic edits and handle-preserving ownership.
- Complete Configurable element definition/default and override contracts with typed XML source mapping, contextual reference/choice/range checks, schema-valid atomic edits and owned removal.
- Complete Parameter BASE and EXTENDED contracts with scoped parameter/file references, owned Value handles, shared numeric/source evaluation and atomic typed edits.
- Complete Name group source getters, standard setter signatures and absent-content rules, schema-specific names, generated text ownership and atomic registered document renaming.
- Complete Module parameter BASE and EXTENDED contracts with generated module/type holders, numeric/source values and owned atomic edits.
- Complete Constraint Set timing-percentage traversal and atomic additions with clock-name validation and parsed handle ownership.
- Complete Component traversal, typed required-argument factories, mode expressions, reference edits and owned removal with handle invalidation.
- Complete Catalog category traversal and typed entry edits, cross-category name/VLNV uniqueness, and owned removal with handle invalidation.
- Complete Bus interface modes, typed abstraction and local references, SV numeric/source values, remapping, channels and owned atomic edits.
- Complete Bus definition numeric/source getters, typed limits and references, strict capabilities, and owned choice/system-group edits.
- Complete Address space SV numeric/source getters, alias and local-map traversal, executable-image references, typed block creation and atomic owned edits.
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

- Organize IEEE 1685-2022 tests under a standard/version hierarchy, preserve common test modules and isolate XML context caches between version-specific tests.
- Consolidate shared TGI expression, range and model traversal implementations, and delegate higher-level value operations to existing standard functions while preserving domain policies and commentary.
- Restore Miscellaneous standard commentary and inline Annex references, correcting stale behavior descriptions and documenting actual argument and return contracts.
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

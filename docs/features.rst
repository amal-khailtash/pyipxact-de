Feature implementation status
=============================

☑ = implemented; ☐ = planned or not yet implemented.
The implementation scope includes all IP-XACT data and behavior; TGI coverage
is tracked separately and does not replace core feature implementation. Checked operations
do not imply complete semantic, transport, expression, or GUI conformance.

Current priority is IEEE/IP-XACT document semantics, validation, and applicable TGI requirements.
Further caching and GUI work is deferred until the remaining standard aspects are implemented.
Deferred items remain visible below.

Data model, semantics, interoperability, and GUI
------------------------------------------------

TGI package organization
~~~~~~~~~~~~~~~~~~~~~~~~

- ☑ Organize TGI under ``amal/eda/accellera/ipxact/v1685_2022/tgi``, with a matching ``spirit`` namespace for future versions.
- ☑ Reuse shared XML/expression validation, typed ranges and model traversal beneath category operations, preserving standard API contracts.
- ☑ Organize IEEE 1685-2022 tests by standard/version, retaining common and cross-version tests at the top level.

XML document identification
~~~~~~~~~~~~~~~~~~~~~~~~~~~

- ☑ Identify documents using a default namespace across supported SPIRIT/IP-XACT versions.
- ☑ Identify documents using arbitrary prefixes rather than fixed ipxact/spirit names.
- ☑ Use the expanded root name for identity, ignoring unrelated namespace declarations.
- ☑ Reject unsupported standard versions during document identification.
- ☑ Leave identification failures retryable after the source document is corrected.

XML binding compatibility
~~~~~~~~~~~~~~~~~~~~~~~~~

- ☑ Preserve empty generic bus-interface choice names during 2014/2022 XML round trips.
- ☑ Construct catalog file URI values using regenerated keyword-only models.

XML schema validation
~~~~~~~~~~~~~~~~~~~~~

- ☑ Return structured validation issues for missing or unreadable XML files.
- ☑ Return malformed-XML diagnostics with line and column locations.
- ☑ Validate offline using an explicit local Accellera schema directory.
- ☑ Return actual XSD diagnostics and source locations from in-process validation.
- ☑ Return structured failures for missing, malformed, or invalid local schemas.

Repository discovery
~~~~~~~~~~~~~~~~~~~~

- ☑ Extract root VLNV values independently of default or arbitrary XML namespace prefixes.
- ☑ Index top-level documents from all recognized SPIRIT/IP-XACT editions while restricting TGI model operations to 1685-2022.
- ☑ Discover XML files case-insensitively in recursive repository scans.
- ☑ Preserve search-path order and scan overlapping files once.
- ☑ Diagnose duplicate VLNV values and retain the first search-path match on fresh and cached scans.
- ☑ Continue scanning when a discovered file disappears before it can be read.

Catalog dependency discovery
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- ☑ Resolve relative, absolute, and percent-encoded local file URIs from catalogs.
- ☑ Discover nested catalogs and register referenced documents outside the search paths.
- ☑ Detect catalog reference cycles and deduplicate shared dependencies.
- ☑ Diagnose missing targets, mismatched VLNVs, incomplete entries, and unsupported remote URIs.
- ☑ Recheck unchanged catalogs and remove or restore dependency registrations as files disappear or return.

Repository cache integrity
~~~~~~~~~~~~~~~~~~~~~~~~~~

- ☑ Validate cache records independently and retain valid records beside malformed entries.
- ☑ Detect changed files using nanosecond modification/change times and file size.
- ☑ Discard stale or deleted files during validating cache-only registry loading and clear empty cached registries.
- ☑ List saved inventory without source-file checks; update inventory through explicit registry scans.
- ☑ Batch styled registry output and provide aligned, unwrapped plain text for redirected output.
- ☑ Report registry loading and scan progress with compact XML filename, edition and document-type results.
- ☑ Discover XML files progressively and support explicit registry listing color modes for pipelines.
- ☑ Create requested cache directories before persisting scan results.
- ☑ Replace cache files atomically and preserve existing data when replacement fails.

Catalog reference validation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- ☑ Reject catalog references with incomplete VLNV attributes.
- ☑ Diagnose referenced root-category mismatches across supported catalog categories.
- ☑ Recover from malformed XML targets without skipping valid sibling references.
- ☑ Reject invalid or empty local URIs and unsupported query/fragment forms per entry.
- ☑ Retain first-record precedence and diagnose duplicate VLNVs during cache-only loading.

Catalog target eligibility
~~~~~~~~~~~~~~~~~~~~~~~~~~

- ☑ Reject unsupported referenced standard/version combinations before registration.
- ☑ Reject referenced roots with incomplete VLNVs.
- ☑ Reject malformed percent escapes and invalid UTF-8 encoded paths per entry.
- ☑ Reject decoded NUL paths without stopping sibling discovery.
- ☑ Ignore vendor-extension lookalikes when discovering catalog references.

Repository refresh behavior
~~~~~~~~~~~~~~~~~~~~~~~~~~~

- ☑ Clear registrations and persisted cache when no search paths remain.
- ☑ Verify explicit-path precedence over environment search paths.
- ☑ Recover from unreadable cache files during fresh scans.
- ☑ Diagnose unsupported discovered documents while loading valid siblings.
- ☑ Invalidate same-size edits with preserved modification times.

Standard root creation
~~~~~~~~~~~~~~~~~~~~~~

- ☑ Create generated catalog, component, design, design configuration, and typeDefinitions roots from VLNVs.
- ☑ Register created roots, return null for duplicate VLNVs, and reject malformed VLNV arguments.
- ☑ Preserve root metadata across XML round trips for the five verified creators.

Architecture and shared completion contract
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- ☐ Separate versioned generated data models, document/workspace services, semantic analysis, command/mutation services, TGI adapters, and GUI models.
- ☐ Define document ownership, dirty state, atomic save, save-as, XML encoding, namespace handling, schema location, optional/default values, extension preservation, and recoverable diagnostics.
- ☐ Repository service: ordered search paths, relative URI resolution, catalogs, VLNV/version resolution, duplicate/conflict handling, missing references, cycle detection, incremental invalidation, and cache validation.
- ☐ Resolve names and references in the proper hierarchy/configuration, keeping source and effective configured values distinct.
- ☐ Mutation commands preserve invariants, parent relationships, ordering and ID lifecycle; enable transactions, undo/redo, change notification, and rollback after validation failure.
- ☐ One semantic/command backend serves Python, CLI, TGI and GUI. GUI operations must not bypass constraints or implement separate expression evaluation.
- ☐ Every top-level item below supports create/open/import, inspect, full schema-valid editing, validate, resolve dependencies, clone, save/export, reload, version-aware conversion, and complete relevant TGI access.
- ☐ Every optional element/attribute, choice alternative, nested collection, inherited type/group, vendor extension and expression has an explicit model and GUI representation, including advanced properties when absent from the primary panel.
- ☐ Per-item acceptance: minimal and maximal valid documents; each choice arm; malformed/invalid input; round trips; mutation/save/reload; reference failures; relevant Annex B rules; all applicable TGI positive/negative contracts; GUI edits, undo/redo, navigation and diagnostics.

Feature plan by top-level IP-XACT document
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

busDefinition - IEEE 5.2, 5.12-5.13; TGI F.7.17-18
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- ☐ VLNV/name metadata; direct connection, addressability, maximum initiators/targets, system group names, extension references and vendor extensions.
- ☐ Resolve extension chains and compatibility; reject cycles/incompatible modes and cross-reference errors. Apply clock/reset semantics with abstraction definitions.
- ☐ GUI: library entry, identity/properties editor, allowed-mode/system-group tables, inheritance graph and compatibility diagnostics.
- ☐ Tests: base/derived buses, addressable/nonaddressable cases, connection limits, incompatible definitions and unresolved parents.

abstractionDefinition - IEEE 5.3-5.13; TGI F.7.2-3
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- ☐ Bus type reference, abstraction inheritance, logical ports, matching rules, choices, wire and transactional alternatives, packets and packet fields.
- ☐ Initiator/target/system modes and mirrored constraints; presence, direction, width, default values, driver requirements, qualifiers, load/drive/timing constraints, transactional initiative/kind/protocol/bus width.
- ☐ Packet width/value expressions, field/packet endianness, ordering and qualifiers; inherited port merging and compatibility.
- ☐ GUI: logical-port matrix by mode, wire/transactional detail panels, packet layout viewer, constraints editor, bus/inheritance navigation.
- ☐ Tests: all port styles/modes, inherited overrides, packet boundaries and mode-specific compatibility.

component - IEEE 6.1-6.21; TGI component and dependent categories
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- ☐ Identity, descriptions, parameters/choices, external type-definition references, vendor extensions and general component metadata.
- ☐ Power domains: always-on/configurable values, hierarchy, domain membership, supply/ground relationships and port/field power constraints.
- ☐ Bus interfaces: references to bus/abstraction definitions; all interface modes and mirrored/system/monitor forms; abstraction types/view references, physical/logical port maps, slices, exclusions, bridges, memory-map/address-space references, endian/bit-steering behavior and parameters.
- ☐ Indirect interfaces: access handles, indirect addressing, index/data references, address range/offset and field relationships.
- ☐ Channels: participating interfaces, address modifications and bit steering; modes: conditions, port/field slices and validity across configurations.
- ☐ Address spaces: address unit bits, range/width, segments, local memory maps, parameters and addressable interface relationships.
- ☐ Memory maps/remaps: address blocks, nested banks, register files/registers, subspace maps, usage, access policies, addressing, remap states and conditions.
- ☐ Registers/fields: sizes/offsets, nested arrays and strides, volatility/access, resets/reset-type references, enumerated values, write/read effects and constraints, access policies, aliases/definition references, reserved bits, field slices, testability and extensions. Distinguish source metadata from computed address and effective values.
- ☐ Model: views; component/design/design-configuration instantiations; module parameters; language/model names; file-set references; physical ports (wire, transactional, structured), vectors, arrays, type definitions, drivers, default/tied values, port slices and subports; model assertions and constraints.
- ☐ Component generators: API type, executable, parameters, scope/phase and invocation requirements.
- ☐ File sets/files/builders: file types, paths/dependencies, include/logical names, build commands/flags, environment/configuration, exported names/functions and extension metadata, preserving full schema detail.
- ☐ Clearbox elements and references, CPU regions/executable images/memory-map references, other clock drivers and reset types.
- ☐ GUI: component overview plus model/view editor; ports/interface mapping matrix and connection preview; memory hierarchy/address-map and register bitfield views; parameters with source/evaluated values; power/mode diagrams; file/build browser; CPU/clearbox/clock/reset panels; generator configuration.
- ☐ Tests: all component schema choices, constructor-safe builders, nested structures, register boundary/reset/access cases, multiple views, arrays/structured ports, configuration-dependent addressing, external reusable definitions and serialization choice preservation.

design - IEEE 7; TGI F.7.37-38
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- ☐ Component instances, VLNV references, instance names/display names, configurable element values, power-domain links and vendor metadata.
- ☐ Interconnections and monitor interconnections; active/hierarchical/monitored/monitor interfaces; exclusions, complex interconnections and abstractor/configuration relationships.
- ☐ Ad hoc connections: internal/external port references, structured subports, part selects and tied values; choices and hierarchy resolution.
- ☐ Validate all connectivity, direction/width/type/mode compatibility and endpoint existence; compute configured hierarchy, address routes and visibility.
- ☐ GUI: hierarchical block diagram, connection inspector and matrix, instance browser, property/configuration editor, external ports, power links, address-route and field/bit visibility overlays. Persist layout separately from normative metadata unless an explicit extension is used.
- ☐ Tests: nested designs, monitors, multichannel connections, tied/sliced ports, duplicate instances, missing references and incompatible connections.

abstractor - IEEE 8; TGI F.7.4-5
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- ☐ Bus/abstraction interfaces and mode mapping; models/views, wire/transactional/structured physical ports, vectors/types/constraints and generators.
- ☐ Resolve supported abstraction transitions; validate interface and port correspondence and configured placement.
- ☐ GUI: abstraction bridge diagram, side-by-side interface/port mapping, model/view details and generator panel.
- ☐ Tests: both sides of transition, structured and transactional alternatives, incompatible abstractions and configured abstractor instances.

typeDefinitions - IEEE 9; TGI F.7.81-82 and memory/register/access-policy categories
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- ☐ Reusable field access policies, enumerations, fields, registers, register files, address blocks, banks, memory maps and memory remaps; parameters, nested definitions, identifiers/references and extensions.
- ☐ External definition imports, resolution scope, overrides/configuration, cyclic-reference rejection and effective instance expansion without destroying reusable source definitions.
- ☐ GUI: definition library and dependency graph, reusable memory/register/field editors, preview of instantiations and impact analysis for edits.
- ☐ Tests: each reusable definition family, nested/external references, cycles, overrides and definition-versus-instance round trips.
- ☐ These are members of the typeDefinitions document; do not invent independent roots for the commented-out schema choices.

generatorChain - IEEE 10; TGI F.7.51-52 and generator/file-builder categories
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- ☐ Chain identity, selectors, component selectors, generator references/executables, ordering/phases, parameters, choices and vendor extensions.
- ☐ Generator execution lifecycle, invocation URL resolution/encoding, API negotiation and session linkage; deterministic selection, errors, cancellation and diagnostics.
- ☐ GUI: chain steps/ordering editor, selector preview, parameters, run monitor/logs and generated-artifact review.
- ☐ Tests: selector combinations, order, parameter defaults/fixed values, invocation formatting and failed/cancelled executions using controlled generators.

designConfiguration - IEEE 11; TGI F.7.39-40
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- ☐ Design reference, view configurations, interconnection configurations, abstractor instances and their references/parameters/extensions.
- ☐ Resolve active views and hierarchy, configure abstractor placements, validate completeness/consistency without mutating the original design implicitly.
- ☐ GUI: configuration selection/comparison, per-instance view table, interconnection/abstractor overlay and effective-design preview.
- ☐ Tests: alternative valid configurations, broken design/view references, abstractor mismatches, expression/configuration propagation and round trips.

catalog - IEEE 12; TGI F.7.23-24
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- ☐ Entries for all catalog-supported item categories, nested catalogs, VLNV/path pairs, descriptions/extensions and path-relative dependency resolution.
- ☐ Detect referenced-file identity mismatch, duplicates, cycles, moved/missing files and incomplete packages; inspect version ordering separately from arbitrary version strings.
- ☐ GUI: repository browser with type filters, search, preview, dependency graph, validation status and import/package management.
- ☐ Tests: every entry family, nested/relative paths, stale cache, duplicate VLNV and mismatched file identity.

Cross-cutting IEEE behavior
~~~~~~~~~~~~~~~~~~~~~~~~~~~

- ☐ Clauses 1-4: interoperability roles and exchange flows; define supported DE capabilities, import/export/package behavior and conformance statements.
- ☐ Clause 13: calculate bit addresses, bus addresses, indirect-interface addresses, channel modifications and bridge translation with units, overflow/range checks, arrays and configured hierarchy.
- ☐ Clause 14: mapped address masks, interconnection modifications, channel bit steering and visibility of bits. Provide explainable route/visibility results and disconnected/ambiguous diagnostics.
- ☐ Annex B: individually inventory and implement all consistency rules for cross-references/VLNVs, interconnections, channels/bridges/abstractors, monitors, configurable elements, ports, registers, memory maps, addressing, hierarchy, hierarchy/memory maps, constraints, design configurations, expressions and access handles. Separate XSD validation from these semantic checks.
- ☐ Annex C: all access-handle variants/access resolution/access policies; arrays/indices/strides; assertions; cell specifications/strength/function; choices; configurable values; constraints; defaults; endianness; file types; references and paths; name groups/name-value pairs; parameters; part selects/slices/vectors/ranges; power constraints; vendor extensions; versioned identifiers/version comparison; view references; xml:id and component-versus-abstraction port distinctions.
- ☐ Annex D: enforce lexical/value domains for every standard type, enum and constrained scalar; represent unspecified values distinctly from valid zero/false/empty values.
- ☑ Slang-backed SystemVerilog constant-expression parser with named constants, diagnostics, native widths/signedness and X/Z preservation.
- ☑ SystemVerilog expression REPL with history, suggestions, syntax highlighting and a Makefile entry point.
- ☐ Annex E: expression parser/evaluator for the specified SystemVerilog subset, literals/types/operators/functions, escaped identifiers, parameter references, scope/resolution/configuration, arrays and IP-XACT functions. Record unsupported syntax explicitly during development; final complete-2022 scope requires all standard-supported forms. Detect cycles and invalid types/ranges; retain source expressions and evaluation provenance.
- ☐ GUI shared tools: expression editor/completion/dependency graph and effective value preview; validation panel with rule IDs and navigation; extension XML editor; identity/name metadata panels; access-handle browser; source XML with synchronized semantic selection.

Complete TGI delivery - Annex F
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- ☐ F.1-F.2: SOAP/REST communication modes, generator invocation, URL construction, endpoint resolution, argument encoding and example-derived tests.
- ☐ F.3: full API contract, administrative commands, standard fault codes, return types, BASE/EXTENDED profiles and support discovery; do not substitute Python convenience semantics for normative returns.
- ☐ F.4-F.6: session-scoped IDs, configurable/evaluated values, messages and vendor attributes accessible through eligible IDs; preserve XML IDs as a distinct concept.
- ☐ Every getter, list/reference accessor, expression/evaluated-value/ID accessor, setter, adder and remover: precise argument types/order, accepted ID types, ordering, absent optional behavior, successful/no-op return, invalid-ID/type/reference/configuration faults and mutation side effects.
- ☐ F.7.89: all ID types, validity/lifetime, parent lookup, deletion invalidation, session boundaries and access-handle identity.
- ☐ Category coverage includes abstraction definition, abstractor, access handle/policy, address space, array, assertion, bus definition/interface, CPU, catalog, choice, clearbox, component, configurable element, constraint/set, design/configuration, driver, element attribute, file builder/set, generator/chain, indirect interface, instantiation, memory map, miscellaneous, module parameter, name group, parameter, port/map, power, register/file, slice, top element, type definitions, vector, vendor extensions and view.
- ☐ Audit category exports and imports, duplicate definitions, spelling/case-sensitive names, dynamic/generated functions and wrong signatures. Existing explicit-function matches in the ledger remain unverified.
- ☐ Bind transport schemas to Python contracts; validate SOAP requests/responses/faults and REST mappings with integration fixtures. Preserve all required transport capabilities independently of the deferred MCP server.
- ☐ GUI uses corresponding service/TGI operations where suitable; protocol-only operations belong in session/runner tooling rather than an artificial form widget. Record explicit GUI placement or reason for no direct widget for every row.

Older standards and conversion
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- ☐ Build a feature/version matrix for each top-level root and nested feature: available, changed, deprecated, unsupported editing, preserved-only, convertible and lossy. Select older editable features in future plan updates without shrinking full 2022 scope.
- ☐ Cover historical initiator/target terminology, optional presence/configuration semantics, port/interface/model changes, register/access/reset representations, hierarchy, type reuse and standard vendor extensions. Derive actual mappings from schemas/stylesheets rather than assuming name substitutions suffice.
- ☐ Conversion engine selects a supported directed route, records stylesheet versions and parameters, keeps originals, uses atomic output, validates every stage and updates related repository files/references coherently.
- ☐ Produce structured diagnostics for lost, changed, extension-carried and unresolved information. Preserve unknown extensions when feasible; do not promise lossless conversion or silent downgrades.
- ☐ Reverse/downgrade conversion remains an explicit future capability requiring new mappings and loss policy; never infer it from forward XSLT availability.
- ☐ GUI: source-version badges, capability-aware forms, preserved-only fields, migration wizard with route preview/diff/loss report and destination selection, batch conversion and result validation.
- ☐ Tests: each actual stylesheet edge, abstraction-specific routes, complete chains, malformed/intermediate failures, legacy feature fixtures, extension preservation, changed semantics and mixed-version repository references. Define older TGI profiles separately if later required.

Future GUI delivery
~~~~~~~~~~~~~~~~~~~

- ☐ Audit existing Qt prototypes; choose Qt model/view architecture and documented service boundaries before expanding them.
- ☐ Workspace shell: repository tree, document tabs, recent/open/save actions, dirty indicators, global search, dependency navigation, properties, diagnostics and source viewer.
- ☐ Schema-aware property editor covers every supported declaration, choice/cardinality, ordering, defaults and extensions. Specialized views supplement the complete property editor.
- ☐ Diagrams: component/design connectivity and hierarchy, definition dependencies, power/modes, address translation and generator chains. Bidirectional selection links diagrams, tree, tables and XML.
- ☐ Memory/register views show address units, computed offsets/ranges, arrays, bitfield layouts, resets/access/enumerations and visibility with zoom/filter/export.
- ☐ Editing: transactions, undo/redo, copy/paste/clone, identity/reference refactoring, conflict detection on external changes, validation before save and recoverable errors.
- ☐ Performance: lazy trees, virtualization for large maps/designs, background parsing/validation/evaluation, cancellable tasks and deterministic model notifications.
- ☐ Accessibility: keyboard navigation, readable colors/labels, stable focus and diagnostics beyond color alone. GUI state/layout stays separate from standard documents.
- ☐ GUI tests exercise each top-level editor and critical nested flows, unsupported older features, conversion, dirty/save behavior, undo/redo and large-workspace responsiveness.

Verification and living-plan maintenance
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- ☐ Maintain schema, TGI, semantic and version matrices as separate linked evidence; automate completeness checks against their authoritative inputs.
- ☐ Reconcile extracted declarations with reachable roots, all restrictions/facets/groups/choices and normative prose; inventory additions cannot remain implicitly unowned.
- ☐ Use deterministic checked-in or otherwise stable local fixtures for routine tests; isolate network-dependent archive acquisition from core conformance checks.
- ☐ Round trips compare semantic meaning plus required XML preservation; namespace prefixes alone must not create false failures, and semantic loss must not be hidden by canonicalization.
- ☐ Measure large repository scans, configured hierarchy, expression graphs, register arrays and GUI responsiveness with recorded limits.
- ☐ Run wheel/source installation and resource-loading checks outside the checkout; verify schema/XSL/WSDL assets and supported Python environments.
- ☐ Final full-2022 completion requires all nine roots, all reachable schema features, all applicable semantic rules/types/expressions, addressing/visibility, all Annex F operation and ID contracts, required transports and GUI representations to have evidence. Older support claims must match their explicit feature/version matrix.

TGI operation checklist
-----------------------

This inventory lists operation names and section identifiers for tracking.
The local IEEE reference, schemas, and WSDL define their contracts. Duplicate
documentation entries retain their section identifiers until reconciled.

Unmarked operations may have existing implementations that still need audit.

Abstraction definition (BASE)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- ☑ ``getAbstractionDefBusTypeRefByVLNV`` (F.7.2.1)
- ☑ ``getAbstractionDefChoiceIDs`` (F.7.2.2)
- ☑ ``getAbstractionDefExtendsRefByVLNV`` (F.7.2.3)
- ☑ ``getAbstractionDefPortIDs`` (F.7.2.4)
- ☑ ``getAbstractionDefPortLogicalName`` (F.7.2.5)
- ☑ ``getAbstractionDefPortMatch`` (F.7.2.6)
- ☑ ``getAbstractionDefPortOnSystemIDs`` (F.7.2.7)
- ☑ ``getAbstractionDefPortPacketIDs`` (F.7.2.8)
- ☑ ``getAbstractionDefPortStyle`` (F.7.2.9)
- ☑ ``getAbstractionDefPortTransactionalModeBusWidth`` (F.7.2.10) - Self-contained SystemVerilog integer expressions; parameter/scope resolution pending.
- ☑ ``getAbstractionDefPortTransactionalModeBusWidthExpression`` (F.7.2.11)
- ☑ ``getAbstractionDefPortTransactionalModeBusWidthID`` (F.7.2.12)
- ☑ ``getAbstractionDefPortTransactionalModeInitiative`` (F.7.2.13)
- ☑ ``getAbstractionDefPortTransactionalModeKindID`` (F.7.2.14)
- ☑ ``getAbstractionDefPortTransactionalModePresence`` (F.7.2.15)
- ☑ ``getAbstractionDefPortTransactionalModeProtocolID`` (F.7.2.16)
- ☑ ``getAbstractionDefPortTransactionalOnInitiatorID`` (F.7.2.17)
- ☑ ``getAbstractionDefPortTransactionalOnSystemIDs`` (F.7.2.18)
- ☑ ``getAbstractionDefPortTransactionalOnTargetID`` (F.7.2.19)
- ☑ ``getAbstractionDefPortTransactionalQualifierID`` (F.7.2.20)
- ☑ ``getAbstractionDefPortWireDefaultValue`` (F.7.2.21) - Self-contained SystemVerilog integer expressions; parameter/scope resolution pending.
- ☑ ``getAbstractionDefPortWireDefaultValueExpression`` (F.7.2.22)
- ☑ ``getAbstractionDefPortWireDefaultValueID`` (F.7.2.23)
- ☑ ``getAbstractionDefPortWireModeDirection`` (F.7.2.24)
- ☑ ``getAbstractionDefPortWireModeMirroredModeConstraintsID`` (F.7.2.25)
- ☑ ``getAbstractionDefPortWireModeModeConstraintsID`` (F.7.2.26)
- ☑ ``getAbstractionDefPortWireModePresence`` (F.7.2.27)
- ☑ ``getAbstractionDefPortWireModeWidth`` (F.7.2.28) - Self-contained SystemVerilog integer expressions; parameter/scope resolution pending.
- ☑ ``getAbstractionDefPortWireModeWidthExpression`` (F.7.2.29)
- ☑ ``getAbstractionDefPortWireModeWidthID`` (F.7.2.30)
- ☑ ``getAbstractionDefPortWireOnInitiatorID`` (F.7.2.31)
- ☑ ``getAbstractionDefPortWireOnSystemIDs`` (F.7.2.32)
- ☑ ``getAbstractionDefPortWireOnTargetID`` (F.7.2.33)
- ☑ ``getAbstractionDefPortWireQualifierID`` (F.7.2.34)
- ☑ ``getAbstractionDefPortWireRequiresDriver`` (F.7.2.35)
- ☑ ``getAbstractionDefPortWireRequiresDriverID`` (F.7.2.36)
- ☑ ``getModeConstraintsDriveConstraintCellSpecificationID`` (F.7.2.37)
- ☑ ``getModeConstraintsLoadConstraintID`` (F.7.2.38)
- ☑ ``getModeConstraintsTimingConstraintIDs`` (F.7.2.39)
- ☑ ``getOnSystemGroup`` (F.7.2.40)
- ☑ ``getPacketEndianness`` (F.7.2.41)
- ☑ ``getPacketFieldEndianness`` (F.7.2.42)
- ☑ ``getPacketFieldQualifierID`` (F.7.2.43)
- ☑ ``getPacketFieldValue`` (F.7.2.44) - Self-contained SystemVerilog integer expressions; parameter/scope resolution pending.
- ☑ ``getPacketFieldValueExpression`` (F.7.2.45)
- ☑ ``getPacketFieldValueID`` (F.7.2.46)
- ☑ ``getPacketFieldWidth`` (F.7.2.47) - Self-contained SystemVerilog integer expressions; parameter/scope resolution pending.
- ☑ ``getPacketFieldWidthExpression`` (F.7.2.48)
- ☑ ``getPacketFieldWidthID`` (F.7.2.49)
- ☑ ``getPacketPacketFieldIDs`` (F.7.2.50)

Abstraction definition (EXTENDED)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- ☑ ``addAbstractionDefChoice`` (F.7.3.1)
- ☑ ``addAbstractionDefPort`` (F.7.3.2)
- ☑ ``addAbstractionDefPortMode`` (F.7.3.3)
- ☑ ``addAbstractionDefPortPacket`` (F.7.3.4)
- ☑ ``addAbstractionDefPortTransactionalOnSystem`` (F.7.3.5)
- ☑ ``addAbstractionDefPortWireOnSystem`` (F.7.3.6)
- ☑ ``addModeConstraintsTimingConstraint`` (F.7.3.7)
- ☑ ``addPacketPacketField`` (F.7.3.8)
- ☑ ``removeAbstractionDefChoice`` (F.7.3.9)
- ☑ ``removeAbstractionDefExtends`` (F.7.3.10)
- ☑ ``removeAbstractionDefPort`` (F.7.3.11)
- ☑ ``removeAbstractionDefPortMatch`` (F.7.3.12)
- ☑ ``removeAbstractionDefPortMode`` (F.7.3.13)
- ☑ ``removeAbstractionDefPortTransactionalModeBusWidth`` (F.7.3.14)
- ☑ ``removeAbstractionDefPortTransactionalModeInitiative`` (F.7.3.15)
- ☑ ``removeAbstractionDefPortTransactionalModeKind`` (F.7.3.16)
- ☑ ``removeAbstractionDefPortTransactionalModePresence`` (F.7.3.17)
- ☑ ``removeAbstractionDefPortTransactionalModeProtocol`` (F.7.3.18)
- ☑ ``removeAbstractionDefPortTransactionalOnInitiator`` (F.7.3.19)
- ☑ ``removeAbstractionDefPortTransactionalOnSystem`` (F.7.3.20)
- ☑ ``removeAbstractionDefPortTransactionalOnTarget`` (F.7.3.21)
- ☑ ``removeAbstractionDefPortTransactionalQualifier`` (F.7.3.22)
- ☑ ``removeAbstractionDefPortWireDefaultValue`` (F.7.3.23)
- ☑ ``removeAbstractionDefPortWireModeDirection`` (F.7.3.24)
- ☑ ``removeAbstractionDefPortWireModeMirroredModeConstraints`` (F.7.3.25)
- ☑ ``removeAbstractionDefPortWireModeModeConstraints`` (F.7.3.26)
- ☑ ``removeAbstractionDefPortWireModePresence`` (F.7.3.27)
- ☑ ``removeAbstractionDefPortWireModeWidth`` (F.7.3.28)
- ☑ ``removeAbstractionDefPortWireOnInitiator`` (F.7.3.29)
- ☑ ``removeAbstractionDefPortWireOnSystem`` (F.7.3.30)
- ☑ ``removeAbstractionDefPortWireOnTarget`` (F.7.3.31)
- ☑ ``removeAbstractionDefPortWireQualifier`` (F.7.3.32)
- ☑ ``removeAbstractionDefPortWireRequiresDriver`` (F.7.3.33)
- ☑ ``removeCustomAttribute`` (F.7.3.34)
- ☑ ``removeMandatoryAttribute`` (F.7.3.35)
- ☑ ``removeModeConstraintsDriveConstraint`` (F.7.3.36)
- ☑ ``removeModeConstraintsLoadConstraint`` (F.7.3.37)
- ☑ ``removeModeConstraintsTimingConstraint`` (F.7.3.38)
- ☑ ``removePacketEndianness`` (F.7.3.39)
- ☑ ``removePacketFieldEndianness`` (F.7.3.40)
- ☑ ``removePacketFieldQualifier`` (F.7.3.41)
- ☑ ``removePacketFieldValue`` (F.7.3.42)
- ☑ ``removePacketPacketField`` (F.7.3.43)
- ☑ ``setAbstractionDefExtends`` (F.7.3.44)
- ☑ ``setAbstractionDefPortLogicalName`` (F.7.3.45)
- ☑ ``setAbstractionDefPortMatch`` (F.7.3.46)
- ☑ ``setAbstractionDefPortMode`` (F.7.3.47)
- ☑ ``setAbstractionDefPortTransactionalModeBusWidth`` (F.7.3.48)
- ☑ ``setAbstractionDefPortTransactionalModeInitiative`` (F.7.3.49)
- ☑ ``setAbstractionDefPortTransactionalModeKind`` (F.7.3.50)
- ☑ ``setAbstractionDefPortTransactionalModePresence`` (F.7.3.51)
- ☑ ``setAbstractionDefPortTransactionalModeProtocol`` (F.7.3.52)
- ☑ ``setAbstractionDefPortTransactionalOnInitiator`` (F.7.3.53)
- ☑ ``setAbstractionDefPortTransactionalOnTarget`` (F.7.3.54)
- ☑ ``setAbstractionDefPortTransactionalQualifier`` (F.7.3.55)
- ☑ ``setAbstractionDefPortWire`` (F.7.3.56)
- ☑ ``setAbstractionDefPortTransactional`` (F.7.3.57)
- ☑ ``setAbstractionDefPortWireDefaultValue`` (F.7.3.58)
- ☑ ``setAbstractionDefPortWireModeDirection`` (F.7.3.59)
- ☑ ``setAbstractionDefPortWireModeMirroredModeConstraints`` (F.7.3.60)
- ☑ ``setAbstractionDefPortWireModeModeConstraints`` (F.7.3.61)
- ☑ ``setAbstractionDefPortWireModePresence`` (F.7.3.62)
- ☑ ``setAbstractionDefPortWireModeWidth`` (F.7.3.63)
- ☑ ``setAbstractionDefPortWireOnInitiator`` (F.7.3.64)
- ☑ ``setAbstractionDefPortWireOnTarget`` (F.7.3.65)
- ☑ ``setAbstractionDefPortWireQualifier`` (F.7.3.66)
- ☑ ``setAbstractionDefPortWireRequiresDriver`` (F.7.3.67)
- ☑ ``setModeConstraintsDriveConstraint`` (F.7.3.68)
- ☑ ``setModeConstraintsLoadConstraint`` (F.7.3.69)
- ☑ ``setOnSystemGroup`` (F.7.3.70)
- ☑ ``setPacketEndianness`` (F.7.3.71)
- ☑ ``setPacketFieldEndianness`` (F.7.3.72)
- ☑ ``setPacketFieldQualifier`` (F.7.3.73)
- ☑ ``setPacketFieldValue`` (F.7.3.74)
- ☑ ``setPacketFieldWidth`` (F.7.3.75)

Abstractor (BASE)
~~~~~~~~~~~~~~~~~

- ☑ ``getAbstractorAbstractorGeneratorIDs`` (F.7.4.1)
- ☑ ``getAbstractorAbstractorInterfaceIDs`` (F.7.4.2)
- ☑ ``getAbstractorAbstractorMode`` (F.7.4.3)
- ☑ ``getAbstractorAbstractorModeID`` (F.7.4.4)
- ☑ ``getAbstractorBusTypeRefByVLNV`` (F.7.4.5)
- ☑ ``getAbstractorChoiceIDs`` (F.7.4.6)
- ☑ ``getAbstractorComponentInstantiationIDs`` (F.7.4.7)
- ☑ ``getAbstractorFileSetIDs`` (F.7.4.8)
- ☑ ``getAbstractorInterfaceAbstractionTypeIDs`` (F.7.4.9)
- ☑ ``getAbstractorPortIDs`` (F.7.4.10)
- ☑ ``getAbstractorViewIDs`` (F.7.4.11)

Abstractor (EXTENDED)
~~~~~~~~~~~~~~~~~~~~~

- ☑ ``addAbstractorAbstractorGenerator`` (F.7.5.1)
- ☑ ``addAbstractorChoice`` (F.7.5.2)
- ☑ ``addAbstractorComponentInstantiation`` (F.7.5.3)
- ☑ ``addAbstractorFileSet`` (F.7.5.4)
- ☑ ``addAbstractorInterfaceAbstractionType`` (F.7.5.5)
- ☑ ``addAbstractorStructuredInterfacePort`` (F.7.5.6)
- ☑ ``addAbstractorStructuredStructPort`` (F.7.5.7)
- ☑ ``addAbstractorStructuredUnionPort`` (F.7.5.8)
- ☑ ``addAbstractorTransactionalPort`` (F.7.5.9)
- ☑ ``addAbstractorView`` (F.7.5.10)
- ☑ ``addAbstractorWirePort`` (F.7.5.11)
- ☑ ``removeAbstractorAbstractorGenerator`` (F.7.5.12)
- ☑ ``removeAbstractorAbstractorInterface`` (F.7.5.13)
- ☑ ``removeAbstractorChoice`` (F.7.5.14)
- ☑ ``removeAbstractorComponentInstantiation`` (F.7.5.15)
- ☑ ``removeAbstractorFileSet`` (F.7.5.16)
- ☑ ``removeAbstractorInterfaceAbstractionType`` (F.7.5.17)
- ☑ ``removeAbstractorPort`` (F.7.5.18)
- ☑ ``removeAbstractorView`` (F.7.5.19)
- ☑ ``removeFileSetRefGroupFileSetRef`` (F.7.5.20)
- ☑ ``setAbstractorAbstractorMode`` (F.7.5.21)
- ☑ ``setAbstractorBusType`` (F.7.5.22)

Access handle (BASE)
~~~~~~~~~~~~~~~~~~~~

- ☑ ``getAccessHandleForce`` (F.7.7.1)
- ☑ ``getAccessHandleIDs`` (F.7.7.2)
- ☑ ``getAccessHandleIndicesIDs`` (F.7.7.3)
- ☑ ``getAccessHandlePathSegmentIDs`` (F.7.7.4)
- ☑ ``getAccessHandleSliceIDs`` (F.7.7.5)
- ☑ ``getAccessHandleViewRefIDs`` (F.7.7.6)

Access handle (EXTENDED)
~~~~~~~~~~~~~~~~~~~~~~~~

- ☑ ``addAccessHandle`` (F.7.8.1)
- ☑ ``addAccessHandleIndex`` (F.7.8.2)
- ☑ ``addAccessHandlePathSegment`` (F.7.8.3)
- ☑ ``addAccessHandleSlice`` (F.7.8.4)
- ☑ ``addAccessHandleViewRef`` (F.7.8.5)
- ☑ ``removeAccessHandle`` (F.7.8.6)
- ☑ ``removeAccessHandleIndex`` (F.7.8.7)
- ☑ ``removeAccessHandlePathSegment`` (F.7.8.8)
- ☑ ``removeAccessHandleSlice`` (F.7.8.9)
- ☑ ``removeAccessHandleViewRef`` (F.7.8.10)
- ☑ ``setAccessHandleForce`` (F.7.8.11)

Access policy (BASE)
~~~~~~~~~~~~~~~~~~~~

- ☑ ``getFieldAccessPolicyModeRefByID`` (F.7.6.1)
- ☑ ``getAccessPolicyAccess`` (F.7.9.1)
- ☑ ``getAccessPolicyModeRefByID`` (F.7.9.2)
- ☑ ``getAccessPolicyModeRefByNames`` (F.7.9.3)
- ☑ ``getAccessPolicyModeRefIDs`` (F.7.9.4)
- ☑ ``getAccessRestrictionModeRefIDs`` (F.7.9.5)
- ☑ ``getAccessRestrictionModeRefbyID`` (F.7.9.6)
- ☑ ``getAccessRestrictionModeRefbyNames`` (F.7.9.7)
- ☑ ``getAccessRestrictionReadAccessMask`` (F.7.9.8)
- ☑ ``getAccessRestrictionReadAccessMaskExpression`` (F.7.9.9)
- ☑ ``getAccessRestrictionReadAccessMaskID`` (F.7.9.10)
- ☑ ``getAccessRestrictionWriteAccessMask`` (F.7.9.11)
- ☑ ``getAccessRestrictionWriteAccessMaskExpression`` (F.7.9.12)
- ☑ ``getAccessRestrictionWriteAccessMaskID`` (F.7.9.13)
- ☑ ``getAlternateRegisterAccessPolicyIDs`` (F.7.9.14)
- ☑ ``getBankAccessPoliciesIDs`` (F.7.9.15)
- ☑ ``getFieldAccessPoliciesFieldAccessPolicyIDs`` (F.7.9.16)
- ☑ ``getFieldAccessPolicyAccess`` (F.7.9.17)
- ☑ ``getFieldAccessPolicyAccessRestrictionIDs`` (F.7.9.18)
- ☑ ``getFieldAccessPolicyFieldAccessPolicyDefinitionRefByExternalTypeDefID`` (F.7.9.19)
- ☑ ``getFieldAccessPolicyFieldAccessPolicyDefinitionRefByID`` (F.7.9.20)
- ☑ ``getFieldAccessPolicyFieldAccessPolicyDefinitionRefByName`` (F.7.9.21)
- ☑ ``getFieldAccessPolicyFieldAccessPolicyDefinitionRefID`` (F.7.9.22)
- ☑ ``getFieldAccessPolicyModeRefByName`` (F.7.9.23)
- ☑ ``getFieldAccessPolicyModeRefIDs`` (F.7.9.24)
- ☑ ``getFieldAccessPolicyModifiedWriteValue`` (F.7.9.25)
- ☑ ``getFieldAccessPolicyModifiedWriteValueID`` (F.7.9.26)
- ☑ ``getFieldAccessPolicyReadAction`` (F.7.9.27)
- ☑ ``getFieldAccessPolicyReadActionID`` (F.7.9.28)
- ☑ ``getFieldAccessPolicyReadResponse`` (F.7.9.29)
- ☑ ``getFieldAccessPolicyReadResponseExpression`` (F.7.9.30)
- ☑ ``getFieldAccessPolicyReadResponseID`` (F.7.9.31)
- ☑ ``getFieldAccessPolicyReserved`` (F.7.9.32)
- ☑ ``getFieldAccessPolicyReservedExpression`` (F.7.9.33)
- ☑ ``getFieldAccessPolicyReservedID`` (F.7.9.34)
- ☑ ``getFieldAccessPolicyTestable`` (F.7.9.35)
- ☑ ``getFieldAccessPolicyTestableID`` (F.7.9.36)
- ☑ ``getFieldAccessPolicyWriteValueConstraintID`` (F.7.9.37)
- ☑ ``getFieldAccesspolicyBroadcastToIDs`` (F.7.9.38)
- ☑ ``getRegisterAccessPolicyIDs`` (F.7.9.39)
- ☑ ``getRegisterFieldFieldAccessPoliciesID`` (F.7.9.40)
- ☑ ``getTypeDefinitionsFieldAccessPolicyDefinitionIDs`` (F.7.9.41)
- ☑ ``getWriteValueConstraintMaximum`` (F.7.9.42)
- ☑ ``getWriteValueConstraintMaximumExpression`` (F.7.9.43)
- ☑ ``getWriteValueConstraintMaximumID`` (F.7.9.44)
- ☑ ``getWriteValueConstraintMinimum`` (F.7.9.45)
- ☑ ``getWriteValueConstraintMinimumExpression`` (F.7.9.46)
- ☑ ``getWriteValueConstraintMinimumID`` (F.7.9.47)
- ☑ ``getWriteValueConstraintUseEnumeratedValues`` (F.7.9.48)
- ☑ ``getWriteValueConstraintWriteAsRead`` (F.7.9.49)

Access policy (EXTENDED)
~~~~~~~~~~~~~~~~~~~~~~~~

- ☑ ``addAccessRestrictionModeRef`` (F.7.10.1)
- ☑ ``addAddressBlockAccessPolicy`` (F.7.10.2)
- ☑ ``addAlternateRegisterAccessPolicy`` (F.7.10.3)
- ☑ ``addExternalTypeDefinitionsResetTypeLink`` (F.7.10.4)
- ☑ ``addFieldAccessPoliciesFieldAccessPolicy`` (F.7.10.5)
- ☑ ``addFieldAccessPolicyAccessRestriction`` (F.7.10.6)
- ☑ ``addFieldAccessPolicyBroadcastTo`` (F.7.10.7)
- ☑ ``addFieldAccessPolicyModeRef`` (F.7.10.8)
- ☑ ``addFieldDefinitionFieldAccessPolicy`` (F.7.10.9)
- ☑ ``addRegisterAccessPolicy`` (F.7.10.10)
- ☑ ``addRegisterFileAccessPolicy`` (F.7.10.11)
- ☑ ``removeAccessPolicyAccess`` (F.7.10.12)
- ☑ ``removeAccessRestrictionModeRef`` (F.7.10.13)
- ☑ ``removeAccessRestrictionReadAccessMask`` (F.7.10.14)
- ☑ ``removeAccessRestrictionWriteAccessMask`` (F.7.10.15)
- ☑ ``removeAddressBlockAccessPolicyID`` (F.7.10.16)
- ☑ ``removeAlternateRegisterAccessPolicy`` (F.7.10.17)
- ☑ ``removeFieldAccessPoliciesFieldAccessPolicy`` (F.7.10.18)
- ☑ ``removeFieldAccessPolicyAccess`` (F.7.10.19)
- ☑ ``removeFieldAccessPolicyAccessRestriction`` (F.7.10.20)
- ☑ ``removeFieldAccessPolicyBroadcastTo`` (F.7.10.21)
- ☑ ``removeFieldAccessPolicyFieldAccessPolicyDefinitionRef`` (F.7.10.22)
- ☑ ``removeFieldAccessPolicyModeRef`` (F.7.10.23)
- ☑ ``removeFieldAccessPolicyModifiedWriteValue`` (F.7.10.24)
- ☑ ``removeFieldAccessPolicyReadAction`` (F.7.10.25)
- ☑ ``removeFieldAccessPolicyReadResponse`` (F.7.10.26)
- ☑ ``removeFieldAccessPolicyReserved`` (F.7.10.27)
- ☑ ``removeFieldAccessPolicyTestable`` (F.7.10.28)
- ☑ ``removeFieldAccessPolicyWriteValueConstraint`` (F.7.10.29)
- ☑ ``removeFieldDefinitionFieldAccessPolicy`` (F.7.10.30)
- ☑ ``removeRegisterAccessPolicy`` (F.7.10.31)
- ☑ ``removeRegisterFileAccessPolicy`` (F.7.10.32)
- ☑ ``setAccessPolicyAccess`` (F.7.10.33)
- ☑ ``setAccessRestrictionReadAccessMask`` (F.7.10.34)
- ☑ ``setAccessRestrictionWriteAccessMask`` (F.7.10.35)
- ☑ ``setFieldAccessPolicyAccess`` (F.7.10.36)
- ☑ ``setFieldAccessPolicyFieldAccessPolicyDefinitionRef`` (F.7.10.37)
- ☑ ``setFieldAccessPolicyModifiedWriteValue`` (F.7.10.38)
- ☑ ``setFieldAccessPolicyReadAction`` (F.7.10.39)
- ☑ ``setFieldAccessPolicyReadResponse`` (F.7.10.40)
- ☑ ``setFieldAccessPolicyReserved`` (F.7.10.41)
- ☑ ``setFieldAccessPolicyTestable`` (F.7.10.42)
- ☑ ``setFieldAccessPolicyWriteValueConstraintMinMax`` (F.7.10.43)
- ☑ ``setFieldAccessPolicyWriteValueConstraintUseEnumeratedValue`` (F.7.10.44)
- ☑ ``setFieldAccessPolicyWriteValueConstraintWriteAsRead`` (F.7.10.45)
- ☑ ``setWriteValueConstraintMaximum`` (F.7.10.46)
- ☑ ``setWriteValueConstraintMinimum`` (F.7.10.47)
- ☑ ``setWriteValueConstraintUseEnumeratedValues`` (F.7.10.48)
- ☑ ``setWriteValueConstraintWriteAsRead`` (F.7.10.49)

Address space (BASE)
~~~~~~~~~~~~~~~~~~~~

- ☑ ``getAddressSpaceAddressUnitBits`` (F.7.11.1)
- ☑ ``getAddressSpaceAddressUnitBitsExpression`` (F.7.11.2)
- ☑ ``getAddressSpaceAddressUnitBitsID`` (F.7.11.3)
- ☑ ``getAddressSpaceLocalMemoryMapID`` (F.7.11.4)
- ☑ ``getAddressSpaceRange`` (F.7.11.5)
- ☑ ``getAddressSpaceRangeExpression`` (F.7.11.6)
- ☑ ``getAddressSpaceRangeID`` (F.7.11.7)
- ☑ ``getAddressSpaceSegmentIDs`` (F.7.11.8)
- ☑ ``getAddressSpaceWidth`` (F.7.11.9)
- ☑ ``getAddressSpaceWidthExpression`` (F.7.11.10)
- ☑ ``getAddressSpaceWidthID`` (F.7.11.11)
- ☑ ``getAliasOfAddressSpaceRefByName`` (F.7.11.12)
- ☑ ``getAliasOfAddressSpaceRefID`` (F.7.11.13)
- ☑ ``getLocalMemoryMapAddressBlockIDs`` (F.7.11.14)
- ☑ ``getLocalMemoryMapBankIDs`` (F.7.11.15)
- ☑ ``getRegionAddressOffset`` (F.7.11.16)
- ☑ ``getRegionAddressOffsetExpression`` (F.7.11.17)
- ☑ ``getRegionAddressOffsetID`` (F.7.11.18)
- ☑ ``getRegionRange`` (F.7.11.19)
- ☑ ``getRegionRangeExpression`` (F.7.11.20)
- ☑ ``getRegionRangeID`` (F.7.11.21)
- ☑ ``getSegmentAddressOffset`` (F.7.11.22)
- ☑ ``getSegmentAddressOffsetExpression`` (F.7.11.23)
- ☑ ``getSegmentAddressOffsetID`` (F.7.11.24)
- ☑ ``getSegmentRange`` (F.7.11.25)
- ☑ ``getSegmentRangeExpression`` (F.7.11.26)
- ☑ ``getSegmentRangeID`` (F.7.11.27)

Address space (EXTENDED)
~~~~~~~~~~~~~~~~~~~~~~~~

- ☑ ``addAddressSpaceSegment`` (F.7.12.1)
- ☑ ``addExecutableImageFileSetRef`` (F.7.12.2)
- ☑ ``addLocalMemoryMapAddressBlock`` (F.7.12.3)
- ☑ ``removeAddressSpaceAddressUnitBits`` (F.7.12.4)
- ☑ ``removeAddressSpaceLocalMemoryMap`` (F.7.12.5)
- ☑ ``removeAddressSpaceSegment`` (F.7.12.6)
- ☑ ``removeExecutableImageFileSetRef`` (F.7.12.7)
- ☑ ``removeLinkerCommandFileGenerator`` (F.7.12.8)
- ☑ ``removeLocalMemoryMapAddressBlock`` (F.7.12.9)
- ☑ ``removeLocalMemoryMapBank`` (F.7.12.10)
- ☑ ``setAddressSpaceAddressUnitBits`` (F.7.12.11)
- ☑ ``setAddressSpaceLocalMemoryMap`` (F.7.12.12)
- ☑ ``setAddressSpaceRange`` (F.7.12.13)
- ☑ ``setAddressSpaceWidth`` (F.7.12.14)
- ☑ ``setSegmentAddressOffset`` (F.7.12.15)
- ☑ ``setSegmentRange`` (F.7.12.16)

Array (BASE)
~~~~~~~~~~~~

- ☑ ``getArrayDimIDs`` (F.7.13.1)
- ☑ ``getArrayIDs`` (F.7.13.2)
- ☑ ``getArrayLeftID`` (F.7.13.3)
- ☑ ``getArrayRange`` (F.7.13.4)
- ☑ ``getArrayRangeExpression`` (F.7.13.5)
- ☑ ``getArrayRightID`` (F.7.13.6)
- ☑ ``getArrayStride`` (F.7.13.7)
- ☑ ``getArrayStrideExpression`` (F.7.13.8)
- ☑ ``getArrayStrideID`` (F.7.13.9)
- ☑ ``getDimExpression`` (F.7.13.10)
- ☑ ``getDimIndexVar`` (F.7.13.11)
- ☑ ``getDimValue`` (F.7.13.12)
- ☑ ``getRegisterArrayID`` (F.7.13.13)
- ☑ ``getRegisterFieldArrayID`` (F.7.13.14)

Array (EXTENDED)
~~~~~~~~~~~~~~~~

- ☑ ``addArray`` (F.7.14.1)
- ☑ ``addArrayDim`` (F.7.14.2)
- ☑ ``removeArray`` (F.7.14.3)
- ☑ ``removeArrayDim`` (F.7.14.4)
- ☑ ``removeArrayStride`` (F.7.14.5)
- ☑ ``removeIndexVarAttribute`` (F.7.14.6)
- ☑ ``setArrayStride`` (F.7.14.7)
- ☑ ``setDimIndexVar`` (F.7.14.8)

Assertion (BASE)
~~~~~~~~~~~~~~~~

- ☑ ``getAssertionAssert`` (F.7.15.1)
- ☑ ``getAssertionAssertExpression`` (F.7.15.2)
- ☑ ``getAssertionAssertID`` (F.7.15.3)
- ☑ ``getAssertionIDs`` (F.7.15.4)

Assertion (EXTENDED)
~~~~~~~~~~~~~~~~~~~~

- ☑ ``addAssertion`` (F.7.16.1)
- ☑ ``removeAssertion`` (F.7.16.2)
- ☑ ``setAssertionAssert`` (F.7.16.3)

Bus definition (BASE)
~~~~~~~~~~~~~~~~~~~~~

- ☑ ``getBusDefinitionBroadcast`` (F.7.17.1)
- ☑ ``getBusDefinitionChoiceIDs`` (F.7.17.2)
- ☑ ``getBusDefinitionDirectConnection`` (F.7.17.3)
- ☑ ``getBusDefinitionExtendsRefByVLNV`` (F.7.17.4)
- ☑ ``getBusDefinitionIsAddressable`` (F.7.17.5)
- ☑ ``getBusDefinitionMaxInitiators`` (F.7.17.6)
- ☑ ``getBusDefinitionMaxInitiatorsExpression`` (F.7.17.7)
- ☑ ``getBusDefinitionMaxInitiatorsID`` (F.7.17.8)
- ☑ ``getBusDefinitionMaxTargets`` (F.7.17.9)
- ☑ ``getBusDefinitionMaxTargetsExpression`` (F.7.17.10)
- ☑ ``getBusDefinitionMaxTargetsID`` (F.7.17.11)
- ☑ ``getBusDefinitionSystemGroupNameIDs`` (F.7.17.12)

Bus definition (EXTENDED)
~~~~~~~~~~~~~~~~~~~~~~~~~

- ☑ ``addBusDefinitionChoice`` (F.7.18.1)
- ☑ ``addBusDefinitionSystemGroupName`` (F.7.18.2)
- ☑ ``removeBusDefinitionBroadcast`` (F.7.18.3)
- ☑ ``removeBusDefinitionChoice`` (F.7.18.4)
- ☑ ``removeBusDefinitionExtends`` (F.7.18.5)
- ☑ ``removeBusDefinitionMaxInitiators`` (F.7.18.6)
- ☑ ``removeBusDefinitionMaxTargets`` (F.7.18.7)
- ☑ ``setBusDefinitionBroadcast`` (F.7.18.8)
- ☑ ``setBusDefinitionDirectConnection`` (F.7.18.9)
- ☑ ``setBusDefinitionExtends`` (F.7.18.10)
- ☑ ``setBusDefinitionIsAddressable`` (F.7.18.11)
- ☑ ``setBusDefinitionMaxInitiators`` (F.7.18.12)
- ☑ ``setBusDefinitionMaxTargets`` (F.7.18.13)

Bus interface (BASE)
~~~~~~~~~~~~~~~~~~~~

- ☑ ``getAbstractionTypeAbstractionRefByID`` (F.7.19.1)
- ☑ ``getAbstractionTypeAbstractionRefByVLNV`` (F.7.19.2)
- ☑ ``getAbstractionTypePortMapIDs`` (F.7.19.3)
- ☑ ``getAbstractionTypeViewRefByID`` (F.7.19.4)
- ☑ ``getAbstractionTypeViewRefByNames`` (F.7.19.5)
- ☑ ``getAbstractionTypeViewRefIDs`` (F.7.19.6)
- ☑ ``getAddressSpaceRefBaseAddress`` (F.7.19.7)
- ☑ ``getAddressSpaceRefBaseAddressExpression`` (F.7.19.8)
- ☑ ``getAddressSpaceRefBaseAddressID`` (F.7.19.9)
- ☑ ``getAddressSpaceRefModeRefByID`` (F.7.19.10)
- ☑ ``getAddressSpaceRefModeRefByNames`` (F.7.19.11)
- ☑ ``getBaseAddressesRange`` (F.7.19.12)
- ☑ ``getBaseAddressesRangeExpression`` (F.7.19.13)
- ☑ ``getBaseAddressesRangeID`` (F.7.19.14)
- ☑ ``getBaseAddressesRemapAddressIDs`` (F.7.19.15)
- ☑ ``getBusInterfaceAbstractionTypeIDs`` (F.7.19.16)
- ☑ ``getBusInterfaceBitSteering`` (F.7.19.17)
- ☑ ``getBusInterfaceBitSteeringExpression`` (F.7.19.18)
- ☑ ``getBusInterfaceBitSteeringID`` (F.7.19.19)
- ☑ ``getBusInterfaceBitsInLau`` (F.7.19.20)
- ☑ ``getBusInterfaceBitsInLauExpression`` (F.7.19.21)
- ☑ ``getBusInterfaceBitsInLauID`` (F.7.19.22)
- ☑ ``getBusInterfaceBusTypeID`` (F.7.19.23)
- ☑ ``getBusInterfaceBusTypeRefByID`` (F.7.19.24)
- ☑ ``getBusInterfaceBusTypeRefByVLNV`` (F.7.19.25)
- ☑ ``getBusInterfaceConnectionRequired`` (F.7.19.26)
- ☑ ``getBusInterfaceEndianness`` (F.7.19.27)
- ☑ ``getBusInterfaceInitiatorID`` (F.7.19.28)
- ☑ ``getBusInterfaceInterfaceMode`` (F.7.19.29)
- ☑ ``getBusInterfaceMirroredSystemID`` (F.7.19.30)
- ☑ ``getBusInterfaceMirroredTargetID`` (F.7.19.31)
- ☑ ``getBusInterfaceMonitorID`` (F.7.19.32)
- ☑ ``getBusInterfaceRefLocalName`` (F.7.19.33)
- ☑ ``getBusInterfaceSystemID`` (F.7.19.34)
- ☑ ``getBusInterfaceTargetID`` (F.7.19.35)
- ☑ ``getChannelBusInterfaceRefByID`` (F.7.19.36)
- ☑ ``getChannelBusInterfaceRefIDs`` (F.7.19.37)
- ☑ ``getFileSetRefGroupGroup`` (F.7.19.38)
- ☑ ``getIndirectInterfaceBitsInLauID`` (F.7.19.39)
- ☑ ``getInitiatorAddressSpaceRefByName`` (F.7.19.40)
- ☑ ``getInitiatorAddressSpaceRefID`` (F.7.19.41)
- ☑ ``getMemoryMapRefModeRefByID`` (F.7.19.42)
- ☑ ``getMemoryMapRefModeRefByNames`` (F.7.19.43)
- ☑ ``getMirroredSystemGroup`` (F.7.19.44)
- ☑ ``getMirroredTargetBaseAddressesID`` (F.7.19.45)
- ☑ ``getMonitorGroup`` (F.7.19.46)
- ☑ ``getRemapAddressModeRefByID`` (F.7.19.47)
- ☑ ``getRemapAddressesRemapAddressID`` (F.7.19.48)
- ☑ ``getSystemGroup`` (F.7.19.49)
- ☑ ``getTargetFileSetRefGroupIDs`` (F.7.19.50)
- ☑ ``getTargetMemoryMapRefByName`` (F.7.19.51)
- ☑ ``getTargetMemoryMapRefID`` (F.7.19.52)
- ☑ ``getTargetTransparentBridgeIDs`` (F.7.19.53)

Bus interface (EXTENDED)
~~~~~~~~~~~~~~~~~~~~~~~~

- ☑ ``addAbstractionTypePortMap`` (F.7.20.1)
- ☑ ``addAbstractionTypeViewRef`` (F.7.20.2)
- ☑ ``addAddressSpaceRefModeRef`` (F.7.20.3)
- ☑ ``addBaseAddressesRemapAddresses`` (F.7.20.4)
- ☑ ``addBusInterfaceAbstractionType`` (F.7.20.5)
- ☑ ``addChannelBusInterfaceRef`` (F.7.20.6)
- ☑ ``addMemoryMapRefModeRef`` (F.7.20.7)
- ☑ ``addTargetFileSetRefGroup`` (F.7.20.8)
- ☑ ``addTargetTransparentBridge`` (F.7.20.9)
- ☑ ``removeAbstractionTypePortMap`` (F.7.20.10)
- ☑ ``removeAbstractionTypeViewRef`` (F.7.20.11)
- ☑ ``removeAddressSpaceRefBaseAddress`` (F.7.20.12)
- ☑ ``removeAddressSpaceRefModeRef`` (F.7.20.13)
- ☑ ``removeBaseAddressesRemapAddresses`` (F.7.20.14)
- ☑ ``removeBusDefinitionSystemGroupName`` (F.7.20.15)
- ☑ ``removeBusInterfaceAbstractionType`` (F.7.20.16)
- ☑ ``removeBusInterfaceBitSteering`` (F.7.20.17)
- ☑ ``removeBusInterfaceBitsInLau`` (F.7.20.18)
- ☑ ``removeBusInterfaceConnectionRequired`` (F.7.20.19)
- ☑ ``removeBusInterfaceEndianness`` (F.7.20.20)
- ☑ ``removeChannelBusInterfaceRef`` (F.7.20.21)
- ☑ ``removeFileSetRefGroupGroup`` (F.7.20.22)
- ☑ ``removeIndirectInterfaceBitsInLau`` (F.7.20.23)
- ☑ ``removeInitiatorAddressSpaceRef`` (F.7.20.24)
- ☑ ``removeMemoryMapRefModeRef`` (F.7.20.25)
- ☑ ``removeMirroredTargetBaseAddresses`` (F.7.20.26)
- ☑ ``removeMonitorGroup`` (F.7.20.27)
- ☑ ``removeTargetFileSetRefGroup`` (F.7.20.28)
- ☑ ``removeTargetMemoryMapRef`` (F.7.20.29)
- ☑ ``removeTargetTransparentBridge`` (F.7.20.30)
- ☑ ``setAddressSpaceRefBaseAddress`` (F.7.20.31)
- ☑ ``setBaseAddressesRange`` (F.7.20.32)
- ☑ ``setBusInterfaceBitSteering`` (F.7.20.33)
- ☑ ``setBusInterfaceBitsInLau`` (F.7.20.34)
- ☑ ``setBusInterfaceBusType`` (F.7.20.35)
- ☑ ``setBusInterfaceConnectionRequired`` (F.7.20.36)
- ☑ ``setBusInterfaceEndianness`` (F.7.20.37)
- ☑ ``setBusInterfaceInitiator`` (F.7.20.38)
- ☑ ``setBusInterfaceMirroredInitiator`` (F.7.20.39)
- ☑ ``setBusInterfaceMirroredSystem`` (F.7.20.40)
- ☑ ``setBusInterfaceMirroredTarget`` (F.7.20.41)
- ☑ ``setBusInterfaceMonitor`` (F.7.20.42)
- ☑ ``setBusInterfaceRefLocalName`` (F.7.20.43)
- ☑ ``setBusInterfaceSystem`` (F.7.20.44)
- ☑ ``setBusInterfaceTarget`` (F.7.20.45)
- ☑ ``setFileSetRefGroupGroup`` (F.7.20.46)
- ☑ ``setFileSetRefLocalName`` (F.7.20.47)
- ☑ ``setIndirectInterfaceBitsInLau`` (F.7.20.48)
- ☑ ``setInitiatorAddressSpaceRef`` (F.7.20.49)
- ☑ ``setMirroredSystemGroup`` (F.7.20.50)
- ☑ ``setMirroredTargetBaseAddresses`` (F.7.20.51)
- ☑ ``setMonitorGroup`` (F.7.20.52)
- ☑ ``setRemapAddressesRemapAddress`` (F.7.20.53)
- ☑ ``setSystemGroup`` (F.7.20.54)
- ☑ ``setTargetMemoryMapRef`` (F.7.20.55)

CPU (BASE)
~~~~~~~~~~

- ☑ ``getCpuAddressUnitBits`` (F.7.21.1)
- ☑ ``getCpuAddressUnitBitsExpression`` (F.7.21.2)
- ☑ ``getCpuAddressUnitBitsID`` (F.7.21.3)
- ☑ ``getCpuExecutableImageIDs`` (F.7.21.4)
- ☑ ``getCpuMemoryMapRefByID`` (F.7.21.5)
- ☑ ``getCpuMemoryMapRefByName`` (F.7.21.6)
- ☑ ``getCpuRange`` (F.7.21.7)
- ☑ ``getCpuRangeExpression`` (F.7.21.8)
- ☑ ``getCpuRangeID`` (F.7.21.9)
- ☑ ``getCpuRegionIDs`` (F.7.21.10)
- ☑ ``getCpuWidth`` (F.7.21.11)
- ☑ ``getCpuWidthExpression`` (F.7.21.12)
- ☑ ``getCpuWidthID`` (F.7.21.13)

CPU (EXTENDED)
~~~~~~~~~~~~~~

- ☑ ``addCpuExecutableImage`` (F.7.22.1)
- ☑ ``addCpuRegion`` (F.7.22.2)
- ☑ ``removeCpuAddressUnitBits`` (F.7.22.3)
- ☑ ``removeCpuExecutableImage`` (F.7.22.4)
- ☑ ``removeCpuRegion`` (F.7.22.5)
- ☑ ``setCpuAddressUnitBits`` (F.7.22.6)
- ☑ ``setCpuMemoryMapRef`` (F.7.22.7)
- ☑ ``setCpuRange`` (F.7.22.8)
- ☑ ``setCpuWidth`` (F.7.22.9)
- ☑ ``setRegionAddressOffset`` (F.7.22.10)
- ☑ ``setRegionRange`` (F.7.22.11)

Catalog (BASE)
~~~~~~~~~~~~~~

- ☑ ``getCatalogAbstractionDefIpxactFileIDs`` (F.7.23.1) - Standard typed handles and legacy objects; ordered source traversal and parsed ownership.
- ☑ ``getCatalogAbstractorsIpxactFileIDs`` (F.7.23.2) - Standard typed handles and legacy objects; ordered source traversal and parsed ownership.
- ☑ ``getCatalogBusDefinitionsIpxactFileIDs`` (F.7.23.3) - Standard typed handles and legacy objects; ordered source traversal and parsed ownership.
- ☑ ``getCatalogCatalogsIpxactFileIDs`` (F.7.23.4) - Standard typed handles and legacy objects; ordered source traversal and parsed ownership.
- ☑ ``getCatalogComponentsIpxactFileIDs`` (F.7.23.5) - Standard typed handles and legacy objects; ordered source traversal and parsed ownership.
- ☑ ``getCatalogDesignConfigurationsIpxactFileIDs`` (F.7.23.6) - Standard typed handles and legacy objects; ordered source traversal and parsed ownership.
- ☑ ``getCatalogDesignsIpxactFileIDs`` (F.7.23.7) - Standard typed handles and legacy objects; ordered source traversal and parsed ownership.
- ☑ ``getCatalogGeneratorChainsIpxactFileIDs`` (F.7.23.8) - Standard typed handles and legacy objects; ordered source traversal and parsed ownership.
- ☑ ``getCatalogTypeDefinitionsIpxactFileIDs`` (F.7.23.9) - Standard typed handles and legacy objects; ordered source traversal and parsed ownership.
- ☑ ``getIpxactFileName`` (F.7.23.10) - Standard typed handles and legacy objects; ordered source traversal and parsed ownership.
- ☑ ``getIpxactFileVlnvRefByVLNV`` (F.7.23.11) - Standard typed handles and legacy objects; ordered source traversal and parsed ownership.

Catalog (EXTENDED)
~~~~~~~~~~~~~~~~~~

- ☑ ``addCatalogAbstractionDefIpxactFile`` (F.7.24.1)
- ☑ ``addCatalogAbstractorsIpxactFile`` (F.7.24.2)
- ☑ ``addCatalogBusDefinitionsIpxactFile`` (F.7.24.3)
- ☑ ``addCatalogCatalogsIpxactFile`` (F.7.24.4)
- ☑ ``addCatalogComponentsIpxactFile`` (F.7.24.5)
- ☑ ``addCatalogDesignConfigurationsIpxactFile`` (F.7.24.6)
- ☑ ``addCatalogDesignsIpxactFile`` (F.7.24.7)
- ☑ ``addCatalogGeneratorChainsIpxactFile`` (F.7.24.8)
- ☑ ``addCatalogTypeDefinitionsIpxactFile`` (F.7.24.9)
- ☑ ``removeCatalogAbstractionDefIpxactFile`` (F.7.24.10)
- ☑ ``removeCatalogAbstractorsIpxactFile`` (F.7.24.11)
- ☑ ``removeCatalogBusDefinitionsIpxactFile`` (F.7.24.12)
- ☑ ``removeCatalogCatalogsIpxactFile`` (F.7.24.13)
- ☑ ``removeCatalogComponentsIpxactFile`` (F.7.24.14)
- ☑ ``removeCatalogDesignConfigurationsIpxactFile`` (F.7.24.15)
- ☑ ``removeCatalogDesignsIpxactFile`` (F.7.24.16)
- ☑ ``removeCatalogGeneratorChainsIpxactFile`` (F.7.24.17)
- ☑ ``removeCatalogTypeDefinitionsIpxactFile`` (F.7.24.18)
- ☑ ``setIpxactFileName`` (F.7.24.19)
- ☑ ``setIpxactFileVlnv`` (F.7.24.20)

Choice (BASE)
~~~~~~~~~~~~~

- ☑ ``getChoiceEnumerationIDs`` (F.7.25.1)
- ☑ ``getEnumerationValue`` (F.7.25.2)
- ☑ ``getEnumerationValueExpression`` (F.7.25.3)

Choice (EXTENDED)
~~~~~~~~~~~~~~~~~

- ☑ ``addChoiceEnumeration`` (F.7.26.1)
- ☑ ``removeChoiceEnumeration`` (F.7.26.2)
- ☑ ``setEnumerationValue`` (F.7.26.3)

Clearbox (BASE)
~~~~~~~~~~~~~~~

- ☑ ``getClearboxElementClearboxType`` (F.7.27.1)
- ☑ ``getClearboxElementDriveable`` (F.7.27.2)
- ☑ ``getClearboxElementRefByID`` (F.7.27.3)
- ☑ ``getClearboxElementRefLocationIDs`` (F.7.27.4)

Clearbox (EXTENDED)
~~~~~~~~~~~~~~~~~~~

- ☑ ``addClearboxElementRefLocation`` (F.7.28.1)
- ☑ ``addLocationSlice`` (F.7.28.2)
- ☑ ``removeClearboxElementDriveable`` (F.7.28.3)
- ☑ ``removeClearboxElementRefLocation`` (F.7.28.4)
- ☑ ``setClearboxElementClearboxType`` (F.7.28.5)
- ☑ ``setClearboxElementDriveable`` (F.7.28.6)

Component (BASE)
~~~~~~~~~~~~~~~~

- ☑ ``getComponentAddressSpaceIDs`` (F.7.29.1)
- ☑ ``getComponentBusInterfaceIDs`` (F.7.29.2)
- ☑ ``getComponentChannelIDs`` (F.7.29.3)
- ☑ ``getComponentChoiceIDs`` (F.7.29.4)
- ☑ ``getComponentClearboxElementIDs`` (F.7.29.5)
- ☑ ``getComponentComponentGeneratorIDs`` (F.7.29.6)
- ☑ ``getComponentComponentInstantiationIDs`` (F.7.29.7) - verified with mixed generated choices.
- ☑ ``getComponentCpuIDs`` (F.7.29.8)
- ☑ ``getComponentDesignConfigurationInstantiationIDs`` (F.7.29.9) - verified with mixed generated choices.
- ☑ ``getComponentDesignInstantiationIDs`` (F.7.29.10) - verified with mixed generated choices.
- ☑ ``getComponentExternalTypeDefinitionsIDs`` (F.7.29.11)
- ☑ ``getComponentFileSetIDs`` (F.7.29.12)
- ☑ ``getComponentIndirectInterfaceIDs`` (F.7.29.13)
- ☑ ``getComponentMemoryMapIDs`` (F.7.29.14)
- ☑ ``getComponentModeIDs`` (F.7.29.15)
- ☑ ``getComponentOtherClockDriverIDs`` (F.7.29.16)
- ☑ ``getComponentPortIDs`` (F.7.29.17) - verified with generated structured choices and parsed lifecycle ownership.
- ☑ ``getComponentPowerDomainIDs`` (F.7.29.18)
- ☑ ``getComponentResetTypeIDs`` (F.7.29.19)
- ☑ ``getComponentSelectedViewIDs`` (F.7.29.20)
- ☑ ``getComponentViewIDs`` (F.7.29.21)
- ☑ ``getModeCondition`` (F.7.29.22)
- ☑ ``getModeConditionExpression`` (F.7.29.23)
- ☑ ``getModeName`` (F.7.29.24)

Component (EXTENDED)
~~~~~~~~~~~~~~~~~~~~

- ☑ ``addComponentAddressSpace`` (F.7.30.1)
- ☑ ``addComponentChannel`` (F.7.30.2)
- ☑ ``addComponentChoice`` (F.7.30.3)
- ☑ ``addComponentClearboxElement`` (F.7.30.4)
- ☑ ``addComponentComponentGenerator`` (F.7.30.5)
- ☑ ``addComponentComponentInstantiation`` (F.7.30.6) - generated creation and immediate lifecycle verified.
- ☑ ``addComponentCpu`` (F.7.30.7)
- ☑ ``addComponentDesignConfigurationInstantiation`` (F.7.30.8) - generated creation and immediate lifecycle verified.
- ☑ ``addComponentDesignInstantiation`` (F.7.30.9) - generated creation and immediate lifecycle verified.
- ☑ ``addComponentFileSet`` (F.7.30.10)
- ☑ ``addComponentIndirectInterface`` (F.7.30.11)
- ☑ ``addComponentInitiatorBusInterface`` (F.7.30.12)
- ☑ ``addComponentMemoryMap`` (F.7.30.13)
- ☑ ``addComponentMirroredInitiatorBusInterface`` (F.7.30.14)
- ☑ ``addComponentMirroredSystemBusInterface`` (F.7.30.15)
- ☑ ``addComponentMirroredTargetBusInterface`` (F.7.30.16)
- ☑ ``addComponentMode`` (F.7.30.17)
- ☑ ``addComponentMonitorBusInterface`` (F.7.30.18)
- ☑ ``addComponentOtherClockDriver`` (F.7.30.19) - uses generated models, standard arguments and immediate ownership.
- ☑ ``addComponentResetType`` (F.7.30.20)
- ☑ ``addComponentStructuredInterfacePort`` (F.7.30.21) - verified with generated structured choices and parsed lifecycle ownership.
- ☑ ``addComponentStructuredStructPort`` (F.7.30.22) - verified with generated structured choices and parsed lifecycle ownership.
- ☑ ``addComponentStructuredUnionPort`` (F.7.30.23) - verified with generated structured choices and parsed lifecycle ownership.
- ☑ ``addComponentSystemBusInterface`` (F.7.30.24)
- ☑ ``addComponentTargetBusInterface`` (F.7.30.25)
- ☑ ``addComponentTransactionalPort`` (F.7.30.26) - uses generated models, standard arguments and immediate ownership.
- ☑ ``addComponentView`` (F.7.30.27) - uses generated models, standard arguments and immediate ownership.
- ☑ ``addComponentWirePort`` (F.7.30.28) - uses generated models, standard arguments and immediate ownership.
- ☑ ``removeComponentAddressSpace`` (F.7.30.29)
- ☑ ``removeComponentBusInterface`` (F.7.30.30)
- ☑ ``removeComponentChannel`` (F.7.30.31)
- ☑ ``removeComponentChoice`` (F.7.30.32)
- ☑ ``removeComponentClearboxElement`` (F.7.30.33)
- ☑ ``removeComponentComponentGenerator`` (F.7.30.34)
- ☑ ``removeComponentComponentInstantiation`` (F.7.30.35) - verified with mixed generated choices.
- ☑ ``removeComponentCpu`` (F.7.30.36)
- ☑ ``removeComponentDesignConfigurationInstantiation`` (F.7.30.37) - verified with mixed generated choices.
- ☑ ``removeComponentDesignInstantiation`` (F.7.30.38) - verified with mixed generated choices.
- ☑ ``removeComponentFileSet`` (F.7.30.39) - uses its standard child handle with parsed ownership and descendant invalidation.
- ☑ ``removeComponentIndirectInterface`` (F.7.30.40)
- ☑ ``removeComponentMemoryMap`` (F.7.30.41) - uses its standard child handle with parsed ownership and descendant invalidation.
- ☑ ``removeComponentMode`` (F.7.30.42)
- ☑ ``removeComponentOtherClockDriver`` (F.7.30.43) - uses its standard child handle with parsed ownership and descendant invalidation.
- ☑ ``removeComponentPort`` (F.7.30.44) - uses its standard child handle with parsed ownership and descendant invalidation; verified with generated structured choices and parsed lifecycle ownership.
- ☑ ``removeComponentResetType`` (F.7.30.45) - uses its standard child handle with parsed ownership and descendant invalidation.
- ☑ ``removeComponentView`` (F.7.30.46) - uses generated models, standard arguments and immediate ownership; verified with registered parsed roots or typed local target lifecycle.
- ☑ ``removeMemoryMapAddressUnitBits`` (F.7.30.47)
- ☑ ``removeModeCondition`` (F.7.30.48)
- ☑ ``removePowerDomainAlwaysOn`` (F.7.30.49)
- ☑ ``setIndirectInterfaceIndirectAddressRef`` (F.7.30.50)
- ☑ ``setIndirectInterfaceIndirectDataRef`` (F.7.30.51)
- ☑ ``setMemoryMapAddressUnitBits`` (F.7.30.52)
- ☑ ``setModeCondition`` (F.7.30.53)
- ☑ ``setModeName`` (F.7.30.54)

Configurable element (BASE)
~~~~~~~~~~~~~~~~~~~~~~~~~~~

- ☑ ``getConfigurableElementIDs`` (F.7.31.1)
- ☑ ``getConfigurableElementValue`` (F.7.31.2)
- ☑ ``getConfigurableElementValueExpression`` (F.7.31.3)
- ☑ ``getConfigurableElementValueIDs`` (F.7.31.4)
- ☑ ``getConfigurableElementValueReferenceID`` (F.7.31.5)
- ☑ ``getConfigurableElementValueValueExpression`` (F.7.31.6)
- ☑ ``getUnconfiguredID`` (F.7.31.7)

Configurable element (EXTENDED)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- ☑ ``addConfigurableElementValue`` (F.7.32.1)
- ☑ ``addViewConfigurationConfigurableElementValue`` (F.7.32.2)
- ☑ ``removeConfigurableElementValue`` (F.7.32.3)
- ☑ ``setConfigurableElementValue`` (F.7.32.4)
- ☑ ``setConfigurableElementValueReferenceID`` (F.7.32.5)
- ☑ ``setConfigurableElementValueValue`` (F.7.32.6)

Constraint (BASE)
~~~~~~~~~~~~~~~~~

- ☑ ``getCellSpecificationCellClass`` (F.7.33.1)
- ☑ ``getCellSpecificationCellFunction`` (F.7.33.2)
- ☑ ``getCellSpecificationCellFunctionID`` (F.7.33.3)
- ☑ ``getConstraintSetDriveConstraintCellSpecificationID`` (F.7.33.4)
- ☑ ``getConstraintSetLoadConstraintID`` (F.7.33.5)
- ☑ ``getConstraintSetRefLocalName`` (F.7.33.6)
- ☑ ``getConstraintSetReferenceName`` (F.7.33.7)
- ☑ ``getConstraintSetTimingConstraintIDs`` (F.7.33.8)
- ☑ ``getConstraintSetVector`` (F.7.33.9)
- ☑ ``getConstraintSetVectorExpression`` (F.7.33.10)
- ☑ ``getConstraintSetVectorLeftID`` (F.7.33.11)
- ☑ ``getConstraintSetVectorRightID`` (F.7.33.12)
- ☑ ``getDriveConstraintOther`` (F.7.33.13)
- ☑ ``getDriveConstraintType`` (F.7.33.14)
- ☑ ``getDriveConstraintValue`` (F.7.33.15)
- ☑ ``getLoadConstraintCellSpecificationID`` (F.7.33.16)
- ☑ ``getLoadConstraintCount`` (F.7.33.17)
- ☑ ``getLoadConstraintCountExpression`` (F.7.33.18)
- ☑ ``getLoadConstraintCountID`` (F.7.33.19)
- ☑ ``getLoadConstraintOther`` (F.7.33.20)
- ☑ ``getLoadConstraintType`` (F.7.33.21)
- ☑ ``getLoadConstraintValue`` (F.7.33.22)
- ☑ ``getTimingConstraintValue`` (F.7.33.23)

Constraint (EXTENDED)
~~~~~~~~~~~~~~~~~~~~~

- ☑ ``removeConstraintSetDriveConstraint`` (F.7.34.1)
- ☑ ``removeConstraintSetLoadConstraint`` (F.7.34.2)
- ☑ ``removeConstraintSetTimingConstraint`` (F.7.34.3)
- ☑ ``removeConstraintSetVector`` (F.7.34.4)
- ☑ ``removeLoadConstraintCount`` (F.7.34.5)
- ☑ ``setCellSpecificationCellClass`` (F.7.34.6)
- ☑ ``setCellSpecificationCellFunction`` (F.7.34.7)
- ☑ ``setConstraintSetDriveConstraint`` (F.7.34.8)
- ☑ ``setConstraintSetLoadConstraint`` (F.7.34.9)
- ☑ ``setConstraintSetReferenceName`` (F.7.34.10)
- ☑ ``setConstraintSetVector`` (F.7.34.11)
- ☑ ``setDriveConstraintOtherValue`` (F.7.34.12)
- ☑ ``setDriveConstraintValue`` (F.7.34.13)
- ☑ ``setLoadConstraintCellSpecification`` (F.7.34.14)
- ☑ ``setLoadConstraintCount`` (F.7.34.15)
- ☑ ``setLoadConstraintOtherValue`` (F.7.34.16)
- ☑ ``setTimingConstraintValue`` (F.7.34.17)

Constraint Set (BASE)
~~~~~~~~~~~~~~~~~~~~~

- ☑ ``getConstraintSetTimingConstraints`` (F.7.35.1)

Constraint Set (EXTENDED)
~~~~~~~~~~~~~~~~~~~~~~~~~

- ☑ ``addConstraintSetTimingConstraint`` (F.7.36.1)

Design (BASE)
~~~~~~~~~~~~~

- ☐ ``getActiveinterfaceExcludePortIDs`` (F.7.37.1)
- ☐ ``getAdHocConnectionExternalPortReferenceIDs`` (F.7.37.2)
- ☐ ``getAdHocConnectionInternalPortReferenceIDs`` (F.7.37.3)
- ☐ ``getAdHocConnectionTiedValue`` (F.7.37.4)
- ☐ ``getAdHocConnectionTiedValueExpression`` (F.7.37.5)
- ☐ ``getAdHocConnectionTiedValueID`` (F.7.37.6)
- ☐ ``getInternalPortReferenceComponentInstanceRefByName`` (F.7.37.7)
- ☐ ``getComponentInstanceComponentRefByID`` (F.7.37.8)
- ☐ ``getComponentInstanceComponentRefByVLNV`` (F.7.37.9)
- ☐ ``getComponentInstanceName`` (F.7.37.10)
- ☐ ``getComponentInstancePowerDomainLinkIDs`` (F.7.37.11)
- ☐ ``getDesignAdHocConnectionIDs`` (F.7.37.12)
- ☐ ``getDesignChoiceIDs`` (F.7.37.13)
- ☐ ``getDesignComponentInstanceIDs`` (F.7.37.14)
- ☐ ``getDesignID`` (F.7.37.15)
- ☑ ``getDesignInterconnectionIDs`` (F.7.37.16)
- ☑ ``getDesignMonitorInterconnectionIDs`` (F.7.37.17)
- ☐ ``getExternalPortReferencePartSelectID`` (F.7.37.18)
- ☐ ``getExternalPortReferencePortRefByName`` (F.7.37.19)
- ☐ ``getExternalPortReferenceSubPortReferenceIDs`` (F.7.37.20)
- ☐ ``getInterconnectionActiveInterfaceIDs`` (F.7.37.21)
- ☐ ``getInterconnectionHierInterfaceIDs`` (F.7.37.22)
- ☐ ``getInternalPortReferencePartSelectID`` (F.7.37.23)
- ☐ ``getInternalPortReferencePortRefByName`` (F.7.37.24)
- ☐ ``getInternalPortReferenceSubPortReferenceIDs`` (F.7.37.25)
- ☐ ``getMonitorInterconnectionMonitorInterfaceIDs`` (F.7.37.26)
- ☐ ``getMonitorInterconnectionMonitoredActiveInterfaceID`` (F.7.37.27)
- ☐ ``getPowerDomainLinkExternalPowerDomainRef`` (F.7.37.28)
- ☐ ``getPowerDomainLinkExternalPowerDomainRefByID`` (F.7.37.29)
- ☐ ``getPowerDomainLinkExternalPowerDomainRefByName`` (F.7.37.30)
- ☐ ``getPowerDomainLinkExternalPowerDomainRefExpression`` (F.7.37.31)
- ☐ ``getPowerDomainLinkExternalPowerDomainRefID`` (F.7.37.32)
- ☐ ``getPowerDomainLinkInternalPowerDomainRefs`` (F.7.37.33)

Design (EXTENDED)
~~~~~~~~~~~~~~~~~

- ☐ ``addActiveInterfaceExcludePort`` (F.7.38.1)
- ☐ ``addAdHocConnectionExternalPortReference`` (F.7.38.2)
- ☐ ``addAdHocConnectionInternalPortReference`` (F.7.38.3)
- ☐ ``addDesignAdHocConnection`` (F.7.38.4)
- ☐ ``addDesignChoice`` (F.7.38.5)
- ☐ ``addDesignComponentInstance`` (F.7.38.6)
- ☐ ``addDesignExternalAdHocConnection`` (F.7.38.7)
- ☐ ``addDesignInterconnection`` (F.7.38.8)
- ☐ ``addDesignMonitorInterconnection`` (F.7.38.9)
- ☐ ``addInterconnectionActiveInterface`` (F.7.38.10)
- ☐ ``addInterconnectionHierInterface`` (F.7.38.11)
- ☐ ``addMonitorInterconnectionMonitorInterface`` (F.7.38.12)
- ☐ ``removeActiveInterfaceExcludePort`` (F.7.38.13)
- ☐ ``removeAdHocConnectionExternalPortReference`` (F.7.38.14)
- ☐ ``removeAdHocConnectionInternalPortReference`` (F.7.38.15)
- ☐ ``removeAdHocConnectionTiedValue`` (F.7.38.16)
- ☐ ``removeDesignAdHocConnection`` (F.7.38.17)
- ☐ ``removeDesignChoice`` (F.7.38.18)
- ☐ ``removeDesignComponentInstance`` (F.7.38.19)
- ☐ ``removeDesignInterconnection`` (F.7.38.20)
- ☐ ``removeDesignMonitorConnection`` (F.7.38.21)
- ☐ ``removeExternalPortReferencePartSelect`` (F.7.38.22)
- ☐ ``removeExternalPortReferenceSubPortReference`` (F.7.38.23)
- ☐ ``removeInterconnectionActiveInterface`` (F.7.38.24)
- ☐ ``removeInterconnectionHierInterface`` (F.7.38.25)
- ☐ ``removeInternalPortReferencePartSelect`` (F.7.38.26)
- ☐ ``removeInternalPortReferenceSubPortReference`` (F.7.38.27)
- ☐ ``removeMonitorInterconnectionMonitorInterface`` (F.7.38.28)
- ☐ ``setAdHocConnectionTiedValue`` (F.7.38.29)
- ☐ ``setComponentInstanceComponentRef`` (F.7.38.30)
- ☐ ``setExternalPortReferencePartSelect`` (F.7.38.31)
- ☐ ``setInternalPortReferencePartSelect`` (F.7.38.32)
- ☐ ``setInterconnectionActiveInterface`` (F.7.38.33)
- ☐ ``setInterconnectionHierInterface`` (F.7.38.34)
- ☐ ``setMonitorInterconnectionMonitoredActiveInterface`` (F.7.38.35)
- ☐ ``setMonitoredActiveInterfacePath`` (F.7.38.36)
- ☐ ``setPowerDomainLinkExternalPowerDomainRef`` (F.7.38.37)

Design configuration (BASE)
~~~~~~~~~~~~~~~~~~~~~~~~~~~

- ☑ ``getAbstractorInstanceAbstractorRefByID`` (F.7.39.1)
- ☑ ``getAbstractorInstanceAbstractorRefByVLNV`` (F.7.39.2)
- ☑ ``getAbstractorInstanceInstanceName`` (F.7.39.3)
- ☑ ``getAbstractorInstanceViewName`` (F.7.39.4)
- ☑ ``getAbstractorInstancesAbstractorInstanceIDs`` (F.7.39.5)
- ☑ ``getAbstractorInstancesInterfaceRefIDs`` (F.7.39.6)
- ☑ ``getDesignConfigurationChoiceIDs`` (F.7.39.7)
- ☑ ``getDesignConfigurationDesignRefByID`` (F.7.39.8)
- ☑ ``getDesignConfigurationDesignRefByVLNV`` (F.7.39.9)
- ☑ ``getDesignConfigurationGeneratorChainConfigurationIDs`` (F.7.39.10)
- ☑ ``getDesignConfigurationInterconnectionConfigurationIDs`` (F.7.39.11)
- ☑ ``getDesignConfigurationViewConfigurationIDs`` (F.7.39.12)
- ☑ ``getGeneratorChainConfigurationRefByID`` (F.7.39.13)
- ☑ ``getGeneratorChainConfigurationRefByVLNV`` (F.7.39.14)
- ☑ ``getInterconnectionConfigurationAbstractorsInstancesIDs`` (F.7.39.15)
- ☑ ``getInterconnectionConfigurationInterconnectionRefByID`` (F.7.39.16)
- ☑ ``getInterconnectionConfigurationInterconnectionRefByName`` (F.7.39.17)
- ☑ ``getViewConfigurationConfigurableElementValueIDs`` (F.7.39.18)
- ☑ ``getViewConfigurationInstanceName`` (F.7.39.19)
- ☑ ``getViewConfigurationViewID`` (F.7.39.20)
- ☑ ``getViewConfigurationViewRefByName`` (F.7.39.21)

Design configuration (EXTENDED)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- ☑ ``addAbstractorInstancesAbstractorInstance`` (F.7.40.1)
- ☑ ``addAbstractorInstancesInterfaceRef`` (F.7.40.2)
- ☑ ``addDesignConfChoice`` (F.7.40.3)
- ☑ ``addDesignConfigurationGeneratorChainConfiguration`` (F.7.40.4)
- ☑ ``addDesignConfigurationInterconnectionConfiguration`` (F.7.40.5)
- ☑ ``addDesignConfigurationViewConfiguration`` (F.7.40.6)
- ☑ ``addInterconnectionConfigurationAbstractorInstances`` (F.7.40.7)
- ☑ ``removeAbstractorInstancesAbstractorInstance`` (F.7.40.8)
- ☑ ``removeAbstractorInstancesInterfaceRef`` (F.7.40.9)
- ☑ ``removeDesignConfChoice`` (F.7.40.10)
- ☑ ``removeDesignConfigurationDesignRef`` (F.7.40.11)
- ☑ ``removeDesignConfigurationGeneratorChainConfiguration`` (F.7.40.12)
- ☑ ``removeDesignConfigurationInterconnectionConfiguration`` (F.7.40.13)
- ☑ ``removeDesignConfigurationViewConfiguration`` (F.7.40.14)
- ☑ ``removeInterconnectionConfigurationAbstractorInstances`` (F.7.40.15)
- ☑ ``removeViewConfigurationConfigurableElementValue`` (F.7.40.16)
- ☑ ``setAbstractorInstanceAbstractorRef`` (F.7.40.17)
- ☑ ``setAbstractorInstanceInstanceName`` (F.7.40.18)
- ☑ ``setAbstractorInstanceViewName`` (F.7.40.19)
- ☑ ``setDesignConfigurationDesignRef`` (F.7.40.20)
- ☑ ``setInterconnectionConfigurationInterconnectionRef`` (F.7.40.21)
- ☑ ``setViewConfigurationInstanceName`` (F.7.40.22)
- ☑ ``setViewConfigurationView`` (F.7.40.23)

Driver (BASE)
~~~~~~~~~~~~~

- ☑ ``getClockDriverClockPeriod`` (F.7.41.1)
- ☑ ``getClockDriverClockPeriodExpression`` (F.7.41.2)
- ☑ ``getClockDriverClockPeriodID`` (F.7.41.3)
- ☑ ``getClockDriverClockPulseDuration`` (F.7.41.4)
- ☑ ``getClockDriverClockPulseDurationExpression`` (F.7.41.5)
- ☑ ``getClockDriverClockPulseDurationID`` (F.7.41.6)
- ☑ ``getClockDriverClockPulseOffset`` (F.7.41.7)
- ☑ ``getClockDriverClockPulseOffsetExpression`` (F.7.41.8)
- ☑ ``getClockDriverClockPulseOffsetID`` (F.7.41.9)
- ☑ ``getClockDriverClockPulseValue`` (F.7.41.10)
- ☑ ``getClockDriverClockPulseValueExpression`` (F.7.41.11)
- ☑ ``getClockDriverClockPulseValueID`` (F.7.41.12)
- ☑ ``getDriverClockDriverID`` (F.7.41.13)
- ☑ ``getDriverDefaultValue`` (F.7.41.14)
- ☑ ``getDriverDefaultValueExpression`` (F.7.41.15)
- ☑ ``getDriverDefaultValueID`` (F.7.41.16)
- ☑ ``getDriverLeftID`` (F.7.41.17)
- ☑ ``getDriverRange`` (F.7.41.18)
- ☑ ``getDriverRangeExpression`` (F.7.41.19)
- ☑ ``getDriverRightID`` (F.7.41.20)
- ☑ ``getDriverSingleShotDriverID`` (F.7.41.21)
- ☑ ``getDriverViewRefByID`` (F.7.41.22)
- ☑ ``getDriverViewRefIDs`` (F.7.41.23)
- ☑ ``getOtherClockDriverClockPeriod`` (F.7.41.24)
- ☑ ``getOtherClockDriverClockPeriodExpression`` (F.7.41.25)
- ☑ ``getOtherClockDriverClockPeriodID`` (F.7.41.26)
- ☑ ``getOtherClockDriverClockPulseDuration`` (F.7.41.27)
- ☑ ``getOtherClockDriverClockPulseDurationExpression`` (F.7.41.28)
- ☑ ``getOtherClockDriverClockPulseDurationID`` (F.7.41.29)
- ☑ ``getOtherClockDriverClockPulseOffset`` (F.7.41.30)
- ☑ ``getOtherClockDriverClockPulseOffsetExpression`` (F.7.41.31)
- ☑ ``getOtherClockDriverClockPulseOffsetID`` (F.7.41.32)
- ☑ ``getOtherClockDriverClockPulseValue`` (F.7.41.33)
- ☑ ``getOtherClockDriverClockPulseValueExpression`` (F.7.41.34)
- ☑ ``getOtherClockDriverClockPulseValueID`` (F.7.41.35)
- ☑ ``getSingleShotDriverSingleShotDuration`` (F.7.41.36)
- ☑ ``getSingleShotDriverSingleShotDurationExpression`` (F.7.41.37)
- ☑ ``getSingleShotDriverSingleShotDurationID`` (F.7.41.38)
- ☑ ``getSingleShotDriverSingleShotOffset`` (F.7.41.39)
- ☑ ``getSingleShotDriverSingleShotOffsetExpression`` (F.7.41.40)
- ☑ ``getSingleShotDriverSingleShotOffsetID`` (F.7.41.41)
- ☑ ``getSingleShotDriverSingleShotValue`` (F.7.41.42)
- ☑ ``getSingleShotDriverSingleShotValueExpression`` (F.7.41.43)
- ☑ ``getSingleShotDriverSingleShotValueID`` (F.7.41.44)

Driver (EXTENDED)
~~~~~~~~~~~~~~~~~

- ☑ ``addDriverSingleShotDriver`` (F.7.42.1)
- ☑ ``addDriverViewRef`` (F.7.42.2)
- ☑ ``removeDriverClockDriver`` (F.7.42.3)
- ☑ ``removeDriverRange`` (F.7.42.4)
- ☑ ``removeDriverSingleShotDriver`` (F.7.42.5)
- ☑ ``removeDriverViewRef`` (F.7.42.6)
- ☑ ``setClockDriverClockPeriod`` (F.7.42.7)
- ☑ ``setClockDriverClockPulseDuration`` (F.7.42.8)
- ☑ ``setClockDriverClockPulseOffset`` (F.7.42.9)
- ☑ ``setClockDriverClockPulseValue`` (F.7.42.10)
- ☑ ``setDriverClockDriver`` (F.7.42.11)
- ☑ ``setDriverSingleShotDriver`` (F.7.42.12)
- ☑ ``setDriverDefaultValue`` (F.7.42.13)
- ☑ ``setDriverRange`` (F.7.42.14)
- ☑ ``setOtherClockDriverClockPeriod`` (F.7.42.15)
- ☑ ``setOtherClockDriverClockPulseDuration`` (F.7.42.16)
- ☑ ``setOtherClockDriverClockPulseOffset`` (F.7.42.17)
- ☑ ``setOtherClockDriverClockPulseValue`` (F.7.42.18)
- ☑ ``setSingleShotDriverSingleShotDuration`` (F.7.42.19)
- ☑ ``setSingleShotDriverSingleShotOffset`` (F.7.42.20)
- ☑ ``setSingleShotDriverSingleShotValue`` (F.7.42.21)

Element attribute (BASE)
~~~~~~~~~~~~~~~~~~~~~~~~

- ☑ ``getAddressBlockRefAttribute`` (F.7.43.1)
- ☑ ``getAddressBlockRefAttributeByID`` (F.7.43.2)
- ☑ ``getAddressSpaceRefAttribute`` (F.7.43.3)
- ☑ ``getAddressSpaceRefAttributeByID`` (F.7.43.4)
- ☑ ``getAllBitsBooleanAttribute`` (F.7.43.5)
- ☑ ``getAllLogicalDirectionsAllowedBooleanAttribute`` (F.7.43.6)
- ☑ ``getAllLogicalInitiativesAllowedBooleanAttribute`` (F.7.43.7)
- ☑ ``getAlternateRegisterRefAttribute`` (F.7.43.8)
- ☑ ``getAlternateRegisterRefAttributeByID`` (F.7.43.9)
- ☑ ``getAppendBooleanAttribute`` (F.7.43.10)
- ☑ ``getArrayIdAttribute`` (F.7.43.11)
- ☑ ``getBankAlignmentAttribute`` (F.7.43.12)
- ☑ ``getBankRefAttribute`` (F.7.43.13)
- ☑ ``getBankRefAttributeByID`` (F.7.43.14)
- ☑ ``getBusRefAttribute`` (F.7.43.15)
- ☑ ``getBusRefAttributeByID`` (F.7.43.16)
- ☑ ``getCellStrengthAttribute`` (F.7.43.17)
- ☑ ``getChoiceRefAttribute`` (F.7.43.18)
- ☑ ``getChoiceRefAttributeByID`` (F.7.43.19)
- ☑ ``getClockEdgeAttribute`` (F.7.43.20)
- ☑ ``getClockNameAttribute`` (F.7.43.21)
- ☑ ``getClockSourceAttribute`` (F.7.43.22)
- ☑ ``getComponentInstanceRefAttribute`` (F.7.43.23)
- ☑ ``getComponentInstanceRefAttributeByID`` (F.7.43.24)
- ☑ ``getComponentRefAttribute`` (F.7.43.25)
- ☑ ``getComponentRefAttributeByID`` (F.7.43.26)
- ☑ ``getConfigGroupsAttribute`` (F.7.43.27)
- ☑ ``getConstrainedAttributeValues`` (F.7.43.28)
- ☑ ``getConstraintSetIdAttribute`` (F.7.43.29)
- ☑ ``getCustomAttribute`` (F.7.43.30)
- ☑ ``getDataTypeAttribute`` (F.7.43.31)
- ☑ ``getDataTypeDefinitionAttribute`` (F.7.43.32)
- ☑ ``getDefaultBooleanAttribute`` (F.7.43.33)
- ☑ ``getDelayTypeAttribute`` (F.7.43.34)
- ☑ ``getDirectionAttribute`` (F.7.43.35)
- ☑ ``getDriverTypeAttribute`` (F.7.43.36)
- ☑ ``getExactBooleanAttribute`` (F.7.43.37)
- ☑ ``getExternalDeclarationsBooleanAttribute`` (F.7.43.38)
- ☑ ``getFieldRefAttribute`` (F.7.43.39)
- ☑ ``getFieldRefAttributeByID`` (F.7.43.40)
- ☑ ``getFileIdAttribute`` (F.7.43.41)
- ☑ ``getFlowTypeAttribute`` (F.7.43.42)
- ☑ ``getForceBooleanAttribute`` (F.7.43.43)
- ☑ ``getGroupAttribute`` (F.7.43.44)
- ☑ ``getHelpAttribute`` (F.7.43.45)
- ☑ ``getHiddenBooleanAttribute`` (F.7.43.46)
- ☑ ``getIdAttribute`` (F.7.43.47)
- ☑ ``getImageIdAttribute`` (F.7.43.48)
- ☑ ``getImageTypeAttribute`` (F.7.43.49)
- ☑ ``getImplicitBooleanAttribute`` (F.7.43.50)
- ☑ ``getIndexVarAttribute`` (F.7.43.51)
- ☑ ``getInitiatorRefAttribute`` (F.7.43.52)
- ☑ ``getInitiatorRefAttributeByID`` (F.7.43.53)
- ☑ ``getInterfaceModeAttribute`` (F.7.43.54)
- ☑ ``getInvertAttribute`` (F.7.43.55)
- ☑ ``getIsIOBooleanAttribute`` (F.7.43.56)
- ☑ ``getLevelAttribute`` (F.7.43.57)
- ☑ ``getLibextAttribute`` (F.7.43.58)
- ☑ ``getLibraryAttribute`` (F.7.43.59)
- ☑ ``getMandatoryBooleanAttribute`` (F.7.43.60)
- ☑ ``getMaximumAttribute`` (F.7.43.61)
- ☑ ``getMaximumDoubleAttribute`` (F.7.43.62)
- ☑ ``getMaximumIntAttribute`` (F.7.43.63)
- ☑ ``getMemoryMapRefAttribute`` (F.7.43.64)
- ☑ ``getMemoryMapRefAttributeByID`` (F.7.43.65)
- ☑ ``getMemoryReMapRefAttributeByID`` (F.7.43.66)
- ☑ ``getMemoryRemapRefAttribute`` (F.7.43.67)
- ☑ ``getMinimumAttribute`` (F.7.43.68)
- ☑ ``getMinimumDoubleAttribute`` (F.7.43.69)
- ☑ ``getMinimumIntAttribute`` (F.7.43.70)
- ☑ ``getMisalignmentAllowedBooleanAttribute`` (F.7.43.71)
- ☑ ``getModeRefAttribute`` (F.7.43.72)
- ☑ ``getModifyAttribute`` (F.7.43.73)
- ☑ ``getMultipleGroupSelectionOperatorAttribute`` (F.7.43.74)
- ☑ ``getNameAttribute`` (F.7.43.75)
- ☑ ``getOrderFloatAttribute`` (F.7.43.76)
- ☑ ``getOtherAnyAttribute`` (F.7.43.77)
- ☑ ``getOtherAttribute`` (F.7.43.78)
- ☑ ``getOtherAttributes`` (F.7.43.79)
- ☑ ``getPackedBooleanAttribute`` (F.7.43.80)
- ☑ ``getParameterIdAttribute`` (F.7.43.81)
- ☑ ``getPathAttribute`` (F.7.43.82)
- ☑ ``getPhantomBooleanAttribute`` (F.7.43.83)
- ☑ ``getPortRefAttribute`` (F.7.43.84)
- ☑ ``getPortRefAttributeByID`` (F.7.43.85)
- ☑ ``getPowerDomainRefAttribute`` (F.7.43.86)
- ☑ ``getPowerDomainRefAttributeByID`` (F.7.43.87)
- ☑ ``getPrefixAttribute`` (F.7.43.88)
- ☑ ``getPriorityIntAttribute`` (F.7.43.89)
- ☑ ``getPromptAttribute`` (F.7.43.90)
- ☑ ``getReferenceIdAttribute`` (F.7.43.91)
- ☑ ``getRegisterFileRefAttribute`` (F.7.43.92)
- ☑ ``getRegisterFileRefAttributeByID`` (F.7.43.93)
- ☑ ``getRegisterRefAttribute`` (F.7.43.94)
- ☑ ``getReplicateBooleanAttribute`` (F.7.43.95)
- ☑ ``getResetTypeRefAttribute`` (F.7.43.96)
- ☑ ``getResetTypeRefAttributeByID`` (F.7.43.97)
- ☑ ``getResolveAttribute`` (F.7.43.98)
- ☑ ``getScopeAttribute`` (F.7.43.99)
- ☑ ``getSegmentRefAttribute`` (F.7.43.100)
- ☑ ``getSegmentRefAttributeByID`` (F.7.43.101)
- ☑ ``getSignAttribute`` (F.7.43.102)
- ☑ ``getStrictBooleanAttribute`` (F.7.43.103)
- ☑ ``getSubPortRefAttribute`` (F.7.43.104)
- ☑ ``getSubPortRefAttributeByID`` (F.7.43.105)
- ☑ ``getTestConstraintAttribute`` (F.7.43.106)
- ☑ ``getTextAttribute`` (F.7.43.107)
- ☑ ``getTypeAttribute`` (F.7.43.108)
- ☑ ``getTypeDefinitionsAttribute`` (F.7.43.109)
- ☑ ``getUniqueBooleanAttribute`` (F.7.43.110)
- ☑ ``getUnitAttribute`` (F.7.43.111)
- ☑ ``getUnitsAttribute`` (F.7.43.112)
- ☑ ``getUsageAttribute`` (F.7.43.113)
- ☑ ``getUsageTypeAttribute`` (F.7.43.114)
- ☑ ``getUserAttribute`` (F.7.43.115)
- ☑ ``getVectorIdAttribute`` (F.7.43.116)
- ☑ ``getVendorAttribute`` (F.7.43.117)
- ☑ ``getVersionAttribute`` (F.7.43.118)
- ☑ ``getViewRefAttribute`` (F.7.43.119)
- ☑ ``getViewRefAttributeByID`` (F.7.43.120)

Element attribute (EXTENDED)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- ☑ ``addConstrainedAttribute`` (F.7.44.1)
- ☑ ``isSetAttribute`` (F.7.44.2)
- ☑ ``removeAllBitsAttribute`` (F.7.44.3)
- ☑ ``removeAppendAttribute`` (F.7.44.4)
- ☑ ``removeArrayIdAttribute`` (F.7.44.5)
- ☑ ``removeAttribute`` (F.7.44.6)
- ☑ ``removeCellStrengthAttribute`` (F.7.44.7)
- ☑ ``removeChoiceRefAttribute`` (F.7.44.8)
- ☑ ``removeClockEdgeAttribute`` (F.7.44.9)
- ☑ ``removeClockNameAttribute`` (F.7.44.10)
- ☑ ``removeClockSourceAttribute`` (F.7.44.11)
- ☑ ``removeConstrainedAttribute`` (F.7.44.12)
- ☑ ``removeConstraintSetIdAttribute`` (F.7.44.13)
- ☑ ``removeDataTypeAttribute`` (F.7.44.14)
- ☑ ``removeDataTypeDefinitionAttribute`` (F.7.44.15)
- ☑ ``removeDefaultAttribute`` (F.7.44.16)
- ☑ ``removeDelayTypeAttribute`` (F.7.44.17)
- ☑ ``removeDirectionAttribute`` (F.7.44.18)
- ☑ ``removeDriverTypeAttribute`` (F.7.44.19)
- ☑ ``removeExternalDeclarationsAttribute`` (F.7.44.20)
- ☑ ``removeFileIdAttribute`` (F.7.44.21)
- ☑ ``removeFlowTypeAttribute`` (F.7.44.22)
- ☑ ``removeForceAttribute`` (F.7.44.23)
- ☑ ``removeGroupAttribute`` (F.7.44.24)
- ☑ ``removeHelpAttribute`` (F.7.44.25)
- ☑ ``removeHiddenAttribute`` (F.7.44.26)
- ☑ ``removeIdAttribute`` (F.7.44.27)
- ☑ ``removeImageTypeAttribute`` (F.7.44.28)
- ☑ ``removeImplicitAttribute`` (F.7.44.29)
- ☑ ``removeInvertAttribute`` (F.7.44.30)
- ☑ ``removeIsIOAttribute`` (F.7.44.31)
- ☑ ``removeLevelAttribute`` (F.7.44.32)
- ☑ ``removeLibextAttribute`` (F.7.44.33)
- ☑ ``removeMaximumAttribute`` (F.7.44.34)
- ☑ ``removeMinimumAttribute`` (F.7.44.35)
- ☑ ``removeMisalignmentAllowedAttribute`` (F.7.44.36)
- ☑ ``removeModeAttribute`` (F.7.44.37)
- ☑ ``removeModifyAttribute`` (F.7.44.38)
- ☑ ``removeMultipleGroupSelectionOperatorAttribute`` (F.7.44.39)
- ☑ ``removeOrderAttribute`` (F.7.44.40)
- ☑ ``removeOtherAnyAttribute`` (F.7.44.41)
- ☑ ``removeOtherAttribute`` (F.7.44.42)
- ☑ ``removePackedAttribute`` (F.7.44.43)
- ☑ ``removeParameterIdAttribute`` (F.7.44.44)
- ☑ ``removePathAttribute`` (F.7.44.45)
- ☑ ``removePhantomAttribute`` (F.7.44.46)
- ☑ ``removePowerDomainRefAttribute`` (F.7.44.47)
- ☑ ``removePrefixAttribute`` (F.7.44.48)
- ☑ ``removePromptAttribute`` (F.7.44.49)
- ☑ ``removeReplicateAttribute`` (F.7.44.50)
- ☑ ``removeResetTypeRefAttribute`` (F.7.44.51)
- ☑ ``removeResolveAttribute`` (F.7.44.52)
- ☑ ``removeScopeAttribute`` (F.7.44.53)
- ☑ ``removeSegmentRefAttribute`` (F.7.44.54)
- ☑ ``removeSignAttribute`` (F.7.44.55)
- ☑ ``removeStrictAttribute`` (F.7.44.56)
- ☑ ``removeTestConstraintAttribute`` (F.7.44.57)
- ☑ ``removeTextAttribute`` (F.7.44.58)
- ☑ ``removeTypeAttribute`` (F.7.44.59)
- ☑ ``removeUniqueAttribute`` (F.7.44.60)
- ☑ ``removeUnitAttribute`` (F.7.44.61)
- ☑ ``removeUnitsAttribute`` (F.7.44.62)
- ☑ ``removeUsageTypeAttribute`` (F.7.44.63)
- ☑ ``removeUserAttribute`` (F.7.44.64)
- ☑ ``removeVectorIdAttribute`` (F.7.44.65)
- ☑ ``setAddressBlockRefAttribute`` (F.7.44.66)
- ☑ ``setAddressSpaceRefAttribute`` (F.7.44.67)
- ☑ ``setAllBitsBooleanAttribute`` (F.7.44.68)
- ☑ ``setAllLogicalDirectionsAllowedBooleanAttribute`` (F.7.44.69)
- ☑ ``setAllLogicalInitiativesAllowedBooleanAttribute`` (F.7.44.70)
- ☑ ``setAlternateRegisterRefAttribute`` (F.7.44.71)
- ☑ ``setAppendBooleanAttribute`` (F.7.44.72)
- ☑ ``setArrayIdAttribute`` (F.7.44.73)
- ☑ ``setBankAlignmentAttribute`` (F.7.44.74)
- ☑ ``setBankRefAttribute`` (F.7.44.75)
- ☑ ``setBusRefAttribute`` (F.7.44.76)
- ☑ ``setCellStrengthAttribute`` (F.7.44.77)
- ☑ ``setChoiceRefAttribute`` (F.7.44.78)
- ☑ ``setClockEdgeAttribute`` (F.7.44.79)
- ☑ ``setClockNameAttribute`` (F.7.44.80)
- ☑ ``setClockSourceAttribute`` (F.7.44.81)
- ☑ ``setComponentInstanceRefAttribute`` (F.7.44.82)
- ☑ ``setComponentRefAttribute`` (F.7.44.83)
- ☑ ``setConfigGroupsAttribute`` (F.7.44.84)
- ☑ ``setConstraintSetIdAttribute`` (F.7.44.85)
- ☑ ``setCustomAttribute`` (F.7.44.86)
- ☑ ``setDataTypeAttribute`` (F.7.44.87)
- ☑ ``setDataTypeDefinitionAttribute`` (F.7.44.88)
- ☑ ``setDefaultBooleanAttribute`` (F.7.44.89)
- ☑ ``setDelayTypeAttribute`` (F.7.44.90)
- ☑ ``setDirectionAttribute`` (F.7.44.91)
- ☑ ``setDriverTypeAttribute`` (F.7.44.92)
- ☑ ``setExactBooleanAttribute`` (F.7.44.93)
- ☑ ``setExternalDeclarationsBooleanAttribute`` (F.7.44.94)
- ☑ ``setFieldRefAttribute`` (F.7.44.95)
- ☑ ``setFileIdAttribute`` (F.7.44.96)
- ☑ ``setFlowTypeAttribute`` (F.7.44.97)
- ☑ ``setForceBooleanAttribute`` (F.7.44.98)
- ☑ ``setGroupAttribute`` (F.7.44.99)
- ☑ ``setHelpAttribute`` (F.7.44.100)
- ☑ ``setHiddenBooleanAttribute`` (F.7.44.101)
- ☑ ``setIdAttribute`` (F.7.44.102)
- ☑ ``setImageIdAttribute`` (F.7.44.103)
- ☑ ``setImageTypeAttribute`` (F.7.44.104)
- ☑ ``setImplicitBooleanAttribute`` (F.7.44.105)
- ☑ ``setIndexVarAttribute`` (F.7.44.106)
- ☑ ``setInitiatorRefAttribute`` (F.7.44.107)
- ☑ ``setInterfaceModeAttribute`` (F.7.44.108)
- ☑ ``setInvertAttribute`` (F.7.44.109)
- ☑ ``setIsIOBooleanAttribute`` (F.7.44.110)
- ☑ ``setLevelAttribute`` (F.7.44.111)
- ☑ ``setLibextAttribute`` (F.7.44.112)
- ☑ ``setLibraryAttribute`` (F.7.44.113)
- ☑ ``setMandatoryBooleanAttribute`` (F.7.44.114)
- ☑ ``setMaximumAttribute`` (F.7.44.115)
- ☑ ``setMaximumDoubleAttribute`` (F.7.44.116)
- ☑ ``setMaximumIntAttribute`` (F.7.44.117)
- ☑ ``setMemoryMapRefAttribute`` (F.7.44.118)
- ☑ ``setMemoryRemapRefAttribute`` (F.7.44.119)
- ☑ ``setMinimumAttribute`` (F.7.44.120)
- ☑ ``setMinimumDoubleAttribute`` (F.7.44.121)
- ☑ ``setMinimumIntAttribute`` (F.7.44.122)
- ☑ ``setMisalignmentAllowedBooleanAttribute`` (F.7.44.123)
- ☑ ``setModeRefAttribute`` (F.7.44.124)
- ☑ ``setModifyAttribute`` (F.7.44.125)
- ☑ ``setMultipleGroupSelectionOperatorAttribute`` (F.7.44.126)
- ☑ ``setNameAttribute`` (F.7.44.127)
- ☑ ``setOrderFloatAttribute`` (F.7.44.128)
- ☑ ``setOtherAnyAttribute`` (F.7.44.129)
- ☑ ``setOtherAttribute`` (F.7.44.130)
- ☑ ``setPackedBooleanAttribute`` (F.7.44.131)
- ☑ ``setParameterIdAttribute`` (F.7.44.132)
- ☑ ``setPathAttribute`` (F.7.44.133)
- ☑ ``setPhantomBooleanAttribute`` (F.7.44.134)
- ☑ ``setPortRefAttribute`` (F.7.44.135)
- ☑ ``setPowerDomainRefAttribute`` (F.7.44.136)
- ☑ ``setPrefixAttribute`` (F.7.44.137)
- ☑ ``setPriorityIntAttribute`` (F.7.44.138)
- ☑ ``setPromptAttribute`` (F.7.44.139)
- ☑ ``setReferenceIdAttribute`` (F.7.44.140)
- ☑ ``setRegisterFileRefAttribute`` (F.7.44.141)
- ☑ ``setRegisterRefAttribute`` (F.7.44.142)
- ☑ ``setReplicateBooleanAttribute`` (F.7.44.143)
- ☑ ``setResetTypeRefAttribute`` (F.7.44.144)
- ☑ ``setResolveAttribute`` (F.7.44.145)
- ☑ ``setScopeAttribute`` (F.7.44.146)
- ☑ ``setSegmentRefAttribute`` (F.7.44.147)
- ☑ ``setSignAttribute`` (F.7.44.148)
- ☑ ``setStrictBooleanAttribute`` (F.7.44.149)
- ☑ ``setSubPortRefAttribute`` (F.7.44.150)
- ☑ ``setTestConstraintAttribute`` (F.7.44.151)
- ☑ ``setTextAttribute`` (F.7.44.152)
- ☑ ``setTypeAttribute`` (F.7.44.153)
- ☑ ``setTypeDefinitionsAttribute`` (F.7.44.154)
- ☑ ``setUniqueBooleanAttribute`` (F.7.44.155)
- ☑ ``setUnitAttribute`` (F.7.44.156)
- ☑ ``setUnitsAttribute`` (F.7.44.157)
- ☑ ``setUsageAttribute`` (F.7.44.158)
- ☑ ``setUsageTypeAttribute`` (F.7.44.159)
- ☑ ``setUserAttribute`` (F.7.44.160)
- ☑ ``setVectorIdAttribute`` (F.7.44.161)
- ☑ ``setVendorAttribute`` (F.7.44.162)
- ☑ ``setVersionAttribute`` (F.7.44.163)
- ☑ ``setViewRefAttribute`` (F.7.44.164)

File builder (BASE)
~~~~~~~~~~~~~~~~~~~

- ☑ ``getBuildCommandCommand`` (F.7.45.1)
- ☑ ``getBuildCommandCommandExpression`` (F.7.45.2)
- ☑ ``getBuildCommandCommandID`` (F.7.45.3)
- ☑ ``getBuildCommandFlags`` (F.7.45.4)
- ☑ ``getBuildCommandFlagsExpression`` (F.7.45.5)
- ☑ ``getBuildCommandFlagsID`` (F.7.45.6)
- ☑ ``getBuildCommandReplaceDefaultFlags`` (F.7.45.7)
- ☑ ``getBuildCommandReplaceDefaultFlagsID`` (F.7.45.8)
- ☑ ``getBuildCommandTargetName`` (F.7.45.9)
- ☑ ``getBuildCommandTargetNameExpression`` (F.7.45.10)
- ☑ ``getExecutableImageFileBuilderIDs`` (F.7.45.11) - Generated linker/source traversal with parsed ownership for child handles.
- ☑ ``getExecutableImageFileSetRefIDs`` (F.7.45.12) - Generated linker/source traversal with parsed ownership for child handles.
- ☑ ``getExecutableImageLanguageToolsID`` (F.7.45.13) - Generated linker/source traversal with parsed ownership for child handles.
- ☑ ``getExecutableImageLinker`` (F.7.45.14) - Generated linker/source traversal with parsed ownership for child handles.
- ☑ ``getExecutableImageLinkerCommandFileID`` (F.7.45.15) - Generated linker/source traversal with parsed ownership for child handles.
- ☑ ``getExecutableImageLinkerExpression`` (F.7.45.16) - Generated linker/source traversal with parsed ownership for child handles.
- ☑ ``getExecutableImageLinkerFlags`` (F.7.45.17) - Generated linker/source traversal with parsed ownership for child handles.
- ☑ ``getExecutableImageLinkerFlagsExpression`` (F.7.45.18) - Generated linker/source traversal with parsed ownership for child handles.
- ☑ ``getFileBuildCommandID`` (F.7.45.19)
- ☑ ``getFileBuilderCommand`` (F.7.45.20)
- ☑ ``getFileBuilderCommandExpression`` (F.7.45.21)
- ☑ ``getFileBuilderCommandID`` (F.7.45.22)
- ☑ ``getFileBuilderFileType`` (F.7.45.23)
- ☑ ``getFileBuilderFileTypeID`` (F.7.45.24)
- ☑ ``getFileBuilderFlags`` (F.7.45.25)
- ☑ ``getFileBuilderFlagsExpression`` (F.7.45.26)
- ☑ ``getFileBuilderFlagsID`` (F.7.45.27)
- ☑ ``getFileBuilderReplaceDefaultFlags`` (F.7.45.28)
- ☑ ``getFileBuilderReplaceDefaultFlagsExpression`` (F.7.45.29)
- ☑ ``getFileBuilderReplaceDefaultFlagsID`` (F.7.45.30)
- ☑ ``getGeneratorRefByID`` (F.7.45.31)
- ☑ ``getLanguageToolsFileBuilderIDs`` (F.7.45.32)
- ☑ ``getLanguageToolsLinker`` (F.7.45.33)
- ☑ ``getLanguageToolsLinkerCommandFileID`` (F.7.45.34)
- ☑ ``getLanguageToolsLinkerExpression`` (F.7.45.35)
- ☑ ``getLanguageToolsLinkerFlags`` (F.7.45.36)
- ☑ ``getLanguageToolsLinkerFlagsExpression`` (F.7.45.37)
- ☑ ``getLanguageToolsLinkerFlagsID`` (F.7.45.38)
- ☑ ``getLanguageToolsLinkerID`` (F.7.45.39)
- ☑ ``getLinkerCommandFileCommandLineSwitch`` (F.7.45.40)
- ☑ ``getLinkerCommandFileCommandLineSwitchExpression`` (F.7.45.41)
- ☑ ``getLinkerCommandFileCommandLineSwitchID`` (F.7.45.42)
- ☑ ``getLinkerCommandFileEnable`` (F.7.45.43)
- ☑ ``getLinkerCommandFileEnableExpression`` (F.7.45.44)
- ☑ ``getLinkerCommandFileEnableID`` (F.7.45.45)
- ☑ ``getLinkerCommandFileGeneratorRefByID`` (F.7.45.46)
- ☑ ``getLinkerCommandFileGeneratorRefByNames`` (F.7.45.47)
- ☑ ``getLinkerCommandFileGeneratorRefIDs`` (F.7.45.48)
- ☑ ``getLinkerCommandFileLineSwitch`` (F.7.45.49)
- ☑ ``getLinkerCommandFileLineSwitchExpression`` (F.7.45.50)
- ☑ ``getLinkerCommandFileName`` (F.7.45.51)
- ☑ ``getLinkerCommandFileNameExpression`` (F.7.45.52)
- ☑ ``getLinkerCommandFileNameID`` (F.7.45.53)
- ☑ ``getLinkerCommandFileNameValue`` (F.7.45.54)

File builder (EXTENDED)
~~~~~~~~~~~~~~~~~~~~~~~

- ☑ ``addExecutableImageFileBuilderID`` (F.7.46.1)
- ☑ ``addExecutableImageLinkerCommandFile`` (F.7.46.2)
- ☑ ``addLanguageToolsFileBuilder`` (F.7.46.3)
- ☑ ``addLinkerCommandFileGeneratorRef`` (F.7.46.4)
- ☑ ``removeBuildCommandCommand`` (F.7.46.5)
- ☑ ``removeBuildCommandFlags`` (F.7.46.6)
- ☑ ``removeBuildCommandReplaceDefaultFlags`` (F.7.46.7)
- ☑ ``removeBuildCommandTargetName`` (F.7.46.8)
- ☑ ``removeDefaultFileBuilderCommand`` (F.7.46.9)
- ☑ ``removeExecutableImageFileBuilderID`` (F.7.46.10)
- ☑ ``removeExecutableImageLanguageTools`` (F.7.46.11)
- ☑ ``removeExecutableImageLinkerCommandFile`` (F.7.46.12)
- ☑ ``removeFileBuilderCommand`` (F.7.46.13)
- ☑ ``removeFileBuilderFlags`` (F.7.46.14)
- ☑ ``removeFileBuilderReplaceDefaultFlags`` (F.7.46.15)
- ☑ ``removeLanguageToolsFileBuilder`` (F.7.46.16)
- ☑ ``removeLanguageToolsLinkerCommandFile`` (F.7.46.17)
- ☑ ``removeLanguageToolsLinkerFlags`` (F.7.46.18)
- ☑ ``removeLinkerCommandFileGeneratorRef`` (F.7.46.19)
- ☑ ``setBuildCommandCommand`` (F.7.46.20)
- ☑ ``setBuildCommandFlags`` (F.7.46.21)
- ☑ ``setBuildCommandReplaceDefaultFlags`` (F.7.46.22)
- ☑ ``setBuildCommandTargetName`` (F.7.46.23)
- ☑ ``setExecutableImageLanguageTools`` (F.7.46.24)
- ☑ ``setExecutableImageLinker`` (F.7.46.25)
- ☑ ``setExecutableImageLinkerFlags`` (F.7.46.26)
- ☑ ``setFileBuildCommand`` (F.7.46.27)
- ☑ ``setFileBuilderCommand`` (F.7.46.28)
- ☑ ``setFileBuilderFileType`` (F.7.46.29)
- ☑ ``setFileBuilderFlags`` (F.7.46.30)
- ☑ ``setFileBuilderReplaceDefaultFlags`` (F.7.46.31)
- ☑ ``setLanguageToolsLinker`` (F.7.46.32)
- ☑ ``setLanguageToolsLinkerCommandFile`` (F.7.46.33)
- ☑ ``setLanguageToolsLinkerFlags`` (F.7.46.34)
- ☑ ``setLinkerCommandFileCommandLineSwitch`` (F.7.46.35)
- ☑ ``setLinkerCommandFileEnable`` (F.7.46.36)
- ☑ ``setLinkerCommandFileName`` (F.7.46.37)

File set (BASE)
~~~~~~~~~~~~~~~

- ☑ ``getBuildCommandReplaceDefaultFlagsExpression`` (F.7.47.1)
- ☑ ``getFileDefineIDs`` (F.7.47.2)
- ☑ ``getFileDefineSymbolValue`` (F.7.47.3)
- ☑ ``getFileDependencyIDs`` (F.7.47.4)
- ☑ ``getFileExportedNameIDs`` (F.7.47.5)
- ☑ ``getFileExportedNames`` (F.7.47.6)
- ☑ ``getFileFileTypeIDs`` (F.7.47.7)
- ☑ ``getFileFileTypes`` (F.7.47.8)
- ☑ ``getFileImageTypeIDs`` (F.7.47.9)
- ☑ ``getFileImageTypes`` (F.7.47.10)
- ☑ ``getFileIsIncludeFile`` (F.7.47.11)
- ☑ ``getFileIsIncludeFileID`` (F.7.47.12)
- ☑ ``getFileIsStructural`` (F.7.47.13)
- ☑ ``getFileLogicalName`` (F.7.47.14)
- ☑ ``getFileLogicalNameID`` (F.7.47.15)
- ☑ ``getFileName`` (F.7.47.16)
- ☑ ``getFileSetDefaultFileBuilderIDs`` (F.7.47.17)
- ☑ ``getFileSetDependencyIDs`` (F.7.47.18)
- ☑ ``getFileSetFileIDs`` (F.7.47.19)
- ☑ ``getFileSetFunctionIDs`` (F.7.47.20)
- ☑ ``getFileSetGroupFileSetRefIDs`` (F.7.47.21)
- ☑ ``getFileSetGroupIDs`` (F.7.47.22)
- ☑ ``getFileSetGroups`` (F.7.47.23)
- ☑ ``getFileSetRefByID`` (F.7.47.24)
- ☑ ``getFileSetRefGroupFileSetRefIDs`` (F.7.47.25)
- ☑ ``getFileSetRefLocalNameRefByID`` (F.7.47.26)
- ☑ ``getFunctionArgumentDataType`` (F.7.47.27) - Generated source value or stable handle with parsed ownership.
- ☑ ``getFunctionArgumentIDs`` (F.7.47.28) - Generated source value or stable handle with parsed ownership.
- ☑ ``getFunctionDisabled`` (F.7.47.29)
- ☑ ``getFunctionDisabledExpression`` (F.7.47.30) - Generated source value or stable handle with parsed ownership.
- ☑ ``getFunctionDisabledID`` (F.7.47.31) - Generated source value or stable handle with parsed ownership.
- ☑ ``getFunctionEntryPoint`` (F.7.47.32) - Generated source value or stable handle with parsed ownership.
- ☑ ``getFunctionFileID`` (F.7.47.33)
- ☑ ``getFunctionFileRefByID`` (F.7.47.34)
- ☑ ``getFunctionFileRefByName`` (F.7.47.35) - Generated source type/value; configured resolution remains separate.
- ☑ ``getFunctionReplicate`` (F.7.47.36) - Generated source type/value; configured resolution remains separate.
- ☑ ``getFunctionReturnType`` (F.7.47.37) - Generated source type/value; configured resolution remains separate.
- ☑ ``getFunctionSourceFileIDs`` (F.7.47.38) - Generated source value or stable handle with parsed ownership.
- ☑ ``getFunctionSourceFileName`` (F.7.47.39) - Generated source value or stable handle with parsed ownership.
- ☑ ``getFunctionSourceFileType`` (F.7.47.40) - Generated source type/value; configured resolution remains separate.
- ☑ ``getSourceFileFileType`` (F.7.47.41) - Generated source type/value; configured resolution remains separate.
- ☑ ``getSourceFileFileTypeID`` (F.7.47.42)
- ☑ ``getSourceFileSourceName`` (F.7.47.43)

File set (EXTENDED)
~~~~~~~~~~~~~~~~~~~

- ☑ ``addFileDefine`` (F.7.48.1)
- ☑ ``addFileDependency`` (F.7.48.2)
- ☑ ``addFileExportedName`` (F.7.48.3)
- ☑ ``addFileFileType`` (F.7.48.4)
- ☑ ``addFileImageType`` (F.7.48.5)
- ☑ ``addFileSetDefaultFileBuilder`` (F.7.48.6)
- ☑ ``addFileSetDependency`` (F.7.48.7)
- ☑ ``addFileSetFile`` (F.7.48.8)
- ☑ ``addFileSetFunction`` (F.7.48.9)
- ☑ ``addFileSetGroup`` (F.7.48.10)
- ☑ ``addFileSetRefGroupFileSetRef`` (F.7.48.11)
- ☑ ``addFunctionArgument`` (F.7.48.12)
- ☑ ``addFunctionSourceFile`` (F.7.48.13)
- ☑ ``removeFileBuildCommand`` (F.7.48.14)
- ☑ ``removeFileDefine`` (F.7.48.15)
- ☑ ``removeFileDependency`` (F.7.48.16)
- ☑ ``removeFileExportedName`` (F.7.48.17)
- ☑ ``removeFileFileType`` (F.7.48.18)
- ☑ ``removeFileImageType`` (F.7.48.19)
- ☑ ``removeFileIsIncludeFile`` (F.7.48.20)
- ☑ ``removeFileIsStructural`` (F.7.48.21)
- ☑ ``removeFileLogicalName`` (F.7.48.22)
- ☑ ``removeFileSetDefaultFileBuilder`` (F.7.48.23)
- ☑ ``removeFileSetDependency`` (F.7.48.24)
- ☑ ``removeFileSetFile`` (F.7.48.25)
- ☑ ``removeFileSetFunction`` (F.7.48.26)
- ☑ ``removeFileSetGroup`` (F.7.48.27)
- ☑ ``removeFunctionArgument`` (F.7.48.28)
- ☑ ``removeFunctionDisabled`` (F.7.48.29)
- ☑ ``removeFunctionEntryPoint`` (F.7.48.30)
- ☑ ``removeFunctionReturnType`` (F.7.48.31)
- ☑ ``removeFunctionSourceFile`` (F.7.48.32)
- ☑ ``setFileIsIncludeFile`` (F.7.48.33)
- ☑ ``setFileIsStructural`` (F.7.48.34)
- ☑ ``setFileLogicalName`` (F.7.48.35)
- ☑ ``setFileName`` (F.7.48.36)
- ☑ ``setFunctionArgumentDataType`` (F.7.48.37)
- ☑ ``setFunctionDisabled`` (F.7.48.38)
- ☑ ``setFunctionEntryPoint`` (F.7.48.39)
- ☑ ``setFunctionFileRef`` (F.7.48.40)
- ☑ ``setFunctionReplicate`` (F.7.48.41)
- ☑ ``setFunctionReturnType`` (F.7.48.42)
- ☑ ``setFunctionSourceFileName`` (F.7.48.43)
- ☑ ``setSourceFileFileType`` (F.7.48.44)
- ☑ ``setSourceFileSourceName`` (F.7.48.45)

Generator (BASE)
~~~~~~~~~~~~~~~~

- ☑ ``getAbstractorGeneratorGroup`` (F.7.49.1) - Ordered instance-generator groups and scope with typed handles and parsed ownership.
- ☑ ``getAbstractorGeneratorGroupIDs`` (F.7.49.2) - Ordered instance-generator groups and scope with typed handles and parsed ownership.
- ☑ ``getComponentGeneratorGroupIDs`` (F.7.49.3) - Ordered instance-generator groups and scope with typed handles and parsed ownership.
- ☑ ``getGeneratorApiService`` (F.7.49.4) - Generated metadata across standalone/component/abstractor generators; parsed child ownership.
- ☑ ``getGeneratorApiTypeID`` (F.7.49.5) - Generated metadata across standalone/component/abstractor generators; parsed child ownership.
- ☑ ``getGeneratorExecutable`` (F.7.49.6) - Generated metadata across standalone/component/abstractor generators; parsed child ownership.
- ☑ ``getGeneratorGeneratorExe`` (F.7.49.7) - Generated metadata across standalone/component/abstractor generators; parsed child ownership.
- ☑ ``getGeneratorGroups`` (F.7.49.8) - Ordered instance-generator groups and scope with typed handles and parsed ownership.
- ☑ ``getGeneratorPhase`` (F.7.49.9)
- ☑ ``getGeneratorPhaseExpression`` (F.7.49.10)
- ☑ ``getGeneratorPhaseID`` (F.7.49.11) - Generated metadata across standalone/component/abstractor generators; parsed child ownership.
- ☑ ``getGeneratorScope`` (F.7.49.12) - Ordered instance-generator groups and scope with typed handles and parsed ownership.
- ☑ ``getGeneratorTransportMethodsID`` (F.7.49.13) - Generated source/child traversal with typed handles and parsed ownership; target resolution separate.
- ☑ ``getTransportMethodsTransportMethodID`` (F.7.49.14) - Generated source/child traversal with typed handles and parsed ownership; target resolution separate.

Generator (EXTENDED)
~~~~~~~~~~~~~~~~~~~~

- ☑ ``addAbstractorGeneratorGroup`` (F.7.50.1)
- ☑ ``addComponentGeneratorGroup`` (F.7.50.2)
- ☑ ``removeAbstractorGeneratorGroup`` (F.7.50.3)
- ☑ ``removeComponentGeneratorGroup`` (F.7.50.4)
- ☑ ``removeGeneratorApiService`` (F.7.50.5)
- ☑ ``removeGeneratorApiType`` (F.7.50.6)
- ☑ ``removeGeneratorPhase`` (F.7.50.7)
- ☑ ``removeGeneratorTransportMethods`` (F.7.50.8)
- ☑ ``removeTransportMethodsTransportMethod`` (F.7.50.9)
- ☑ ``setGeneratorApiService`` (F.7.50.10)
- ☑ ``setGeneratorApiType`` (F.7.50.11)
- ☑ ``setGeneratorGeneratorExe`` (F.7.50.12)
- ☑ ``setGeneratorPhase`` (F.7.50.13)
- ☑ ``setGeneratorScope`` (F.7.50.14)
- ☑ ``setGeneratorTransportMethods`` (F.7.50.15)
- ☑ ``setTransportMethodsTransportMethod`` (F.7.50.16)

Generator chain (BASE)
~~~~~~~~~~~~~~~~~~~~~~

- ☑ ``getComponentGeneratorSelectorGroupSelectorID`` (F.7.51.1) - Generated group-selector source traversal with stable handles and parsed ownership.
- ☑ ``getGeneratorChainChainGroupIDs`` (F.7.51.2) - Ordered typed traversal of generated chain collections with parsed ownership.
- ☑ ``getGeneratorChainChoiceIDs`` (F.7.51.3) - Ordered typed traversal of generated chain collections with parsed ownership.
- ☑ ``getGeneratorChainComponentGeneratorSelectorIDs`` (F.7.51.4) - Ordered typed traversal of generated chain collections with parsed ownership.
- ☑ ``getGeneratorChainGeneratorChainSelectorIDs`` (F.7.51.5) - Ordered typed traversal of generated chain collections with parsed ownership.
- ☑ ``getGeneratorChainGeneratorIDs`` (F.7.51.6) - Ordered typed traversal of generated chain collections with parsed ownership.
- ☑ ``getGeneratorChainSelectorGeneratorChainRefByID`` (F.7.51.7)
- ☑ ``getGeneratorChainSelectorGeneratorChainRefByVLNV`` (F.7.51.8)
- ☑ ``getGeneratorChainSelectorGroupSelectorID`` (F.7.51.9) - Generated group-selector source traversal with stable handles and parsed ownership.
- ☑ ``getGroupSelectorNameIDs`` (F.7.51.10) - Generated group-selector source traversal with stable handles and parsed ownership.
- ☑ ``getGroupSelectorSelectionNames`` (F.7.51.11) - Generated group-selector source traversal with stable handles and parsed ownership.
- ☑ ``getGroupSelectorSelectionOperator`` (F.7.51.12) - Generated group-selector source traversal with stable handles and parsed ownership.

Generator chain (EXTENDED)
~~~~~~~~~~~~~~~~~~~~~~~~~~

- ☑ ``addGeneratorChainChainGroup`` (F.7.52.1)
- ☑ ``addGeneratorChainChoice`` (F.7.52.2)
- ☑ ``addGeneratorChainComponentGeneratorSelector`` (F.7.52.3)
- ☑ ``addGeneratorChainGenerator`` (F.7.52.4)
- ☑ ``addGeneratorChainGeneratorChainSelector`` (F.7.52.5)
- ☑ ``addGroupSelectorName`` (F.7.52.6)
- ☑ ``removeGeneratorChainChainGroup`` (F.7.52.7)
- ☑ ``removeGeneratorChainChoice`` (F.7.52.8)
- ☑ ``removeGeneratorChainComponentGeneratorSelector`` (F.7.52.9)
- ☑ ``removeGeneratorChainGenerator`` (F.7.52.10)
- ☑ ``removeGeneratorChainGeneratorChainSelector`` (F.7.52.11)
- ☑ ``removeGroupSelectorName`` (F.7.52.12)
- ☑ ``setComponentGeneratorSelectorGroupSelector`` (F.7.52.13)
- ☑ ``setGeneratorChainSelectorGeneratorChainRef`` (F.7.52.14)
- ☑ ``setGeneratorChainSelectorGroupSelector`` (F.7.52.15)

Indirect interface (BASE)
~~~~~~~~~~~~~~~~~~~~~~~~~

- ☐ ``getIndirectAddressRefAddressBlockRefByName`` (F.7.53.1)
- ☐ ``getIndirectAddressRefAddressBlockRefID`` (F.7.53.2)
- ☐ ``getIndirectAddressRefAddressSpaceRefByName`` (F.7.53.3)
- ☐ ``getIndirectAddressRefAddressSpaceRefID`` (F.7.53.4)
- ☐ ``getIndirectAddressRefAlternateRegisterRefByName`` (F.7.53.5)
- ☐ ``getIndirectAddressRefAlternateRegisterRefID`` (F.7.53.6)
- ☐ ``getIndirectAddressRefBankRefByNames`` (F.7.53.7)
- ☐ ``getIndirectAddressRefBankRefIDs`` (F.7.53.8)
- ☐ ``getIndirectAddressRefFieldRefByName`` (F.7.53.9)
- ☐ ``getIndirectAddressRefFieldRefID`` (F.7.53.10)
- ☐ ``getIndirectAddressRefMemoryMapRefByName`` (F.7.53.11)
- ☐ ``getIndirectAddressRefMemoryMapRefID`` (F.7.53.12)
- ☐ ``getIndirectAddressRefMemoryRemapRefByID`` (F.7.53.13)
- ☐ ``getIndirectAddressRefMemoryRemapRefByName`` (F.7.53.14)
- ☐ ``getIndirectAddressRefMemoryRemapRefID`` (F.7.53.15)
- ☐ ``getIndirectAddressRefRegisterFileRefByNames`` (F.7.53.16)
- ☐ ``getIndirectAddressRefRegisterFileRefIDs`` (F.7.53.17)
- ☐ ``getIndirectAddressRefRegisterRefByName`` (F.7.53.18)
- ☐ ``getIndirectAddressRefRegisterRefID`` (F.7.53.19)
- ☐ ``getIndirectDataRefAddressBlockRefByName`` (F.7.53.20)
- ☐ ``getIndirectDataRefAddressBlockRefID`` (F.7.53.21)
- ☐ ``getIndirectDataRefAddressSpaceRefByName`` (F.7.53.22)
- ☐ ``getIndirectDataRefAddressSpaceRefID`` (F.7.53.23)
- ☐ ``getIndirectDataRefAlternateRegisterRefByName`` (F.7.53.24)
- ☐ ``getIndirectDataRefAlternateRegisterRefID`` (F.7.53.25)
- ☐ ``getIndirectDataRefBankRefByNames`` (F.7.53.26)
- ☐ ``getIndirectDataRefBankRefIDs`` (F.7.53.27)
- ☐ ``getIndirectDataRefFieldRefByName`` (F.7.53.28)
- ☐ ``getIndirectDataRefFieldRefID`` (F.7.53.29)
- ☐ ``getIndirectDataRefMemoryMapRefByName`` (F.7.53.30)
- ☐ ``getIndirectDataRefMemoryMapRefID`` (F.7.53.31)
- ☐ ``getIndirectDataRefMemoryRemapRefByID`` (F.7.53.32)
- ☐ ``getIndirectDataRefMemoryRemapRefByName`` (F.7.53.33)
- ☐ ``getIndirectDataRefMemoryRemapRefID`` (F.7.53.34)
- ☐ ``getIndirectDataRefRegisterFileRefByNames`` (F.7.53.35)
- ☐ ``getIndirectDataRefRegisterFileRefIDs`` (F.7.53.36)
- ☐ ``getIndirectDataRefRegisterRefByName`` (F.7.53.37)
- ☐ ``getIndirectDataRefRegisterRefID`` (F.7.53.38)
- ☐ ``getIndirectInterfaceBitsInLau`` (F.7.53.39)
- ☐ ``getIndirectInterfaceBitsInLauExpression`` (F.7.53.40)
- ☐ ``getIndirectInterfaceEndianness`` (F.7.53.41)
- ☐ ``getIndirectInterfaceIndirectAddressRefID`` (F.7.53.42)
- ☐ ``getIndirectInterfaceIndirectDataRefID`` (F.7.53.43)
- ☐ ``getIndirectInterfaceMemoryMapRefByID`` (F.7.53.44)
- ☐ ``getIndirectInterfaceMemoryMapRefByName`` (F.7.53.45)
- ☐ ``getIndirectInterfaceTransparentBridgeIDs`` (F.7.53.46)

Indirect interface (EXTENDED)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- ☐ ``addIndirectAddressRefBankRef`` (F.7.54.1)
- ☐ ``addIndirectAddressRefRegisterFileRef`` (F.7.54.2)
- ☐ ``addIndirectDataRefBankRef`` (F.7.54.3)
- ☐ ``addIndirectDataRefRegisterFileRef`` (F.7.54.4)
- ☐ ``addIndirectInterfaceTransparentBridge`` (F.7.54.5)
- ☐ ``removeAliasOfMemoryRemapRef`` (F.7.54.6)
- ☐ ``removeBroadcastToAddressSpaceRef`` (F.7.54.7)
- ☐ ``removeIndirectAddressRefAddressBlockRef`` (F.7.54.8)
- ☐ ``removeIndirectAddressRefAddressSpaceRef`` (F.7.54.9)
- ☐ ``removeIndirectAddressRefAlternateRegisterRef`` (F.7.54.10)
- ☐ ``removeIndirectAddressRefBankRef`` (F.7.54.11)
- ☐ ``removeIndirectAddressRefMemoryMapRef`` (F.7.54.12)
- ☐ ``removeIndirectAddressRefMemoryRemapRef`` (F.7.54.13)
- ☐ ``removeIndirectAddressRefRegisterFileRef`` (F.7.54.14)
- ☐ ``removeIndirectAddressRefRegisterRef`` (F.7.54.15)
- ☐ ``removeIndirectDataRefAddressBlockRef`` (F.7.54.16)
- ☐ ``removeIndirectDataRefAddressSpaceRef`` (F.7.54.17)
- ☐ ``removeIndirectDataRefAlternateRegisterRef`` (F.7.54.18)
- ☐ ``removeIndirectDataRefBankRef`` (F.7.54.19)
- ☐ ``removeIndirectDataRefMemoryMapRef`` (F.7.54.20)
- ☐ ``removeIndirectDataRefMemoryRemapRef`` (F.7.54.21)
- ☐ ``removeIndirectDataRefRegisterFileRef`` (F.7.54.22)
- ☐ ``removeIndirectDataRefRegisterRef`` (F.7.54.23)
- ☐ ``removeIndirectInterfaceEndianness`` (F.7.54.24)
- ☐ ``removeIndirectInterfaceTransparentBridge`` (F.7.54.25)
- ☐ ``setIndirectAddressRefAddressBlockRef`` (F.7.54.26)
- ☐ ``setIndirectAddressRefAddressSpaceRef`` (F.7.54.27)
- ☐ ``setIndirectAddressRefAlternateRegisterRef`` (F.7.54.28)
- ☐ ``setIndirectAddressRefFieldRef`` (F.7.54.29)
- ☐ ``setIndirectAddressRefMemoryMapRef`` (F.7.54.30)
- ☐ ``setIndirectAddressRefMemoryRemapRef`` (F.7.54.31)
- ☐ ``setIndirectAddressRefRegisterRef`` (F.7.54.32)
- ☐ ``setIndirectDataRefAddressBlockRef`` (F.7.54.33)
- ☐ ``setIndirectDataRefAddressSpaceRef`` (F.7.54.34)
- ☐ ``setIndirectDataRefAlternateRegisterRef`` (F.7.54.35)
- ☐ ``setIndirectDataRefFieldRef`` (F.7.54.36)
- ☐ ``setIndirectDataRefMemoryMapRef`` (F.7.54.37)
- ☐ ``setIndirectDataRefMemoryRemapRef`` (F.7.54.38)
- ☐ ``setIndirectDataRefRegisterRef`` (F.7.54.39)
- ☐ ``setIndirectInterfaceEndianness`` (F.7.54.40)
- ☐ ``setIndirectInterfaceMemoryMapRef`` (F.7.54.41)

Instantiation (BASE)
~~~~~~~~~~~~~~~~~~~~

- ☑ ``getAbstractionTypeAbstractionRefID`` (F.7.55.1)
- ☑ ``getAbstractorInstanceAbstractorRefID`` (F.7.55.2)
- ☑ ``getComponentInstanceComponentRefID`` (F.7.55.3)
- ☑ ``getComponentInstantiationArchitectureName`` (F.7.55.4)
- ☑ ``getComponentInstantiationClearboxElementRefIDs`` (F.7.55.5)
- ☑ ``getComponentInstantiationConfigurationName`` (F.7.55.6)
- ☑ ``getComponentInstantiationConstraintSetRefIDs`` (F.7.55.7)
- ☑ ``getComponentInstantiationDefaultFileBuilderIDs`` (F.7.55.8)
- ☑ ``getComponentInstantiationFileSetRefIDs`` (F.7.55.9)
- ☑ ``getComponentInstantiationIsVirtual`` (F.7.55.10)
- ☑ ``getComponentInstantiationLanguage`` (F.7.55.11) - preserves generated source values and identity.
- ☑ ``getComponentInstantiationLanguageID`` (F.7.55.12)
- ☑ ``getComponentInstantiationLibraryName`` (F.7.55.13)
- ☑ ``getComponentInstantiationModuleName`` (F.7.55.14)
- ☑ ``getComponentInstantiationPackageName`` (F.7.55.15)
- ☑ ``getDesignConfigurationInstantiationDesignConfigurationRefByID`` (F.7.55.16)
- ☑ ``getDesignConfigurationInstantiationDesignConfigurationRefByVLNV`` (F.7.55.17)
- ☑ ``getDesignConfigurationInstantiationDesignConfigurationRefID`` (F.7.55.18)
- ☑ ``getDesignConfigurationInstantiationLanguage`` (F.7.55.19) - preserves generated source values and identity.
- ☑ ``getDesignConfigurationInstantiationLanguageID`` (F.7.55.20)
- ☑ ``getDesignInstantiationDesignRefByID`` (F.7.55.21)
- ☑ ``getDesignInstantiationDesignRefByVLNV`` (F.7.55.22)
- ☑ ``getDesignInstantiationDesignRefID`` (F.7.55.23)
- ☑ ``getExternalTypeDefinitionsTypeDefinitionsRefID`` (F.7.55.24)
- ☑ ``getFileSetRefLocalName`` (F.7.55.25)
- ☑ ``getGeneratorChainSelectorGeneratorChainRefID`` (F.7.55.26)

Instantiation (EXTENDED)
~~~~~~~~~~~~~~~~~~~~~~~~

- ☑ ``addComponentInstantiationClearboxElementRef`` (F.7.56.1)
- ☑ ``addComponentInstantiationConstraintSetRef`` (F.7.56.2)
- ☑ ``addComponentInstantiationDefaultFileBuilder`` (F.7.56.3)
- ☑ ``addComponentInstantiationFileSetRef`` (F.7.56.4)
- ☑ ``removeComponentInstantiationArchitectureName`` (F.7.56.5)
- ☑ ``removeComponentInstantiationClearboxElementRef`` (F.7.56.6)
- ☑ ``removeComponentInstantiationConfigurationName`` (F.7.56.7)
- ☑ ``removeComponentInstantiationConstraintSetRef`` (F.7.56.8)
- ☑ ``removeComponentInstantiationDefaultFileBuilder`` (F.7.56.9)
- ☑ ``removeComponentInstantiationFileSetRef`` (F.7.56.10)
- ☑ ``removeComponentInstantiationIsVirtual`` (F.7.56.11)
- ☑ ``removeComponentInstantiationLanguage`` (F.7.56.12)
- ☑ ``removeComponentInstantiationLibraryName`` (F.7.56.13)
- ☑ ``removeComponentInstantiationModuleName`` (F.7.56.14)
- ☑ ``removeComponentInstantiationPackageName`` (F.7.56.15)
- ☑ ``removeDesignConfigurationInstantiationLanguage`` (F.7.56.16)
- ☑ ``setComponentInstantiationArchitectureName`` (F.7.56.17)
- ☑ ``setComponentInstantiationConfigurationName`` (F.7.56.18)
- ☑ ``setComponentInstantiationIsVirtual`` (F.7.56.19)
- ☑ ``setComponentInstantiationLanguage`` (F.7.56.20) - preserves generated source values and identity.
- ☑ ``setComponentInstantiationLibraryName`` (F.7.56.21)
- ☑ ``setComponentInstantiationModuleName`` (F.7.56.22)
- ☑ ``setComponentInstantiationPackageName`` (F.7.56.23)
- ☑ ``setDesignConfigurationInstantiationDesignConfigurationRef`` (F.7.56.24) - preserves generated source values and identity.
- ☑ ``setDesignConfigurationInstantiationLanguage`` (F.7.56.25) - preserves generated source values and identity.
- ☑ ``setDesignInstantiationDesignRef`` (F.7.56.26)

Memory map (BASE)
~~~~~~~~~~~~~~~~~

- ☐ ``getAddressBlockAccessPolicyIDs`` (F.7.57.1)
- ☐ ``getAddressBlockAddressBlockDefinitionRefByExternalTypeDefID`` (F.7.57.2)
- ☐ ``getAddressBlockAddressBlockDefinitionRefByID`` (F.7.57.3)
- ☐ ``getAddressBlockAddressBlockDefinitionRefByName`` (F.7.57.4)
- ☐ ``getAddressBlockAddressBlockDefinitionRefID`` (F.7.57.5)
- ☐ ``getAddressBlockArrayID`` (F.7.57.6)
- ☐ ``getAddressBlockBaseAddress`` (F.7.57.7)
- ☐ ``getAddressBlockBaseAddressExpression`` (F.7.57.8)
- ☐ ``getAddressBlockBaseAddressID`` (F.7.57.9)
- ☐ ``getAddressBlockRange`` (F.7.57.10)
- ☐ ``getAddressBlockRangeExpression`` (F.7.57.11)
- ☐ ``getAddressBlockRangeID`` (F.7.57.12)
- ☐ ``getAddressBlockRefIndexIDs`` (F.7.57.13)
- ☐ ``getAddressBlockRegisterFileIDs`` (F.7.57.14)
- ☐ ``getAddressBlockRegisterIDs`` (F.7.57.15)
- ☐ ``getAddressBlockTypeIdentifier`` (F.7.57.16)
- ☐ ``getAddressBlockUsage`` (F.7.57.17)
- ☐ ``getAddressBlockVolatility`` (F.7.57.18)
- ☐ ``getAddressBlockWidth`` (F.7.57.19)
- ☐ ``getAddressBlockWidthExpression`` (F.7.57.20)
- ☐ ``getAddressBlockWidthID`` (F.7.57.21)
- ☐ ``getAliasOfAddressBlockRefByName`` (F.7.57.22)
- ☐ ``getAliasOfAddressBlockRefID`` (F.7.57.23)
- ☐ ``getAliasOfBankRefByNames`` (F.7.57.24)
- ☐ ``getAliasOfBankRefIDs`` (F.7.57.25)
- ☐ ``getAliasOfMemoryMapRefByName`` (F.7.57.26)
- ☐ ``getAliasOfMemoryMapRefID`` (F.7.57.27)
- ☐ ``getAliasOfMemoryRemapRefByID`` (F.7.57.28)
- ☐ ``getAliasOfMemoryRemapRefByName`` (F.7.57.29)
- ☐ ``getAliasOfMemoryRemapRefID`` (F.7.57.30)
- ☐ ``getBankAddressBlockIDs`` (F.7.57.31)
- ☐ ``getBankBankDefinitionRefByExternalTypeDefID`` (F.7.57.32)
- ☐ ``getBankBankDefinitionRefByID`` (F.7.57.33)
- ☐ ``getBankBankDefinitionRefByName`` (F.7.57.34)
- ☐ ``getBankBankDefinitionRefID`` (F.7.57.35)
- ☐ ``getBankBankIDs`` (F.7.57.36)
- ☐ ``getBankBaseAddress`` (F.7.57.37)
- ☐ ``getBankBaseAddressExpression`` (F.7.57.38)
- ☐ ``getBankBaseAddressID`` (F.7.57.39)
- ☐ ``getBankBlockAndSubspaceElementIDs`` (F.7.57.40)
- ☐ ``getBankSubspaceMapIDs`` (F.7.57.41)
- ☐ ``getBankUsage`` (F.7.57.42)
- ☐ ``getBankVolatility`` (F.7.57.43)
- ☐ ``getMemoryMapAddressBlockIDs`` (F.7.57.44)
- ☐ ``getMemoryMapAddressUnitBits`` (F.7.57.45)
- ☐ ``getMemoryMapAddressUnitBitsExpression`` (F.7.57.46)
- ☐ ``getMemoryMapAddressUnitBitsID`` (F.7.57.47)
- ☐ ``getMemoryMapBankIDs`` (F.7.57.48)
- ☐ ``getMemoryMapElementIDs`` (F.7.57.49)
- ☐ ``getMemoryMapElementType`` (F.7.57.50)
- ☐ ``getMemoryMapMemoryMapDefinitionRefByExternalTypeDefID`` (F.7.57.51)
- ☐ ``getMemoryMapMemoryMapDefinitionRefByID`` (F.7.57.52)
- ☐ ``getMemoryMapMemoryMapDefinitionRefByName`` (F.7.57.53)
- ☐ ``getMemoryMapMemoryMapDefinitionRefID`` (F.7.57.54)
- ☐ ``getMemoryMapMemoryRemapIDs`` (F.7.57.55)
- ☐ ``getMemoryMapRemapIDs`` (F.7.57.56)
- ☐ ``getMemoryMapShared`` (F.7.57.57)
- ☐ ``getMemoryMapSubspaceMapIDs`` (F.7.57.58)
- ☐ ``getMemoryRemapAddressBlockIDs`` (F.7.57.59)
- ☐ ``getMemoryRemapBankIDs`` (F.7.57.60)
- ☐ ``getMemoryRemapElementIDs`` (F.7.57.61)
- ☐ ``getMemoryRemapModeRefByID`` (F.7.57.62)
- ☐ ``getMemoryRemapModeRefByNames`` (F.7.57.63)
- ☐ ``getMemoryRemapModeRefIDs`` (F.7.57.64)
- ☐ ``getMemoryRemapRemapDefinitionRefByExternalTypeDefID`` (F.7.57.65)
- ☐ ``getMemoryRemapRemapDefinitionRefByID`` (F.7.57.66)
- ☐ ``getMemoryRemapRemapDefinitionRefByName`` (F.7.57.67)
- ☐ ``getMemoryRemapRemapDefinitionRefID`` (F.7.57.68)
- ☐ ``getMemoryRemapSubspaceMapIDs`` (F.7.57.69)
- ☐ ``getSubspaceMapBaseAddress`` (F.7.57.70)
- ☐ ``getSubspaceMapBaseAddressExpression`` (F.7.57.71)
- ☐ ``getSubspaceMapBaseAddressID`` (F.7.57.72)
- ☐ ``getSubspaceMapSegmentRefByName`` (F.7.57.73)

Memory map (EXTENDED)
~~~~~~~~~~~~~~~~~~~~~

- ☐ ``addAccessPolicyModeRef`` (F.7.58.1)
- ☐ ``addAddressBlockRefIndex`` (F.7.58.2)
- ☐ ``addAddressBlockRegister`` (F.7.58.3)
- ☐ ``addAddressBlockRegisterFile`` (F.7.58.4)
- ☐ ``addAliasOfBankRef`` (F.7.58.5)
- ☐ ``addBankAccessPolicy`` (F.7.58.6)
- ☐ ``addBankAddressBlock`` (F.7.58.7)
- ☐ ``addBankBank`` (F.7.58.8)
- ☐ ``addBankSubspaceMap`` (F.7.58.9)
- ☐ ``addLocalMemoryMapBank`` (F.7.58.10)
- ☐ ``addMemoryMapAddressBlock`` (F.7.58.11)
- ☐ ``addMemoryMapBank`` (F.7.58.12)
- ☐ ``addMemoryMapMemoryRemap`` (F.7.58.13)
- ☐ ``addMemoryMapSubspaceMap`` (F.7.58.14)
- ☐ ``addMemoryRemapAddressBlock`` (F.7.58.15)
- ☐ ``addMemoryRemapBank`` (F.7.58.16)
- ☐ ``addMemoryRemapModeRef`` (F.7.58.17)
- ☐ ``addMemoryRemapSubspaceMap`` (F.7.58.18)
- ☐ ``addRegisterFileRegisterFile`` (F.7.58.19)
- ☐ ``removeAccessPolicyModeRef`` (F.7.58.20)
- ☐ ``removeAddressBlockArray`` (F.7.58.21)
- ☐ ``removeAddressBlockRefIndex`` (F.7.58.22)
- ☐ ``removeAddressBlockRegister`` (F.7.58.23)
- ☐ ``removeAddressBlockRegisterFile`` (F.7.58.24)
- ☐ ``removeAddressBlockTypeIdentifier`` (F.7.58.25)
- ☐ ``removeAddressBlockUsage`` (F.7.58.26)
- ☐ ``removeAddressBlockVolatility`` (F.7.58.27)
- ☐ ``removeAliasOfAddressBlockRef`` (F.7.58.28)
- ☐ ``removeAliasOfAddressSpaceRef`` (F.7.58.29)
- ☐ ``removeAliasOfBankRef`` (F.7.58.30)
- ☐ ``removeAliasOfMemoryMapRef`` (F.7.58.31)
- ☐ ``removeBankAccessPolicy`` (F.7.58.32)
- ☐ ``removeBankAddressBlock`` (F.7.58.33)
- ☐ ``removeBankBank`` (F.7.58.34)
- ☐ ``removeBankSubspaceMap`` (F.7.58.35)
- ☐ ``removeBankUsage`` (F.7.58.36)
- ☐ ``removeBankVolatility`` (F.7.58.37)
- ☐ ``removeMemoryMapAddressBlock`` (F.7.58.38)
- ☐ ``removeMemoryMapBank`` (F.7.58.39)
- ☐ ``removeMemoryMapMemoryRemap`` (F.7.58.40)
- ☐ ``removeMemoryMapShared`` (F.7.58.41)
- ☐ ``removeMemoryMapSubspaceMap`` (F.7.58.42)
- ☐ ``removeMemoryRemapBank`` (F.7.58.43)
- ☐ ``removeMemoryRemapMapAddressBlock`` (F.7.58.44)
- ☐ ``removeMemoryRemapModeRef`` (F.7.58.45)
- ☐ ``removeMemoryRemapSubspaceMap`` (F.7.58.46)
- ☐ ``removeRegisterArray`` (F.7.58.47)
- ☐ ``removeRegisterFileArray`` (F.7.58.48)
- ☐ ``setAddressBlockAddressBlockDefinitionRef`` (F.7.58.49)
- ☐ ``setAddressBlockArray`` (F.7.58.50)
- ☐ ``setAddressBlockBaseAddress`` (F.7.58.51)
- ☐ ``setAddressBlockDefinitionRef`` (F.7.58.52)
- ☐ ``setAddressBlockRange`` (F.7.58.53)
- ☐ ``setAddressBlockTypeIdentifier`` (F.7.58.54)
- ☐ ``setAddressBlockUsage`` (F.7.58.55)
- ☐ ``setAddressBlockVolatility`` (F.7.58.56)
- ☐ ``setAddressBlockWidth`` (F.7.58.57)
- ☐ ``setAliasOfAddressBlockRef`` (F.7.58.58)
- ☐ ``setAliasOfAddressSpaceRef`` (F.7.58.59)
- ☐ ``setAliasOfMemoryMapRef`` (F.7.58.60)
- ☐ ``setAliasOfMemoryRemapRef`` (F.7.58.61)
- ☐ ``setBankBankDefinitionRef`` (F.7.58.62)
- ☐ ``setBankBaseAddress`` (F.7.58.63)
- ☐ ``setBankUsage`` (F.7.58.64)
- ☐ ``setBankVolatility`` (F.7.58.65)
- ☐ ``setBroadcastToAddressSpaceRef`` (F.7.58.66)
- ☐ ``setMemoryMapMemoryMapDefinitionRef`` (F.7.58.67)
- ☐ ``setMemoryMapShared`` (F.7.58.68)
- ☐ ``setMemoryRemapRemapDefinitionRef`` (F.7.58.69)
- ☐ ``setRegisterArray`` (F.7.58.70)
- ☐ ``setRegisterFieldArray`` (F.7.58.71)
- ☐ ``setRegisterFieldBitOffset`` (F.7.58.72)
- ☐ ``setRegisterFileArray`` (F.7.58.73)
- ☐ ``setSubSpaceMapBaseAddress`` (F.7.58.74)

Miscellaneous (BASE)
~~~~~~~~~~~~~~~~~~~~

- ☑ ``getArgumentValue`` (F.7.59.1)
- ☑ ``getArgumentValueExpression`` (F.7.59.2)
- ☑ ``getArgumentValueID`` (F.7.59.3)
- ☑ ``getBooleanValue`` (F.7.59.4)
- ☑ ``getDefineValue`` (F.7.59.5)
- ☑ ``getDefineValueExpression`` (F.7.59.6)
- ☑ ``getDefineValueID`` (F.7.59.7)
- ☑ ``getExpression`` (F.7.59.8)
- ☑ ``getExpressionIntValue`` (F.7.59.9)
- ☑ ``getExpressionValue`` (F.7.59.10)
- ☑ ``getGroup`` (F.7.59.11)
- ☑ ``getPartSelectIndexIDs`` (F.7.59.12)
- ☑ ``getPartSelectIndices`` (F.7.59.13)
- ☑ ``getPartSelectIndicesExpression`` (F.7.59.14)
- ☑ ``getPartSelectRange`` (F.7.59.15)
- ☑ ``getPartSelectRangeExpression`` (F.7.59.16)
- ☑ ``getPartSelectRangeLeftID`` (F.7.59.17)
- ☑ ``getPartSelectRangeRightID`` (F.7.59.18)
- ☑ ``getValue`` (F.7.59.19)
- ☑ ``getXML`` (F.7.59.20)

Miscellaneous (EXTENDED)
~~~~~~~~~~~~~~~~~~~~~~~~

- ☑ ``addPartSelectIndex`` (F.7.60.1)
- ☑ ``end`` (F.7.60.2)
- ☑ ``init`` (F.7.60.3)
- ☑ ``isSetElement`` (F.7.60.4)
- ☑ ``message`` (F.7.60.5)
- ☑ ``registerCatalogVLNVs`` (F.7.60.6)
- ☑ ``registerVLNV`` (F.7.60.7)
- ☑ ``removePartSelectIndex`` (F.7.60.8)
- ☑ ``resolveExpression`` (F.7.60.9)
- ☑ ``save`` (F.7.60.10)
- ☑ ``setArgumentValue`` (F.7.60.11)
- ☑ ``setBooleanValue`` (F.7.60.12)
- ☑ ``setDefineValue`` (F.7.60.13)
- ☑ ``setExpressionValue`` (F.7.60.14)
- ☑ ``setPartSelectRange`` (F.7.60.15)
- ☑ ``setValue`` (F.7.60.16)
- ☑ ``removePartSelectRange`` (F.7.60.17)
- ☑ ``unregisterCatalogVLNVs`` (F.7.60.18)
- ☑ ``unregisterVLNV`` (F.7.60.19)

Module parameter (BASE)
~~~~~~~~~~~~~~~~~~~~~~~

- ☑ ``getModuleParameterIDs`` (F.7.61.1)
- ☑ ``getModuleParameterValue`` (F.7.61.2)
- ☑ ``getModuleParameterValueExpression`` (F.7.61.3)

Module parameter (EXTENDED)
~~~~~~~~~~~~~~~~~~~~~~~~~~~

- ☑ ``addModuleParameter`` (F.7.62.1)
- ☑ ``removeModuleParameter`` (F.7.62.2)
- ☑ ``setModuleParameterValue`` (F.7.62.3)

Name group (BASE)
~~~~~~~~~~~~~~~~~

- ☑ ``getDescription`` (F.7.63.1)
- ☑ ``getDisplayName`` (F.7.63.2)
- ☑ ``getName`` (F.7.63.3)
- ☑ ``getShortDescription`` (F.7.63.4)

Name group (EXTENDED)
~~~~~~~~~~~~~~~~~~~~~

- ☑ ``removeDescription`` (F.7.64.1)
- ☑ ``removeDisplayName`` (F.7.64.2)
- ☑ ``removeName`` (F.7.64.3)
- ☑ ``removeShortDescription`` (F.7.64.4)
- ☑ ``setDescription`` (F.7.64.5)
- ☑ ``setDisplayName`` (F.7.64.6)
- ☑ ``setName`` (F.7.64.7)
- ☑ ``setShortDescription`` (F.7.64.8)

Parameter (BASE)
~~~~~~~~~~~~~~~~

- ☑ ``getModuleParameterDataTypeDefinitionRefByID`` (F.7.65.1)
- ☑ ``getParameterChoiceRefByName`` (F.7.65.2)
- ☑ ``getParameterIDFromReferenceID`` (F.7.65.3)
- ☑ ``getParameterIDs`` (F.7.65.4)
- ☑ ``getParameterNameFromReferenceID`` (F.7.65.5)
- ☑ ``getParameterValue`` (F.7.65.6)
- ☑ ``getParameterValueExpression`` (F.7.65.7)
- ☑ ``getParameterValueID`` (F.7.65.8)

Parameter (EXTENDED)
~~~~~~~~~~~~~~~~~~~~

- ☑ ``addParameter`` (F.7.66.1)
- ☑ ``removeConfigGroupsAttribute`` (F.7.66.2)
- ☑ ``removeParameter`` (F.7.66.3)
- ☑ ``setParameterValue`` (F.7.66.4)

Port (BASE)
~~~~~~~~~~~

- ☐ ``getAccessPortAccessType`` (F.7.67.1)
- ☐ ``getDomainTypeDefTypeDefinitionIDs`` (F.7.67.2)
- ☐ ``getDomainTypeDefTypeDefinitions`` (F.7.67.3)
- ☐ ``getDomainTypeDefTypeName`` (F.7.67.4)
- ☐ ``getDomainTypeDefTypeNameID`` (F.7.67.5)
- ☐ ``getDomainTypeDefViewIDs`` (F.7.67.6)
- ☐ ``getDomainTypeDefViewRefIDs`` (F.7.67.7)
- ☐ ``getDomainTypeDefViewRefs`` (F.7.67.8)
- ☐ ``getFieldDefinitionAccessPoliciesIDs`` (F.7.67.9)
- ☐ ``getFieldMapFieldSliceID`` (F.7.67.10)
- ☐ ``getFieldMapModeRefByID`` (F.7.67.11)
- ☐ ``getFieldMapModeRefByNames`` (F.7.67.12)
- ☐ ``getFieldMapModeRefIDs`` (F.7.67.13)
- ☐ ``getFieldMapModeRefs`` (F.7.67.14)
- ☐ ``getFieldMapPartSelectID`` (F.7.67.15)
- ☐ ``getFieldMapSubPortReferenceIDs`` (F.7.67.16)
- ☐ ``getPayloadExtension`` (F.7.67.17)
- ☐ ``getPayloadExtensionID`` (F.7.67.18)
- ☐ ``getPayloadType`` (F.7.67.19)
- ☐ ``getPortAccessID`` (F.7.67.20)
- ☐ ``getPortDomainTypeDefIDs`` (F.7.67.21)
- ☐ ``getPortFieldMapIDs`` (F.7.67.22)
- ☐ ``getPortSignalTypeDefIDs`` (F.7.67.23)
- ☐ ``getPortStructuredID`` (F.7.67.24)
- ☐ ``getPortStructuredInterfaceID`` (F.7.67.25)
- ☐ ``getPortStructuredStructID`` (F.7.67.26)
- ☐ ``getPortStructuredStructPortTypeDefIDs`` (F.7.67.27)
- ☐ ``getPortStructuredSubPortIDs`` (F.7.67.28)
- ☐ ``getPortStructuredUnionID`` (F.7.67.29)
- ☐ ``getPortStructuredVectorIDs`` (F.7.67.30)
- ☐ ``getPortStyle`` (F.7.67.31)
- ☐ ``getPortTransactionalBusWidth`` (F.7.67.32)
- ☐ ``getPortTransactionalBusWidthExpression`` (F.7.67.33)
- ☐ ``getPortTransactionalBusWidthID`` (F.7.67.34)
- ☐ ``getPortTransactionalID`` (F.7.67.35)
- ☐ ``getPortTransactionalInitiative`` (F.7.67.36)
- ☐ ``getPortTransactionalKind`` (F.7.67.37)
- ☐ ``getPortTransactionalKindID`` (F.7.67.38)
- ☐ ``getPortTransactionalMaxConnections`` (F.7.67.39)
- ☐ ``getPortTransactionalMaxConnectionsExpression`` (F.7.67.40)
- ☐ ``getPortTransactionalMaxConnectionsID`` (F.7.67.41)
- ☐ ``getPortTransactionalMinConnections`` (F.7.67.42)
- ☐ ``getPortTransactionalMinConnectionsExpression`` (F.7.67.43)
- ☐ ``getPortTransactionalMinConnectionsID`` (F.7.67.44)
- ☐ ``getPortTransactionalProtocolID`` (F.7.67.45)
- ☐ ``getPortTransactionalQualifierID`` (F.7.67.46)
- ☐ ``getPortTransactionalTransTypeDefIDs`` (F.7.67.47)
- ☐ ``getPortWireConstraintSetIDs`` (F.7.67.48)
- ☐ ``getPortWireDirection`` (F.7.67.49)
- ☐ ``getPortWireDriverIDs`` (F.7.67.50)
- ☐ ``getPortWireID`` (F.7.67.51)
- ☐ ``getPortWireQualifierID`` (F.7.67.52)
- ☐ ``getPortWireTypeDefIDs`` (F.7.67.53)
- ☐ ``getProtocolPayloadID`` (F.7.67.54)
- ☐ ``getProtocolProtocolType`` (F.7.67.55)
- ☐ ``getProtocolProtocolTypeID`` (F.7.67.56)
- ☐ ``getQualifierIsAddress`` (F.7.67.57)
- ☐ ``getQualifierIsClock`` (F.7.67.58)
- ☐ ``getQualifierIsClockEn`` (F.7.67.59)
- ☐ ``getQualifierIsClockEnID`` (F.7.67.60)
- ☐ ``getQualifierIsData`` (F.7.67.61)
- ☐ ``getQualifierIsFlowControl`` (F.7.67.62)
- ☐ ``getQualifierIsFlowControlID`` (F.7.67.63)
- ☐ ``getQualifierIsInterrupt`` (F.7.67.64)
- ☐ ``getQualifierIsOpcode`` (F.7.67.65)
- ☐ ``getQualifierIsPowerEn`` (F.7.67.66)
- ☐ ``getQualifierIsPowerEnID`` (F.7.67.67)
- ☐ ``getQualifierIsPowerEnPowerDomainRefByName`` (F.7.67.68)
- ☐ ``getQualifierIsProtection`` (F.7.67.69)
- ☐ ``getQualifierIsRequest`` (F.7.67.70)
- ☐ ``getQualifierIsReset`` (F.7.67.71)
- ☐ ``getQualifierIsResetID`` (F.7.67.72)
- ☐ ``getQualifierIsResponse`` (F.7.67.73)
- ☐ ``getQualifierIsUser`` (F.7.67.74)
- ☐ ``getQualifierIsUserID`` (F.7.67.75)
- ☐ ``getQualifierIsValid`` (F.7.67.76)
- ☐ ``getServiceTypeDefServiceTypeDefIDs`` (F.7.67.77)
- ☐ ``getServiceTypeDefTypeDefinitionIDs`` (F.7.67.78)
- ☐ ``getServiceTypeDefTypeName`` (F.7.67.79)
- ☐ ``getServiceTypeDefTypeNameID`` (F.7.67.80)
- ☐ ``getServiceTypeDefTypeParameterIDs`` (F.7.67.81)
- ☐ ``getServiceTypeDefTypeParametersIDs`` (F.7.67.82)
- ☐ ``getSignalTypeDefSignalType`` (F.7.67.83)
- ☐ ``getSignalTypeDefViewIDs`` (F.7.67.84)
- ☐ ``getSignalTypeDefViewRefIDs`` (F.7.67.85)
- ☐ ``getSignalTypeDefViewRefs`` (F.7.67.86)
- ☐ ``getStrucPortTypeDefViewRefIDs`` (F.7.67.87)
- ☐ ``getStructPortTypeDefRole`` (F.7.67.88)
- ☐ ``getStructPortTypeDefTypeDefinitionIDs`` (F.7.67.89)
- ☐ ``getStructPortTypeDefTypeDefinitions`` (F.7.67.90)
- ☐ ``getStructPortTypeDefTypeName`` (F.7.67.91)
- ☐ ``getStructPortTypeDefTypeNameID`` (F.7.67.92)
- ☐ ``getStructPortTypeDefTypeParameterIDs`` (F.7.67.93)
- ☐ ``getStructPortTypeDefViewIDs`` (F.7.67.94)
- ☐ ``getSubPortPartSelectID`` (F.7.67.95)
- ☐ ``getSubPortReferencePartSelectID`` (F.7.67.96)
- ☐ ``getSubPortReferenceSubPortRefByName`` (F.7.67.97)
- ☐ ``getTransTypeDefServiceTypeDefIDs`` (F.7.67.98)
- ☐ ``getTransTypeDefTypeDefinitionIDs`` (F.7.67.99)
- ☐ ``getTransTypeDefTypeDefinitions`` (F.7.67.100)
- ☐ ``getTransTypeDefTypeName`` (F.7.67.101)
- ☐ ``getTransTypeDefTypeNameID`` (F.7.67.102)
- ☐ ``getTransTypeDefTypeParameterIDs`` (F.7.67.103)
- ☐ ``getTransTypeDefTypeParametersIDs`` (F.7.67.104)
- ☐ ``getTransTypeDefViewRefByID`` (F.7.67.105)
- ☐ ``getTransTypeDefViewRefIDs`` (F.7.67.106)
- ☐ ``getWireTypeDefTypeDefinitionIDs`` (F.7.67.107)
- ☐ ``getWireTypeDefTypeDefinitions`` (F.7.67.108)
- ☐ ``getWireTypeDefTypeName`` (F.7.67.109)
- ☐ ``getWireTypeDefTypeNameID`` (F.7.67.110)
- ☐ ``getWireTypeDefViewIDs`` (F.7.67.111)
- ☐ ``getWireTypeDefViewRefIDs`` (F.7.67.112)
- ☐ ``getWireTypeDefViewRefs`` (F.7.67.113)

Port (EXTENDED)
~~~~~~~~~~~~~~~

- ☐ ``addDomainTypeDefTypeDefinition`` (F.7.68.1)
- ☐ ``addDomainTypeDefViewRef`` (F.7.68.2)
- ☐ ``addExternalPortReferenceSubPortReference`` (F.7.68.3)
- ☐ ``addFieldMapIndex`` (F.7.68.4)
- ☐ ``addFieldMapModeRef`` (F.7.68.5)
- ☐ ``addFieldMapSubPortReference`` (F.7.68.6)
- ☐ ``addInternalPortReferenceSubPortReference`` (F.7.68.7)
- ☐ ``addPortClockDriver`` (F.7.68.8)
- ☐ ``addPortClockDriverExpresion`` (F.7.68.9)
- ☐ ``addPortDefaultDriver`` (F.7.68.10)
- ☐ ``addPortDefaultDriverExpression`` (F.7.68.11)
- ☐ ``addPortDomainTypeDef`` (F.7.68.12)
- ☐ ``addPortFieldMap`` (F.7.68.13)
- ☐ ``addPortSignalTypeDef`` (F.7.68.14)
- ☐ ``addPortSingleShotDriver`` (F.7.68.15)
- ☐ ``addPortSingleShotDriverExpression`` (F.7.68.16)
- ☐ ``addPortStructuredStructPortTypeDef`` (F.7.68.17)
- ☐ ``addPortStructuredSubStructuredPort`` (F.7.68.18)
- ☐ ``addPortStructuredSubWirePort`` (F.7.68.19)
- ☐ ``addPortStructuredVector`` (F.7.68.20)
- ☐ ``addPortTransactionalTransTypeDef`` (F.7.68.21)
- ☐ ``addPortWireConstraintSet`` (F.7.68.22)
- ☐ ``addPortWireDriver`` (F.7.68.23)
- ☐ ``addPortWireTypeDef`` (F.7.68.24)
- ☐ ``addServiceTypeDefServiceTypeDef`` (F.7.68.25)
- ☐ ``addServiceTypeDefTypeDefinition`` (F.7.68.26)
- ☐ ``addServiceTypeDefTypeParameter`` (F.7.68.27)
- ☐ ``addSignalTypeDefViewRef`` (F.7.68.28)
- ☐ ``addStructPortTypeDefTypeDefinition`` (F.7.68.29)
- ☐ ``addStructPortTypeDefTypeParameter`` (F.7.68.30)
- ☐ ``addStructPortTypeDefViewRef`` (F.7.68.31)
- ☐ ``addTransTypeDefServiceTypeDef`` (F.7.68.32)
- ☐ ``addTransTypeDefTypeDefinition`` (F.7.68.33)
- ☐ ``addTransTypeDefTypeParameter`` (F.7.68.34)
- ☐ ``addTransTypeDefViewRef`` (F.7.68.35)
- ☐ ``addWireTypeDefTypeDefinition`` (F.7.68.36)
- ☐ ``addWireTypeDefViewRef`` (F.7.68.37)
- ☑ ``removeAbstractionDefPortPacket`` (F.7.68.38)
- ☐ ``removeAccessPortAccessType`` (F.7.68.39)
- ☐ ``removeAllLogicalDirectionsAllowedAttribute`` (F.7.68.40)
- ☐ ``removeAllLogicalInitiativesAllowedAttribute`` (F.7.68.41)
- ☐ ``removeDomainTypeDefTypeDefinition`` (F.7.68.42)
- ☐ ``removeDomainTypeDefTypeName`` (F.7.68.43)
- ☐ ``removeDomainTypeDefViewRef`` (F.7.68.44)
- ☐ ``removeExactAttribute`` (F.7.68.45)
- ☐ ``removeFieldMapModeRef`` (F.7.68.46)
- ☐ ``removeFieldMapPartSelect`` (F.7.68.47)
- ☐ ``removeFieldMapSubPortReference`` (F.7.68.48)
- ☐ ``removePayloadExtension`` (F.7.68.49)
- ☐ ``removePortAccess`` (F.7.68.50)
- ☐ ``removePortClockDriver`` (F.7.68.51)
- ☐ ``removePortDefaultDriver`` (F.7.68.52)
- ☐ ``removePortDomainTypeDef`` (F.7.68.53)
- ☐ ``removePortFieldMap`` (F.7.68.54)
- ☐ ``removePortSignalTypeDef`` (F.7.68.55)
- ☐ ``removePortSingleShotDriver`` (F.7.68.56)
- ☐ ``removePortStructuredStructPortTypeDef`` (F.7.68.57)
- ☐ ``removePortStructuredSubPort`` (F.7.68.58)
- ☐ ``removePortStructuredVector`` (F.7.68.59)
- ☐ ``removePortTransactionalBusWidth`` (F.7.68.60)
- ☐ ``removePortTransactionalKind`` (F.7.68.61)
- ☐ ``removePortTransactionalMaxConnections`` (F.7.68.62)
- ☐ ``removePortTransactionalMinConnections`` (F.7.68.63)
- ☐ ``removePortTransactionalPowerConstraint`` (F.7.68.64)
- ☐ ``removePortTransactionalProtocol`` (F.7.68.65)
- ☐ ``removePortTransactionalQualifier`` (F.7.68.66)
- ☐ ``removePortTransactionalTransTypeDef`` (F.7.68.67)
- ☐ ``removePortWireConstraintSet`` (F.7.68.68)
- ☐ ``removePortWireDriver`` (F.7.68.69)
- ☐ ``removePortWirePowerConstraint`` (F.7.68.70)
- ☐ ``removePortWireQualifier`` (F.7.68.71)
- ☐ ``removePortWireTypeDef`` (F.7.68.72)
- ☐ ``removeProtocolPayload`` (F.7.68.73)
- ☐ ``removeQualifierIsAddress`` (F.7.68.74)
- ☐ ``removeQualifierIsClock`` (F.7.68.75)
- ☐ ``removeQualifierIsClockEn`` (F.7.68.76)
- ☐ ``removeQualifierIsData`` (F.7.68.77)
- ☐ ``removeQualifierIsFlowControl`` (F.7.68.78)
- ☐ ``removeQualifierIsInterrupt`` (F.7.68.79)
- ☐ ``removeQualifierIsOpcode`` (F.7.68.80)
- ☐ ``removeQualifierIsPowerEn`` (F.7.68.81)
- ☐ ``removeQualifierIsProtection`` (F.7.68.82)
- ☐ ``removeQualifierIsRequest`` (F.7.68.83)
- ☐ ``removeQualifierIsReset`` (F.7.68.84)
- ☐ ``removeQualifierIsResponse`` (F.7.68.85)
- ☐ ``removeQualifierIsUser`` (F.7.68.86)
- ☐ ``removeQualifierIsValid`` (F.7.68.87)
- ☐ ``removeServiceTypeDefServiceTypeDef`` (F.7.68.88)
- ☐ ``removeServiceTypeDefTypeDefinition`` (F.7.68.89)
- ☐ ``removeServiceTypeDefTypeParameter`` (F.7.68.90)
- ☐ ``removeSignalTypeDefViewRef`` (F.7.68.91)
- ☐ ``removeStructPortTypeDefRole`` (F.7.68.92)
- ☐ ``removeStructPortTypeDefTypeDefinition`` (F.7.68.93)
- ☐ ``removeStructPortTypeDefTypeParameter`` (F.7.68.94)
- ☐ ``removeStructPortTypeDefViewRef`` (F.7.68.95)
- ☐ ``removeSubPortMapPartSelect`` (F.7.68.96)
- ☐ ``removeSubPortReferencePartSelect`` (F.7.68.97)
- ☐ ``removeTransTypeDefServiceTypeDef`` (F.7.68.98)
- ☐ ``removeTransTypeDefTypeDefinition`` (F.7.68.99)
- ☐ ``removeTransTypeDefTypeName`` (F.7.68.100)
- ☐ ``removeTransTypeDefTypeParameter`` (F.7.68.101)
- ☐ ``removeTransTypeDefViewRef`` (F.7.68.102)
- ☐ ``removeWireTypeDefTypeDefinition`` (F.7.68.103)
- ☐ ``removeWireTypeDefTypeName`` (F.7.68.104)
- ☐ ``removeWireTypeDefViewRef`` (F.7.68.105)
- ☐ ``setAbstractionDefBusType`` (F.7.68.106)
- ☐ ``setAccessPortAccessType`` (F.7.68.107)
- ☐ ``setExternalPortReferencePortReference`` (F.7.68.108)
- ☐ ``setInternalPortReferenceComponentInstanceReference`` (F.7.68.109)
- ☐ ``setInternalPortReferencePortReference`` (F.7.68.110)
- ☐ ``setDomainTypeDefTypeName`` (F.7.68.111)
- ☐ ``setFieldMapAddressBlockRef`` (F.7.68.112)
- ☐ ``setFieldMapFieldRef`` (F.7.68.113)
- ☐ ``setFieldMapFieldSlice`` (F.7.68.114)
- ☐ ``setFieldMapMemoryMapRef`` (F.7.68.115)
- ☐ ``setFieldMapPartSelect`` (F.7.68.116)
- ☐ ``setFieldMapRegisterRef`` (F.7.68.117)
- ☐ ``setPayloadExtension`` (F.7.68.118)
- ☐ ``setPayloadType`` (F.7.68.119)
- ☐ ``setPortAccess`` (F.7.68.120)
- ☐ ``setPortStructured`` (F.7.68.121)
- ☐ ``setPortStructuredInterface`` (F.7.68.122)
- ☐ ``setPortStructuredStruct`` (F.7.68.123)
- ☐ ``setPortStructuredUnion`` (F.7.68.124)
- ☐ ``setPortTransactional`` (F.7.68.125)
- ☐ ``setPortTransactionalBusWidth`` (F.7.68.126)
- ☐ ``setPortTransactionalInitiative`` (F.7.68.127)
- ☐ ``setPortTransactionalKind`` (F.7.68.128)
- ☐ ``setPortTransactionalMaxConnections`` (F.7.68.129)
- ☐ ``setPortTransactionalMinConnections`` (F.7.68.130)
- ☐ ``setPortTransactionalProtocol`` (F.7.68.131)
- ☐ ``setPortTransactionalQualifier`` (F.7.68.132)
- ☐ ``setPortWire`` (F.7.68.133)
- ☐ ``setPortWireDirection`` (F.7.68.134)
- ☐ ``setPortWireQualifier`` (F.7.68.135)
- ☐ ``setProtocolPayload`` (F.7.68.136)
- ☐ ``setProtocolProtocolType`` (F.7.68.137)
- ☐ ``setQualifierIsAddress`` (F.7.68.138)
- ☐ ``setQualifierIsClock`` (F.7.68.139)
- ☐ ``setQualifierIsClockEn`` (F.7.68.140)
- ☐ ``setQualifierIsData`` (F.7.68.141)
- ☐ ``setQualifierIsFlowControl`` (F.7.68.142)
- ☐ ``setQualifierIsInterrupt`` (F.7.68.143)
- ☐ ``setQualifierIsOpcode`` (F.7.68.144)
- ☐ ``setQualifierIsPowerEn`` (F.7.68.145)
- ☐ ``setQualifierIsProtection`` (F.7.68.146)
- ☐ ``setQualifierIsRequest`` (F.7.68.147)
- ☐ ``setQualifierIsReset`` (F.7.68.148)
- ☐ ``setQualifierIsResponse`` (F.7.68.149)
- ☐ ``setQualifierIsUser`` (F.7.68.150)
- ☐ ``setQualifierIsValid`` (F.7.68.151)
- ☐ ``setServiceTypeDefTypeName`` (F.7.68.152)
- ☐ ``setSignalTypeDefSignalType`` (F.7.68.153)
- ☐ ``setStructPortTypeDefRole`` (F.7.68.154)
- ☐ ``setStructPortTypeDefTypeName`` (F.7.68.155)
- ☐ ``setSubPortReferencePartSelect`` (F.7.68.156)
- ☐ ``setTransTypeDefTypeName`` (F.7.68.157)
- ☐ ``setWireTypeDefTypeName`` (F.7.68.158)

Port map (BASE)
~~~~~~~~~~~~~~~

- ☑ ``getLogicalPortRange`` (F.7.69.1)
- ☑ ``getLogicalPortRangeExpression`` (F.7.69.2)
- ☑ ``getLogicalPortRangeLeftID`` (F.7.69.3)
- ☑ ``getLogicalPortRangeRightID`` (F.7.69.4)
- ☑ ``getPhysicalPortPartSelectID`` (F.7.69.5)
- ☑ ``getPhysicalPortSubPortIDs`` (F.7.69.6)
- ☑ ``getPortMapIsInformative`` (F.7.69.7)
- ☑ ``getPortMapLogicalPortID`` (F.7.69.8)
- ☑ ``getPortMapLogicalTieOff`` (F.7.69.9)
- ☑ ``getPortMapLogicalTieOffExpression`` (F.7.69.10)
- ☑ ``getPortMapLogicalTieOffID`` (F.7.69.11)
- ☑ ``getPortMapPhysicalPortID`` (F.7.69.12)

Port map (EXTENDED)
~~~~~~~~~~~~~~~~~~~

- ☑ ``addPhysicalPortSubPort`` (F.7.70.1)
- ☑ ``addPortMapPhysicalPortSubPort`` (F.7.70.2)
- ☑ ``removePhysicalPortPartSelect`` (F.7.70.3)
- ☑ ``removePhysicalPortSubPort`` (F.7.70.4)
- ☑ ``removePortMapIsInformative`` (F.7.70.5)
- ☑ ``setAbstractionTypeAbstractionRef`` (F.7.70.6)
- ☑ ``setLogicalPortRange`` (F.7.70.7)
- ☑ ``setPhysicalPortPartSelect`` (F.7.70.8)
- ☑ ``setPortMapIsInformative`` (F.7.70.9)
- ☑ ``setPortMapLogicalPort`` (F.7.70.10)
- ☑ ``setPortMapLogicalTieOff`` (F.7.70.11)
- ☑ ``setPortMapPhysicalPort`` (F.7.70.12)
- ☑ ``setSubPortMapPartSelect`` (F.7.70.13)

Power (BASE)
~~~~~~~~~~~~

- ☑ ``getPortTransactionalPowerConstraintIDs`` (F.7.71.1)
- ☑ ``getPortWirePowerConstraintIDs`` (F.7.71.2)
- ☑ ``getPowerConstraintPowerDomainRefByID`` (F.7.71.3)
- ☑ ``getPowerConstraintPowerDomainRefByName`` (F.7.71.4)
- ☑ ``getPowerConstraintRange`` (F.7.71.5)
- ☑ ``getPowerConstraintRangeLeftID`` (F.7.71.6)
- ☑ ``getPowerConstraintRangeRightID`` (F.7.71.7)
- ☑ ``getPowerDomainAlwaysOn`` (F.7.71.8)
- ☑ ``getPowerDomainAlwaysOnExpression`` (F.7.71.9)
- ☑ ``getPowerDomainAlwaysOnID`` (F.7.71.10)
- ☑ ``getPowerDomainName`` (F.7.71.11)
- ☑ ``getPowerDomainSubDomainOf`` (F.7.71.12)
- ☑ ``getPowerDomainSubDomainOfRefByID`` (F.7.71.13)

Power (EXTENDED)
~~~~~~~~~~~~~~~~

- ☑ ``addComponentInstancePowerDomainLink`` (F.7.72.1)
- ☑ ``addComponentPowerDomain`` (F.7.72.2)
- ☑ ``addPortTransactionalPowerConstraint`` (F.7.72.3)
- ☑ ``addPortWirePowerConstraint`` (F.7.72.4)
- ☑ ``addPowerDomainLinkInternalPowerDomainReference`` (F.7.72.5)
- ☑ ``removeComponentInstancePowerDomainLink`` (F.7.72.6)
- ☑ ``removeComponentPowerDomain`` (F.7.72.7)
- ☑ ``removePowerConstraintRange`` (F.7.72.8)
- ☑ ``removePowerDomainLinkInternalPowerDomainRef`` (F.7.72.9)
- ☑ ``removePowerDomainSubDomainOf`` (F.7.72.10)
- ☑ ``setPowerConstraintPowerDomainRef`` (F.7.72.11)
- ☑ ``setPowerConstraintRange`` (F.7.72.12)
- ☑ ``setPowerDomainAlwaysOn`` (F.7.72.13)
- ☑ ``setPowerDomainSubDomainOf`` (F.7.72.14)

Register (BASE)
~~~~~~~~~~~~~~~

- ☐ ``getAliasOfAlternateRegisterRefByName`` (F.7.73.1)
- ☐ ``getAliasOfAlternateRegisterRefID`` (F.7.73.2)
- ☐ ``getAliasOfFieldRefByName`` (F.7.73.3)
- ☐ ``getAliasOfFieldRefID`` (F.7.73.4)
- ☐ ``getAliasOfRegisterRefByName`` (F.7.73.5)
- ☐ ``getAliasOfRegisterRefID`` (F.7.73.6)
- ☐ ``getAlternateRegisterFieldIDs`` (F.7.73.7)
- ☐ ``getAlternateRegisterModeRefIDs`` (F.7.73.8)
- ☐ ``getAlternateRegisterRefAlternateRegisterRefByName`` (F.7.73.9)
- ☐ ``getAlternateRegisterTypeIdentifier`` (F.7.73.10)
- ☐ ``getAlternateRegisterVolatility`` (F.7.73.11)
- ☐ ``getBroadcastToAddressBlockRefByName`` (F.7.73.12)
- ☐ ``getBroadcastToAddressBlockRefID`` (F.7.73.13)
- ☐ ``getBroadcastToAddressSpaceRefByName`` (F.7.73.14)
- ☐ ``getBroadcastToAddressSpaceRefID`` (F.7.73.15)
- ☐ ``getBroadcastToAlternateRegisterRefByName`` (F.7.73.16)
- ☐ ``getBroadcastToAlternateRegisterRefID`` (F.7.73.17)
- ☐ ``getBroadcastToBankRefByNames`` (F.7.73.18)
- ☐ ``getBroadcastToBankRefIDs`` (F.7.73.19)
- ☐ ``getBroadcastToFieldRefByName`` (F.7.73.20)
- ☐ ``getBroadcastToFieldRefID`` (F.7.73.21)
- ☐ ``getBroadcastToMemoryMapRefByName`` (F.7.73.22)
- ☐ ``getBroadcastToMemoryMapRefID`` (F.7.73.23)
- ☐ ``getBroadcastToRegisterFileRefByNames`` (F.7.73.24)
- ☐ ``getBroadcastToRegisterFileRefIDs`` (F.7.73.25)
- ☐ ``getBroadcastToRegisterRefByName`` (F.7.73.26)
- ☐ ``getBroadcastToRegisterRefID`` (F.7.73.27)
- ☐ ``getEnumeratedValueExpression`` (F.7.73.28)
- ☐ ``getEnumeratedValueUsage`` (F.7.73.29)
- ☐ ``getEnumeratedValueValue`` (F.7.73.30)
- ☐ ``getEnumeratedValueValueExpression`` (F.7.73.31)
- ☐ ``getEnumeratedValueValueID`` (F.7.73.32)
- ☐ ``getEnumeratedValuesEnumeratedValueIDs`` (F.7.73.33)
- ☐ ``getEnumeratedValuesEnumerationDefinitionRefByExternalTypeDefID`` (F.7.73.34)
- ☐ ``getEnumeratedValuesEnumerationDefinitionRefByID`` (F.7.73.35)
- ☐ ``getEnumeratedValuesEnumerationDefinitionRefByName`` (F.7.73.36)
- ☐ ``getEnumeratedValuesEnumerationDefinitionRefID`` (F.7.73.37)
- ☐ ``getFieldBitOffsetID`` (F.7.73.38)
- ☐ ``getFieldDefinitionBitWidthID`` (F.7.73.39)
- ☐ ``getFieldDefinitionEnumeratedValueIDs`` (F.7.73.40)
- ☐ ``getFieldDefinitionTypeIdentifier`` (F.7.73.41)
- ☐ ``getFieldDefinitionVolatile`` (F.7.73.42)
- ☐ ``getFieldRefFieldRefByName`` (F.7.73.43)
- ☐ ``getFieldRefIndexIDs`` (F.7.73.44)
- ☐ ``getRegisterAddressOffset`` (F.7.73.45)
- ☐ ``getRegisterAddressOffsetExpression`` (F.7.73.46)
- ☐ ``getRegisterAddressOffsetID`` (F.7.73.47)
- ☐ ``getRegisterAlternateRegisterIDs`` (F.7.73.48)
- ☐ ``getRegisterFieldAliasOfID`` (F.7.73.49)
- ☐ ``getRegisterFieldBitOffset`` (F.7.73.50)
- ☐ ``getRegisterFieldBitOffsetExpression`` (F.7.73.51)
- ☐ ``getRegisterFieldBitOffsetID`` (F.7.73.52)
- ☐ ``getRegisterFieldBitWidth`` (F.7.73.53)
- ☐ ``getRegisterFieldBitWidthExpression`` (F.7.73.54)
- ☐ ``getRegisterFieldBitWidthID`` (F.7.73.55)
- ☐ ``getRegisterFieldEnumeratedValuesID`` (F.7.73.56)
- ☐ ``getRegisterFieldFieldDefinitionRefByExternalTypeDefID`` (F.7.73.57)
- ☐ ``getRegisterFieldFieldDefinitionRefByID`` (F.7.73.58)
- ☐ ``getRegisterFieldFieldDefinitionRefByName`` (F.7.73.59)
- ☐ ``getRegisterFieldFieldDefinitionRefID`` (F.7.73.60)
- ☐ ``getRegisterFieldIDs`` (F.7.73.61)
- ☐ ``getRegisterFieldResetIDs`` (F.7.73.62)
- ☐ ``getRegisterFieldTypeIdentifier`` (F.7.73.63)
- ☐ ``getRegisterFieldVolatility`` (F.7.73.64)
- ☐ ``getRegisterFileAddressOffsetID`` (F.7.73.65)
- ☐ ``getRegisterRefAttributeByID`` (F.7.73.66)
- ☐ ``getRegisterRefIndexIDs`` (F.7.73.67)
- ☐ ``getRegisterRefRegisterRefByName`` (F.7.73.68)
- ☐ ``getRegisterRegisterDefinitionRefByExternalTypeDefID`` (F.7.73.69)
- ☐ ``getRegisterRegisterDefinitionRefByID`` (F.7.73.70)
- ☐ ``getRegisterRegisterDefinitionRefByName`` (F.7.73.71)
- ☐ ``getRegisterRegisterDefinitionRefID`` (F.7.73.72)
- ☐ ``getRegisterSize`` (F.7.73.73)
- ☐ ``getRegisterSizeExpression`` (F.7.73.74)
- ☐ ``getRegisterSizeID`` (F.7.73.75)
- ☐ ``getRegisterTypeIdentifier`` (F.7.73.76)
- ☐ ``getRegisterVolatility`` (F.7.73.77)
- ☐ ``getResetMask`` (F.7.73.78)
- ☐ ``getResetMaskExpression`` (F.7.73.79)
- ☐ ``getResetMaskID`` (F.7.73.80)
- ☐ ``getResetValue`` (F.7.73.81)
- ☐ ``getResetValueExpression`` (F.7.73.82)
- ☐ ``getResetValueID`` (F.7.73.83)

Register (EXTENDED)
~~~~~~~~~~~~~~~~~~~

- ☐ ``addAlternateRegisterField`` (F.7.74.1)
- ☐ ``addAlternaterRegisterModeRef`` (F.7.74.2)
- ☐ ``addBroadcastToBankRef`` (F.7.74.3)
- ☐ ``addBroadcastToRegisterFileRef`` (F.7.74.4)
- ☐ ``addEnumeratedValuesFieldEnumeratedValue`` (F.7.74.5)
- ☐ ``addFieldRefIndex`` (F.7.74.6)
- ☐ ``addRegisterAlternateRegister`` (F.7.74.7)
- ☐ ``addRegisterField`` (F.7.74.8)
- ☐ ``addRegisterFieldReset`` (F.7.74.9)
- ☐ ``addRegisterRefIndex`` (F.7.74.10)
- ☐ ``removeAliasOfAlternateRegisterRef`` (F.7.74.11)
- ☐ ``removeAliasOfRegisterRef`` (F.7.74.12)
- ☐ ``removeAlternateRegisterField`` (F.7.74.13)
- ☐ ``removeAlternateRegisterTypeIdentifier`` (F.7.74.14)
- ☐ ``removeAlternateRegisterVolatility`` (F.7.74.15)
- ☐ ``removeAlternaterRegisterModeRef`` (F.7.74.16)
- ☐ ``removeBroadcastToAddressBlockRef`` (F.7.74.17)
- ☐ ``removeBroadcastToAlternateRegisterRef`` (F.7.74.18)
- ☐ ``removeBroadcastToBankRef`` (F.7.74.19)
- ☐ ``removeBroadcastToMemoryMapRef`` (F.7.74.20)
- ☐ ``removeBroadcastToRegisterFileRef`` (F.7.74.21)
- ☐ ``removeBroadcastToRegisterRef`` (F.7.74.22)
- ☐ ``removeEnumeratedValuesEnumeratedValue`` (F.7.74.23)
- ☐ ``removeFieldRefIndex`` (F.7.74.24)
- ☐ ``removeRegisterAlternateRegister`` (F.7.74.25)
- ☐ ``removeRegisterField`` (F.7.74.26)
- ☐ ``removeRegisterFieldArray`` (F.7.74.27)
- ☐ ``removeRegisterFieldBitWidth`` (F.7.74.28)
- ☐ ``removeRegisterFieldEnumeratedValues`` (F.7.74.29)
- ☐ ``removeRegisterFieldFieldAccessPolicices`` (F.7.74.30)
- ☐ ``removeRegisterFieldReset`` (F.7.74.31)
- ☐ ``removeRegisterFieldTypeIdentifier`` (F.7.74.32)
- ☐ ``removeRegisterFieldVolatility`` (F.7.74.33)
- ☐ ``removeRegisterRefIndex`` (F.7.74.34)
- ☐ ``removeRegisterTypeIdentifier`` (F.7.74.35)
- ☐ ``removeRegisterVolatility`` (F.7.74.36)
- ☐ ``removeResetMask`` (F.7.74.37)
- ☐ ``removeUsageAttribute`` (F.7.74.38)
- ☐ ``setAliasOfAlternateRegisterRef`` (F.7.74.39)
- ☐ ``setAliasOfFieldRef`` (F.7.74.40)
- ☐ ``setAliasOfRegisterRef`` (F.7.74.41)
- ☐ ``setAlternateRegisterTypeIdentifier`` (F.7.74.42)
- ☐ ``setAlternateRegisterVolatility`` (F.7.74.43)
- ☐ ``setBroadcastToAddressBlockRef`` (F.7.74.44)
- ☐ ``setBroadcastToAlternateRegisterRef`` (F.7.74.45)
- ☐ ``setBroadcastToFieldRef`` (F.7.74.46)
- ☐ ``setBroadcastToMemoryMapRef`` (F.7.74.47)
- ☐ ``setBroadcastToRegisterRef`` (F.7.74.48)
- ☐ ``setEnumeratedValueUsage`` (F.7.74.49)
- ☐ ``setEnumeratedValueValue`` (F.7.74.50)
- ☐ ``setEnumeratedValuesEnumerationDefinitionRef`` (F.7.74.51)
- ☐ ``setFieldDefinitionBitWidth`` (F.7.74.52)
- ☐ ``setFieldDefinitionTypeIdentifier`` (F.7.74.53)
- ☐ ``setFieldDefinitionVolatile`` (F.7.74.54)
- ☐ ``setModeRefPriority`` (F.7.74.55)
- ☐ ``setRegisterAddressOffset`` (F.7.74.56)
- ☐ ``setRegisterFieldAliasOf`` (F.7.74.57)
- ☐ ``setRegisterFieldBitWidth`` (F.7.74.58)
- ☐ ``setRegisterFieldEnumeratedValues`` (F.7.74.59)
- ☐ ``setRegisterFieldFieldAccessPolicies`` (F.7.74.60)
- ☐ ``setRegisterFieldFieldDefinitionRef`` (F.7.74.61)
- ☐ ``setRegisterFieldTypeIdentifier`` (F.7.74.62)
- ☐ ``setRegisterFieldVolatility`` (F.7.74.63)
- ☐ ``setRegisterRegisterDefinitionRef`` (F.7.74.64)
- ☐ ``setRegisterSize`` (F.7.74.65)
- ☐ ``setRegisterTypeIdentifier`` (F.7.74.66)
- ☐ ``setRegisterVolatility`` (F.7.74.67)
- ☐ ``setResetMask`` (F.7.74.68)
- ☐ ``setResetValue`` (F.7.74.69)

Register file (BASE)
~~~~~~~~~~~~~~~~~~~~

- ☑ ``getAliasOfRegisterFileRefByNames`` (F.7.75.1)
- ☑ ``getAliasOfRegisterFileRefIDs`` (F.7.75.2)
- ☑ ``getRegisterFileAccessHandleIDs`` (F.7.75.3)
- ☑ ``getRegisterFileAccessPolicyIDs`` (F.7.75.4)
- ☑ ``getRegisterFileAddressOffset`` (F.7.75.5)
- ☑ ``getRegisterFileAddressOffsetExpression`` (F.7.75.6)
- ☑ ``getRegisterFileArrayID`` (F.7.75.7)
- ☑ ``getRegisterFileRange`` (F.7.75.8)
- ☑ ``getRegisterFileRangeExpression`` (F.7.75.9)
- ☑ ``getRegisterFileRangeID`` (F.7.75.10)
- ☑ ``getRegisterFileRefIndexIDs`` (F.7.75.11)
- ☑ ``getRegisterFileRegisterFileDefinitionRefByExternalTypeDefID`` (F.7.75.12)
- ☑ ``getRegisterFileRegisterFileDefinitionRefByID`` (F.7.75.13)
- ☑ ``getRegisterFileRegisterFileDefinitionRefByName`` (F.7.75.14)
- ☑ ``getRegisterFileRegisterFileDefinitionRefID`` (F.7.75.15)
- ☑ ``getRegisterFileRegisterFileIDs`` (F.7.75.16)
- ☑ ``getRegisterFileRegisterIDs`` (F.7.75.17)
- ☑ ``getRegisterFileTypeIdentifier`` (F.7.75.18)

Register file (EXTENDED)
~~~~~~~~~~~~~~~~~~~~~~~~

- ☑ ``addAliasOfRegisterFileRef`` (F.7.76.1)
- ☑ ``addRegisterFileDefinitionRegisterFile`` (F.7.76.2)
- ☑ ``addRegisterFileRefIndex`` (F.7.76.3)
- ☑ ``addRegisterFileRegister`` (F.7.76.4)
- ☑ ``removeAliasOfRegisterFileRef`` (F.7.76.5)
- ☑ ``removeRegisterFileAccessHandle`` (F.7.76.6)
- ☑ ``removeRegisterFileRefIndex`` (F.7.76.7)
- ☑ ``removeRegisterFileRegister`` (F.7.76.8)
- ☑ ``removeRegisterFileRegisterFile`` (F.7.76.9)
- ☑ ``removeRegisterFileTypeIdentifier`` (F.7.76.10)
- ☑ ``setRegisterFileAddressOffset`` (F.7.76.11)
- ☑ ``setRegisterFileRange`` (F.7.76.12)
- ☑ ``setRegisterFileRegisterFileDefinitionRef`` (F.7.76.13)
- ☑ ``setRegisterFileTypeIdentifier`` (F.7.76.14)

Slice (BASE)
~~~~~~~~~~~~

- ☐ ``getFieldSliceAddressBlockRefByID`` (F.7.77.1)
- ☑ ``getFieldSliceAddressBlockRefByName`` (F.7.77.2)
- ☑ ``getFieldSliceAddressBlockRefID`` (F.7.77.3)
- ☐ ``getFieldSliceAddressSpaceRefByID`` (F.7.77.4)
- ☑ ``getFieldSliceAddressSpaceRefByName`` (F.7.77.5)
- ☑ ``getFieldSliceAddressSpaceRefID`` (F.7.77.6)
- ☐ ``getFieldSliceAlternateRegisterRefByID`` (F.7.77.7)
- ☑ ``getFieldSliceAlternateRegisterRefByName`` (F.7.77.8)
- ☑ ``getFieldSliceAlternateRegisterRefID`` (F.7.77.9)
- ☑ ``getFieldSliceBankRefByNames`` (F.7.77.10)
- ☑ ``getFieldSliceBankRefIDs`` (F.7.77.11)
- ☑ ``getFieldSliceFieldRefByName`` (F.7.77.12)
- ☑ ``getFieldSliceFieldRefID`` (F.7.77.13)
- ☐ ``getFieldSliceMemoryMapRefByID`` (F.7.77.14)
- ☑ ``getFieldSliceMemoryMapRefByName`` (F.7.77.15)
- ☑ ``getFieldSliceMemoryMapRefID`` (F.7.77.16)
- ☐ ``getFieldSliceMemoryRemapRefByID`` (F.7.77.17)
- ☑ ``getFieldSliceMemoryRemapRefByName`` (F.7.77.18)
- ☑ ``getFieldSliceMemoryRemapRefID`` (F.7.77.19)
- ☑ ``getFieldSliceRange`` (F.7.77.20)
- ☑ ``getFieldSliceRangeLeftID`` (F.7.77.21)
- ☑ ``getFieldSliceRangeRightID`` (F.7.77.22)
- ☑ ``getFieldSliceRegisterFileRefByNames`` (F.7.77.23)
- ☑ ``getFieldSliceRegisterFileRefIDs`` (F.7.77.24)
- ☐ ``getFieldSliceRegisterRefByID`` (F.7.77.25)
- ☑ ``getFieldSliceRegisterRefByName`` (F.7.77.26)
- ☑ ``getFieldSliceRegisterRefID`` (F.7.77.27)
- ☑ ``getLocationSliceIDs`` (F.7.77.28)
- ☑ ``getModeFieldSliceIDs`` (F.7.77.29)
- ☑ ``getModePortSliceIDs`` (F.7.77.30)
- ☑ ``getPortSlicePartSelectID`` (F.7.77.31)
- ☑ ``getPortSlicePortRefByName`` (F.7.77.32)
- ☑ ``getPortSliceSubPortReferenceIDs`` (F.7.77.33)
- ☑ ``getSlicePathSegmentIDs`` (F.7.77.34)
- ☑ ``getSliceRange`` (F.7.77.35)
- ☑ ``getSliceRangeExpression`` (F.7.77.36)
- ☑ ``getSliceRangeLeftID`` (F.7.77.37)
- ☑ ``getSliceRangeRightID`` (F.7.77.38)

Slice (EXTENDED)
~~~~~~~~~~~~~~~~

- ☑ ``addFieldSliceBankRef`` (F.7.78.1)
- ☑ ``addFieldSliceRegisterFileRef`` (F.7.78.2)
- ☑ ``addModeFieldSlice`` (F.7.78.3)
- ☑ ``addModePortSlice`` (F.7.78.4)
- ☑ ``addPortSliceSubPortReference`` (F.7.78.5)
- ☑ ``addSlicePathSegment`` (F.7.78.6)
- ☑ ``removeFieldSliceAlternateRegisterRef`` (F.7.78.7)
- ☑ ``removeFieldSliceBankRef`` (F.7.78.8)
- ☑ ``removeFieldSliceMemoryRemapRef`` (F.7.78.9)
- ☑ ``removeFieldSliceRange`` (F.7.78.10)
- ☑ ``removeFieldSliceRegisterFileRef`` (F.7.78.11)
- ☑ ``removeLocationSlice`` (F.7.78.12)
- ☑ ``removeModeFieldSlice`` (F.7.78.13)
- ☑ ``removeModePortSlice`` (F.7.78.14)
- ☑ ``removePortSlicePartSelect`` (F.7.78.15)
- ☑ ``removePortSliceSubPortReference`` (F.7.78.16)
- ☑ ``removeSlicePathSegment`` (F.7.78.17)
- ☑ ``removeSliceRange`` (F.7.78.18)
- ☑ ``setFieldSliceAddressBlockRef`` (F.7.78.19)
- ☑ ``setFieldSliceAddressSpaceRef`` (F.7.78.20)
- ☑ ``setFieldSliceAlternateRegisterRef`` (F.7.78.21)
- ☑ ``setFieldSliceFieldRef`` (F.7.78.22)
- ☑ ``setFieldSliceMemoryMapRef`` (F.7.78.23)
- ☑ ``setFieldSliceMemoryRemapRef`` (F.7.78.24)
- ☑ ``setFieldSliceRange`` (F.7.78.25)
- ☑ ``setFieldSliceRegisterRef`` (F.7.78.26)
- ☑ ``setPortSlicePartSelect`` (F.7.78.27)
- ☑ ``setPortSlicePortRef`` (F.7.78.28)
- ☑ ``setSliceRange`` (F.7.78.29)

Top element (BASE)
~~~~~~~~~~~~~~~~~~

- ☑ ``getAbstractionDefIDs`` (F.7.79.1)
- ☑ ``getAbstractorIDs`` (F.7.79.2)
- ☑ ``getBusDefIDs`` (F.7.79.3)
- ☑ ``getCatalogIDs`` (F.7.79.4)
- ☑ ``getComponentIDs`` (F.7.79.5)
- ☑ ``getDesignConfigurationIDs`` (F.7.79.6)
- ☑ ``getDesignIDs`` (F.7.79.7)
- ☑ ``getGeneratorChainIDs`` (F.7.79.8)
- ☑ ``getID`` (F.7.79.9)
- ☑ ``getTypeDefinitionsIDs`` (F.7.79.10)
- ☑ ``getVLNV`` (F.7.79.11)
- ☑ ``getXMLPath`` (F.7.79.12)

Top element (EXTENDED)
~~~~~~~~~~~~~~~~~~~~~~

- ☑ ``createAbstractionDef`` (F.7.80.1)
- ☑ ``createAbstractor`` (F.7.80.2)
- ☑ ``createBusDefinition`` (F.7.80.3)
- ☑ ``createCatalog`` (F.7.80.4)
- ☑ ``createComponent`` (F.7.80.5)
- ☑ ``createDesign`` (F.7.80.6)
- ☑ ``createDesignConfiguration`` (F.7.80.7)
- ☑ ``createGeneratorChain`` (F.7.80.8)
- ☑ ``createTypeDefinitions`` (F.7.80.9)
- ☑ ``edit`` (F.7.80.10)
- ☑ ``setXMLPath`` (F.7.80.11)

Type definitions (BASE)
~~~~~~~~~~~~~~~~~~~~~~~

- ☐ ``getAddressBlockDefinitionAddressUnitBits`` (F.7.81.1)
- ☐ ``getAddressBlockDefinitionAddressUnitBitsExpression`` (F.7.81.2)
- ☐ ``getAddressBlockDefinitionAddressUnitBitsID`` (F.7.81.3)
- ☐ ``getBankDefinitionAddressUnitBits`` (F.7.81.4)
- ☐ ``getBankDefinitionAddressUnitBitsExpression`` (F.7.81.5)
- ☐ ``getBankDefinitionAddressUnitBitsID`` (F.7.81.6)
- ☐ ``getEnumerationDefinitionEnumeratedValueIDs`` (F.7.81.7)
- ☐ ``getEnumerationDefinitionWidth`` (F.7.81.8)
- ☐ ``getEnumerationDefinitionWidthExpression`` (F.7.81.9)
- ☐ ``getEnumerationDefinitionWidthID`` (F.7.81.10)
- ☐ ``getExternalTypeDefinitionsModeLinksIDs`` (F.7.81.11)
- ☐ ``getExternalTypeDefinitionsResetTypeLinkIDs`` (F.7.81.12)
- ☐ ``getExternalTypeDefinitionsTypeDefinitionsRefByID`` (F.7.81.13)
- ☐ ``getExternalTypeDefinitionsTypeDefinitionsRefByVLNV`` (F.7.81.14)
- ☐ ``getExternalTypeDefinitionsViewLinkIDs`` (F.7.81.15)
- ☐ ``getMemoryRemapDefinitionAddressUnitBits`` (F.7.81.16)
- ☐ ``getMemoryRemapDefinitionAddressUnitBitsExpression`` (F.7.81.17)
- ☐ ``getMemoryRemapDefinitionAddressUnitBitsID`` (F.7.81.18)
- ☐ ``getModeLinkExternalModeReferenceRefByName`` (F.7.81.19)
- ☐ ``getModeLinkExternalModeReferenceID`` (F.7.81.20)
- ☐ ``getModeLinkModeReferenceRefByName`` (F.7.81.21)
- ☐ ``getModeLinkModeReferenceID`` (F.7.81.22)
- ☐ ``getRegisterFileDefinitionAddressUnitBits`` (F.7.81.23)
- ☐ ``getRegisterFileDefinitionAddressUnitBitsExpression`` (F.7.81.24)
- ☐ ``getRegisterFileDefinitionAddressUnitBitsID`` (F.7.81.25)
- ☐ ``getResetTypeLinkExternalResetTypeRefByName`` (F.7.81.26)
- ☐ ``getResetTypeLinkExternalResetTypeReferenceID`` (F.7.81.27)
- ☐ ``getResetTypeLinkResetTypeReferenceRefByName`` (F.7.81.28)
- ☐ ``getResetTypeLinkResetTypeReferenceID`` (F.7.81.29)
- ☐ ``getTypeDefinitionsAddressBlockDefinitionIDs`` (F.7.81.30)
- ☐ ``getTypeDefinitionsBankDefinitionIDs`` (F.7.81.31)
- ☐ ``getTypeDefinitionsChoiceIDs`` (F.7.81.32)
- ☐ ``getTypeDefinitionsEnumerationDefinitionIDs`` (F.7.81.33)
- ☐ ``getTypeDefinitionsExternalTypeDefinitionsIDs`` (F.7.81.34)
- ☐ ``getTypeDefinitionsFieldDefinitionIDs`` (F.7.81.35)
- ☐ ``getTypeDefinitionsMemoryMapDefinitionIDs`` (F.7.81.36)
- ☐ ``getTypeDefinitionsMemoryRemapDefinitionIDs`` (F.7.81.37)
- ☐ ``getTypeDefinitionsModeIDs`` (F.7.81.38)
- ☐ ``getTypeDefinitionsRegisterDefinitionIDs`` (F.7.81.39)
- ☐ ``getTypeDefinitionsRegisterFileDefinitionIDs`` (F.7.81.40)
- ☐ ``getTypeDefinitionsResetTypeIDs`` (F.7.81.41)
- ☐ ``getTypeDefinitionsViewIDs`` (F.7.81.42)
- ☐ ``getViewLinkExternalViewReferenceRefByName`` (F.7.81.43)
- ☐ ``getViewLinkExternalViewReferenceID`` (F.7.81.44)
- ☐ ``getViewLinkViewReferenceRefByID`` (F.7.81.45)
- ☐ ``getViewLinkViewReferenceRefByName`` (F.7.81.46)
- ☐ ``getViewLinkViewReferenceID`` (F.7.81.47)

Type definitions (EXTENDED)
~~~~~~~~~~~~~~~~~~~~~~~~~~~

- ☐ ``addComponentExternalTypeDefinitions`` (F.7.82.1)
- ☐ ``addEnumerationDefinition`` (F.7.82.2)
- ☐ ``addEnumerationDefinitionEnumeratedValue`` (F.7.82.3)
- ☐ ``addExternalTypeDefinitionsModeLink`` (F.7.82.4)
- ☐ ``addExternalTypeDefinitionsViewLink`` (F.7.82.5)
- ☐ ``addFieldDefinitionsEnumeratedValue`` (F.7.82.6)
- ☐ ``addTypeDefinitionsAddressBlockDefinition`` (F.7.82.7)
- ☐ ``addTypeDefinitionsBankDefinition`` (F.7.82.8)
- ☐ ``addTypeDefinitionsChoice`` (F.7.82.9)
- ☐ ``addTypeDefinitionsEnumerationDefinition`` (F.7.82.10)
- ☐ ``addTypeDefinitionsExternalTypeDefinitions`` (F.7.82.11)
- ☐ ``addTypeDefinitionsFieldAccessPolicyDefinition`` (F.7.82.12)
- ☐ ``addTypeDefinitionsFieldDefinition`` (F.7.82.13)
- ☐ ``addTypeDefinitionsMemoryMapDefinition`` (F.7.82.14)
- ☐ ``addTypeDefinitionsMemoryRemapDefinition`` (F.7.82.15)
- ☐ ``addTypeDefinitionsMode`` (F.7.82.16)
- ☐ ``addTypeDefinitionsRegisterDefinition`` (F.7.82.17)
- ☐ ``addTypeDefinitionsRegisterFileDefinition`` (F.7.82.18)
- ☐ ``addTypeDefinitionsResetType`` (F.7.82.19)
- ☐ ``addTypeDefinitionsView`` (F.7.82.20)
- ☐ ``removeAddressBlockDefinitionAddressUnitBits`` (F.7.82.21)
- ☐ ``removeBankDefinitionAddressUnitBits`` (F.7.82.22)
- ☐ ``removeComponentExternalTypeDefinitions`` (F.7.82.23)
- ☐ ``removeEnumerationDefinitionEnumeratedValue`` (F.7.82.24)
- ☐ ``removeExternalTypeDefinitionsModeLink`` (F.7.82.25)
- ☐ ``removeExternalTypeDefinitionsResetTypeLink`` (F.7.82.26)
- ☐ ``removeExternalTypeDefinitionsViewLink`` (F.7.82.27)
- ☐ ``removeFieldDefinitionEnumerationDefinitionRef`` (F.7.82.28)
- ☐ ``removeFieldDefinitionsEnumeratedValue`` (F.7.82.29)
- ☐ ``removeMemoryRemapDefinitionAddressUnitBits`` (F.7.82.30)
- ☐ ``removeRegisterFileDefinitionAddressUnitBits`` (F.7.82.31)
- ☐ ``removeTypeDefinitionsAddressBlockDefinition`` (F.7.82.32)
- ☐ ``removeTypeDefinitionsBankDefinition`` (F.7.82.33)
- ☐ ``removeTypeDefinitionsChoice`` (F.7.82.34)
- ☐ ``removeTypeDefinitionsEnumerationDefinition`` (F.7.82.35)
- ☐ ``removeTypeDefinitionsExternalTypeDefinitions`` (F.7.82.36)
- ☐ ``removeTypeDefinitionsFieldAccessPolicyDefinition`` (F.7.82.37)
- ☐ ``removeTypeDefinitionsFieldDefinition`` (F.7.82.38)
- ☐ ``removeTypeDefinitionsMemoryMapDefinition`` (F.7.82.39)
- ☐ ``removeTypeDefinitionsMemoryRemapDefinition`` (F.7.82.40)
- ☐ ``removeTypeDefinitionsMode`` (F.7.82.41)
- ☐ ``removeTypeDefinitionsRegisterDefinition`` (F.7.82.42)
- ☐ ``removeTypeDefinitionsRegisterFileDefinition`` (F.7.82.43)
- ☐ ``removeTypeDefinitionsResetType`` (F.7.82.44)
- ☐ ``removeTypeDefinitionsView`` (F.7.82.45)
- ☐ ``setAddressBlockDefinitionAddressUnitBits`` (F.7.82.46)
- ☐ ``setBankDefinitionAddressUnitBits`` (F.7.82.47)
- ☐ ``setEnumerationDefinitionWidth`` (F.7.82.48)
- ☐ ``setExternalTypeDefinitionsTypeDefinitionsRef`` (F.7.82.49)
- ☐ ``setMemoryRemapDefinitionAddressUnitBits`` (F.7.82.50)
- ☐ ``setModeLinkExternalModeReference`` (F.7.82.51)
- ☐ ``setModeLinkModeReference`` (F.7.82.52)
- ☐ ``setRegisterFileDefinitionAddressUnitBits`` (F.7.82.53)
- ☐ ``setResetTypeLinkExternalResetTypeReference`` (F.7.82.54)
- ☐ ``setResetTypeLinkResetTypeReference`` (F.7.82.55)
- ☐ ``setViewLinkExternalViewReference`` (F.7.82.56)
- ☐ ``setViewLinkViewReference`` (F.7.82.57)

Vector (BASE)
~~~~~~~~~~~~~

- ☑ ``getVectorIDs`` (F.7.83.1)
- ☑ ``getVectorLeftID`` (F.7.83.2)
- ☑ ``getVectorRange`` (F.7.83.3)
- ☑ ``getVectorRangeExpression`` (F.7.83.4)
- ☑ ``getVectorRightID`` (F.7.83.5)

Vector (EXTENDED)
~~~~~~~~~~~~~~~~~

- ☑ ``addVector`` (F.7.84.1)
- ☑ ``removeVector`` (F.7.84.2)

Vendor extensions (BASE)
~~~~~~~~~~~~~~~~~~~~~~~~

- ☑ ``getVendorExtensions`` (F.7.85.1)

Vendor extensions (EXTENDED)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- ☑ ``addVendorExtensions`` (F.7.86.1)
- ☑ ``removeVendorExtensions`` (F.7.86.2)
- ☑ ``setVendorExtensions`` (F.7.86.3)

View (BASE)
~~~~~~~~~~~

- ☑ ``getAbstractorInstanceViewNameRefByID`` (F.7.87.1)
- ☑ ``getViewComponentInstantiationRefByID`` (F.7.87.2) - Resolves typed local targets within the owning component, including registered parsed views; configured/external resolution remains planned.
- ☑ ``getViewComponentInstantiationRefByName`` (F.7.87.3) - uses generated source strings and the standard view handle.
- ☑ ``getViewDesignConfigurationInstantiationID`` (F.7.87.4) - Resolves typed local targets within the owning component, including registered parsed views; configured/external resolution remains planned.
- ☑ ``getViewDesignConfigurationInstantiationRefByID`` (F.7.87.5) - Resolves typed local targets within the owning component, including registered parsed views; configured/external resolution remains planned.
- ☑ ``getViewDesignConfigurationInstantiationRefByName`` (F.7.87.6) - uses generated source strings and the standard view handle.
- ☑ ``getViewDesignInstantiationRefByID`` (F.7.87.7) - Resolves typed local targets within the owning component, including registered parsed views; configured/external resolution remains planned.
- ☑ ``getViewDesignInstantiationRefByName`` (F.7.87.8) - uses generated source strings and the standard view handle.
- ☑ ``getViewEnvIdentifierIDs`` (F.7.87.9) - supports generated component/abstractor views, source values and ownership.
- ☑ ``getViewEnvIdentifiers`` (F.7.87.10) - supports generated component/abstractor views, source values and ownership.
- ☑ ``getViewRefByName`` (F.7.87.11) - and setViewRefValue across driver, wire, structured, domain, transactional and signal definitions.

View (EXTENDED)
~~~~~~~~~~~~~~~

- ☑ ``addViewEnvIdentifier`` (F.7.88.1) - supports generated component/abstractor views, source values and ownership.
- ☑ ``removeViewComponentInstantiationRef`` (F.7.88.2) - uses generated source strings and the standard view handle.
- ☑ ``removeViewDesignConfigurationInstantiationRef`` (F.7.88.3) - uses generated source strings and the standard view handle.
- ☑ ``removeViewDesignInstantiationRef`` (F.7.88.4) - uses generated source strings and the standard view handle.
- ☑ ``removeViewEnvIdentifier`` (F.7.88.5) - supports generated component/abstractor views, source values and ownership.
- ☑ ``setViewComponentInstantiationRef`` (F.7.88.6) - uses generated source strings and the standard view handle.
- ☑ ``setViewDesignConfigurationInstantiationRef`` (F.7.88.7) - uses generated source strings and the standard view handle.
- ☑ ``setViewDesignInstantiationRef`` (F.7.88.8) - uses generated source strings and the standard view handle.
- ☑ ``setViewRefValue`` (F.7.88.9) - across driver, wire, structured, domain, transactional and signal definitions.

Development and release automation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- ☑ Configure PR tests, distribution and documentation builds, and informational Codecov uploads.
- ☑ Configure release-please version/changelog PRs and verified uv trusted publication.
- ☑ Add Read the Docs configuration and contributor/release setup instructions.
- ☐ Activate external service integrations and verify hosted PR checks and automatic publication.

Release automation
~~~~~~~~~~~~~~~~~~

- ☑ Dispatch publication directly with the configured PyPI trusted publisher workflow identity.
- ☑ Synchronize and activate released Read the Docs versions before requesting their builds.

Abstraction root creation
~~~~~~~~~~~~~~~~~~~~~~~~~

- ☑ Create abstraction definitions with bus references and initial wire/transactional logical ports.
- ☑ Create abstractors with standard modes and exactly two named interfaces.
- ☑ Preserve registry identity and parent handles during abstraction creation and traversal.
- ☐ Complete semantic validation, including required groups for system-mode abstractors.

Abstractor structured model initialization
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- ☑ Initialize named sub-ports with registered parent identity during structured-port creation.
- ☑ Initialize structured type definitions with the supplied type name and preserve XML round trips.
- ☐ Validate structured type resolution and complete sub-port semantic constraints.

Logical port style conversion
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- ☑ Set the generated wire/transactional choice and preserve existing matching style content.
- ☑ Read styles, logical names, and packets after wire/transactional conversions.
- ☑ Preserve port identity, match metadata and independent packet content; reject invalid handles atomically.
- ☐ Complete recursive descendant handle invalidation and style semantic validation.

Abstraction constraint semantic validation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- ☑ SCR 12.3 NoOutputDriveModeConstraint for local IEEE 1685-2022 abstraction wire modes.
- ☑ SCR 12.4 NoInputLoadModeConstraint for local IEEE 1685-2022 abstraction wire modes.
- ☑ SCR 12.5 NoOutputLoadMirroredModeConstraint for local IEEE 1685-2022 abstraction wire modes.
- ☑ SCR 12.6 NoInputDriveMirroredModeConstraint for local IEEE 1685-2022 abstraction wire modes.
- ☑ SCR 12.8 ConstraintClockLogicalPortExists for local IEEE 1685-2022 abstraction wire modes.
- ☑ Return scoped rule coverage and XPath diagnostics without document mutation.
- ☐ Resolve inherited/configured definitions and complete the remaining Annex B semantic rules.

XML and CLI semantic validation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- ☑ Select offline schema validation with CLI --schema-root.
- ☑ Request scoped abstraction semantic checks with Python semantic=True or CLI --semantic.
- ☑ Run semantic checks after successful XSD validation and report unsupported roots explicitly.
- ☑ Return semantic rule IDs, XPath locations, source lines and checked-rule coverage.
- ☑ Validate all CLI inputs and return exit status 1 when any document fails.
- ☐ Extend semantic coverage to other roots, versions and inherited/configured documents.

Component constraint semantic validation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- ☑ Check SCR 12.1 output drive and SCR 12.2 input load constraints.
- ☑ Check SCR 12.7 timing references against component clockDriver and otherClockDriver names.
- ☑ Use the containing port name for unnamed clock drivers and another-port fallback when no drivers exist.
- ☑ Expose scoped component rules through Python XML validation and CLI --semantic.
- ☑ Preserve document content and return rule coverage with XPath and source diagnostics.
- ☐ Resolve configured views, driver ranges and expressions for SCR 12.9 single-bit validation.

TGI descendant handle invalidation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- ☑ Invalidate packet-field width and value handles when removing a field.
- ☑ Invalidate fields and expression descendants when removing a packet or logical port.
- ☑ Invalidate mode widths, constraint containers and timing handles when removing a mode.
- ☑ Invalidate replaced style descendants during wire/transactional conversion while preserving packets.
- ☑ Invalidate choice enumerations when removing their owning choice.
- ☑ Traverse generated model children without requiring prior ownership getters; preserve unaffected siblings.
- ☐ Audit every TGI remover and reference alias for complete session lifetime conformance.

Component child removal contracts
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- ☐ Complete component creation contracts, view ownership and remaining remover audits.

Component port view and clock creation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- ☐ Complete configured view references, expressions, name constraints and structured component ports.

Structured component port contracts
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- ☐ Resolve external structured types and complete sub-port semantic constraints.

View environment metadata
~~~~~~~~~~~~~~~~~~~~~~~~~

- ☑ Legacy getViewName helper supports generated views; not counted as a standard operation.
- ☐ Complete view reference resolution and parsed view parent ownership.

View source instantiation references
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- ☐ Resolve reference targets, validate configuration semantics and restore parsed view root ownership.

View reference API behavior
~~~~~~~~~~~~~~~~~~~~~~~~~~~

The component, design and design-configuration instantiation reference APIs
operate on a component view handle. Setters accept a nonempty source name;
name getters return that string or ``None`` when absent. Removers return
``True`` when a reference was present and ``False`` when already absent.
Changing or removing a reference preserves the referenced object and other
view fields. Invalid view handles raise ``INVALID_ID``; invalid setter values
raise ``INVALID_ARGUMENT`` before mutation. These source operations do not
resolve targets or establish configured-reference validity.

View target resolution
~~~~~~~~~~~~~~~~~~~~~~

- ☐ Complete configured reference semantics.

Parsed view ownership and target lifecycle
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- ☐ Complete configured/external reference semantics and unrestricted view discovery.

Registered component roots restore parsed view ownership by object identity.
Referenced targets are resolved within that component, separated by instantiation
type. Missing or ambiguous targets raise ``NOT_FOUND``; an unowned referenced
view raises ``INVALID_ID``. Absent references return ``None``. Removing the view
or its source reference preserves instantiation objects.

Generated viewRef source editing
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- ☑ Preserve source-reference identity and XML metadata through edits and reload.
- ☑ Reject unrelated handles and empty reference names before mutation.
- ☐ Resolve referenced views and complete configured applicability semantics.

ViewRef source APIs take a generated viewRef handle. Getters return the stored
name; setters accept a nonempty string and preserve the same element and xml:id.
Target existence and configured applicability are validated separately.

Generated component instantiation creation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- ☐ Support design-configuration instantiation placement on component instances.

Instantiation language and reference metadata
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- ☐ Resolve targets and complete configured language/reference semantics.

Language setters accept nonempty source strings, preserve existing strict
metadata and child identity, and reject invalid input before mutation. Reference
updates validate four nonempty VLNV parts and preserve configuration metadata.

Instantiation source name access and editing
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Name getters preserve explicit empty strings and whitespace; setters reject non-string values.
Source getters do not synthesize configured defaults.

Instantiation optional name removal
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Name removers clear the selected field and preserve sibling metadata.
Repeated removal succeeds; unrelated and stale handles are rejected.

Instantiation virtual state and language lifetime
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Preserve absent/false/true virtual source states, reject non-Boolean edits, restore parsed language ownership and invalidate removed language handles.

Instantiation local reference lifecycle
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Restore parsed reference ownership, validate schema lexical names, preserve siblings and invalidate removed handles. Target existence/configured resolution remain pending.

Generated clearbox reference paths
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Generated required location/slice/pathSegments preserve HDL source, parsed ownership and descendant invalidation. Clearbox target resolution remains pending.

Generated file builder metadata
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Generated file-builder source edits preserve child identity and metadata; removals invalidate child handles. Expression evaluation remains pending.

Build command source editing
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Build command/flags source editing preserves generated identity and append/extensions, supports standard buildCommand handles and legacy file handles, and invalidates removed expressions.

Build command target and replacement metadata
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Generated build-command target and replacement source editing with typed ownership, identity and removal lifetime; effective expression evaluation remains pending.

Clearbox type and driveable metadata
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Generated clearbox type enums and optional Boolean driveable edits validate inputs atomically and survive schema validation/XML reload.

Default file builder lifecycle
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Generated default builders validate standard file types, restore parsed ownership, preserve siblings and enforce typed removal lifetime.

File BASE source collections
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

BASE file collection getters preserve order/source values, return define value text, and restore parsed ownership without changing document content.

File BASE identity metadata
~~~~~~~~~~~~~~~~~~~~~~~~~~~

BASE file identity/source metadata traversal restores parsed child ownership and preserves optional states, lexical source and schema metadata.

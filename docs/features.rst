Feature implementation status
=============================

Checked entries have focused behavioral tests. They do not imply complete
category, transport, expression, or GUI conformance.

Bus definition — batch 1
------------------------

* ☑ Read the extended bus VLNV through ``getBusDefinitionExtendsRefByVLNV``.
* ☑ Set the extended bus reference using the four-part ``busDefVLNV`` input.
* ☑ Add a named bus choice with ordered enumeration values.
* ☑ Remove bus choices, invalidate their handles, and clear an empty choices container.
* ☑ Add system group names with the standard ``value`` argument and correct parent ownership.

Validation: ``tests/test_tgi_bus_definition.py`` covers invalid/wrong-type
handles, reference replacement, child ordering and removal, XSD validation,
and XML serialization/parsing of the resulting bus definitions.

Bus definition — batch 2
------------------------

* ☑ Set broadcast with the standard Boolean ``value`` contract.
* ☑ Set direct connection with the standard Boolean ``value`` contract.
* ☑ Set addressability with the standard Boolean ``value`` contract.
* ☑ Remove broadcast while distinguishing an absent element from ``false``.
* ☑ Remove and restore the extended bus reference.

Validation: Boolean type rejection leaves data unchanged; true/false values
and optional removals survive XSD-validated XML round trips. Invalid and
wrong-type handles are rejected by every operation.

Remaining work
--------------

* ☐ Complete remaining bus-definition TGI contracts and semantic consistency rules.
* ☐ Complete expression evaluation and inheritance compatibility.
* ☐ Complete abstraction definitions, components, designs, abstractors,
  type definitions, generator chains, design configurations, and catalogs.
* ☐ Complete common concepts, addressing, data visibility, and TGI transports.
* ☐ Implement planned older-standard editing and conversion capabilities.
* ☐ Implement GUI representations and their acceptance tests.

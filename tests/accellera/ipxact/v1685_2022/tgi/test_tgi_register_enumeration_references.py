"""Register enumeration-reference Annex contracts and scoped resolution."""

from collections.abc import Iterator
from inspect import signature

import pytest
from lxml import etree

from amal.eda.accellera.ipxact.v1685_2022 import tgi as root_api
from amal.eda.accellera.ipxact.v1685_2022.tgi import register as api
from amal.eda.accellera.ipxact.v1685_2022.tgi.component import _register_graph
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import TgiError, TgiFaultCode, get_handle, registry, resolve_handle
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import (
    AddressBlock,
    AddressUnitBits,
    BaseAddress,
    Component,
    ComponentType,
    ConfigurableLibraryRefType,
    EnumeratedValues,
    EnumeratedValueType,
    EnumerationDefinitions,
    ExternalTypeDefinitions,
    FieldDefinitions,
    FieldType,
    MemoryMaps,
    MemoryMapType,
    TypeDefinitions,
    UnsignedBitVectorExpression,
    UnsignedIntExpression,
    UnsignedLongintExpression,
    UnsignedPositiveIntExpression,
    UnsignedPositiveLongintExpression,
    UsageType,
)

_SCHEMA = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))
_LOCAL_VLNV = ("example.org", "types", "owner", "1.0")
_TARGET_VLNV = ("example.org", "types", "shared", "1.0")


@pytest.fixture(autouse=True)
def clear_registry() -> Iterator[None]:
    registry.clear()
    yield
    registry.clear()


def _enumeration(name: str) -> EnumerationDefinitions.EnumerationDefinition:
    return EnumerationDefinitions.EnumerationDefinition(
        name=name,
        width=UnsignedPositiveIntExpression(value="4"),
    )


def _holder(reference: EnumeratedValues.EnumerationDefinitionRef | None = None) -> EnumeratedValues:
    members = [reference] if reference is not None else []
    return EnumeratedValues(enumeration_definition_ref_or_enumerated_value=members)


def _field(holder: EnumeratedValues) -> FieldDefinitions.FieldDefinition:
    return FieldDefinitions.FieldDefinition(
        name="state",
        bit_width=UnsignedPositiveIntExpression(value="4"),
        enumerated_values=holder,
    )


def _owner(
    holder: EnumeratedValues,
    external: ExternalTypeDefinitions,
    vlnv: tuple[str, str, str, str] = _LOCAL_VLNV,
) -> TypeDefinitions:
    return TypeDefinitions(
        vendor=vlnv[0],
        library=vlnv[1],
        name=vlnv[2],
        version=vlnv[3],
        external_type_definitions=[external],
        field_definitions=FieldDefinitions(field_definition=[_field(holder)]),
    )


def _external(name: str, target: tuple[str, str, str, str] = _TARGET_VLNV) -> ExternalTypeDefinitions:
    return ExternalTypeDefinitions(
        name=name,
        type_definitions_ref=ConfigurableLibraryRefType(
            vendor=target[0], library=target[1], name=target[2], version=target[3]
        ),
    )


def test_exact_annex_signatures_exports_and_static_docs() -> None:
    operations = {
        "getEnumeratedValuesEnumerationDefinitionRefByExternalTypeDefID": (
            "F.7.73.34",
            ("enumeratedValuesID",),
            str | None,
        ),
        "getEnumeratedValuesEnumerationDefinitionRefByID": ("F.7.73.35", ("enumeratedValuesID",), str | None),
        "getEnumeratedValuesEnumerationDefinitionRefByName": ("F.7.73.36", ("enumeratedValuesID",), str | None),
        "getEnumeratedValuesEnumerationDefinitionRefID": ("F.7.73.37", ("enumeratedValuesID",), str | None),
        "setEnumeratedValuesEnumerationDefinitionRef": (
            "F.7.74.51",
            ("enumeratedValuesID", "enumerationDefinitionRef", "typeDefinitions"),
            bool,
        ),
    }
    for name, (section, parameters, _return) in operations.items():
        function = getattr(api, name)
        assert tuple(signature(function).parameters) == parameters
        assert name in api.__all__ and getattr(root_api, name) is function
        assert f"Section: {section}." in function.__doc__
        assert "Args:" in function.__doc__ and "Returns:" in function.__doc__


def test_reference_getters_scope_local_declaration_and_imported_definition() -> None:
    reference = EnumeratedValues.EnumerationDefinitionRef(value="state", type_definitions="sharedTypes")
    holder = _holder(reference)
    external = _external("sharedTypes")
    owner = _owner(holder, external)
    # Register just the root; this exercises ownership discovery for parsed trees.
    registry.register(owner, _LOCAL_VLNV)
    definition = _enumeration("state")
    target = TypeDefinitions(
        vendor=_TARGET_VLNV[0],
        library=_TARGET_VLNV[1],
        name=_TARGET_VLNV[2],
        version=_TARGET_VLNV[3],
        enumeration_definitions=EnumerationDefinitions(enumeration_definition=[definition]),
    )
    registry.register(target, _TARGET_VLNV)

    holder_id = get_handle(holder)
    assert api.getEnumeratedValuesEnumerationDefinitionRefByName(holder_id) == "state"
    assert api.getEnumeratedValuesEnumerationDefinitionRefID(holder_id) == get_handle(reference)
    assert api.getEnumeratedValuesEnumerationDefinitionRefByExternalTypeDefID(holder_id) == get_handle(external)
    assert api.getEnumeratedValuesEnumerationDefinitionRefByID(holder_id) == get_handle(definition)

    # A same-name declaration in a different registered document cannot shadow the local one.
    decoy = _external("sharedTypes", ("example.org", "types", "decoy", "1.0"))
    other_vlnv = ("example.org", "types", "otherOwner", "1.0")
    other = _owner(
        _holder(EnumeratedValues.EnumerationDefinitionRef(value="other", type_definitions="sharedTypes")),
        decoy,
        other_vlnv,
    )
    registry.register(other, other_vlnv)
    assert api.getEnumeratedValuesEnumerationDefinitionRefByExternalTypeDefID(holder_id) == get_handle(external)
    assert api.getEnumeratedValuesEnumerationDefinitionRefByID(holder_id) == get_handle(definition)


def test_reference_round_trip_with_external_type_definition() -> None:
    holder = _holder(EnumeratedValues.EnumerationDefinitionRef(value="state", type_definitions="sharedTypes"))
    owner = _owner(holder, _external("sharedTypes"))
    xml = XmlDocument.serializer().render(owner)
    parsed = XmlDocument.parser().from_string(xml, TypeDefinitions)
    parsed_xml = XmlDocument.serializer().render(parsed)
    assert parsed_xml == xml
    assert _SCHEMA.validate(etree.fromstring(xml.encode())), _SCHEMA.error_log
    parsed_holder = parsed.field_definitions.field_definition[0].enumerated_values
    assert parsed_holder is not None
    parsed_id = get_handle(parsed_holder)
    registry.register(parsed, _LOCAL_VLNV)
    definition = _enumeration("state")
    target = TypeDefinitions(
        vendor=_TARGET_VLNV[0],
        library=_TARGET_VLNV[1],
        name=_TARGET_VLNV[2],
        version=_TARGET_VLNV[3],
        enumeration_definitions=EnumerationDefinitions(enumeration_definition=[definition]),
    )
    registry.register(target, _TARGET_VLNV)
    assert api.getEnumeratedValuesEnumerationDefinitionRefByExternalTypeDefID(parsed_id) is not None
    assert api.getEnumeratedValuesEnumerationDefinitionRefByName(parsed_id) == "state"
    assert api.getEnumeratedValuesEnumerationDefinitionRefByID(parsed_id) == get_handle(definition)


def test_component_nested_type_definitions_are_the_local_reference_scope() -> None:
    holder = _holder(EnumeratedValues.EnumerationDefinitionRef(value="state", type_definitions="sharedTypes"))
    field = FieldType(
        name="state",
        bit_offset=UnsignedIntExpression(value="0"),
        choice=[UnsignedPositiveIntExpression(value="4"), holder],
    )
    register = AddressBlock.Register(
        name="control",
        address_offset=UnsignedLongintExpression(value="0"),
        choice=[UnsignedPositiveIntExpression(value="8"), field],
    )
    block = AddressBlock(
        name="registers",
        base_address=BaseAddress(value="0"),
        choice=[
            UnsignedPositiveLongintExpression(value="16"),
            UnsignedPositiveIntExpression(value="8"),
            UsageType.REGISTER,
            register,
        ],
    )
    component = Component(
        vendor="example.org",
        library="components",
        name="device",
        version="1.0",
        type_definitions=ComponentType.TypeDefinitions(external_type_definitions=[_external("sharedTypes")]),
        memory_maps=MemoryMaps(memory_map=[MemoryMapType(name="map", choice=[block, AddressUnitBits(value="8")])]),
    )
    registry.register(component, ("example.org", "components", "device", "1.0"))

    external = component.type_definitions.external_type_definitions[0]
    assert api.getEnumeratedValuesEnumerationDefinitionRefByExternalTypeDefID(get_handle(holder)) == get_handle(
        external
    )


@pytest.mark.parametrize("target_mode", ["missing", "duplicate", "wrong_edition"])
def test_declared_external_target_faults(target_mode: str) -> None:
    reference = EnumeratedValues.EnumerationDefinitionRef(value="state", type_definitions="sharedTypes")
    holder = _holder(reference)
    owner = _owner(holder, _external("sharedTypes"))
    registry.register(owner, _LOCAL_VLNV)
    target_vlnv = _TARGET_VLNV
    if target_mode == "duplicate":
        definitions = [_enumeration("state"), _enumeration("state")]
    else:
        definitions = [_enumeration("state")]
    target = TypeDefinitions(
        vendor=target_vlnv[0],
        library=target_vlnv[1],
        name=target_vlnv[2],
        version=target_vlnv[3],
        enumeration_definitions=EnumerationDefinitions(enumeration_definition=definitions),
    )
    if target_mode != "missing":
        if target_mode == "wrong_edition":
            registry.register(target, target_vlnv, standard="ipxact", schema_version="1685-2014")
        else:
            registry.register(target, target_vlnv)

    with pytest.raises(TgiError) as error:
        api.getEnumeratedValuesEnumerationDefinitionRefByID(get_handle(holder))
    assert error.value.fault_code == (
        TgiFaultCode.INVALID_ARGUMENT if target_mode == "duplicate" else TgiFaultCode.NOT_FOUND
    )


def test_missing_local_external_declaration_is_not_found() -> None:
    holder = _holder(EnumeratedValues.EnumerationDefinitionRef(value="state", type_definitions="missing"))
    with pytest.raises(TgiError) as error:
        api.getEnumeratedValuesEnumerationDefinitionRefByExternalTypeDefID(get_handle(holder))
    assert error.value.fault_code == TgiFaultCode.NOT_FOUND


def test_duplicate_local_external_declarations_are_ambiguous() -> None:
    reference = EnumeratedValues.EnumerationDefinitionRef(value="state", type_definitions="sharedTypes")
    holder = _holder(reference)
    owner = _owner(holder, _external("sharedTypes"))
    owner.external_type_definitions = [owner.external_type_definitions[0], _external("sharedTypes")]
    registry.register(owner, _LOCAL_VLNV)

    with pytest.raises(TgiError) as error:
        api.getEnumeratedValuesEnumerationDefinitionRefByExternalTypeDefID(get_handle(holder))
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT


@pytest.mark.parametrize(
    ("value", "type_definitions"),
    [("invalid name", "sharedTypes"), ("state", "invalid name")],
)
def test_getters_reject_malformed_stored_name_content(value: str, type_definitions: str) -> None:
    holder = _holder(EnumeratedValues.EnumerationDefinitionRef(value=value, type_definitions=type_definitions))

    with pytest.raises(TgiError) as error:
        api.getEnumeratedValuesEnumerationDefinitionRefByName(get_handle(holder))
    assert error.value.fault_code == TgiFaultCode.INVALID_ID
    with pytest.raises(TgiError) as error:
        api.getEnumeratedValuesEnumerationDefinitionRefByExternalTypeDefID(get_handle(holder))
    assert error.value.fault_code == TgiFaultCode.INVALID_ID


def test_absent_reference_and_wrong_handles() -> None:
    holder = _holder()
    holder_id = get_handle(holder)
    assert api.getEnumeratedValuesEnumerationDefinitionRefByExternalTypeDefID(holder_id) is None
    assert api.getEnumeratedValuesEnumerationDefinitionRefByID(holder_id) is None
    assert api.getEnumeratedValuesEnumerationDefinitionRefByName(holder_id) is None
    assert api.getEnumeratedValuesEnumerationDefinitionRefID(holder_id) is None
    for getter in (
        api.getEnumeratedValuesEnumerationDefinitionRefByExternalTypeDefID,
        api.getEnumeratedValuesEnumerationDefinitionRefByID,
        api.getEnumeratedValuesEnumerationDefinitionRefByName,
        api.getEnumeratedValuesEnumerationDefinitionRefID,
    ):
        with pytest.raises(TgiError) as error:
            getter(get_handle(object()))
        assert error.value.fault_code == TgiFaultCode.INVALID_ID


def test_setter_validates_atomically_and_replaces_inline_subtree() -> None:
    inline = EnumeratedValues(
        enumeration_definition_ref_or_enumerated_value=(
            # Tuple storage is retained when validation rejects the edit.
            EnumeratedValueType(name="idle", value=UnsignedBitVectorExpression(value="0")),
        )
    )
    _register_graph(inline)
    original_sequence = inline.enumeration_definition_ref_or_enumerated_value
    value = original_sequence[0]
    value_id = get_handle(value)
    expression_id = get_handle(value.value)
    holder_id = get_handle(inline)

    with pytest.raises(TgiError) as error:
        api.setEnumeratedValuesEnumerationDefinitionRef(holder_id, "invalid name", "types")
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert inline.enumeration_definition_ref_or_enumerated_value is original_sequence
    assert resolve_handle(value_id) is value and resolve_handle(expression_id) is value.value
    with pytest.raises(TgiError) as error:
        api.setEnumeratedValuesEnumerationDefinitionRef(holder_id, "state", "invalid name")
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    with pytest.raises(TgiError) as error:
        api.setEnumeratedValuesEnumerationDefinitionRef(get_handle(object()), "invalid name", "types")
    assert error.value.fault_code == TgiFaultCode.INVALID_ID
    assert inline.enumeration_definition_ref_or_enumerated_value is original_sequence

    assert api.setEnumeratedValuesEnumerationDefinitionRef(holder_id, "state", "sharedTypes") is True
    assert len(inline.enumeration_definition_ref_or_enumerated_value) == 1
    reference = inline.enumeration_definition_ref_or_enumerated_value[0]
    assert isinstance(reference, EnumeratedValues.EnumerationDefinitionRef)
    assert reference.value == "state" and reference.type_definitions == "sharedTypes"
    assert resolve_handle(value_id) is None and resolve_handle(expression_id) is None
    assert api.getEnumeratedValuesEnumerationDefinitionRefID(holder_id) == get_handle(reference)


def test_setter_updates_existing_reference_in_place() -> None:
    reference = EnumeratedValues.EnumerationDefinitionRef(value="old", type_definitions="oldTypes")
    holder = _holder(reference)
    reference_id = get_handle(reference)
    holder_id = get_handle(holder)

    assert api.setEnumeratedValuesEnumerationDefinitionRef(holder_id, "new", "newTypes") is True
    assert api.getEnumeratedValuesEnumerationDefinitionRefID(holder_id) == reference_id
    assert resolve_handle(reference_id) is reference
    assert reference.value == "new" and reference.type_definitions == "newTypes"

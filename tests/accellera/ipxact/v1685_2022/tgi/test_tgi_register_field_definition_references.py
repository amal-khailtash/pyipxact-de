"""Register field-definition reference contracts from IEEE 1685-2022 Annex F."""

from collections.abc import Iterator
from inspect import getdoc, signature

import pytest
from lxml import etree

from amal.eda.accellera.ipxact.v1685_2022 import tgi as root_api
from amal.eda.accellera.ipxact.v1685_2022.tgi import register as api
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import (
    TgiError,
    TgiFaultCode,
    get_handle,
    registry,
    resolve_handle,
)
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022.address_block import AddressBlock
from org.accellera.ipxact.v1685_2022.address_block_type import AddressBlockType
from org.accellera.ipxact.v1685_2022.address_unit_bits import AddressUnitBits
from org.accellera.ipxact.v1685_2022.base_address import BaseAddress
from org.accellera.ipxact.v1685_2022.component import Component
from org.accellera.ipxact.v1685_2022.component_type import ComponentType
from org.accellera.ipxact.v1685_2022.configurable_library_ref_type import ConfigurableLibraryRefType
from org.accellera.ipxact.v1685_2022.external_type_definitions import ExternalTypeDefinitions
from org.accellera.ipxact.v1685_2022.field_definitions import FieldDefinitions
from org.accellera.ipxact.v1685_2022.field_ref import FieldRef
from org.accellera.ipxact.v1685_2022.field_type import FieldType
from org.accellera.ipxact.v1685_2022.memory_map_type import MemoryMapType
from org.accellera.ipxact.v1685_2022.memory_maps import MemoryMaps
from org.accellera.ipxact.v1685_2022.parameters import Parameters
from org.accellera.ipxact.v1685_2022.reset import Reset
from org.accellera.ipxact.v1685_2022.type_definitions import TypeDefinitions
from org.accellera.ipxact.v1685_2022.unsigned_bit_vector_expression import UnsignedBitVectorExpression
from org.accellera.ipxact.v1685_2022.unsigned_int_expression import UnsignedIntExpression
from org.accellera.ipxact.v1685_2022.unsigned_longint_expression import UnsignedLongintExpression
from org.accellera.ipxact.v1685_2022.unsigned_positive_int_expression import UnsignedPositiveIntExpression
from org.accellera.ipxact.v1685_2022.unsigned_positive_longint_expression import UnsignedPositiveLongintExpression
from org.accellera.ipxact.v1685_2022.usage_type import UsageType
from org.accellera.ipxact.v1685_2022.vendor_extensions import VendorExtensions

_SCHEMA = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))
_LOCAL_VLNV = ("example.org", "components", "device", "1.0")
_TARGET_VLNV = ("example.org", "types", "shared", "1.0")


@pytest.fixture(autouse=True)
def clear_registry() -> Iterator[None]:
    registry.clear()
    yield
    registry.clear()


def _external(name: str = "sharedTypes", target: tuple[str, str, str, str] = _TARGET_VLNV):
    return ExternalTypeDefinitions(
        name=name,
        type_definitions_ref=ConfigurableLibraryRefType(
            vendor=target[0], library=target[1], name=target[2], version=target[3]
        ),
    )


def _field(choice: list[object] | tuple[object, ...]) -> FieldType:
    return FieldType(name="status", bit_offset=UnsignedIntExpression(value="0"), choice=choice)


def _component(field: FieldType, declarations: list[ExternalTypeDefinitions] | None = None) -> Component:
    register = AddressBlockType.Register(
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
    return Component(
        vendor=_LOCAL_VLNV[0],
        library=_LOCAL_VLNV[1],
        name=_LOCAL_VLNV[2],
        version=_LOCAL_VLNV[3],
        type_definitions=ComponentType.TypeDefinitions(external_type_definitions=declarations or []),
        memory_maps=MemoryMaps(memory_map=[MemoryMapType(name="map", choice=[block, AddressUnitBits(value="8")])]),
    )


def _target(names: tuple[str, ...] = ("sharedField",)) -> TypeDefinitions:
    return TypeDefinitions(
        vendor=_TARGET_VLNV[0],
        library=_TARGET_VLNV[1],
        name=_TARGET_VLNV[2],
        version=_TARGET_VLNV[3],
        field_definitions=FieldDefinitions(
            field_definition=[
                FieldDefinitions.FieldDefinition(
                    name=name,
                    bit_width=UnsignedPositiveIntExpression(value="8"),
                )
                for name in names
            ]
        ),
    )


def _register_component(field: FieldType, declarations: list[ExternalTypeDefinitions] | None = None) -> Component:
    component = _component(field, declarations if declarations is not None else [_external()])
    registry.register(component, _LOCAL_VLNV)
    return component


def _field_from_component(component: Component) -> FieldType:
    block = component.memory_maps.memory_map[0].choice[0]
    register = block.choice[3]
    return register.choice[1]


def _set_ref(field_id: str, name: str = "sharedField", external_name: str = "sharedTypes") -> bool:
    return api.setRegisterFieldFieldDefinitionRef(field_id, name, external_name)


def test_public_operations_match_annex_signatures_exports_and_docs() -> None:
    operations = {
        "getRegisterFieldFieldDefinitionRefByExternalTypeDefID": (
            "F.7.73.57",
            ("registerFieldID",),
            str | None,
        ),
        "getRegisterFieldFieldDefinitionRefByID": ("F.7.73.58", ("registerFieldID",), str | None),
        "getRegisterFieldFieldDefinitionRefByName": ("F.7.73.59", ("registerFieldID",), str | None),
        "getRegisterFieldFieldDefinitionRefID": ("F.7.73.60", ("registerFieldID",), str | None),
        "setRegisterFieldFieldDefinitionRef": (
            "F.7.74.61",
            ("registerFieldID", "value", "typeDefinitions"),
            bool,
        ),
    }
    for name, (section, parameters, result) in operations.items():
        operation = getattr(api, name)
        assert getattr(root_api, name) is operation
        assert name in api.__all__ and name in root_api.__all__
        operation_signature = signature(operation)
        assert tuple(operation_signature.parameters) == parameters
        assert all(parameter.annotation is str for parameter in operation_signature.parameters.values())
        assert operation_signature.return_annotation == result
        docstring = getdoc(operation)
        assert docstring is not None
        assert f"Section: {section}." in docstring
        assert "Args:" in docstring and "Returns:" in docstring


def test_getters_resolve_import_in_parsed_component_scope() -> None:
    reference = FieldType.FieldDefinitionRef(value="sharedField", type_definitions="sharedTypes")
    component = _component(_field([reference]), [_external()])
    xml = XmlDocument.serializer().render(component)
    parsed = XmlDocument.parser().from_string(xml, Component)
    registry.register(parsed, _LOCAL_VLNV)
    target = _target()
    registry.register(target, _TARGET_VLNV)

    field = _field_from_component(parsed)
    field_id = get_handle(field)
    reference_id = get_handle(reference := field.choice[0])
    external_id = get_handle(parsed.type_definitions.external_type_definitions[0])
    definition = target.field_definitions.field_definition[0]

    assert api.getRegisterFieldFieldDefinitionRefByName(field_id) == "sharedField"
    assert api.getRegisterFieldFieldDefinitionRefID(field_id) == reference_id
    assert api.getRegisterFieldFieldDefinitionRefByExternalTypeDefID(field_id) == external_id
    assert api.getRegisterFieldFieldDefinitionRefByID(field_id) == get_handle(definition)
    assert reference.value == "sharedField"

    decoy_vlnv = ("example.org", "components", "decoy", "1.0")
    decoy_field = _field([FieldType.FieldDefinitionRef(value="decoyField", type_definitions="sharedTypes")])
    decoy = _component(
        decoy_field,
        [_external(target=("example.org", "types", "decoy", "1.0"))],
    )
    decoy.vendor, decoy.library, decoy.name, decoy.version = decoy_vlnv
    registry.register(decoy, decoy_vlnv)
    assert api.getRegisterFieldFieldDefinitionRefByID(field_id) == get_handle(definition)


@pytest.mark.parametrize(
    ("target_mode", "fault"),
    [
        ("unregistered", TgiFaultCode.NOT_FOUND),
        ("missing_name", TgiFaultCode.NOT_FOUND),
        ("duplicate_name", TgiFaultCode.INVALID_ARGUMENT),
    ],
)
def test_target_resolution_reports_unavailable_and_ambiguous_definitions(target_mode: str, fault: str) -> None:
    field = _field([FieldType.FieldDefinitionRef(value="sharedField", type_definitions="sharedTypes")])
    _register_component(field)
    if target_mode == "missing_name":
        registry.register(_target(("otherField",)), _TARGET_VLNV)
    elif target_mode == "duplicate_name":
        registry.register(_target(("sharedField", "sharedField")), _TARGET_VLNV)

    with pytest.raises(TgiError) as error:
        api.getRegisterFieldFieldDefinitionRefByID(get_handle(field))
    assert error.value.fault_code == fault


def test_invalid_register_field_ids_fault_as_invalid_id() -> None:
    wrong_model_id = get_handle(UnsignedPositiveIntExpression(value="8"))
    for bad_id in (None, [], "missing-handle", wrong_model_id):
        for operation in (
            api.getRegisterFieldFieldDefinitionRefByExternalTypeDefID,
            api.getRegisterFieldFieldDefinitionRefByID,
            api.getRegisterFieldFieldDefinitionRefByName,
            api.getRegisterFieldFieldDefinitionRefID,
        ):
            with pytest.raises(TgiError) as error:
                operation(bad_id)
            assert error.value.fault_code == TgiFaultCode.INVALID_ID
        with pytest.raises(TgiError) as error:
            api.setRegisterFieldFieldDefinitionRef(bad_id, "sharedField", "sharedTypes")
        assert error.value.fault_code == TgiFaultCode.INVALID_ID


def test_inline_field_getters_are_optional_and_setter_allows_deferred_reference() -> None:
    field = _field([UnsignedPositiveIntExpression(value="8")])
    _register_component(field)
    field_id = get_handle(field)
    assert api.getRegisterFieldFieldDefinitionRefByExternalTypeDefID(field_id) is None
    assert api.getRegisterFieldFieldDefinitionRefByID(field_id) is None
    assert api.getRegisterFieldFieldDefinitionRefByName(field_id) is None
    assert api.getRegisterFieldFieldDefinitionRefID(field_id) is None

    assert _set_ref(field_id, "notRegisteredYet", "laterTypes") is True
    assert field.choice == [FieldType.FieldDefinitionRef(value="notRegisteredYet", type_definitions="laterTypes")]
    assert api.getRegisterFieldFieldDefinitionRefByName(field_id) == "notRegisteredYet"


def test_external_type_definition_getter_requires_a_scoped_local_declaration() -> None:
    field = _field([FieldType.FieldDefinitionRef(value="sharedField", type_definitions="missingTypes")])
    _register_component(field, declarations=[])

    with pytest.raises(TgiError) as error:
        api.getRegisterFieldFieldDefinitionRefByExternalTypeDefID(get_handle(field))
    assert error.value.fault_code == TgiFaultCode.NOT_FOUND


@pytest.mark.parametrize(
    ("name", "external_name"),
    [("", "sharedTypes"), ("bad Name", "sharedTypes"), ("sharedField", "bad/name"), ("sharedField", "")],
)
def test_invalid_setter_names_leave_tuple_choice_unchanged(name: str, external_name: str) -> None:
    width = UnsignedPositiveIntExpression(value="8")
    field = _field(("Original_Type", width, False))
    _register_component(field)
    field.choice = original = tuple(field.choice)
    field_id = get_handle(field)

    with pytest.raises(TgiError) as error:
        _set_ref(field_id, name, external_name)
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert field.choice is original
    assert resolve_handle(get_handle(width)) is width


def test_setter_replaces_inline_choice_invalidates_owned_nodes_and_preserves_metadata() -> None:
    reset_value = UnsignedBitVectorExpression(value="0")
    resets = FieldType.Resets(reset=[Reset(value=reset_value)])
    width = UnsignedPositiveIntExpression(value="8")
    field = _field(["Inline_Type", width, False, resets])
    field.access_handles = FieldType.AccessHandles()
    field.array = FieldType.Array()
    field.parameters = Parameters()
    field.vendor_extensions = VendorExtensions()
    _register_component(field)
    field_id = get_handle(field)
    width_id = get_handle(width)
    resets_id = get_handle(resets)
    reset_value_id = get_handle(reset_value)
    type_identifier_id = get_handle("Inline_Type")
    false_id = get_handle(False)
    metadata = (field.access_handles, field.array, field.parameters, field.vendor_extensions)

    assert _set_ref(field_id) is True
    assert len(field.choice) == 1 and isinstance(field.choice[0], FieldType.FieldDefinitionRef)
    assert field.access_handles is metadata[0]
    assert field.array is metadata[1]
    assert field.parameters is metadata[2]
    assert field.vendor_extensions is metadata[3]
    assert all(resolve_handle(handle) is None for handle in (width_id, resets_id, reset_value_id))
    assert resolve_handle(type_identifier_id) == "Inline_Type"
    assert resolve_handle(false_id) is False


def test_setter_replaces_alias_and_invalidates_alias_descendants() -> None:
    field_ref = FieldRef(field_ref="oldField")
    alias = FieldType.AliasOf(field_ref=field_ref)
    field = _field(("Alias_Type", alias))
    _register_component(field)
    field_id = get_handle(field)
    alias_id = get_handle(alias)
    field_ref_id = get_handle(field_ref)

    assert _set_ref(field_id) is True
    assert len(field.choice) == 1 and isinstance(field.choice[0], FieldType.FieldDefinitionRef)
    assert resolve_handle(alias_id) is None
    assert resolve_handle(field_ref_id) is None


def test_setter_updates_reference_node_and_handle_in_place() -> None:
    reference = FieldType.FieldDefinitionRef(value="sharedField", type_definitions="sharedTypes")
    field = _field([reference])
    field_id = get_handle(field)
    reference_id = get_handle(reference)

    assert _set_ref(field_id, "updatedField", "newImport") is True
    assert field.choice == [reference]
    assert field.choice[0] is reference
    assert reference.value == "updatedField" and reference.type_definitions == "newImport"
    assert api.getRegisterFieldFieldDefinitionRefID(field_id) == reference_id


def test_malformed_stored_reference_names_fault_as_invalid_id() -> None:
    reference = FieldType.FieldDefinitionRef(value="bad Name", type_definitions="sharedTypes")
    field = _field([reference])
    with pytest.raises(TgiError) as error:
        api.getRegisterFieldFieldDefinitionRefByName(get_handle(field))
    assert error.value.fault_code == TgiFaultCode.INVALID_ID


def test_reference_round_trip_satisfies_the_2022_schema() -> None:
    field = _field([UnsignedPositiveIntExpression(value="8")])
    component = _register_component(field)
    assert _set_ref(get_handle(field)) is True

    xml = XmlDocument.serializer().render(component)
    assert _SCHEMA.validate(etree.fromstring(xml.encode())), _SCHEMA.error_log
    parsed = XmlDocument.parser().from_string(xml, Component)
    reparsed_xml = XmlDocument.serializer().render(parsed)
    assert reparsed_xml == xml
    parsed_field = _field_from_component(parsed)
    assert api.getRegisterFieldFieldDefinitionRefByName(get_handle(parsed_field)) == "sharedField"

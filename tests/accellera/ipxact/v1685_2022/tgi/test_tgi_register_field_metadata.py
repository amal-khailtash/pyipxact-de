"""Register field typeIdentifier and volatility TGI contracts."""

from collections.abc import Iterator

import pytest
from lxml import etree

from amal.eda.accellera.ipxact.v1685_2022.tgi import register as api
from amal.eda.accellera.ipxact.v1685_2022.tgi.component import _register_graph
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import (
    TgiError,
    TgiFaultCode,
    get_handle,
    get_parent_info,
    registry,
    resolve_handle,
)
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022.address_block import AddressBlock
from org.accellera.ipxact.v1685_2022.address_block_type import AddressBlockType
from org.accellera.ipxact.v1685_2022.address_unit_bits import AddressUnitBits
from org.accellera.ipxact.v1685_2022.alternate_registers import AlternateRegisters
from org.accellera.ipxact.v1685_2022.base_address import BaseAddress
from org.accellera.ipxact.v1685_2022.component import Component
from org.accellera.ipxact.v1685_2022.enumerated_values import EnumeratedValues
from org.accellera.ipxact.v1685_2022.field_ref import FieldRef
from org.accellera.ipxact.v1685_2022.field_type import FieldType
from org.accellera.ipxact.v1685_2022.memory_map_type import MemoryMapType
from org.accellera.ipxact.v1685_2022.memory_maps import MemoryMaps
from org.accellera.ipxact.v1685_2022.register_definitions import RegisterDefinitions
from org.accellera.ipxact.v1685_2022.register_file import RegisterFile
from org.accellera.ipxact.v1685_2022.register_file_definitions import RegisterFileDefinitions
from org.accellera.ipxact.v1685_2022.reset import Reset
from org.accellera.ipxact.v1685_2022.unsigned_bit_vector_expression import UnsignedBitVectorExpression
from org.accellera.ipxact.v1685_2022.unsigned_int_expression import UnsignedIntExpression
from org.accellera.ipxact.v1685_2022.unsigned_longint_expression import UnsignedLongintExpression
from org.accellera.ipxact.v1685_2022.unsigned_positive_int_expression import UnsignedPositiveIntExpression
from org.accellera.ipxact.v1685_2022.unsigned_positive_longint_expression import UnsignedPositiveLongintExpression
from org.accellera.ipxact.v1685_2022.usage_type import UsageType

_SCHEMA = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))
type _RegisterType = (
    type[AddressBlockType.Register]
    | type[RegisterFile.Register]
    | type[RegisterFileDefinitions.RegisterFileDefinition.Register]
)
_REGISTER_TYPES: tuple[_RegisterType, ...] = (
    AddressBlockType.Register,
    RegisterFile.Register,
    RegisterFileDefinitions.RegisterFileDefinition.Register,
)


@pytest.fixture(autouse=True)
def clean_registry() -> Iterator[None]:
    registry.clear()
    yield
    registry.clear()


def _field(choice: tuple[object, ...] | list[object]) -> FieldType:
    return FieldType(name="status", bit_offset=UnsignedIntExpression(value="0"), choice=choice)


def _owned_field(register_type: _RegisterType, field: FieldType) -> tuple[object, FieldType]:
    register = register_type(
        name="control",
        address_offset=UnsignedLongintExpression(value="0"),
        choice=[UnsignedPositiveIntExpression(value="32"), field],
    )
    _register_graph(register)
    return register, field


@pytest.mark.parametrize("register_type", _REGISTER_TYPES)
def test_inline_field_metadata_get_set_remove_for_register_variants(register_type: _RegisterType) -> None:
    width = UnsignedPositiveIntExpression(value="8")
    field = _field(["Initial_Type", width, False])
    _, field = _owned_field(register_type, field)
    field_id = get_handle(field)

    assert api.getRegisterFieldTypeIdentifier(field_id) == "Initial_Type"
    assert api.getRegisterFieldVolatility(field_id) is False
    assert api.setRegisterFieldTypeIdentifier(regFieldID=field_id, typeIdentifier="Updated_Type") is True
    assert api.getRegisterFieldTypeIdentifier(field_id) == "Updated_Type"
    assert api.setRegisterFieldVolatility(regFieldID=field_id, volatile=True) is True
    assert api.getRegisterFieldVolatility(field_id) is True
    assert api.removeRegisterFieldTypeIdentifier(field_id) is True
    assert api.getRegisterFieldTypeIdentifier(field_id) is None
    assert api.removeRegisterFieldVolatility(field_id) is True
    assert api.getRegisterFieldVolatility(field_id) is False
    assert api.removeRegisterFieldTypeIdentifier(field_id) is False
    assert api.removeRegisterFieldVolatility(field_id) is False
    assert field.choice == [width]


def test_absent_inline_volatility_has_false_default_and_removal_is_false() -> None:
    field = _field([UnsignedPositiveIntExpression(value="8")])
    field_id = get_handle(field)

    assert api.getRegisterFieldVolatility(field_id) is False
    assert api.removeRegisterFieldVolatility(field_id) is False
    assert api.setRegisterFieldVolatility(field_id, volatile=False) is True
    assert api.getRegisterFieldVolatility(field_id) is False
    assert field.choice == [field.choice[0], False]


def test_type_identifier_is_allowed_for_alias_but_volatility_is_not() -> None:
    alias = FieldType.AliasOf(field_ref=FieldRef(field_ref="sharedField"))
    field = _field([alias])
    field_id = get_handle(field)
    alias_id = get_handle(alias)

    assert api.getRegisterFieldTypeIdentifier(field_id) is None
    assert api.getRegisterFieldVolatility(field_id) is None
    assert api.removeRegisterFieldTypeIdentifier(field_id) is False
    assert api.removeRegisterFieldVolatility(field_id) is False
    assert api.setRegisterFieldTypeIdentifier(regFieldID=field_id, typeIdentifier="Alias_Type") is True
    assert api.getRegisterFieldTypeIdentifier(field_id) == "Alias_Type"
    assert field.choice == ["Alias_Type", alias]
    assert resolve_handle(alias_id) is alias
    with pytest.raises(TgiError) as error:
        api.setRegisterFieldVolatility(regFieldID=field_id, volatile=True)
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert field.choice == ["Alias_Type", alias]


def test_field_definition_reference_metadata_getters_and_removers_are_neutral() -> None:
    reference = FieldType.FieldDefinitionRef(value="sharedField", type_definitions="sharedTypes")
    field = _field([reference])
    field_id = get_handle(field)
    reference_id = get_handle(reference)

    assert api.getRegisterFieldTypeIdentifier(field_id) is None
    assert api.getRegisterFieldVolatility(field_id) is None
    assert api.removeRegisterFieldTypeIdentifier(field_id) is False
    assert api.removeRegisterFieldVolatility(field_id) is False
    for operation, args in (
        (api.setRegisterFieldTypeIdentifier, (field_id, "Local_Type")),
        (api.setRegisterFieldVolatility, (field_id, True)),
    ):
        with pytest.raises(TgiError) as error:
            operation(*args)
        assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
        assert field.choice == [reference]
        assert resolve_handle(reference_id) is reference


@pytest.mark.parametrize("invalid_name", ("", "not a Name", "bad/name", 12))
def test_invalid_type_identifier_is_rejected_without_mutating_choice(invalid_name: object) -> None:
    width = UnsignedPositiveIntExpression(value="8")
    field = _field([width])
    field.choice = (width,)
    original = field.choice

    with pytest.raises(TgiError) as error:
        api.setRegisterFieldTypeIdentifier(regFieldID=get_handle(field), typeIdentifier=invalid_name)
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert field.choice is original
    assert field.choice == (width,)


@pytest.mark.parametrize("invalid_value", (0, 1, "true", None))
def test_invalid_field_volatility_is_rejected_atomically(invalid_value: object) -> None:
    width = UnsignedPositiveIntExpression(value="8")
    field = _field((width, False))
    original = field.choice

    with pytest.raises(TgiError) as error:
        api.setRegisterFieldVolatility(regFieldID=get_handle(field), volatile=invalid_value)
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert field.choice is original
    assert field.choice == (width, False)


def test_tuple_choices_normalize_and_preserve_sibling_fields_and_scalar_handles() -> None:
    width = UnsignedPositiveIntExpression(value="8")
    first = _field((width,))
    sibling = _field((UnsignedPositiveIntExpression(value="1"), True))
    first_id = get_handle(first)
    sibling_id = get_handle(sibling)
    true_id = get_handle(True)

    assert api.setRegisterFieldTypeIdentifier(regFieldID=first_id, typeIdentifier="Control_Type") is True
    assert api.setRegisterFieldVolatility(regFieldID=first_id, volatile=False) is True
    assert first.choice == ["Control_Type", width, False]
    assert api.getRegisterFieldVolatility(sibling_id) is True
    assert sibling.choice[1] is True
    assert resolve_handle(true_id) is True


def test_metadata_edits_preserve_later_choice_siblings_and_order() -> None:
    width = UnsignedPositiveIntExpression(value="8")
    resets = FieldType.Resets(reset=[Reset(value=UnsignedBitVectorExpression(value="0"))])
    enumerated_values = EnumeratedValues(
        enumeration_definition_ref_or_enumerated_value=[
            EnumeratedValues.EnumerationDefinitionRef(value="sharedEnum", type_definitions="sharedTypes")
        ]
    )
    field = _field([width, False, resets, enumerated_values])
    field_id = get_handle(field)

    assert api.setRegisterFieldTypeIdentifier(regFieldID=field_id, typeIdentifier="Status_Type") is True
    assert api.setRegisterFieldVolatility(regFieldID=field_id, volatile=True) is True
    assert field.choice == ["Status_Type", width, True, resets, enumerated_values]
    assert field.choice[1] is width and field.choice[3] is resets and field.choice[4] is enumerated_values
    assert api.removeRegisterFieldVolatility(field_id) is True
    assert field.choice == ["Status_Type", width, resets, enumerated_values]


def test_duplicate_field_metadata_values_are_rejected_without_changes() -> None:
    duplicate_type = _field(["First_Type", "Second_Type", UnsignedPositiveIntExpression(value="8")])
    duplicate_type_id = get_handle(duplicate_type)
    with pytest.raises(TgiError) as error:
        api.getRegisterFieldTypeIdentifier(duplicate_type_id)
    assert error.value.fault_code == TgiFaultCode.INVALID_ID
    with pytest.raises(TgiError):
        api.removeRegisterFieldTypeIdentifier(duplicate_type_id)
    assert duplicate_type.choice[:2] == ["First_Type", "Second_Type"]

    duplicate_volatile = _field([UnsignedPositiveIntExpression(value="8"), False, True])
    duplicate_volatile_id = get_handle(duplicate_volatile)
    for operation, args in (
        (api.getRegisterFieldVolatility, (duplicate_volatile_id,)),
        (api.setRegisterFieldVolatility, (duplicate_volatile_id, False)),
        (api.removeRegisterFieldVolatility, (duplicate_volatile_id,)),
    ):
        with pytest.raises(TgiError) as error:
            operation(*args)
        assert error.value.fault_code == TgiFaultCode.INVALID_ID
        assert duplicate_volatile.choice[1:] == [False, True]


def test_invalid_field_handles_are_rejected_by_all_six_operations() -> None:
    _, register_field = _owned_field(
        AddressBlockType.Register,
        _field([UnsignedPositiveIntExpression(value="8")]),
    )
    register_id = get_handle(register_field)
    wrong_id = get_handle(UnsignedPositiveIntExpression(value="8"))
    operations = (
        (api.getRegisterFieldTypeIdentifier, ()),
        (api.getRegisterFieldVolatility, ()),
        (api.removeRegisterFieldTypeIdentifier, ()),
        (api.removeRegisterFieldVolatility, ()),
        (api.setRegisterFieldTypeIdentifier, ("Valid_Type",)),
        (api.setRegisterFieldVolatility, (True,)),
    )
    for operation, tail in operations:
        for invalid_id in (wrong_id, "hdeadbeef"):
            with pytest.raises(TgiError) as error:
                operation(invalid_id, *tail)
            assert error.value.fault_code == TgiFaultCode.INVALID_ID
    assert api.getRegisterFieldTypeIdentifier(register_id) is None


def test_detached_alternate_and_register_definition_fields_are_supported() -> None:
    detached = _field(["Detached_Type", UnsignedPositiveIntExpression(value="1")])
    alternate_field = _field(["Alternate_Type", UnsignedPositiveIntExpression(value="1")])
    alternate = AlternateRegisters.AlternateRegister(name="alternate", field_value=[alternate_field])
    definition_field = _field(["Definition_Type", UnsignedPositiveIntExpression(value="1")])
    definition = RegisterDefinitions.RegisterDefinition(
        name="sharedRegister",
        size=UnsignedPositiveIntExpression(value="32"),
        field_value=[definition_field],
    )
    _register_graph(alternate)
    _register_graph(definition)

    for field, expected in (
        (detached, "Detached_Type"),
        (alternate_field, "Alternate_Type"),
        (definition_field, "Definition_Type"),
    ):
        assert api.getRegisterFieldTypeIdentifier(get_handle(field)) == expected


def test_schema_valid_round_trip_retains_parsed_field_ownership() -> None:
    field = _field(["Status_Type", UnsignedPositiveIntExpression(value="8"), True])
    register = AddressBlock.Register(
        name="control",
        address_offset=UnsignedLongintExpression(value="0"),
        choice=[UnsignedPositiveIntExpression(value="32"), field],
    )
    block = AddressBlock(
        name="registers",
        base_address=BaseAddress(value="0"),
        choice=[
            UnsignedPositiveLongintExpression(value="256"),
            UnsignedPositiveIntExpression(value="32"),
            UsageType.REGISTER,
            register,
        ],
    )
    component = Component(
        vendor="test",
        library="library",
        name="registerFieldMetadata",
        version="1",
        memory_maps=MemoryMaps(
            memory_map=[MemoryMapType(name="peripheral", choice=[block, AddressUnitBits(value="8")])]
        ),
    )
    xml = XmlDocument.serializer().render(component)
    _SCHEMA.assertValid(etree.fromstring(xml.encode()))
    parsed = XmlDocument.parser().from_string(xml, Component)
    _register_graph(parsed)
    block_choice = parsed.memory_maps.memory_map[0].choice[0].choice
    parsed_register = next(child for child in block_choice if isinstance(child, AddressBlockType.Register))
    parsed_field = next(child for child in parsed_register.choice if isinstance(child, FieldType))
    field_id = get_handle(parsed_field)

    assert get_parent_info(field_id).parent_handle == get_handle(parsed_register)
    assert api.getRegisterFieldTypeIdentifier(field_id) == "Status_Type"
    assert api.getRegisterFieldVolatility(field_id) is True
    assert api.setRegisterFieldTypeIdentifier(regFieldID=field_id, typeIdentifier="Status_Type_2") is True
    assert api.setRegisterFieldVolatility(regFieldID=field_id, volatile=False) is True
    updated_xml = XmlDocument.serializer().render(parsed)
    _SCHEMA.assertValid(etree.fromstring(updated_xml.encode()))

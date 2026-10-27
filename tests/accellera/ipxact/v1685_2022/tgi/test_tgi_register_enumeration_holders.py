"""Register field and field-definition enumeration-holder contracts."""

import inspect
from collections.abc import Iterator

import pytest
from lxml import etree

from amal.eda.accellera.ipxact.v1685_2022 import tgi
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
from org.accellera.ipxact.v1685_2022 import (
    AddressBlock,
    AddressUnitBits,
    BaseAddress,
    Component,
    EnumeratedValues,
    FieldDefinitions,
    FieldRef,
    FieldType,
    MemoryMaps,
    MemoryMapType,
    UnsignedIntExpression,
    UnsignedLongintExpression,
    UnsignedPositiveIntExpression,
    UnsignedPositiveLongintExpression,
    UsageType,
)

_SCHEMA = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))
_OPERATIONS = [
    ("getFieldDefinitionEnumeratedValueIDs", "fieldDefinitionID", "F.7.73.40"),
    ("getRegisterFieldEnumeratedValuesID", "registerFieldID", "F.7.73.56"),
    ("removeRegisterFieldEnumeratedValues", "registerFieldID", "F.7.74.29"),
    ("setRegisterFieldEnumeratedValues", "registerFieldID", "F.7.74.59"),
]


@pytest.fixture(autouse=True)
def clean_registry() -> Iterator[None]:
    registry.clear()
    yield
    registry.clear()


def _field() -> FieldType:
    return FieldType(
        name="status", bit_offset=UnsignedIntExpression(value="0"), choice=[UnsignedPositiveIntExpression(value="8")]
    )


@pytest.mark.parametrize("name,argument,section", _OPERATIONS)
def test_contract_and_wrong_model_handles(name: str, argument: str, section: str) -> None:
    function = getattr(api, name)
    assert name in api.__all__ and getattr(tgi, name) is function
    assert list(inspect.signature(function).parameters) == [argument]
    assert f"Section: {section}." in function.__doc__
    for handle in ("missing", get_handle(EnumeratedValues())):
        with pytest.raises(TgiError) as error:
            function(handle)
        assert error.value.fault_code == TgiFaultCode.INVALID_ID


def test_creation_is_idempotent_and_preserves_tuple_until_mutation() -> None:
    field = _field()
    field.choice = tuple(field.choice)
    handle = get_handle(field)
    assert api.getRegisterFieldEnumeratedValuesID(handle) is None
    assert isinstance(field.choice, tuple)
    assert api.removeRegisterFieldEnumeratedValues(handle) is False
    assert isinstance(field.choice, tuple)
    assert api.setRegisterFieldEnumeratedValues(handle) is True
    holder_id = api.getRegisterFieldEnumeratedValuesID(handle)
    holder = resolve_handle(holder_id)
    assert isinstance(holder, EnumeratedValues)
    assert holder.enumeration_definition_ref_or_enumerated_value == []
    assert get_parent_info(holder_id).parent_handle == handle
    assert api.setRegisterFieldEnumeratedValues(handle) is True
    assert api.getRegisterFieldEnumeratedValuesID(handle) == holder_id
    assert len(field.choice) == 2
    api.addEnumeratedValuesFieldEnumeratedValue(holder_id, "IDLE", "0")
    value_ids = api.getEnumeratedValuesEnumeratedValueIDs(holder_id)
    assert len(value_ids) == 1


def test_existing_reference_holder_is_preserved_and_removed_with_its_handle() -> None:
    field = _field()
    reference = EnumeratedValues.EnumerationDefinitionRef(value="states", type_definitions="types")
    holder = EnumeratedValues(enumeration_definition_ref_or_enumerated_value=(reference,))
    field.choice = (*field.choice, holder)
    handle = get_handle(field)
    holder_id = api.getRegisterFieldEnumeratedValuesID(handle)
    reference_id = get_handle(reference)
    assert api.setRegisterFieldEnumeratedValues(handle) is True
    assert isinstance(field.choice, tuple)
    assert holder.enumeration_definition_ref_or_enumerated_value == (reference,)
    assert api.removeRegisterFieldEnumeratedValues(handle) is True
    assert resolve_handle(holder_id) is None
    assert resolve_handle(reference_id) is None
    assert api.removeRegisterFieldEnumeratedValues(handle) is False
    assert len(field.choice) == 1


def test_inline_removal_invalidates_value_descendants_without_touching_width() -> None:
    field = _field()
    handle = get_handle(field)
    width = field.choice[0]
    api.setRegisterFieldEnumeratedValues(handle)
    holder_id = api.getRegisterFieldEnumeratedValuesID(handle)
    value_id = api.addEnumeratedValuesFieldEnumeratedValue(holder_id, "READY", "1")
    expression_id = api.getEnumeratedValueValueID(value_id)
    assert api.removeRegisterFieldEnumeratedValues(handle) is True
    assert all(resolve_handle(removed) is None for removed in (holder_id, value_id, expression_id))
    assert field.choice == [width]


def test_field_definition_getter_reads_optional_inline_or_reference_holder() -> None:
    field = FieldDefinitions.FieldDefinition(name="status", bit_width=UnsignedPositiveIntExpression(value="8"))
    handle = get_handle(field)
    assert api.getFieldDefinitionEnumeratedValueIDs(handle) == []
    holder = EnumeratedValues()
    field.enumerated_values = holder
    first = api.addEnumeratedValuesFieldEnumeratedValue(get_handle(holder), "IDLE", "0")
    second = api.addEnumeratedValuesFieldEnumeratedValue(get_handle(holder), "READY", "1")
    holder.enumeration_definition_ref_or_enumerated_value = tuple(holder.enumeration_definition_ref_or_enumerated_value)
    assert api.getFieldDefinitionEnumeratedValueIDs(handle) == [first, second]
    assert isinstance(holder.enumeration_definition_ref_or_enumerated_value, tuple)
    assert get_parent_info(get_handle(holder)).parent_handle == handle
    field.enumerated_values = EnumeratedValues(
        enumeration_definition_ref_or_enumerated_value=[
            EnumeratedValues.EnumerationDefinitionRef(value="states", type_definitions="types")
        ]
    )
    assert api.getFieldDefinitionEnumeratedValueIDs(handle) == []


def test_reference_field_cannot_gain_holder_but_alias_field_can() -> None:
    reference = FieldType.FieldDefinitionRef(value="shared", type_definitions="types")
    field = _field()
    field.choice = (reference,)
    handle = get_handle(field)
    with pytest.raises(TgiError) as error:
        api.setRegisterFieldEnumeratedValues(handle)
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert field.choice == (reference,)
    assert api.getRegisterFieldEnumeratedValuesID(handle) is None
    alias = FieldType.AliasOf(field_ref=FieldRef(field_ref="shared"))
    field.choice = (alias,)
    assert api.setRegisterFieldEnumeratedValues(handle) is True
    assert field.choice[0] is alias
    assert api.getRegisterFieldEnumeratedValuesID(handle) is not None


def test_multiple_holder_model_faults_without_modification() -> None:
    field = _field()
    first, second = EnumeratedValues(), EnumeratedValues()
    field.choice = (*field.choice, first, second)
    original = field.choice
    for function in (
        api.getRegisterFieldEnumeratedValuesID,
        api.setRegisterFieldEnumeratedValues,
        api.removeRegisterFieldEnumeratedValues,
    ):
        with pytest.raises(TgiError) as error:
            function(get_handle(field))
        assert error.value.fault_code == TgiFaultCode.INVALID_ID
        assert field.choice is original


def test_create_fill_parse_remove_roundtrip_is_schema_valid() -> None:
    field = _field()
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
        library="lib",
        name="device",
        version="1",
        memory_maps=MemoryMaps(memory_map=[MemoryMapType(name="map", choice=[block, AddressUnitBits(value="8")])]),
    )
    _register_graph(component)
    api.setRegisterFieldEnumeratedValues(get_handle(field))
    holder_id = api.getRegisterFieldEnumeratedValuesID(get_handle(field))
    api.addEnumeratedValuesFieldEnumeratedValue(holder_id, "IDLE", "0")
    xml = XmlDocument.serializer().render(component)
    _SCHEMA.assertValid(etree.fromstring(xml.encode()))
    parsed = XmlDocument.parser().from_string(xml, Component)
    parsed_field = next(
        child for child in parsed.memory_maps.memory_map[0].choice[0].choice[-1].choice if isinstance(child, FieldType)
    )
    parsed_handle = get_handle(parsed_field)
    parsed_holder = api.getRegisterFieldEnumeratedValuesID(parsed_handle)
    assert parsed_holder is not None
    assert api.removeRegisterFieldEnumeratedValues(parsed_handle) is True
    assert resolve_handle(parsed_holder) is None
    updated = XmlDocument.serializer().render(parsed)
    _SCHEMA.assertValid(etree.fromstring(updated.encode()))

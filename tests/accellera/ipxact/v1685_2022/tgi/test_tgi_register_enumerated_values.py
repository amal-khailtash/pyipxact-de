"""Register enumeration TGI contracts preserve expression nodes and ownership."""

from collections.abc import Iterator
from inspect import getdoc, signature

import pytest
from lxml import etree

from amal.eda.accellera.ipxact.v1685_2022 import tgi as root_api
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
    EnumeratedValues,
    EnumeratedValueType,
    EnumerationDefinitions,
    FieldDefinitions,
    FieldType,
    TypeDefinitions,
    UnsignedBitVectorExpression,
    UnsignedIntExpression,
    UnsignedPositiveIntExpression,
)

type _Value = EnumeratedValueType
type _EnumerationDefinition = EnumerationDefinitions.EnumerationDefinition
_SCHEMA = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))


@pytest.fixture(autouse=True)
def clear_registry() -> Iterator[None]:
    registry.clear()
    yield
    registry.clear()


def _value(name: str, source: str, *, usage: object = None) -> _Value:
    kwargs = {"usage": usage} if usage is not None else {}
    return EnumeratedValueType(name=name, value=UnsignedBitVectorExpression(value=source), **kwargs)


def _field(
    values: list[_Value] | tuple[_Value, ...] = (),
    *,
    width: str = "8",
    holder: EnumeratedValues | None = None,
) -> tuple[FieldType, EnumeratedValues]:
    holder = holder or EnumeratedValues(enumeration_definition_ref_or_enumerated_value=values)
    field = FieldType(
        name="status",
        bit_offset=UnsignedIntExpression(value="0"),
        choice=[UnsignedPositiveIntExpression(value=width), holder],
    )
    _register_graph(field)
    return field, holder


def _definition(value: _Value, width: str = "4") -> _EnumerationDefinition:
    definition = EnumerationDefinitions.EnumerationDefinition(
        name="state",
        width=UnsignedPositiveIntExpression(value=width),
        enumerated_value=[value],
    )
    _register_graph(definition)
    return definition


def test_public_operations_have_annex_signatures_and_exports() -> None:
    operations = {
        "getEnumeratedValueExpression": ("F.7.73.28", ("enumeratedValueID",), str),
        "getEnumeratedValueUsage": ("F.7.73.29", ("enumeratedValueID",), str),
        "getEnumeratedValueValue": ("F.7.73.30", ("enumeratedValueID",), int),
        "getEnumeratedValueValueExpression": ("F.7.73.31", ("enumeratedValueID",), str),
        "getEnumeratedValueValueID": ("F.7.73.32", ("enumeratedValueID",), str),
        "getEnumeratedValuesEnumeratedValueIDs": ("F.7.73.33", ("enumeratedValuesID",), list[str]),
        "addEnumeratedValuesFieldEnumeratedValue": (
            "F.7.74.5",
            ("enumeratedValuesID", "name", "value"),
            str,
        ),
        "removeEnumeratedValuesEnumeratedValue": ("F.7.74.23", ("enumeratedValueID",), bool),
        "setEnumeratedValueUsage": ("F.7.74.49", ("enumeratedValueID", "usage"), bool),
        "setEnumeratedValueValue": ("F.7.74.50", ("enumeratedValueID", "expression"), bool),
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


def test_getters_return_source_default_usage_numeric_cast_and_owned_value_handle() -> None:
    value = _value("wide", "8'h1ff")
    _, holder = _field([value], width="8")
    value_id = get_handle(value)

    assert api.getEnumeratedValueExpression(value_id) == "8'h1ff"
    assert api.getEnumeratedValueValueExpression(value_id) == "8'h1ff"
    assert api.getEnumeratedValueUsage(value_id) == "read-write"
    assert api.getEnumeratedValueValue(value_id) == 0xFF
    assert api.getEnumeratedValuesEnumeratedValueIDs(get_handle(holder)) == [value_id]
    expression_id = api.getEnumeratedValueValueID(value_id)
    assert expression_id == get_handle(value.value)
    assert get_parent_info(expression_id).parent_handle == value_id


def test_numeric_getter_uses_definition_width_and_faults_for_unresolved_source() -> None:
    value = _value("truncated", "8'hff")
    definition = _definition(value, width="4")
    assert api.getEnumeratedValueValue(get_handle(value)) == 0xF
    assert definition.width.value == "4"

    value.value.value = "UNDECLARED"
    with pytest.raises(TgiError) as error:
        api.getEnumeratedValueValue(get_handle(value))
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT


@pytest.mark.parametrize(
    "source,expected",
    [("-1", 0xFF), ("8'b10x1_zz01", 0x91), ("16'h1234", 0x34), ("128'h1 << 100", 1 << 100)],
)
def test_numeric_getter_uses_unsigned_two_state_conversion(source: str, expected: int) -> None:
    value = _value("converted", source)
    if source == "128'h1 << 100":
        _register_graph(value)
    else:
        _field([value], width="8")
    assert api.getEnumeratedValueValue(get_handle(value)) == expected


def test_known_unresolved_field_width_faults_in_numeric_getter() -> None:
    value = _value("ready", "8'hff")
    _field([value], width="FIELD_WIDTH")
    with pytest.raises(TgiError) as error:
        api.getEnumeratedValueValue(get_handle(value))
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT


def test_registry_root_walk_recovers_parsed_field_definition_ownership() -> None:
    value = _value("wide", "8'hff")
    holder = EnumeratedValues(enumeration_definition_ref_or_enumerated_value=[value])
    field = FieldDefinitions.FieldDefinition(
        name="status",
        bit_width=UnsignedPositiveIntExpression(value="4"),
        enumerated_values=holder,
    )
    root = TypeDefinitions(
        vendor="example.org",
        library="types",
        name="device_types",
        version="1.0",
        field_definitions=FieldDefinitions(field_definition=[field]),
    )
    xml = XmlDocument.serializer().render(root)
    root = XmlDocument.parser().from_string(xml, TypeDefinitions)
    field = root.field_definitions.field_definition[0]
    holder = field.enumerated_values
    value = holder.enumeration_definition_ref_or_enumerated_value[0]
    registry.register(root, ("example.org", "types", "device_types", "1.0"))
    value_id = get_handle(value)
    holder_id = get_handle(holder)

    assert get_parent_info(value_id) is None
    assert api.getEnumeratedValueValue(value_id) == 0xF
    assert get_parent_info(value_id).parent_handle == holder_id
    assert api.removeEnumeratedValuesEnumeratedValue(value_id) is True
    assert field.enumerated_values is None
    assert resolve_handle(holder_id) is None


def test_builder_validates_name_and_width_before_mutation_and_defers_constants() -> None:
    existing = _value("idle", "0")
    _, holder = _field([existing], width="4")
    holder_id = get_handle(holder)

    with pytest.raises(TgiError) as error:
        api.addEnumeratedValuesFieldEnumeratedValue(holder_id, "idle", "1")
    assert error.value.fault_code == TgiFaultCode.ALREADY_EXISTS
    assert list(holder.enumeration_definition_ref_or_enumerated_value) == [existing]

    truncated_id = api.addEnumeratedValuesFieldEnumeratedValue(holder_id, "truncated", "5'h10")
    assert api.getEnumeratedValueValue(truncated_id) == 0

    added_id = api.addEnumeratedValuesFieldEnumeratedValue(holder_id, "ready", "STATE_READY")
    added = resolve_handle(added_id)
    assert isinstance(added, EnumeratedValueType)
    assert added.value.value == "STATE_READY"
    assert api.getEnumeratedValueUsage(added_id) == "read-write"
    assert api.getEnumeratedValuesEnumeratedValueIDs(holder_id) == [get_handle(existing), truncated_id, added_id]


def test_builder_rejects_reference_choice_without_replacing_it() -> None:
    reference = EnumeratedValues.EnumerationDefinitionRef(value="state", type_definitions="vendor:lib:types:1")
    holder = EnumeratedValues(enumeration_definition_ref_or_enumerated_value=[reference])
    _register_graph(holder)
    with pytest.raises(TgiError) as error:
        api.addEnumeratedValuesFieldEnumeratedValue(get_handle(holder), "ready", "1")
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert holder.enumeration_definition_ref_or_enumerated_value == [reference]
    assert api.getEnumeratedValuesEnumeratedValueIDs(get_handle(holder)) == []


def test_setters_preserve_wrappers_validate_and_remove_invalidates_owned_tree() -> None:
    value = _value("ready", "1")
    value.id = "enumeration-value-id"
    value.value.other_attributes = {"vendorAttr": "preserve"}
    field, holder = _field([value], width="8")
    value_id = get_handle(value)
    expression = value.value
    expression_id = get_handle(expression)

    assert api.setEnumeratedValueUsage(value_id, "write") is True
    assert value.usage.value == "write"
    with pytest.raises(TgiError) as error:
        api.setEnumeratedValueUsage(value_id, "execute")
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert value.usage.value == "write"

    assert api.setEnumeratedValueValue(value_id, "8'h1ff") is True
    assert value.value is expression
    assert get_handle(value.value) == expression_id
    assert value.value.value == "8'h1ff"
    assert value.value.other_attributes == {"vendorAttr": "preserve"}
    assert value.id == "enumeration-value-id"
    assert api.getEnumeratedValueValue(value_id) == 0xFF

    with pytest.raises(TgiError) as error:
        api.setEnumeratedValueValue(value_id, "4'h + 1")
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert value.value.value == "8'h1ff"

    assert api.removeEnumeratedValuesEnumeratedValue(value_id) is True
    assert holder.enumeration_definition_ref_or_enumerated_value == []
    assert resolve_handle(value_id) is None
    assert resolve_handle(expression_id) is None
    assert get_parent_info(get_handle(holder)) is None
    assert holder not in field.choice


def test_remove_definition_owned_value_is_outside_this_register_operation() -> None:
    value = _value("idle", "0")
    _definition(value)
    with pytest.raises(TgiError) as error:
        api.removeEnumeratedValuesEnumeratedValue(get_handle(value))
    assert error.value.fault_code == TgiFaultCode.INVALID_ID
    assert resolve_handle(get_handle(value)) is value


def test_detached_holder_removes_member_without_pruning_unknown_owner() -> None:
    value = _value("detached", "1")
    holder = EnumeratedValues(enumeration_definition_ref_or_enumerated_value=[value])
    _register_graph(holder)
    holder_id = get_handle(holder)

    assert api.removeEnumeratedValuesEnumeratedValue(get_handle(value)) is True
    assert holder.enumeration_definition_ref_or_enumerated_value == []
    assert resolve_handle(holder_id) is holder


def test_invalid_and_non_string_handles_raise_invalid_id() -> None:
    for getter, handle in (
        (api.getEnumeratedValueExpression, []),
        (api.getEnumeratedValueUsage, "missing"),
        (api.getEnumeratedValueValue, []),
        (api.getEnumeratedValueValueExpression, "missing"),
        (api.getEnumeratedValueValueID, []),
        (api.getEnumeratedValuesEnumeratedValueIDs, []),
    ):
        with pytest.raises(TgiError) as error:
            getter(handle)  # type: ignore[arg-type]
        assert error.value.fault_code == TgiFaultCode.INVALID_ID
    with pytest.raises(TgiError) as error:
        api.addEnumeratedValuesFieldEnumeratedValue([], "ready", "1")  # type: ignore[arg-type]
    assert error.value.fault_code == TgiFaultCode.INVALID_ID
    with pytest.raises(TgiError) as error:
        api.removeEnumeratedValuesEnumeratedValue([])  # type: ignore[arg-type]
    assert error.value.fault_code == TgiFaultCode.INVALID_ID
    with pytest.raises(TgiError) as error:
        api.setEnumeratedValueValue([], "1")  # type: ignore[arg-type]
    assert error.value.fault_code == TgiFaultCode.INVALID_ID


def test_field_definition_holder_round_trips_as_schema_valid_xml() -> None:
    value = _value("ready", "1")
    holder = EnumeratedValues(enumeration_definition_ref_or_enumerated_value=[value])
    field = FieldDefinitions.FieldDefinition(
        name="status",
        bit_width=UnsignedPositiveIntExpression(value="4"),
        enumerated_values=holder,
    )
    root = TypeDefinitions(
        vendor="example.org",
        library="types",
        name="device_types",
        version="1.0",
        field_definitions=FieldDefinitions(field_definition=[field]),
    )
    _register_graph(root)
    api.setEnumeratedValueUsage(get_handle(value), "write")
    api.setEnumeratedValueValue(get_handle(value), "4'hf")

    xml = XmlDocument.serializer().render(root)
    parsed = etree.fromstring(xml.encode())
    assert _SCHEMA.validate(parsed), _SCHEMA.error_log
    restored = XmlDocument.parser().from_string(xml, TypeDefinitions)
    restored_xml = XmlDocument.serializer().render(restored)
    assert _SCHEMA.validate(etree.fromstring(restored_xml.encode())), _SCHEMA.error_log
    restored_value = restored.field_definitions.field_definition[
        0
    ].enumerated_values.enumeration_definition_ref_or_enumerated_value[0]
    assert restored_value.usage.value == "write"
    assert restored_value.value.value == "4'hf"

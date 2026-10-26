"""Expression-bearing Type definitions and field enumeration lifecycle contracts."""

from collections.abc import Iterator
from inspect import Parameter, signature

import pytest
from lxml import etree

from amal.eda.accellera.ipxact.v1685_2022 import tgi
from amal.eda.accellera.ipxact.v1685_2022.tgi import type_definitions as api
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import TgiError, TgiFaultCode, get_handle, registry, resolve_handle
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import (
    EnumeratedValues,
    EnumeratedValueType,
    EnumerationDefinitions,
    FieldDefinitions,
    TypeDefinitions,
    UnsignedBitVectorExpression,
    UnsignedPositiveIntExpression,
)


def _root() -> TypeDefinitions:
    return TypeDefinitions(vendor="example.org", library="types", name="complex", version="1.0")


@pytest.fixture(autouse=True)
def clear_registry() -> Iterator[None]:
    registry.clear()
    yield
    registry.clear()


_BUILDERS = (
    ("addTypeDefinitionsAddressBlockDefinition", ("typeDefinitionsID", "name", "range", "width"), ("64", "32"), 7),
    ("addTypeDefinitionsFieldDefinition", ("typeDefinitionsID", "name", "bitWidth"), ("4",), 13),
    (
        "addTypeDefinitionsRegisterDefinition",
        ("typeDefinitionsID", "name", "size", "fieldName", "fieldOffset", "fieldWidth"),
        ("32", "flag", "0", "4"),
        17,
    ),
    ("addTypeDefinitionsRegisterFileDefinition", ("typeDefinitionsID", "name", "range"), ("64",), 18),
    ("addTypeDefinitionsChoice", ("typeDefinitionsID", "name", "enumerations"), (["1 + 1", '"idle"'],), 9),
)


@pytest.mark.parametrize("builder", _BUILDERS, ids=[row[0] for row in _BUILDERS])
def test_expression_builders_signatures_ownership_duplicates_and_rejections(
    builder: tuple[str, tuple[str, ...], tuple[str | list[str], ...], int],
) -> None:
    name, parameters, values, section = builder
    operation = getattr(api, name)
    assert getattr(tgi, name) is operation
    contract = signature(operation)
    assert tuple(contract.parameters) == parameters
    assert all(parameter.annotation is str for parameter in list(contract.parameters.values())[:-1])
    assert contract.parameters[parameters[-1]].annotation is not Parameter.empty
    assert contract.return_annotation is str
    assert f"F.7.82.{section}" in operation.__doc__
    root = _root()
    child_id = operation(get_handle(root), "first", *values)
    child = resolve_handle(child_id)
    assert child.name == "first"
    with pytest.raises(TgiError) as error:
        operation(get_handle(root), " first ", *values)
    assert error.value.fault_code == TgiFaultCode.ALREADY_EXISTS
    assert resolve_handle(child_id) is child
    for handle in ("stale", get_handle(child)):
        with pytest.raises(TgiError) as error:
            operation(handle, "second", *values)
        assert error.value.fault_code == TgiFaultCode.INVALID_ID


@pytest.mark.parametrize("source", ["0", "-1", "1.5", "1 +", "1 << 80"])
def test_bad_numeric_sources_reject_without_creating_holders(source: str) -> None:
    root = _root()
    for operation, extra in (
        (api.addTypeDefinitionsFieldDefinition, (source,)),
        (api.addTypeDefinitionsAddressBlockDefinition, (source, "32")),
        (api.addTypeDefinitionsRegisterDefinition, (source, "flag", "0", "4")),
        (api.addTypeDefinitionsRegisterFileDefinition, (source,)),
    ):
        with pytest.raises(TgiError) as error:
            operation(get_handle(root), "new", *extra)
        assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert root.field_definitions is None
    assert root.address_block_definitions is None
    assert root.register_definitions is None
    assert root.register_file_definitions is None


def test_register_field_boundaries_and_deferred_sources() -> None:
    root = _root()
    with pytest.raises(TgiError) as error:
        api.addTypeDefinitionsRegisterDefinition(get_handle(root), "bad", "8", "flag", "7", "2")
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert root.register_definitions is None
    child_id = api.addTypeDefinitionsRegisterDefinition(get_handle(root), "ok", "SIZE", "flag", "OFFSET", "WIDTH")
    child = resolve_handle(child_id)
    assert child.size.value == "SIZE"
    assert child.field_value[0].bit_offset.value == "OFFSET"
    assert child.field_value[0].choice[0].value == "WIDTH"


@pytest.mark.parametrize("values", [[], "1", ["1 +"], [3]])
def test_bad_choice_arrays_are_atomic(values: object) -> None:
    root = _root()
    with pytest.raises(TgiError) as error:
        api.addTypeDefinitionsChoice(get_handle(root), "new", values)
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert root.choices is None


def test_enumeration_extension_requires_explicit_keyword_width_and_is_atomic() -> None:
    root = _root()
    operation = api.addEnumerationDefinition
    assert getattr(tgi, operation.__name__) is operation
    contract = signature(operation)
    assert tuple(contract.parameters) == ("typeDefID", "name", "enumeratedName", "enumeratedExpression", "width")
    assert contract.parameters["width"].kind is Parameter.KEYWORD_ONLY
    assert contract.parameters["width"].default is Parameter.empty
    assert all(parameter.annotation is str for parameter in contract.parameters.values())
    assert contract.return_annotation is str
    with pytest.raises(TypeError):
        operation(get_handle(root), "state", "idle", "1")
    for value in ("16", "-1", "1 +"):
        with pytest.raises(TgiError) as error:
            operation(get_handle(root), "state", "idle", value, width="4")
        assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
        assert root.enumeration_definitions is None
    definition_id = operation(get_handle(root), "state", "idle", "'hF", width="4")
    assert api.getEnumerationDefinitionWidth(definition_id) == 4
    values = api.getEnumerationDefinitionEnumeratedValueIDs(definition_id)
    assert len(values) == 1
    assert resolve_handle(values[0]).value.value == "'hF"


def test_field_enumeration_lifecycle_fit_metadata_and_last_holder_pruning() -> None:
    root = _root()
    field_id = api.addTypeDefinitionsFieldDefinition(get_handle(root), "flags", "4")
    field = resolve_handle(field_id)
    first_id = api.addFieldDefinitionsEnumeratedValue(field_id, "first", "'hF")
    holder = field.enumerated_values
    holder_id = get_handle(holder)
    first = resolve_handle(first_id)
    value_id = get_handle(first.value)
    values = (first,)
    holder.enumeration_definition_ref_or_enumerated_value = values
    for name, value in (("first", "2"), ("too_big", "16"), ("bad", "1 +")):
        with pytest.raises(TgiError):
            api.addFieldDefinitionsEnumeratedValue(field_id, name, value)
        assert holder.enumeration_definition_ref_or_enumerated_value is values
    second_id = api.addFieldDefinitionsEnumeratedValue(field_id, "second", "2")
    assert not api.removeFieldDefinitionEnumerationDefinitionRef(field_id)
    assert api.removeFieldDefinitionsEnumeratedValue(first_id)
    assert resolve_handle(first_id) is None
    assert resolve_handle(value_id) is None
    assert resolve_handle(second_id) is holder.enumeration_definition_ref_or_enumerated_value[0]
    assert api.removeFieldDefinitionsEnumeratedValue(second_id)
    assert field.enumerated_values is None
    assert resolve_handle(holder_id) is None


def test_field_reference_removal_branch_integrity_and_invalid_owners() -> None:
    field = FieldDefinitions.FieldDefinition(name="flag", bit_width=UnsignedPositiveIntExpression(value="4"))
    ref = EnumeratedValues.EnumerationDefinitionRef(value="state", type_definitions="types")
    field.enumerated_values = EnumeratedValues(enumeration_definition_ref_or_enumerated_value=(ref,))
    ref_id = get_handle(ref)
    field_id = get_handle(field)
    with pytest.raises(TgiError) as error:
        api.addFieldDefinitionsEnumeratedValue(field_id, "idle", "0")
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert api.removeFieldDefinitionEnumerationDefinitionRef(field_id)
    assert field.enumerated_values is None
    assert resolve_handle(ref_id) is None
    assert not api.removeFieldDefinitionEnumerationDefinitionRef(field_id)
    orphan = EnumeratedValueType(name="orphan", value=UnsignedBitVectorExpression(value="1"))
    for handle in ("stale", get_handle(field), get_handle(orphan)):
        with pytest.raises(TgiError) as error:
            api.removeFieldDefinitionsEnumeratedValue(handle)
        assert error.value.fault_code == TgiFaultCode.INVALID_ID
    wrong = EnumerationDefinitions.EnumerationDefinition(name="state", width=UnsignedPositiveIntExpression(value="4"))
    with pytest.raises(TgiError):
        api.addFieldDefinitionsEnumeratedValue(get_handle(wrong), "idle", "0")


def test_schema_valid_numeric_choice_and_enumeration_roundtrip_and_parsed_removal() -> None:
    root = _root()
    api.addTypeDefinitionsAddressBlockDefinition(get_handle(root), "block", "64", "32")
    api.addTypeDefinitionsRegisterDefinition(get_handle(root), "control", "32", "flag", "0", "4")
    api.addTypeDefinitionsChoice(get_handle(root), "alternatives", ["1 + 1", "3"])
    api.addEnumerationDefinition(get_handle(root), "state", "idle", "1", width="4")
    field_id = api.addTypeDefinitionsFieldDefinition(get_handle(root), "flags", "4")
    api.addFieldDefinitionsEnumeratedValue(field_id, "first", "1")
    api.addFieldDefinitionsEnumeratedValue(field_id, "second", "2")
    xml = XmlDocument.serializer().render(root)
    schema = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))
    schema.assertValid(etree.fromstring(xml.encode()))
    parsed = XmlDocument.parser().from_string(xml, TypeDefinitions)
    registry.register(parsed, (parsed.vendor, parsed.library, parsed.name, parsed.version))
    field = parsed.field_definitions.field_definition[0]
    first, second = field.enumerated_values.enumeration_definition_ref_or_enumerated_value
    first_id = get_handle(first)
    value_id = get_handle(first.value)
    assert api.removeFieldDefinitionsEnumeratedValue(first_id)
    assert resolve_handle(first_id) is None
    assert resolve_handle(value_id) is None
    assert field.enumerated_values.enumeration_definition_ref_or_enumerated_value == [second]
    schema.assertValid(etree.fromstring(XmlDocument.serializer().render(parsed).encode()))


def test_field_enum_remover_rejects_root_enumeration_members() -> None:
    root = _root()
    definition_id = api.addEnumerationDefinition(get_handle(root), "state", "idle", "1", width="4")
    member_id = api.getEnumerationDefinitionEnumeratedValueIDs(definition_id)[0]
    member = resolve_handle(member_id)
    with pytest.raises(TgiError) as error:
        api.removeFieldDefinitionsEnumeratedValue(member_id)
    assert error.value.fault_code == TgiFaultCode.INVALID_ID
    assert resolve_handle(member_id) is member
    assert api.getEnumerationDefinitionEnumeratedValueIDs(definition_id) == [member_id]


def test_mixed_field_enum_choice_rejected_without_tuple_normalization() -> None:
    root = _root()
    field = FieldDefinitions.FieldDefinition(name="flag", bit_width=UnsignedPositiveIntExpression(value="4"))
    member = EnumeratedValueType(name="one", value=UnsignedBitVectorExpression(value="1"))
    reference = EnumeratedValues.EnumerationDefinitionRef(value="state", type_definitions="types")
    values = (member, reference)
    field.enumerated_values = EnumeratedValues(enumeration_definition_ref_or_enumerated_value=values)
    root.field_definitions = FieldDefinitions(field_definition=[field])
    registry.register(root, (root.vendor, root.library, root.name, root.version))
    member_id = get_handle(member)
    for operation, arguments in (
        (api.addFieldDefinitionsEnumeratedValue, (get_handle(field), "two", "2")),
        (api.removeFieldDefinitionEnumerationDefinitionRef, (get_handle(field),)),
        (api.removeFieldDefinitionsEnumeratedValue, (member_id,)),
    ):
        with pytest.raises(TgiError) as error:
            operation(*arguments)
        assert error.value.fault_code == TgiFaultCode.INVALID_ID
        assert field.enumerated_values.enumeration_definition_ref_or_enumerated_value is values
        assert resolve_handle(member_id) is member


@pytest.mark.parametrize(
    ("name", "parameters", "return_type", "section"),
    [
        ("addFieldDefinitionsEnumeratedValue", ("fieldDefinitionID", "name", "expression"), str, 6),
        ("removeFieldDefinitionEnumerationDefinitionRef", ("fieldDefinitionID",), bool, 28),
        ("removeFieldDefinitionsEnumeratedValue", ("domainTypeDefID",), bool, 29),
    ],
)
def test_field_enum_exact_contracts(name: str, parameters: tuple[str, ...], return_type: type, section: int) -> None:
    operation = getattr(api, name)
    contract = signature(operation)
    assert tuple(contract.parameters) == parameters
    assert all(parameter.annotation is str for parameter in contract.parameters.values())
    assert contract.return_annotation is return_type
    assert getattr(tgi, name) is operation
    assert f"F.7.82.{section}" in operation.__doc__


def test_register_file_required_range_roundtrip() -> None:
    root = _root()
    child_id = api.addTypeDefinitionsRegisterFileDefinition(get_handle(root), "registers", "64 + 64")
    child = resolve_handle(child_id)
    assert child.range.value == "64 + 64"
    xml = XmlDocument.serializer().render(root)
    parsed = XmlDocument.parser().from_string(xml, TypeDefinitions)
    assert parsed.register_file_definitions.register_file_definition[0].range.value == "64 + 64"
    schema = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))
    schema.assertValid(etree.fromstring(xml.encode()))

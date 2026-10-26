"""Enumeration-definition TGI operations preserve typed ownership and XML validity."""

from collections.abc import Iterator
from inspect import getdoc, signature

import pytest
from lxml import etree

from amal.eda.accellera.ipxact.v1685_2022 import tgi as root_api
from amal.eda.accellera.ipxact.v1685_2022.tgi import type_definitions as api
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import (
    TgiError,
    TgiFaultCode,
    get_handle,
    get_parent_info,
    register_parent,
    registry,
    resolve_handle,
)
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

_SCHEMA = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))

type _EnumerationDefinition = EnumerationDefinitions.EnumerationDefinition
type _Value = EnumeratedValueType
type _Operation = tuple[str, tuple[str, ...], tuple[object, ...], object]


@pytest.fixture(autouse=True)
def clear_registry() -> Iterator[None]:
    registry.clear()
    yield
    registry.clear()


def _value(name: str, value: str) -> _Value:
    return EnumeratedValueType(name=name, value=UnsignedBitVectorExpression(value=value))


def _definition(
    name: str = "state",
    width: str = "8",
    values: list[_Value] | tuple[_Value, ...] = (),
) -> _EnumerationDefinition:
    return EnumerationDefinitions.EnumerationDefinition(
        name=name,
        width=UnsignedPositiveIntExpression(value=width),
        enumerated_value=values,
    )


def _root(definitions: list[_EnumerationDefinition] | tuple[_EnumerationDefinition, ...] = ()) -> TypeDefinitions:
    return TypeDefinitions(
        vendor="example.org",
        library="types",
        name="device_types",
        version="1.0",
        enumeration_definitions=(EnumerationDefinitions(enumeration_definition=definitions) if definitions else None),
    )


def _assert_schema_valid(root: TypeDefinitions) -> str:
    xml = XmlDocument.serializer().render(root)
    assert _SCHEMA.validate(etree.fromstring(xml.encode())), _SCHEMA.error_log
    return xml


def test_public_operations_have_native_signatures_sections_and_exports() -> None:
    operations: dict[str, _Operation] = {
        "getEnumerationDefinitionEnumeratedValueIDs": (
            "F.7.81.7",
            ("enumerationDefinitionID",),
            (str,),
            list[str],
        ),
        "getTypeDefinitionsEnumerationDefinitionIDs": (
            "F.7.81.33",
            ("typeDefinitionsID",),
            (str,),
            list[str],
        ),
        "setEnumerationDefinitionWidth": (
            "F.7.82.48",
            ("enumerationDefinitionID", "width"),
            (str, str),
            bool,
        ),
        "addEnumerationDefinitionEnumeratedValue": (
            "F.7.82.3",
            ("enumerationDefinitionID", "name", "value"),
            (str, str, str),
            str,
        ),
        "removeEnumerationDefinitionEnumeratedValue": (
            "F.7.82.24",
            ("enumeratedValueID",),
            (str,),
            bool,
        ),
        "addTypeDefinitionsEnumerationDefinition": (
            "F.7.82.10",
            ("typeDefinitionsID", "name", "width"),
            (str, str, str),
            str,
        ),
        "removeTypeDefinitionsEnumerationDefinition": (
            "F.7.82.35",
            ("enumerationDefinitionID",),
            (str,),
            bool,
        ),
    }
    for name, (section, argument_names, arguments, result) in operations.items():
        operation = getattr(api, name)
        assert getattr(root_api, name) is operation
        assert name in api.__all__
        assert name in root_api.__all__
        function_signature = signature(operation)
        assert tuple(function_signature.parameters) == argument_names
        assert tuple(parameter.annotation for parameter in function_signature.parameters.values()) == arguments
        assert all(parameter.default is parameter.empty for parameter in function_signature.parameters.values())
        assert function_signature.return_annotation == result
        docstring = getdoc(operation)
        assert docstring is not None
        assert f"Section: {section}." in docstring
        assert "Args:" in docstring
        assert "Returns:" in docstring


def test_typed_getters_preserve_tuple_containers_and_repair_graph_ownership() -> None:
    value_a = _value("idle", "0")
    value_b = _value("busy", "1")
    values = (value_a, value_b)
    definition = _definition(values=values)
    definitions = (definition,)
    root = _root(definitions)
    root_id = get_handle(root)
    definition_id = get_handle(definition)

    definition_ids = api.getTypeDefinitionsEnumerationDefinitionIDs(root_id)
    value_ids = api.getEnumerationDefinitionEnumeratedValueIDs(definition_id)

    assert definition_ids == [definition_id]
    assert value_ids == [get_handle(value_a), get_handle(value_b)]
    assert root.enumeration_definitions is not None
    assert root.enumeration_definitions.enumeration_definition is definitions
    assert definition.enumerated_value is values
    assert get_parent_info(definition_id) is not None
    assert get_parent_info(definition_id).parent_handle == get_handle(root.enumeration_definitions)
    assert get_parent_info(value_ids[0]) is not None
    assert get_parent_info(value_ids[0]).parent_handle == definition_id

    malformed = _definition()
    malformed.enumerated_value = [object()]  # type: ignore[list-item]
    malformed_id = get_handle(malformed)
    with pytest.raises(TgiError) as error:
        api.getEnumerationDefinitionEnumeratedValueIDs(malformed_id)
    assert error.value.fault_code == TgiFaultCode.INVALID_ID
    repaired_value = _value("ready", "2")
    malformed.enumerated_value = (repaired_value,)
    assert api.getEnumerationDefinitionEnumeratedValueIDs(malformed_id) == [get_handle(repaired_value)]
    assert get_parent_info(get_handle(repaired_value)) is not None
    assert get_parent_info(get_handle(repaired_value)).parent_handle == malformed_id

    malformed_root = _root()
    malformed_root.enumeration_definitions = object()  # type: ignore[assignment]
    malformed_root_id = get_handle(malformed_root)
    with pytest.raises(TgiError) as error:
        api.getTypeDefinitionsEnumerationDefinitionIDs(malformed_root_id)
    assert error.value.fault_code == TgiFaultCode.INVALID_ID
    repaired_definition = _definition()
    malformed_root.enumeration_definitions = EnumerationDefinitions(enumeration_definition=(repaired_definition,))
    assert api.getTypeDefinitionsEnumerationDefinitionIDs(malformed_root_id) == [get_handle(repaired_definition)]
    assert get_parent_info(get_handle(repaired_definition)) is not None
    assert get_parent_info(get_handle(repaired_definition)).parent_handle == get_handle(
        malformed_root.enumeration_definitions
    )


def test_width_setter_preserves_wrapper_metadata_and_repairs_only_bad_source_values() -> None:
    definition = _definition()
    definition.width = UnsignedPositiveIntExpression(value="old", minimum=1, maximum=32)
    definition_id = get_handle(definition)
    width = definition.width
    width_id = get_handle(width)

    assert api.setEnumerationDefinitionWidth(definition_id, "4 * 4")
    assert definition.width is width
    assert definition.width.value == "4 * 4"
    assert definition.width.minimum == 1
    assert definition.width.maximum == 32
    assert api.getEnumerationDefinitionWidthID(definition_id) == width_id
    assert api.getEnumerationDefinitionWidth(definition_id) == 16
    assert api.getEnumerationDefinitionWidthExpression(definition_id) == "4 * 4"

    for invalid in ("", "0", "-1", "2**", None, 4):
        before = definition.width.value
        with pytest.raises(TgiError):
            api.setEnumerationDefinitionWidth(definition_id, invalid)  # type: ignore[arg-type]
        assert definition.width.value == before

    definition.width.value = ""
    assert api.setEnumerationDefinitionWidth(definition_id, "8")
    assert api.getEnumerationDefinitionWidthExpression(definition_id) == "8"

    definition.width = None  # type: ignore[assignment]
    with pytest.raises(TgiError) as error:
        api.setEnumerationDefinitionWidth(definition_id, "8")
    assert error.value.fault_code == TgiFaultCode.INVALID_ID
    definition.width = object()  # type: ignore[assignment]
    with pytest.raises(TgiError) as error:
        api.setEnumerationDefinitionWidth(definition_id, "8")
    assert error.value.fault_code == TgiFaultCode.INVALID_ID


def test_width_changes_reject_known_overflow_atomically_and_defer_unknown_expressions() -> None:
    definition = _definition(values=[_value("maximum", "8'hFF")])
    definition_id = get_handle(definition)
    values_id = api.getEnumerationDefinitionEnumeratedValueIDs(definition_id)[0]
    before = _assert_schema_valid(_root([definition]))

    with pytest.raises(TgiError):
        api.setEnumerationDefinitionWidth(definition_id, "4")
    assert api.getEnumerationDefinitionWidthExpression(definition_id) == "8"
    assert resolve_handle(values_id) is not None
    assert _assert_schema_valid(_root([definition])) == before

    assert api.setEnumerationDefinitionWidth(definition_id, "WIDTH_PARAMETER")
    assert api.getEnumerationDefinitionWidthExpression(definition_id) == "WIDTH_PARAMETER"
    assert api.addEnumerationDefinitionEnumeratedValue(definition_id, "deferred", "VALUE_PARAMETER")


def test_add_value_validates_names_values_width_and_schema_round_trip() -> None:
    definition = _definition()
    definition_id = get_handle(definition)
    first_id = api.addEnumerationDefinitionEnumeratedValue(definition_id, "idle", "0")
    second_id = api.addEnumerationDefinitionEnumeratedValue(definition_id, "active", "8'hFE")
    assert api.getEnumerationDefinitionEnumeratedValueIDs(definition_id) == [first_id, second_id]
    xml = _assert_schema_valid(_root([definition]))
    restored = XmlDocument.parser().from_string(xml, TypeDefinitions)
    restored_id = api.getTypeDefinitionsEnumerationDefinitionIDs(get_handle(restored))[0]
    assert len(api.getEnumerationDefinitionEnumeratedValueIDs(restored_id)) == 2

    before = _assert_schema_valid(_root([definition]))
    for invalid_name in ("", "bad name", "bad/name", "1starts-with-digit"):
        with pytest.raises(TgiError):
            api.addEnumerationDefinitionEnumeratedValue(definition_id, invalid_name, "1")
        assert _assert_schema_valid(_root([definition])) == before
    with pytest.raises(TgiError):
        api.addEnumerationDefinitionEnumeratedValue(definition_id, "idle", "2")
    assert _assert_schema_valid(_root([definition])) == before

    for invalid_value in ("-1", "-1'sd1", "16'h0100", "", "2**", None, 1):
        with pytest.raises(TgiError):
            api.addEnumerationDefinitionEnumeratedValue(definition_id, "candidate", invalid_value)  # type: ignore[arg-type]
        assert _assert_schema_valid(_root([definition])) == before

    assert api.addEnumerationDefinitionEnumeratedValue(definition_id, "unresolved", "VALUE_PARAMETER")
    deferred_width = _definition("deferred_width", width="WIDTH_PARAMETER")
    deferred_width_id = get_handle(deferred_width)
    assert api.addEnumerationDefinitionEnumeratedValue(deferred_width_id, "unknown_width_value", "16'hFFFF")
    assert _assert_schema_valid(_root([definition]))


def test_value_adder_rejects_bad_owner_and_malformed_source_before_mutation() -> None:
    root_id = get_handle(_root())
    with pytest.raises(TgiError):
        api.addEnumerationDefinitionEnumeratedValue(root_id, "value", "0")

    definition = _definition()
    definition_id = get_handle(definition)
    definition.enumerated_value = (object(),)  # type: ignore[list-item]
    with pytest.raises(TgiError):
        api.addEnumerationDefinitionEnumeratedValue(definition_id, "value", "0")
    assert definition.enumerated_value[0].__class__ is object
    definition.enumerated_value = ()
    assert api.addEnumerationDefinitionEnumeratedValue(definition_id, "value", "0")


def test_builder_validates_then_creates_typed_optional_holder_and_stages_valid_xml() -> None:
    root = _root()
    root_id = get_handle(root)
    assert root.enumeration_definitions is None

    for invalid_name in ("", "bad name", "1bad"):
        with pytest.raises(TgiError):
            api.addTypeDefinitionsEnumerationDefinition(root_id, invalid_name, "8")
        assert root.enumeration_definitions is None
    for invalid_width in ("", "0", "-1", "not valid", None, 4):
        with pytest.raises(TgiError):
            api.addTypeDefinitionsEnumerationDefinition(root_id, "control", invalid_width)  # type: ignore[arg-type]
        assert root.enumeration_definitions is None

    definition_id = api.addTypeDefinitionsEnumerationDefinition(root_id, "control", "2 * 4")
    definition = resolve_handle(definition_id)
    assert isinstance(definition, EnumerationDefinitions.EnumerationDefinition)
    assert isinstance(definition.width, UnsignedPositiveIntExpression)
    assert definition.width.value == "2 * 4"
    assert definition.enumerated_value == []
    assert api.getTypeDefinitionsEnumerationDefinitionIDs(root_id) == [definition_id]

    value_id = api.addEnumerationDefinitionEnumeratedValue(definition_id, "enabled", "1")
    assert api.getEnumerationDefinitionEnumeratedValueIDs(definition_id) == [value_id]
    xml = _assert_schema_valid(root)
    restored = XmlDocument.parser().from_string(xml, TypeDefinitions)
    assert len(api.getTypeDefinitionsEnumerationDefinitionIDs(get_handle(restored))) == 1


def test_builder_normalizes_tuple_only_after_validation_and_rejects_duplicate_names() -> None:
    existing = _definition("existing", values=[_value("old", "0")])
    tuple_definitions = (existing,)
    root = _root(tuple_definitions)
    root_id = get_handle(root)
    assert root.enumeration_definitions is not None
    typed_list = root.enumeration_definitions.enumeration_definition
    assert typed_list is tuple_definitions

    with pytest.raises(TgiError):
        api.addTypeDefinitionsEnumerationDefinition(root_id, "bad name", "4")
    assert root.enumeration_definitions.enumeration_definition is tuple_definitions
    with pytest.raises(TgiError):
        api.addTypeDefinitionsEnumerationDefinition(root_id, "existing", "4")
    assert root.enumeration_definitions.enumeration_definition is tuple_definitions

    added_id = api.addTypeDefinitionsEnumerationDefinition(root_id, "new", "4")
    assert isinstance(root.enumeration_definitions.enumeration_definition, list)
    assert root.enumeration_definitions.enumeration_definition == [existing, resolve_handle(added_id)]


@pytest.mark.parametrize("parsed", [False, True])
def test_remove_definition_invalidates_full_subtree_and_removes_last_optional_holder(parsed: bool) -> None:
    peer = _definition("peer", values=[_value("peer_value", "0")])
    target = _definition("target", values=[_value("first", "1"), _value("second", "2")])
    root = _root([target, peer])
    if parsed:
        xml = _assert_schema_valid(root)
        root = XmlDocument.parser().from_string(xml, TypeDefinitions)
    registry.register(root, ("example.org", "types", "device_types", "1.0"))
    root_id = get_handle(root)
    assert root.enumeration_definitions is not None
    target_model, peer_model = root.enumeration_definitions.enumeration_definition
    target_id, peer_id = get_handle(target_model), get_handle(peer_model)
    width_id = get_handle(target_model.width)
    value_ids = [get_handle(item) for item in target_model.enumerated_value]
    payload_ids = [get_handle(item.value) for item in target_model.enumerated_value]

    assert api.removeTypeDefinitionsEnumerationDefinition(target_id)
    assert api.getTypeDefinitionsEnumerationDefinitionIDs(root_id) == [peer_id]
    assert all(resolve_handle(handle) is None for handle in (target_id, width_id, *value_ids, *payload_ids))
    assert all(get_parent_info(handle) is None for handle in (target_id, width_id, *value_ids, *payload_ids))
    assert resolve_handle(peer_id) is not None
    assert resolve_handle(root_id) is root

    assert api.removeTypeDefinitionsEnumerationDefinition(peer_id)
    assert root.enumeration_definitions is None
    with pytest.raises(TgiError):
        api.removeTypeDefinitionsEnumerationDefinition(peer_id)


def test_remove_value_uses_actual_owner_invalidates_payload_and_keeps_empty_value_list() -> None:
    definition = _definition(values=[_value("first", "0"), _value("second", "1")])
    definition_id = get_handle(definition)
    first_id, second_id = api.getEnumerationDefinitionEnumeratedValueIDs(definition_id)
    first = resolve_handle(first_id)
    assert first is not None
    payload_id = get_handle(first.value)

    assert api.removeEnumerationDefinitionEnumeratedValue(first_id)
    assert api.getEnumerationDefinitionEnumeratedValueIDs(definition_id) == [second_id]
    assert resolve_handle(first_id) is None
    assert resolve_handle(payload_id) is None
    assert get_parent_info(first_id) is None
    assert get_parent_info(payload_id) is None
    assert resolve_handle(second_id) is not None

    assert api.removeEnumerationDefinitionEnumeratedValue(second_id)
    assert definition.enumerated_value == []
    assert api.getEnumerationDefinitionEnumeratedValueIDs(definition_id) == []
    with pytest.raises(TgiError):
        api.removeEnumerationDefinitionEnumeratedValue(second_id)


def test_removal_rejects_orphaned_mislinked_and_field_owned_values_atomically() -> None:
    first = _definition("first", values=[_value("one", "0")])
    second = _definition("second", values=[])
    first_id = get_handle(first)
    second_id = get_handle(second)
    value_id = api.getEnumerationDefinitionEnumeratedValueIDs(first_id)[0]
    value = resolve_handle(value_id)
    assert value is not None
    register_parent(value, second, ("enumerated_value",), "list")
    with pytest.raises(TgiError) as error:
        api.removeEnumerationDefinitionEnumeratedValue(value_id)
    assert error.value.fault_code == TgiFaultCode.INVALID_ID
    assert first.enumerated_value == [value]

    orphan_id = get_handle(_value("orphan", "0"))
    with pytest.raises(TgiError):
        api.removeEnumerationDefinitionEnumeratedValue(orphan_id)

    field_value = _value("field_value", "0")
    field = FieldDefinitions.FieldDefinition(
        name="field",
        bit_width=UnsignedPositiveIntExpression(value="1"),
        enumerated_values=EnumeratedValues(enumeration_definition_ref_or_enumerated_value=[field_value]),
    )
    field_id = get_handle(field)
    field_value_id = get_handle(field_value)
    register_parent(field_value, field, ("enumerated_values", "enumeration_definition_ref_or_enumerated_value"), "list")
    with pytest.raises(TgiError):
        api.removeEnumerationDefinitionEnumeratedValue(field_value_id)
    assert len(field.enumerated_values.enumeration_definition_ref_or_enumerated_value) == 1

    assert resolve_handle(first_id) is first
    assert resolve_handle(second_id) is second
    assert resolve_handle(field_id) is field


def test_definition_removal_rejects_wrong_owner_and_stale_handles() -> None:
    root = _root([_definition("target")])
    root_id = get_handle(root)
    definition_id = api.getTypeDefinitionsEnumerationDefinitionIDs(root_id)[0]
    other_root_id = get_handle(_root())
    with pytest.raises(TgiError):
        api.removeTypeDefinitionsEnumerationDefinition(other_root_id)
    assert api.getTypeDefinitionsEnumerationDefinitionIDs(root_id) == [definition_id]
    assert resolve_handle(definition_id) is not None

    assert api.removeTypeDefinitionsEnumerationDefinition(definition_id)
    with pytest.raises(TgiError):
        api.removeTypeDefinitionsEnumerationDefinition(definition_id)
    assert resolve_handle(root_id) is root


def test_parsed_value_removal_recovers_ownership_before_any_getter() -> None:
    root = _root([_definition(values=[_value("first", "0"), _value("second", "1")])])
    xml = _assert_schema_valid(root)
    root = XmlDocument.parser().from_string(xml, TypeDefinitions)
    registry.register(root, ("example.org", "types", "device_types", "1.0"))
    assert root.enumeration_definitions is not None
    owner = root.enumeration_definitions.enumeration_definition[0]
    first, second = owner.enumerated_value
    first_id = get_handle(first)
    payload_id = get_handle(first.value)
    second_id = get_handle(second)
    width_id = get_handle(owner.width)

    assert api.removeEnumerationDefinitionEnumeratedValue(first_id)
    assert owner.enumerated_value == [second]
    assert resolve_handle(first_id) is None
    assert resolve_handle(payload_id) is None
    assert resolve_handle(second_id) is second
    assert resolve_handle(width_id) is owner.width
    _assert_schema_valid(root)

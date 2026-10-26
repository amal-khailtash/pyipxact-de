"""Named field-slice references expose their XML names and owned handles."""

import inspect
from collections.abc import Iterator
from typing import cast

import pytest
from lxml import etree

from amal.eda.accellera.ipxact.v1685_2022 import tgi
from amal.eda.accellera.ipxact.v1685_2022.tgi import slice_ as api
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
    AddressBlockRef,
    AddressSpaces,
    AlternateRegisterRef,
    Component,
    ComponentPortDirectionType,
    ComponentType,
    FieldMap,
    FieldMaps,
    FieldRef,
    Index,
    Indices,
    Left,
    Model,
    Port,
    PortWireType,
    Range,
    RegisterRef,
    Right,
    UnsignedPositiveIntExpression,
    UnsignedPositiveLongintExpression,
)

_SCHEMA = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))
_ModeFieldSlice = ComponentType.Modes.Mode.FieldSlice
_MapFieldSlice = FieldMap.FieldSlice
_FieldSlice = _ModeFieldSlice | _MapFieldSlice
_FieldSliceType = type[_ModeFieldSlice] | type[_MapFieldSlice]

_OPERATIONS: tuple[tuple[str, str, str, type[object]], ...] = (
    ("AddressBlockRef", "address_block_ref", "address_block_ref", AddressBlockRef),
    ("FieldRef", "field_ref", "field_ref", FieldRef),
    ("AlternateRegisterRef", "alternate_register_ref", "alternate_register_ref", AlternateRegisterRef),
)


@pytest.fixture(autouse=True)
def clean_registry() -> Iterator[None]:
    registry.clear()
    yield
    registry.clear()


def _field_slice(kind: _FieldSliceType) -> _FieldSlice:
    if kind is _ModeFieldSlice:
        return _ModeFieldSlice(
            name="control_enable",
            address_space_ref_or_memory_map_ref_or_memory_remap_ref=[
                _ModeFieldSlice.AddressSpaceRef(address_space_ref="register_space")
            ],
            address_block_ref=AddressBlockRef(address_block_ref="registers"),
            register_ref=RegisterRef(register_ref="control"),
            field_ref=FieldRef(field_ref="enable"),
            alternate_register_ref=AlternateRegisterRef(alternate_register_ref="debug"),
            range=Range(left=Left(value="7"), right=Right(value="0")),
        )
    return _MapFieldSlice(
        address_space_ref_or_memory_map_ref_or_memory_remap_ref=[
            _MapFieldSlice.AddressSpaceRef(address_space_ref="register_space")
        ],
        address_block_ref=AddressBlockRef(address_block_ref="registers"),
        register_ref=RegisterRef(register_ref="control"),
        field_ref=FieldRef(field_ref="enable"),
        alternate_register_ref=AlternateRegisterRef(alternate_register_ref="debug"),
        range=Range(left=Left(value="7"), right=Right(value="0")),
    )


def _component(item: _FieldSlice) -> Component:
    port = Port(
        name="data_i",
        wire_or_transactional_or_structured=PortWireType(direction=ComponentPortDirectionType.IN),
    )
    if isinstance(item, _MapFieldSlice):
        port.field_maps = FieldMaps(field_map=[FieldMap(field_slice=item)])
        modes = None
    else:
        modes = ComponentType.Modes(mode=[ComponentType.Modes.Mode(name="active", field_slice=[item])])
    return Component(
        vendor="acme",
        library="devices",
        name="field_slice_component",
        version="1.0",
        model=Model(ports=Model.Ports(port=[port])),
        modes=modes,
        address_spaces=AddressSpaces(
            address_space=[
                AddressSpaces.AddressSpace(
                    name="register_space",
                    range=UnsignedPositiveLongintExpression(value="4096"),
                    width=UnsignedPositiveIntExpression(value="32"),
                )
            ]
        ),
    )


def _parsed_field_slice(kind: _FieldSliceType) -> _FieldSlice:
    root = _component(_field_slice(kind))
    xml = XmlDocument.serializer().render(root)
    tree = etree.fromstring(xml.encode())
    assert _SCHEMA.validate(tree), _SCHEMA.error_log
    parsed = XmlDocument.parser().from_string(xml, Component)
    assert XmlDocument.serializer().render(parsed) == xml
    if kind is _ModeFieldSlice:
        return parsed.modes.mode[0].field_slice[0]
    return parsed.model.ports.port[0].field_maps.field_map[0].field_slice


@pytest.mark.parametrize("kind", [_ModeFieldSlice, _MapFieldSlice], ids=["mode", "field-map"])
@pytest.mark.parametrize(
    "suffix,attribute,xml_attribute,wrapper", _OPERATIONS, ids=["address-block", "field", "alternate-register"]
)
def test_field_slice_named_reference_getters_return_stored_name_and_owned_wrapper(
    kind: _FieldSliceType, suffix: str, attribute: str, xml_attribute: str, wrapper: type[object]
) -> None:
    item = _field_slice(kind)
    field_slice_id = get_handle(item)
    child = getattr(item, attribute)
    expected = getattr(child, xml_attribute)

    by_name = getattr(api, f"getFieldSlice{suffix}ByName")
    by_id = getattr(api, f"getFieldSlice{suffix}ID")
    assert by_name(field_slice_id) == expected
    child_id = by_id(field_slice_id)
    assert child_id == get_handle(child)
    assert resolve_handle(child_id) is child
    parent = get_parent_info(child_id)
    assert parent is not None and parent.parent_handle == field_slice_id and parent.path == (attribute,)
    assert isinstance(resolve_handle(child_id), wrapper)


@pytest.mark.parametrize("kind", [_ModeFieldSlice, _MapFieldSlice], ids=["mode", "field-map"])
@pytest.mark.parametrize(
    "suffix,attribute,xml_attribute,wrapper", _OPERATIONS, ids=["address-block", "field", "alternate-register"]
)
def test_field_slice_named_reference_getters_are_neutral_when_wrapper_is_absent(
    kind: _FieldSliceType, suffix: str, attribute: str, xml_attribute: str, wrapper: type[object]
) -> None:
    item = _field_slice(kind)
    setattr(item, attribute, None)
    field_slice_id = get_handle(item)
    assert getattr(api, f"getFieldSlice{suffix}ByName")(field_slice_id) is None
    assert getattr(api, f"getFieldSlice{suffix}ID")(field_slice_id) is None


@pytest.mark.parametrize("kind", [_ModeFieldSlice, _MapFieldSlice], ids=["mode", "field-map"])
@pytest.mark.parametrize(
    "suffix,attribute,xml_attribute,wrapper", _OPERATIONS, ids=["address-block", "field", "alternate-register"]
)
def test_field_slice_named_reference_setters_update_wrapper_in_place_and_normalize_xml_whitespace(
    kind: _FieldSliceType, suffix: str, attribute: str, xml_attribute: str, wrapper: type[object]
) -> None:
    item = _field_slice(kind)
    field_slice_id = get_handle(item)
    child = getattr(item, attribute)
    child_id = get_handle(child)
    indices = Indices(
        index=[
            Index(
                value="3",
                id="slice-index",
                minimum=0,
                maximum=7,
                other_attributes={"{urn:test}preserved": "yes"},
            )
        ]
    )
    if isinstance(child, (AddressBlockRef, FieldRef)):
        index_node = indices.index[0]
        indices_id = get_handle(indices)
        index_id = get_handle(index_node)
    if isinstance(child, (AddressBlockRef, FieldRef)):
        child.indices = indices
    other_refs = (item.address_block_ref, item.field_ref, item.alternate_register_ref, item.register_ref, item.range)
    other_attributes = ("address_block_ref", "field_ref", "alternate_register_ref", "register_ref", "range")
    other_ids = tuple(get_handle(ref) for ref in other_refs)
    setter = getattr(api, f"setFieldSlice{suffix}")

    assert setter(field_slice_id, " \tΩ:register.item\n")
    assert getattr(item, attribute) is child
    assert getattr(child, xml_attribute) == "Ω:register.item"
    assert getattr(api, f"getFieldSlice{suffix}ID")(field_slice_id) == child_id
    assert resolve_handle(child_id) is child
    if isinstance(child, (AddressBlockRef, FieldRef)):
        assert child.indices is indices
        assert get_handle(child.indices) == indices_id
        assert child.indices.index[0] is index_node
        assert get_handle(index_node) == index_id
        assert (index_node.value, index_node.id, index_node.minimum, index_node.maximum) == (
            "3",
            "slice-index",
            0,
            7,
        )
        assert index_node.other_attributes == {"{urn:test}preserved": "yes"}
    assert tuple(getattr(item, name) for name in other_attributes) == other_refs
    assert tuple(get_handle(ref) for ref in other_refs) == other_ids

    xml = XmlDocument.serializer().render(_component(item))
    assert _SCHEMA.validate(etree.fromstring(xml.encode())), _SCHEMA.error_log
    parsed = XmlDocument.parser().from_string(xml, Component)
    assert XmlDocument.serializer().render(parsed) == xml
    parsed_slice = (
        parsed.modes.mode[0].field_slice[0]
        if kind is _ModeFieldSlice
        else parsed.model.ports.port[0].field_maps.field_map[0].field_slice
    )
    assert getattr(getattr(parsed_slice, attribute), xml_attribute) == "Ω:register.item"


@pytest.mark.parametrize("kind", [_ModeFieldSlice, _MapFieldSlice], ids=["mode", "field-map"])
@pytest.mark.parametrize(
    "suffix,attribute,xml_attribute,wrapper", _OPERATIONS, ids=["address-block", "field", "alternate-register"]
)
def test_field_slice_named_reference_setters_attach_absent_wrapper_and_register_typed_ownership(
    kind: _FieldSliceType, suffix: str, attribute: str, xml_attribute: str, wrapper: type[object]
) -> None:
    item = _field_slice(kind)
    setattr(item, attribute, None)
    field_slice_id = get_handle(item)
    setter = getattr(api, f"setFieldSlice{suffix}")

    assert setter(field_slice_id, "unresolved.forward_ref")
    child = getattr(item, attribute)
    assert isinstance(child, wrapper)
    assert getattr(child, xml_attribute) == "unresolved.forward_ref"
    child_id = getattr(api, f"getFieldSlice{suffix}ID")(field_slice_id)
    assert child_id == get_handle(child)
    info = get_parent_info(child_id)
    assert info is not None and info.parent_handle == field_slice_id and info.path == (attribute,)


@pytest.mark.parametrize("kind", [_ModeFieldSlice, _MapFieldSlice], ids=["mode", "field-map"])
@pytest.mark.parametrize(
    "suffix,attribute,xml_attribute,wrapper", _OPERATIONS, ids=["address-block", "field", "alternate-register"]
)
def test_field_slice_named_reference_setters_reject_invalid_name_without_mutation(
    kind: _FieldSliceType, suffix: str, attribute: str, xml_attribute: str, wrapper: type[object]
) -> None:
    item = _field_slice(kind)
    field_slice_id = get_handle(item)
    child = getattr(item, attribute)
    child_id = get_handle(child)
    original = getattr(child, xml_attribute)
    setter = getattr(api, f"setFieldSlice{suffix}")

    for value in ("", "   ", "1invalid", "has space", "bad/name", "nul\x00name", None, 12):
        with pytest.raises(TgiError) as error:
            setter(field_slice_id, cast(str, value))
        assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
        assert getattr(item, attribute) is child
        assert getattr(child, xml_attribute) == original
        assert getattr(api, f"getFieldSlice{suffix}ID")(field_slice_id) == child_id


@pytest.mark.parametrize("kind", [_ModeFieldSlice, _MapFieldSlice], ids=["mode", "field-map"])
@pytest.mark.parametrize(
    "suffix,attribute,xml_attribute,wrapper", _OPERATIONS, ids=["address-block", "field", "alternate-register"]
)
def test_field_slice_named_reference_getters_fault_on_malformed_existing_wrapper(
    kind: _FieldSliceType, suffix: str, attribute: str, xml_attribute: str, wrapper: type[object]
) -> None:
    item = _field_slice(kind)
    setattr(item, attribute, object())
    field_slice_id = get_handle(item)
    for operation in (f"getFieldSlice{suffix}ByName", f"getFieldSlice{suffix}ID"):
        with pytest.raises(TgiError) as error:
            getattr(api, operation)(field_slice_id)
        assert error.value.fault_code == TgiFaultCode.INVALID_ID
    with pytest.raises(TgiError) as error:
        getattr(api, f"setFieldSlice{suffix}")(field_slice_id, "replacement")
    assert error.value.fault_code == TgiFaultCode.INVALID_ID


@pytest.mark.parametrize("kind", [_ModeFieldSlice, _MapFieldSlice], ids=["mode", "field-map"])
@pytest.mark.parametrize(
    "suffix,attribute,xml_attribute,wrapper", _OPERATIONS, ids=["address-block", "field", "alternate-register"]
)
def test_field_slice_named_reference_name_getters_fault_on_malformed_source(
    kind: _FieldSliceType, suffix: str, attribute: str, xml_attribute: str, wrapper: type[object]
) -> None:
    item = _field_slice(kind)
    child = getattr(item, attribute)
    setattr(child, xml_attribute, 7)

    with pytest.raises(TgiError) as error:
        getattr(api, f"getFieldSlice{suffix}ByName")(get_handle(item))
    assert error.value.fault_code == TgiFaultCode.INVALID_ID


@pytest.mark.parametrize("kind", [_ModeFieldSlice, _MapFieldSlice], ids=["mode", "field-map"])
@pytest.mark.parametrize(
    "suffix,attribute,xml_attribute,wrapper", _OPERATIONS, ids=["address-block", "field", "alternate-register"]
)
def test_parsed_field_slice_named_reference_owners_work_without_prior_traversal(
    kind: _FieldSliceType, suffix: str, attribute: str, xml_attribute: str, wrapper: type[object]
) -> None:
    item = _parsed_field_slice(kind)
    field_slice_id = get_handle(item)
    child = getattr(item, attribute)
    expected_id = get_handle(child)

    assert getattr(api, f"getFieldSlice{suffix}ByName")(field_slice_id) == getattr(child, xml_attribute)
    assert getattr(api, f"getFieldSlice{suffix}ID")(field_slice_id) == expected_id
    assert getattr(api, f"setFieldSlice{suffix}")(field_slice_id, "parsed.updated")
    assert getattr(item, attribute) is child
    assert getattr(child, xml_attribute) == "parsed.updated"
    assert getattr(api, f"getFieldSlice{suffix}ID")(field_slice_id) == expected_id


@pytest.mark.parametrize("kind", [_ModeFieldSlice, _MapFieldSlice], ids=["mode", "field-map"])
def test_field_slice_alternate_register_removal_uses_owner_and_invalidates_only_its_child(
    kind: _FieldSliceType,
) -> None:
    item = _field_slice(kind)
    field_slice_id = get_handle(item)
    alternate_id = api.getFieldSliceAlternateRegisterRefID(field_slice_id)
    assert alternate_id is not None
    address_id = api.getFieldSliceAddressBlockRefID(field_slice_id)
    field_id = api.getFieldSliceFieldRefID(field_slice_id)
    register_id = get_handle(item.register_ref)
    range_id = get_handle(item.range)

    assert api.removeFieldSliceAlternateRegisterRef(field_slice_id)
    assert item.alternate_register_ref is None
    assert api.getFieldSliceAlternateRegisterRefID(field_slice_id) is None
    assert api.getFieldSliceAlternateRegisterRefByName(field_slice_id) is None
    assert resolve_handle(alternate_id) is None
    assert resolve_handle(field_slice_id) is item
    assert resolve_handle(address_id) is item.address_block_ref
    assert resolve_handle(field_id) is item.field_ref
    assert resolve_handle(register_id) is item.register_ref
    assert resolve_handle(range_id) is item.range
    assert api.removeFieldSliceAlternateRegisterRef(field_slice_id) is False
    with pytest.raises(TgiError) as error:
        api.removeFieldSliceAlternateRegisterRef(alternate_id)
    assert error.value.fault_code == TgiFaultCode.INVALID_ID
    invalid_owners = (
        get_handle(Range(left=Left(value="1"), right=Right(value="0"))),
        "missing-owner",
    )
    for invalid_owner in invalid_owners:
        with pytest.raises(TgiError) as error:
            api.removeFieldSliceAlternateRegisterRef(invalid_owner)
        assert error.value.fault_code == TgiFaultCode.INVALID_ID


@pytest.mark.parametrize("kind", [_ModeFieldSlice, _MapFieldSlice], ids=["mode", "field-map"])
def test_parsed_field_slice_alternate_register_removal_invalidates_child_without_getter_traversal(
    kind: _FieldSliceType,
) -> None:
    item = _parsed_field_slice(kind)
    child_id = get_handle(item.alternate_register_ref)
    owner_id = get_handle(item)

    assert api.removeFieldSliceAlternateRegisterRef(owner_id)
    assert item.alternate_register_ref is None
    assert resolve_handle(child_id) is None
    assert resolve_handle(owner_id) is item


@pytest.mark.parametrize("kind", [_ModeFieldSlice, _MapFieldSlice], ids=["mode", "field-map"])
@pytest.mark.parametrize(
    "suffix,attribute,xml_attribute,wrapper", _OPERATIONS, ids=["address-block", "field", "alternate-register"]
)
def test_field_slice_named_reference_operations_reject_invalid_owner_ids(
    kind: _FieldSliceType, suffix: str, attribute: str, xml_attribute: str, wrapper: type[object]
) -> None:
    foreign_id = get_handle(Range(left=Left(value="1"), right=Right(value="0")))
    for operation in (f"getFieldSlice{suffix}ByName", f"getFieldSlice{suffix}ID"):
        with pytest.raises(TgiError) as error:
            getattr(api, operation)(foreign_id)
        assert error.value.fault_code == TgiFaultCode.INVALID_ID
    with pytest.raises(TgiError) as error:
        getattr(api, f"setFieldSlice{suffix}")(foreign_id, "replacement")
    assert error.value.fault_code == TgiFaultCode.INVALID_ID
    assert resolve_handle(get_handle(_field_slice(kind))) is not None


def test_field_slice_named_reference_exports_and_native_signatures_match_tgi_contract() -> None:
    expected: dict[str, tuple[tuple[str, ...], tuple[object, ...], object]] = {}
    for suffix in ("AddressBlockRef", "FieldRef", "AlternateRegisterRef"):
        expected[f"getFieldSlice{suffix}ByName"] = (("fieldSliceID",), (str,), str | None)
        expected[f"getFieldSlice{suffix}ID"] = (("fieldSliceID",), (str,), str | None)
        expected[f"setFieldSlice{suffix}"] = (("fieldSliceID", suffix[0].lower() + suffix[1:]), (str, str), bool)
    expected["removeFieldSliceAlternateRegisterRef"] = (("fieldSliceID",), (str,), bool)

    assert set(expected) <= set(api.__all__)
    for name, (parameter_names, parameter_types, return_type) in expected.items():
        function = getattr(api, name)
        assert getattr(tgi, name) is function
        signature = inspect.signature(function)
        assert tuple(signature.parameters) == parameter_names
        assert tuple(parameter.annotation for parameter in signature.parameters.values()) == parameter_types
        assert all(not isinstance(parameter.annotation, str) for parameter in signature.parameters.values())
        assert signature.return_annotation == return_type

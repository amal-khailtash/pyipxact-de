"""Mode-owned field and port slice builders use generated schema models."""

import inspect
from collections.abc import Iterator, Sequence
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
    Component,
    ComponentPortDirectionType,
    ComponentType,
    FieldMap,
    FieldMaps,
    FieldRef,
    Index,
    Indices,
    Left,
    MemoryMaps,
    MemoryMapType,
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
_Mode = ComponentType.Modes.Mode
_ModeFieldSlice = _Mode.FieldSlice
_ModePortSlice = _Mode.PortSlice
_MapFieldSlice = FieldMap.FieldSlice
_FieldSlice = _ModeFieldSlice | _MapFieldSlice
_FieldSliceType = type[_ModeFieldSlice] | type[_MapFieldSlice]
_KINDS: tuple[_FieldSliceType, ...] = (_ModeFieldSlice, _MapFieldSlice)
_KIND_IDS = ("mode-field-slice", "field-map-field-slice")


@pytest.fixture(autouse=True)
def clean_registry() -> Iterator[None]:
    registry.clear()
    yield
    registry.clear()


def _field_slice(kind: _FieldSliceType, *, name: str = "control_enable") -> _FieldSlice:
    common = {
        "address_space_ref_or_memory_map_ref_or_memory_remap_ref": [kind.MemoryMapRef(memory_map_ref="register_map")],
        "address_block_ref": AddressBlockRef(address_block_ref="registers"),
        "register_ref": RegisterRef(
            register_ref="control",
            indices=Indices(index=[Index(value="2", id="register_index")]),
        ),
        "field_ref": FieldRef(field_ref="enable"),
        "range": Range(left=Left(value="7"), right=Right(value="0")),
    }
    if kind is _ModeFieldSlice:
        return _ModeFieldSlice(name=name, **common)
    return _MapFieldSlice(**common)


def _mode(
    *,
    field_slices: Sequence[_ModeFieldSlice] = (),
    port_slices: Sequence[_ModePortSlice] = (),
) -> _Mode:
    return _Mode(name="active", field_slice=field_slices, port_slice=port_slices)


def _component(mode: _Mode, field_map: FieldMap | None = None) -> Component:
    port = Port(
        name="data_i",
        wire_or_transactional_or_structured=PortWireType(direction=ComponentPortDirectionType.IN),
    )
    if field_map is not None:
        port.field_maps = FieldMaps(field_map=[field_map])
    return Component(
        vendor="acme",
        library="devices",
        name="mode_slice_builder_component",
        version="1.0",
        modes=ComponentType.Modes(mode=[mode]),
        address_spaces=AddressSpaces(
            address_space=[
                AddressSpaces.AddressSpace(
                    name="register_space",
                    range=UnsignedPositiveLongintExpression(value="4096"),
                    width=UnsignedPositiveIntExpression(value="32"),
                )
            ]
        ),
        memory_maps=MemoryMaps(memory_map=[MemoryMapType(name="register_map")]),
        model=Model(ports=Model.Ports(port=[port])),
    )


def _parsed_component(mode: _Mode, field_map: FieldMap | None = None) -> Component:
    root = _component(mode, field_map)
    xml = XmlDocument.serializer().render(root)
    assert _SCHEMA.validate(etree.fromstring(xml.encode())), _SCHEMA.error_log
    parsed = XmlDocument.parser().from_string(xml, Component)
    assert XmlDocument.serializer().render(parsed) == xml
    return parsed


def _assert_fault(operation: object, *args: object, code: TgiFaultCode = TgiFaultCode.INVALID_ID) -> None:
    with pytest.raises(TgiError) as error:
        cast(object, operation)(*args)
    assert error.value.fault_code == code


@pytest.mark.parametrize("kind", _KINDS, ids=_KIND_IDS)
def test_field_slice_register_reference_getters_and_setter_preserve_wrapper_indices(kind: _FieldSliceType) -> None:
    item = _field_slice(kind)
    owner_id = get_handle(item)
    register_ref = item.register_ref
    register_ref_id = get_handle(register_ref)
    indices = register_ref.indices
    indices_id = get_handle(indices)
    index = indices.index[0]
    index_id = get_handle(index)
    siblings = (item.address_block_ref, item.field_ref, item.range)
    sibling_ids = tuple(get_handle(child) for child in siblings)

    assert api.getFieldSliceRegisterRefByName(owner_id) == "control"
    assert api.getFieldSliceRegisterRefID(owner_id) == register_ref_id
    assert resolve_handle(register_ref_id) is register_ref
    assert api.setFieldSliceRegisterRef(owner_id, " \tΩ:updated.register\n")
    assert item.register_ref is register_ref
    assert item.register_ref.register_ref == "Ω:updated.register"
    assert api.getFieldSliceRegisterRefID(owner_id) == register_ref_id
    assert register_ref.indices is indices and get_handle(indices) == indices_id
    assert indices.index[0] is index and get_handle(index) == index_id
    assert (index.value, index.id) == ("2", "register_index")
    assert tuple(getattr(item, attr) for attr in ("address_block_ref", "field_ref", "range")) == siblings
    assert tuple(get_handle(child) for child in siblings) == sibling_ids


@pytest.mark.parametrize("kind", _KINDS, ids=_KIND_IDS)
def test_field_slice_register_reference_setter_creates_missing_wrapper(kind: _FieldSliceType) -> None:
    item = _field_slice(kind)
    item.register_ref = None  # type: ignore[assignment]
    owner_id = get_handle(item)
    assert api.getFieldSliceRegisterRefByName(owner_id) is None
    assert api.getFieldSliceRegisterRefID(owner_id) is None

    assert api.setFieldSliceRegisterRef(owner_id, "control")
    register_ref = item.register_ref
    assert isinstance(register_ref, RegisterRef)
    assert register_ref.register_ref == "control"
    register_id = api.getFieldSliceRegisterRefID(owner_id)
    assert register_id == get_handle(register_ref)
    info = get_parent_info(register_id)
    assert info is not None and info.parent_handle == owner_id and info.path == ("register_ref",)


@pytest.mark.parametrize("kind", _KINDS, ids=_KIND_IDS)
@pytest.mark.parametrize(
    "invalid",
    ("", "  ", "1invalid", "has space", "bad/name", "nul\x00name", None, 12),
    ids=("empty", "whitespace", "digit-start", "space", "slash", "nul", "none", "integer"),
)
def test_field_slice_register_setter_rejects_invalid_names_without_mutation(
    kind: _FieldSliceType, invalid: object
) -> None:
    item = _field_slice(kind)
    owner_id = get_handle(item)
    register_ref = item.register_ref
    register_id = get_handle(register_ref)
    before = register_ref.register_ref

    _assert_fault(api.setFieldSliceRegisterRef, owner_id, cast(str, invalid), code=TgiFaultCode.INVALID_ARGUMENT)
    assert item.register_ref is register_ref
    assert register_ref.register_ref == before
    assert api.getFieldSliceRegisterRefID(owner_id) == register_id


@pytest.mark.parametrize("kind", _KINDS, ids=_KIND_IDS)
def test_field_slice_register_reference_operations_reject_malformed_wrapper(kind: _FieldSliceType) -> None:
    item = _field_slice(kind)
    item.register_ref = object()  # type: ignore[assignment]
    owner_id = get_handle(item)
    _assert_fault(api.getFieldSliceRegisterRefByName, owner_id)
    _assert_fault(api.getFieldSliceRegisterRefID, owner_id)
    _assert_fault(api.setFieldSliceRegisterRef, owner_id, "replacement")


@pytest.mark.parametrize("collection", ("field_slice", "port_slice"), ids=("field", "port"))
def test_mode_slice_list_getters_return_owned_order_and_leave_tuples_unchanged(collection: str) -> None:
    first_field = _field_slice(_ModeFieldSlice, name="first")
    second_field = _field_slice(_ModeFieldSlice, name="second")
    first_port = _ModePortSlice(name="first_port", port_ref=_ModePortSlice.PortRef(port_ref="data_i"))
    second_port = _ModePortSlice(name="second_port", port_ref=_ModePortSlice.PortRef(port_ref="data_o"))
    mode = (
        _mode(field_slices=(first_field, second_field))
        if collection == "field_slice"
        else _mode(port_slices=(first_port, second_port))
    )
    setattr(mode, collection, tuple(getattr(mode, collection)))
    original = getattr(mode, collection)
    mode_id = get_handle(mode)
    suffix = "FieldSlice" if collection == "field_slice" else "PortSlice"
    children = original

    ids = getattr(api, f"getMode{suffix}IDs")(mode_id)
    assert ids == [get_handle(child) for child in children]
    assert getattr(mode, collection) is original and isinstance(original, tuple)
    for child_id, child in zip(ids, children, strict=True):
        assert resolve_handle(child_id) is child
        info = get_parent_info(child_id)
        assert info is not None and info.parent_handle == mode_id and info.path == (collection,)


@pytest.mark.parametrize("collection", ("field_slice", "port_slice"), ids=("field", "port"))
def test_mode_slice_list_getters_return_empty_lists_when_empty(collection: str) -> None:
    mode_id = get_handle(_mode())
    suffix = "FieldSlice" if collection == "field_slice" else "PortSlice"
    assert getattr(api, f"getMode{suffix}IDs")(mode_id) == []


@pytest.mark.parametrize(
    "collection,suffix,builder_args,child_attribute",
    [
        (
            "field_slice",
            "FieldSlice",
            ("new_field", "register_map", "registers", "control", "enable"),
            "field_slice",
        ),
        ("port_slice", "PortSlice", ("new_port", "data_i"), "port_slice"),
    ],
    ids=("field-slice", "port-slice"),
)
def test_mode_slice_builders_create_generated_owned_children_and_normalize_tuples(
    collection: str, suffix: str, builder_args: tuple[str, ...], child_attribute: str
) -> None:
    existing_field = _field_slice(_ModeFieldSlice, name="existing_field")
    existing_port = _ModePortSlice(name="existing_port", port_ref=_ModePortSlice.PortRef(port_ref="data_o"))
    mode = _mode(
        field_slices=(existing_field,),
        port_slices=(existing_port,),
    )
    mode.field_slice = tuple(mode.field_slice)
    mode.port_slice = tuple(mode.port_slice)
    mode_id = get_handle(mode)
    old_children = getattr(mode, collection)
    old_ids = getattr(api, f"getMode{suffix}IDs")(mode_id)
    builder = getattr(api, f"addMode{suffix}")
    child_id = builder(mode_id, *builder_args)
    children = getattr(mode, collection)

    assert isinstance(children, list)
    assert children[0] is old_children[0]
    assert children[1] is resolve_handle(child_id)
    assert getattr(api, f"getMode{suffix}IDs")(mode_id) == [*old_ids, child_id]
    info = get_parent_info(child_id)
    assert info is not None and info.parent_handle == mode_id and info.path == (collection,)

    child = children[1]
    if suffix == "FieldSlice":
        assert child.name == "new_field"
        assert child.address_space_ref_or_memory_map_ref_or_memory_remap_ref[0].memory_map_ref == "register_map"
        assert child.address_block_ref.address_block_ref == "registers"
        assert child.register_ref.register_ref == "control"
        assert child.field_ref.field_ref == "enable"
    else:
        assert child.name == "new_port"
        assert child.port_ref.port_ref == "data_i"
    assert isinstance(child, _ModeFieldSlice if suffix == "FieldSlice" else _ModePortSlice)
    assert child_attribute == collection


@pytest.mark.parametrize(
    "parameter,invalid",
    [
        ("name", "1bad"),
        ("memoryMapRef", "bad name"),
        ("addressBlockRef", "bad/name"),
        ("registerRef", ""),
        ("fieldRef", None),
    ],
    ids=("name", "memory-map", "address-block", "register", "field"),
)
def test_mode_field_slice_builder_validates_every_name_before_attaching(parameter: str, invalid: object) -> None:
    mode = _mode()
    mode.field_slice = ()
    mode.port_slice = ()
    mode_id = get_handle(mode)
    original_fields, original_ports = mode.field_slice, mode.port_slice
    values: dict[str, object] = {
        "name": "new_field",
        "memoryMapRef": "register_map",
        "addressBlockRef": "registers",
        "registerRef": "control",
        "fieldRef": "enable",
    }
    values[parameter] = invalid
    args = tuple(
        cast(str, values[name]) for name in ("name", "memoryMapRef", "addressBlockRef", "registerRef", "fieldRef")
    )

    _assert_fault(api.addModeFieldSlice, mode_id, *args, code=TgiFaultCode.INVALID_ARGUMENT)
    assert mode.field_slice is original_fields and mode.port_slice is original_ports


@pytest.mark.parametrize("parameter", ("name", "portRef"), ids=("name", "port"))
def test_mode_port_slice_builder_validates_every_name_before_attaching(parameter: str) -> None:
    mode = _mode()
    mode.port_slice = ()
    mode_id = get_handle(mode)
    original = mode.port_slice
    values = {"name": "new_port", "portRef": "data_i"}
    values[parameter] = "has space"

    _assert_fault(api.addModePortSlice, mode_id, values["name"], values["portRef"], code=TgiFaultCode.INVALID_ARGUMENT)
    assert mode.port_slice is original


def test_mode_slice_builders_round_trip_schema_valid_completed_slices() -> None:
    mode = _mode()
    mode_id = get_handle(mode)
    field_slice_id = api.addModeFieldSlice(
        mode_id,
        "built_field",
        "register_map",
        "registers",
        "control",
        "enable",
    )
    port_slice_id = api.addModePortSlice(mode_id, "built_port", "data_i")
    assert resolve_handle(field_slice_id) is mode.field_slice[0]
    assert resolve_handle(port_slice_id) is mode.port_slice[0]

    xml = XmlDocument.serializer().render(_component(mode))
    assert _SCHEMA.validate(etree.fromstring(xml.encode())), _SCHEMA.error_log
    parsed = XmlDocument.parser().from_string(xml, Component)
    assert XmlDocument.serializer().render(parsed) == xml
    parsed_mode = parsed.modes.mode[0]
    parsed_mode_id = get_handle(parsed_mode)
    parsed_field = resolve_handle(api.getModeFieldSliceIDs(parsed_mode_id)[0])
    parsed_port = resolve_handle(api.getModePortSliceIDs(parsed_mode_id)[0])
    assert isinstance(parsed_field, _ModeFieldSlice) and parsed_field.name == "built_field"
    assert isinstance(parsed_port, _ModePortSlice) and parsed_port.name == "built_port"


@pytest.mark.parametrize(
    "collection,suffix", [("field_slice", "FieldSlice"), ("port_slice", "PortSlice")], ids=("field", "port")
)
def test_mode_slice_builders_and_getters_reject_malformed_lists_and_wrong_types(collection: str, suffix: str) -> None:
    mode = _mode()
    mode_id = get_handle(mode)
    setattr(mode, collection, object())
    _assert_fault(getattr(api, f"getMode{suffix}IDs"), mode_id)
    operation = getattr(api, f"addMode{suffix}")
    args = (
        ("new_field", "register_map", "registers", "control", "enable")
        if suffix == "FieldSlice"
        else ("new_port", "data_i")
    )
    _assert_fault(operation, mode_id, *args)

    wrong_child = (
        _ModePortSlice(name="wrong", port_ref=_ModePortSlice.PortRef(port_ref="data_i"))
        if suffix == "FieldSlice"
        else _field_slice(_ModeFieldSlice)
    )
    wrong_id = get_handle(wrong_child)
    _assert_fault(getattr(api, f"getMode{suffix}IDs"), wrong_id)
    _assert_fault(operation, wrong_id, *args)
    remover = api.removeModeFieldSlice if suffix == "FieldSlice" else api.removeModePortSlice
    _assert_fault(remover, wrong_id)


@pytest.mark.parametrize("kind", _KINDS, ids=_KIND_IDS)
def test_mode_and_field_map_register_reference_access_is_typed_for_parsed_owners(kind: _FieldSliceType) -> None:
    item = _field_slice(kind)
    mode = _mode(field_slices=(cast(_ModeFieldSlice, item),)) if kind is _ModeFieldSlice else _mode()
    field_map = FieldMap(field_slice=cast(_MapFieldSlice, item)) if kind is _MapFieldSlice else None
    parsed = _parsed_component(mode, field_map)
    parsed_item = (
        parsed.modes.mode[0].field_slice[0]
        if kind is _ModeFieldSlice
        else parsed.model.ports.port[0].field_maps.field_map[0].field_slice
    )
    owner_id = get_handle(parsed_item)
    child = parsed_item.register_ref
    child_id = get_handle(child)

    assert api.getFieldSliceRegisterRefByName(owner_id) == "control"
    assert api.getFieldSliceRegisterRefID(owner_id) == child_id
    assert api.setFieldSliceRegisterRef(owner_id, "parsed.updated")
    assert parsed_item.register_ref is child and child.register_ref == "parsed.updated"


def test_remove_mode_field_slice_invalidates_child_and_all_reference_descendants() -> None:
    child = _field_slice(_ModeFieldSlice)
    mode = _mode(field_slices=(child,))
    mode_id = get_handle(mode)
    children = api.getModeFieldSliceIDs(mode_id)
    child_id = children[0]
    descendants = (
        get_handle(child.register_ref),
        get_handle(child.register_ref.indices),
        *(get_handle(index) for index in child.register_ref.indices.index),
        get_handle(child.field_ref),
        get_handle(child.address_block_ref),
    )

    assert api.removeModeFieldSlice(child_id)
    assert mode.field_slice == []
    assert api.getModeFieldSliceIDs(mode_id) == []
    assert resolve_handle(child_id) is None
    assert all(resolve_handle(descendant_id) is None for descendant_id in descendants)
    assert resolve_handle(mode_id) is mode
    _assert_fault(api.removeModeFieldSlice, child_id)


def test_remove_mode_port_slice_discovers_parsed_owner_and_invalidates_child() -> None:
    port_slice = _ModePortSlice(name="parsed_port", port_ref=_ModePortSlice.PortRef(port_ref="data_i"))
    parsed = _parsed_component(_mode(port_slices=(port_slice,)))
    mode = parsed.modes.mode[0]
    mode_id = get_handle(mode)
    port_slice_id = api.getModePortSliceIDs(mode_id)[0]
    port_ref_id = get_handle(mode.port_slice[0].port_ref)

    assert api.removeModePortSlice(port_slice_id)
    assert mode.port_slice == []
    assert api.getModePortSliceIDs(mode_id) == []
    assert resolve_handle(port_slice_id) is None
    assert resolve_handle(port_ref_id) is None
    assert resolve_handle(mode_id) is mode


def test_mode_slice_builder_exports_and_native_signatures_match_annex_contract() -> None:
    expected: dict[str, tuple[tuple[str, ...], tuple[object, ...], object]] = {
        "getFieldSliceRegisterRefByName": (("fieldSliceID",), (str,), str | None),
        "getFieldSliceRegisterRefID": (("fieldSliceID",), (str,), str | None),
        "setFieldSliceRegisterRef": (("fieldSliceID", "registerRef"), (str, str), bool),
        "getModeFieldSliceIDs": (("modeID",), (str,), list[str]),
        "getModePortSliceIDs": (("modeID",), (str,), list[str]),
        "addModeFieldSlice": (
            ("modeID", "name", "memoryMapRef", "addressBlockRef", "registerRef", "fieldRef"),
            (str, str, str, str, str, str),
            str,
        ),
        "addModePortSlice": (("modeID", "name", "portRef"), (str, str, str), str),
        "removeModeFieldSlice": (("modeFieldSliceID",), (str,), bool),
        "removeModePortSlice": (("modePortSliceID",), (str,), bool),
    }

    assert set(expected) <= set(api.__all__)
    for name, (parameter_names, parameter_types, return_type) in expected.items():
        function = getattr(api, name)
        assert getattr(tgi, name) is function
        signature = inspect.signature(function)
        assert tuple(signature.parameters) == parameter_names
        assert tuple(parameter.annotation for parameter in signature.parameters.values()) == parameter_types
        assert all(not isinstance(parameter.annotation, str) for parameter in signature.parameters.values())
        assert signature.return_annotation == return_type


def test_mode_port_slice_builder_uses_port_name_schema() -> None:
    mode = _Mode(name="active")
    with pytest.raises(TgiError) as error:
        api.addModePortSlice(get_handle(mode), "source", "data·i")
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert mode.port_slice == []

"""Field-slice address-space, memory-map, and remap choices preserve ownership."""

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
    Left,
    MemoryMaps,
    MemoryMapType,
    MemoryRemap,
    MemoryRemapRef,
    Model,
    ModeRef,
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
_ModeOrMapRef = _ModeFieldSlice.AddressSpaceRef | _ModeFieldSlice.MemoryMapRef
_ChoiceItem = _ModeOrMapRef | MemoryRemapRef
_Choice = Sequence[_ChoiceItem]
_KINDS: tuple[_FieldSliceType, ...] = (_ModeFieldSlice, _MapFieldSlice)
_KIND_IDS = ("mode", "field-map")


@pytest.fixture(autouse=True)
def clean_registry() -> Iterator[None]:
    registry.clear()
    yield
    registry.clear()


def _field_slice(kind: _FieldSliceType, choice: _Choice | None = None) -> _FieldSlice:
    initial_choice: _Choice = (
        choice
        if choice is not None
        else (kind.MemoryMapRef(memory_map_ref="register_map"), MemoryRemapRef(memory_remap_ref="window"))
    )
    if kind is _ModeFieldSlice:
        return _ModeFieldSlice(
            name="control_enable",
            address_space_ref_or_memory_map_ref_or_memory_remap_ref=initial_choice,
            address_block_ref=AddressBlockRef(address_block_ref="registers"),
            register_ref=RegisterRef(register_ref="control"),
            field_ref=FieldRef(field_ref="enable"),
            range=Range(left=Left(value="7"), right=Right(value="0")),
        )
    return _MapFieldSlice(
        address_space_ref_or_memory_map_ref_or_memory_remap_ref=initial_choice,
        address_block_ref=AddressBlockRef(address_block_ref="registers"),
        register_ref=RegisterRef(register_ref="control"),
        field_ref=FieldRef(field_ref="enable"),
        range=Range(left=Left(value="7"), right=Right(value="0")),
    )


def _component(item: _FieldSlice) -> Component:
    port = Port(
        name="data_i",
        wire_or_transactional_or_structured=PortWireType(direction=ComponentPortDirectionType.IN),
    )
    if isinstance(item, _MapFieldSlice):
        port.field_maps = FieldMaps(field_map=[FieldMap(field_slice=item)])
        modes = ComponentType.Modes(mode=[ComponentType.Modes.Mode(name="active")])
    else:
        modes = ComponentType.Modes(mode=[ComponentType.Modes.Mode(name="active", field_slice=[item])])
    return Component(
        vendor="acme",
        library="devices",
        name="field_slice_choice_component",
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
        memory_maps=MemoryMaps(
            memory_map=[
                MemoryMapType(
                    name="register_map",
                    choice=[MemoryRemap(name="window", mode_ref=[ModeRef(value="active", priority=0)])],
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


def _choice(item: _FieldSlice) -> _Choice:
    return cast(_Choice, item.address_space_ref_or_memory_map_ref_or_memory_remap_ref)


@pytest.mark.parametrize("kind", _KINDS, ids=_KIND_IDS)
@pytest.mark.parametrize(
    "suffix,attribute,xml_attribute,wrapper_name",
    [
        ("AddressSpaceRef", "address_space_ref", "address_space_ref", "AddressSpaceRef"),
        ("MemoryMapRef", "memory_map_ref", "memory_map_ref", "MemoryMapRef"),
        ("MemoryRemapRef", "memory_remap_ref", "memory_remap_ref", "MemoryRemapRef"),
    ],
    ids=("address-space", "memory-map", "memory-remap"),
)
def test_field_slice_choice_getters_return_names_and_owned_choice_wrappers(
    kind: _FieldSliceType, suffix: str, attribute: str, xml_attribute: str, wrapper_name: str
) -> None:
    if suffix == "AddressSpaceRef":
        choice: _Choice = (kind.AddressSpaceRef(address_space_ref="register_space"),)
    elif suffix == "MemoryMapRef":
        choice = (kind.MemoryMapRef(memory_map_ref="register_map"),)
    else:
        choice = (kind.MemoryMapRef(memory_map_ref="register_map"), MemoryRemapRef(memory_remap_ref="window"))
    item = _field_slice(kind, choice)
    owner_id = get_handle(item)
    children = _choice(item)
    child = next(child for child in children if hasattr(child, xml_attribute))
    child_id = get_handle(child)

    assert getattr(api, f"getFieldSlice{suffix}ByName")(owner_id) == getattr(child, xml_attribute)
    actual_id = getattr(api, f"getFieldSlice{suffix}ID")(owner_id)
    assert actual_id == child_id
    assert resolve_handle(actual_id) is child
    info = get_parent_info(actual_id)
    assert info is not None and info.parent_handle == owner_id
    assert info.path == ("address_space_ref_or_memory_map_ref_or_memory_remap_ref",)
    assert isinstance(child, getattr(kind, wrapper_name) if wrapper_name != "MemoryRemapRef" else MemoryRemapRef)


@pytest.mark.parametrize("kind", _KINDS, ids=_KIND_IDS)
def test_field_slice_choice_getters_are_neutral_for_empty_or_other_branch(kind: _FieldSliceType) -> None:
    item = _field_slice(kind, ())
    owner_id = get_handle(item)
    assert api.getFieldSliceAddressSpaceRefByName(owner_id) is None
    assert api.getFieldSliceAddressSpaceRefID(owner_id) is None
    assert api.getFieldSliceMemoryMapRefByName(owner_id) is None
    assert api.getFieldSliceMemoryMapRefID(owner_id) is None
    assert api.getFieldSliceMemoryRemapRefByName(owner_id) is None
    assert api.getFieldSliceMemoryRemapRefID(owner_id) is None

    item.address_space_ref_or_memory_map_ref_or_memory_remap_ref = [kind.AddressSpaceRef(address_space_ref="space")]
    assert api.getFieldSliceMemoryMapRefByName(owner_id) is None
    assert api.getFieldSliceMemoryMapRefID(owner_id) is None
    assert api.getFieldSliceMemoryRemapRefByName(owner_id) is None
    assert api.getFieldSliceMemoryRemapRefID(owner_id) is None


@pytest.mark.parametrize("kind", _KINDS, ids=_KIND_IDS)
def test_field_slice_choice_getters_do_not_normalize_tuple_collections(kind: _FieldSliceType) -> None:
    item = _field_slice(kind, (kind.AddressSpaceRef(address_space_ref="register_space"),))
    owner_id = get_handle(item)
    collection = item.address_space_ref_or_memory_map_ref_or_memory_remap_ref

    assert isinstance(collection, tuple)
    assert api.getFieldSliceAddressSpaceRefByName(owner_id) == "register_space"
    assert api.getFieldSliceAddressSpaceRefID(owner_id) == get_handle(collection[0])
    assert item.address_space_ref_or_memory_map_ref_or_memory_remap_ref is collection
    assert isinstance(item.address_space_ref_or_memory_map_ref_or_memory_remap_ref, tuple)


@pytest.mark.parametrize("kind", _KINDS, ids=_KIND_IDS)
def test_field_slice_choice_setters_preserve_same_branch_wrappers_and_normalize_collection(
    kind: _FieldSliceType,
) -> None:
    item = _field_slice(
        kind, (kind.MemoryMapRef(memory_map_ref="register_map"), MemoryRemapRef(memory_remap_ref="window"))
    )
    item.address_block_ref.address_block_ref = "registers"
    owner_id = get_handle(item)
    map_ref, remap_ref = _choice(item)
    map_id, remap_id = get_handle(map_ref), get_handle(remap_ref)
    unrelated = (item.address_block_ref, item.register_ref, item.field_ref, item.range)
    unrelated_ids = tuple(get_handle(child) for child in unrelated)

    assert api.setFieldSliceMemoryMapRef(owner_id, "  updated.map\t")
    assert api.setFieldSliceMemoryRemapRef(owner_id, " updated.window ")
    assert item.address_space_ref_or_memory_map_ref_or_memory_remap_ref == [map_ref, remap_ref]
    assert _choice(item)[0] is map_ref and _choice(item)[1] is remap_ref
    assert (map_ref.memory_map_ref, remap_ref.memory_remap_ref) == ("updated.map", "updated.window")
    assert api.getFieldSliceMemoryMapRefID(owner_id) == map_id
    assert api.getFieldSliceMemoryRemapRefID(owner_id) == remap_id
    assert resolve_handle(map_id) is map_ref and resolve_handle(remap_id) is remap_ref
    assert (
        tuple(getattr(item, attr) for attr in ("address_block_ref", "register_ref", "field_ref", "range")) == unrelated
    )
    assert tuple(get_handle(child) for child in unrelated) == unrelated_ids


@pytest.mark.parametrize("kind", _KINDS, ids=_KIND_IDS)
def test_field_slice_choice_setters_switch_branches_and_invalidate_detached_handles(kind: _FieldSliceType) -> None:
    item = _field_slice(kind)
    owner_id = get_handle(item)
    map_id = api.getFieldSliceMemoryMapRefID(owner_id)
    remap_id = api.getFieldSliceMemoryRemapRefID(owner_id)
    assert map_id is not None and remap_id is not None
    old_map, old_remap = _choice(item)

    assert api.setFieldSliceAddressSpaceRef(owner_id, " register_space ")
    address = _choice(item)[0]
    address_id = api.getFieldSliceAddressSpaceRefID(owner_id)
    assert isinstance(address, kind.AddressSpaceRef)
    assert address.address_space_ref == "register_space"
    assert address_id == get_handle(address)
    assert api.getFieldSliceMemoryMapRefID(owner_id) is None
    assert api.getFieldSliceMemoryRemapRefID(owner_id) is None
    assert resolve_handle(map_id) is None and resolve_handle(remap_id) is None
    assert api.setFieldSliceAddressSpaceRef(owner_id, "updated_space")
    assert _choice(item)[0] is address
    assert api.getFieldSliceAddressSpaceRefID(owner_id) == address_id
    assert address.address_space_ref == "updated_space"

    assert api.setFieldSliceMemoryMapRef(owner_id, "register_map")
    new_map = _choice(item)[0]
    assert isinstance(new_map, kind.MemoryMapRef)
    assert new_map.memory_map_ref == "register_map"
    assert api.getFieldSliceAddressSpaceRefID(owner_id) is None
    assert api.getFieldSliceMemoryMapRefID(owner_id) == get_handle(new_map)
    assert resolve_handle(address_id) is None
    assert old_map is not new_map and old_remap not in _choice(item)


@pytest.mark.parametrize("kind", _KINDS, ids=_KIND_IDS)
def test_field_slice_choice_setters_create_address_and_map_branches_from_empty(kind: _FieldSliceType) -> None:
    item = _field_slice(kind, ())
    owner_id = get_handle(item)
    assert api.setFieldSliceAddressSpaceRef(owner_id, "register_space")
    address = _choice(item)[0]
    assert isinstance(address, kind.AddressSpaceRef)
    assert api.setFieldSliceMemoryMapRef(owner_id, "register_map")
    memory_map = _choice(item)[0]
    assert isinstance(memory_map, kind.MemoryMapRef)
    assert len(_choice(item)) == 1
    assert api.getFieldSliceAddressSpaceRefID(owner_id) is None
    assert api.getFieldSliceMemoryMapRefByName(owner_id) == "register_map"


@pytest.mark.parametrize("kind", _KINDS, ids=_KIND_IDS)
def test_field_slice_remap_setter_requires_map_and_removal_keeps_map(kind: _FieldSliceType) -> None:
    item = _field_slice(kind, ())
    owner_id = get_handle(item)
    with pytest.raises(TgiError) as error:
        api.setFieldSliceMemoryRemapRef(owner_id, "window")
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert _choice(item) == ()

    assert api.setFieldSliceAddressSpaceRef(owner_id, "register_space")
    address_ref = _choice(item)[0]
    with pytest.raises(TgiError) as error:
        api.setFieldSliceMemoryRemapRef(owner_id, "window")
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert _choice(item) == [address_ref]

    assert api.setFieldSliceMemoryMapRef(owner_id, "register_map")
    map_ref = _choice(item)[0]
    map_id = get_handle(map_ref)
    assert api.setFieldSliceMemoryRemapRef(owner_id, "window")
    remap_id = api.getFieldSliceMemoryRemapRefID(owner_id)
    assert remap_id is not None
    assert api.removeFieldSliceMemoryRemapRef(owner_id)
    assert len(_choice(item)) == 1 and _choice(item)[0] is map_ref
    assert api.getFieldSliceMemoryMapRefID(owner_id) == map_id
    assert api.getFieldSliceMemoryRemapRefID(owner_id) is None
    assert resolve_handle(remap_id) is None and resolve_handle(map_id) is map_ref
    assert api.removeFieldSliceMemoryRemapRef(owner_id) is False
    with pytest.raises(TgiError) as error:
        api.removeFieldSliceMemoryRemapRef(remap_id)
    assert error.value.fault_code == TgiFaultCode.INVALID_ID


@pytest.mark.parametrize("kind", _KINDS, ids=_KIND_IDS)
@pytest.mark.parametrize(
    "suffix",
    ("AddressSpaceRef", "MemoryMapRef", "MemoryRemapRef"),
    ids=("address-space", "memory-map", "memory-remap"),
)
def test_field_slice_choice_setters_reject_bad_names_atomically(kind: _FieldSliceType, suffix: str) -> None:
    item = _field_slice(kind)
    owner_id = get_handle(item)
    before = _choice(item)
    before_ids = tuple(get_handle(child) for child in before)
    setter = getattr(api, f"setFieldSlice{suffix}")

    for invalid in ("", "  ", "1invalid", "has space", "bad/name", "nul\x00name", None, 12):
        with pytest.raises(TgiError) as error:
            setter(owner_id, cast(str, invalid))
        assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
        assert _choice(item) == before
        assert tuple(get_handle(child) for child in _choice(item)) == before_ids


@pytest.mark.parametrize("kind", _KINDS, ids=_KIND_IDS)
@pytest.mark.parametrize(
    "malformed_case",
    (
        "remap-without-map",
        "scalar-child",
        "list-child",
        "unknown-child",
        "reversed-order",
        "mixed-address-map",
        "reversed-map-address",
        "duplicate-map",
        "duplicate-remap",
        "remap-with-address",
    ),
    ids=(
        "remap-without-map",
        "scalar-child",
        "list-child",
        "unknown-child",
        "reversed-order",
        "mixed-address-map",
        "reversed-map-address",
        "duplicate-map",
        "duplicate-remap",
        "remap-with-address",
    ),
)
def test_field_slice_choice_operations_reject_malformed_models_atomically(
    kind: _FieldSliceType, malformed_case: str
) -> None:
    address_ref = kind.AddressSpaceRef(address_space_ref="register_space")
    map_ref = kind.MemoryMapRef(memory_map_ref="register_map")
    remap_ref = MemoryRemapRef(memory_remap_ref="window")
    malformed: dict[str, tuple[object, ...]] = {
        "remap-without-map": (remap_ref,),
        "scalar-child": ("scalar",),
        "list-child": ([map_ref],),
        "unknown-child": (object(),),
        "reversed-order": (remap_ref, map_ref),
        "mixed-address-map": (address_ref, map_ref),
        "reversed-map-address": (map_ref, address_ref),
        "duplicate-map": (map_ref, kind.MemoryMapRef(memory_map_ref="register_map")),
        "duplicate-remap": (map_ref, remap_ref, MemoryRemapRef(memory_remap_ref="window")),
        "remap-with-address": (address_ref, remap_ref),
    }
    choice = malformed[malformed_case]
    item = _field_slice(kind, cast(_Choice, choice))
    owner_id = get_handle(item)
    before = item.address_space_ref_or_memory_map_ref_or_memory_remap_ref
    before_children = tuple(before)

    for operation in (
        "getFieldSliceAddressSpaceRefByName",
        "getFieldSliceAddressSpaceRefID",
        "getFieldSliceMemoryMapRefByName",
        "getFieldSliceMemoryMapRefID",
        "getFieldSliceMemoryRemapRefByName",
        "getFieldSliceMemoryRemapRefID",
    ):
        with pytest.raises(TgiError) as error:
            getattr(api, operation)(owner_id)
        assert error.value.fault_code == TgiFaultCode.INVALID_ID
    for operation in ("setFieldSliceAddressSpaceRef", "setFieldSliceMemoryMapRef", "setFieldSliceMemoryRemapRef"):
        with pytest.raises(TgiError) as error:
            getattr(api, operation)(owner_id, "replacement")
        assert error.value.fault_code == TgiFaultCode.INVALID_ID
        assert item.address_space_ref_or_memory_map_ref_or_memory_remap_ref is before
        assert tuple(before) == before_children


@pytest.mark.parametrize("kind", _KINDS, ids=_KIND_IDS)
def test_parsed_field_slice_choice_handles_mutate_and_invalidate_before_child_traversal(kind: _FieldSliceType) -> None:
    item = _parsed_field_slice(kind)
    owner_id = get_handle(item)
    attr = "address_space_ref_or_memory_map_ref_or_memory_remap_ref"
    old_children = tuple(getattr(item, attr))
    old_ids = tuple(get_handle(child) for child in old_children)
    assert api.setFieldSliceAddressSpaceRef(owner_id, "register_space")
    assert api.getFieldSliceAddressSpaceRefByName(owner_id) == "register_space"
    assert all(resolve_handle(child_id) is None for child_id in old_ids)
    current_id = api.getFieldSliceAddressSpaceRefID(owner_id)
    assert current_id is not None and resolve_handle(current_id) is getattr(item, attr)[0]
    assert get_parent_info(current_id) is not None
    assert getattr(item, attr)[0] is not old_children[0]

    assert api.setFieldSliceMemoryMapRef(owner_id, "register_map")
    assert api.setFieldSliceMemoryRemapRef(owner_id, "window")
    xml = XmlDocument.serializer().render(_component(item))
    assert _SCHEMA.validate(etree.fromstring(xml.encode())), _SCHEMA.error_log
    parsed_root = XmlDocument.parser().from_string(xml, Component)
    assert XmlDocument.serializer().render(parsed_root) == xml
    if kind is _ModeFieldSlice:
        parsed_item = parsed_root.modes.mode[0].field_slice[0]
    else:
        parsed_item = parsed_root.model.ports.port[0].field_maps.field_map[0].field_slice
    parsed_owner_id = get_handle(parsed_item)
    assert api.getFieldSliceMemoryMapRefByName(parsed_owner_id) == "register_map"
    assert api.getFieldSliceMemoryRemapRefByName(parsed_owner_id) == "window"
    assert len(_choice(parsed_item)) == 2


def test_field_slice_choice_exports_and_native_signatures_match_tgi_contract() -> None:
    expected: dict[str, tuple[tuple[str, ...], tuple[object, ...], object]] = {}
    for suffix in ("AddressSpaceRef", "MemoryMapRef", "MemoryRemapRef"):
        expected[f"getFieldSlice{suffix}ByName"] = (("fieldSliceID",), (str,), str | None)
        expected[f"getFieldSlice{suffix}ID"] = (("fieldSliceID",), (str,), str | None)
        expected[f"setFieldSlice{suffix}"] = (("fieldSliceID", suffix[0].lower() + suffix[1:]), (str, str), bool)
    expected["removeFieldSliceMemoryRemapRef"] = (("fieldSliceID",), (str,), bool)

    assert set(expected) <= set(api.__all__)
    for name, (parameter_names, parameter_types, return_type) in expected.items():
        function = getattr(api, name)
        assert getattr(tgi, name) is function
        signature = inspect.signature(function)
        assert tuple(signature.parameters) == parameter_names
        assert tuple(parameter.annotation for parameter in signature.parameters.values()) == parameter_types
        assert all(not isinstance(parameter.annotation, str) for parameter in signature.parameters.values())
        assert signature.return_annotation == return_type

"""Memory-map and memory-remap references on indirect address/data references."""

import inspect
from collections.abc import Iterator

import pytest
from lxml import etree

from amal.eda.accellera.ipxact.v1685_2022 import tgi
from amal.eda.accellera.ipxact.v1685_2022.tgi import indirect_interface as api
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
    BaseAddress,
    Component,
    ComponentType,
    FieldRef,
    IndirectAddressRef,
    IndirectDataRef,
    IndirectInterface,
    IndirectInterfaces,
    MemoryMaps,
    MemoryMapType,
    MemoryRemap,
    MemoryRemapRef,
    ModeRef,
    UnsignedPositiveIntExpression,
    UnsignedPositiveLongintExpression,
)

_SCHEMA = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))
_CHOICE = "address_space_ref_or_memory_map_ref_or_memory_remap_ref"
_KINDS = ("address", "data")
_GETTERS = (
    "getIndirectAddressRefMemoryRemapRefByID",
    "getIndirectAddressRefMemoryRemapRefByName",
    "getIndirectAddressRefMemoryRemapRefID",
    "getIndirectDataRefMemoryRemapRefByID",
    "getIndirectDataRefMemoryRemapRefByName",
    "getIndirectDataRefMemoryRemapRefID",
)
_REMOVERS = (
    "removeIndirectAddressRefMemoryMapRef",
    "removeIndirectAddressRefMemoryRemapRef",
    "removeIndirectDataRefMemoryMapRef",
    "removeIndirectDataRefMemoryRemapRef",
)
_API_FUNCTIONS = (*_GETTERS, *_REMOVERS)


@pytest.fixture(autouse=True)
def clean_registry() -> Iterator[None]:
    registry.clear()
    yield
    registry.clear()


def _choice_item(kind: str, choice: str, value: str) -> object:
    owner_type = IndirectAddressRef if kind == "address" else IndirectDataRef
    if choice == "memory_map":
        return owner_type.MemoryMapRef(memory_map_ref=value)
    return MemoryRemapRef(memory_remap_ref=value)


def _owner(kind: str, choices: object = ()) -> IndirectAddressRef | IndirectDataRef:
    owner_type = IndirectAddressRef if kind == "address" else IndirectDataRef
    return owner_type(
        address_space_ref_or_memory_map_ref_or_memory_remap_ref=choices,
        field_ref=FieldRef(field_ref=f"{kind}_field"),
    )


def _address_block(name: str) -> AddressBlock:
    return AddressBlock(
        name=name,
        base_address=BaseAddress(value="0"),
        choice=[UnsignedPositiveLongintExpression(value="64"), UnsignedPositiveIntExpression(value="32")],
    )


def _component(
    address_choices: object = (), data_choices: object = (), *, name: str = "indirect_memory_remap"
) -> Component:
    return Component(
        vendor="acme",
        library="devices",
        name=name,
        version="1.0",
        memory_maps=MemoryMaps(
            memory_map=[
                MemoryMapType(
                    name="map_a",
                    choice=[
                        MemoryRemap(
                            name="window_a",
                            mode_ref=[ModeRef(value="mode_a", priority=0)],
                            choice=[_address_block("remap_a")],
                        )
                    ],
                ),
                MemoryMapType(
                    name="map_b",
                    choice=[
                        MemoryRemap(
                            name="window_b",
                            mode_ref=[ModeRef(value="mode_b", priority=0)],
                            choice=[_address_block("remap_b")],
                        )
                    ],
                ),
            ]
        ),
        modes=ComponentType.Modes(
            mode=[
                ComponentType.Modes.Mode(name="mode_a"),
                ComponentType.Modes.Mode(name="mode_b"),
                ComponentType.Modes.Mode(name="mode_duplicate"),
            ]
        ),
        indirect_interfaces=IndirectInterfaces(
            indirect_interface=[
                IndirectInterface(
                    name="primary",
                    indirect_address_ref=_owner("address", address_choices),
                    indirect_data_ref=_owner("data", data_choices),
                    memory_map_ref_or_transparent_bridge=["map_a"],
                ),
                IndirectInterface(
                    name="peer",
                    indirect_address_ref=_owner(
                        "address",
                        (
                            _choice_item("address", "memory_map", "map_b"),
                            _choice_item("address", "memory_remap", "window_b"),
                        ),
                    ),
                    indirect_data_ref=_owner(
                        "data",
                        (_choice_item("data", "memory_map", "map_b"), _choice_item("data", "memory_remap", "window_b")),
                    ),
                    memory_map_ref_or_transparent_bridge=["map_b"],
                ),
            ]
        ),
    )


def _parsed_component(root: Component) -> Component:
    xml = XmlDocument.serializer().render(root)
    _SCHEMA.assertValid(etree.fromstring(xml.encode()))
    parsed = XmlDocument.parser().from_string(xml, Component)
    assert XmlDocument.serializer().render(parsed) == xml
    registry.register(parsed, (parsed.vendor, parsed.library, parsed.name, parsed.version))
    return parsed


def _owner_for(root: Component, kind: str, index: int = 0) -> IndirectAddressRef | IndirectDataRef:
    interface = root.indirect_interfaces.indirect_interface[index]
    owner = interface.indirect_address_ref if kind == "address" else interface.indirect_data_ref
    assert owner is not None
    return owner


def _operations(kind: str) -> tuple[str, str, str, str]:
    prefix = "Address" if kind == "address" else "Data"
    return (
        f"getIndirect{prefix}RefMemoryRemapRefByID",
        f"getIndirect{prefix}RefMemoryRemapRefByName",
        f"getIndirect{prefix}RefMemoryRemapRefID",
        f"removeIndirect{prefix}RefMemoryMapRef",
    )


def test_public_exports_native_signatures_and_annex_f_sections() -> None:
    expected = {
        "getIndirectAddressRefMemoryRemapRefByID": ("indirectAddressRefID", str | None, "F.7.53.13"),
        "getIndirectAddressRefMemoryRemapRefByName": ("indirectAddressRefID", str | None, "F.7.53.14"),
        "getIndirectAddressRefMemoryRemapRefID": ("indirectAddressRefID", str | None, "F.7.53.15"),
        "getIndirectDataRefMemoryRemapRefByID": ("indirectDataRefID", str | None, "F.7.53.32"),
        "getIndirectDataRefMemoryRemapRefByName": ("indirectDataRefID", str | None, "F.7.53.33"),
        "getIndirectDataRefMemoryRemapRefID": ("indirectDataRefID", str | None, "F.7.53.34"),
        "removeIndirectAddressRefMemoryMapRef": ("indirectAddressRefID", bool, "F.7.54.12"),
        "removeIndirectAddressRefMemoryRemapRef": ("indirectAddressRefID", bool, "F.7.54.13"),
        "removeIndirectDataRefMemoryMapRef": ("indirectDataRefID", bool, "F.7.54.20"),
        "removeIndirectDataRefMemoryRemapRef": ("indirectDataRefID", bool, "F.7.54.21"),
    }

    assert set(_API_FUNCTIONS) == set(expected)
    assert set(_API_FUNCTIONS) <= set(api.__all__)
    assert set(_API_FUNCTIONS) <= set(tgi.__all__)
    for name, (parameter_name, return_type, section) in expected.items():
        function = getattr(api, name)
        assert getattr(tgi, name) is function
        signature = inspect.signature(function)
        assert tuple(signature.parameters) == (parameter_name,)
        parameter = next(iter(signature.parameters.values()))
        assert parameter.annotation is str
        assert not isinstance(parameter.annotation, str)
        assert parameter.default is inspect.Signature.empty
        assert signature.return_annotation == return_type
        assert f"Section: {section}." in inspect.getdoc(function)


@pytest.mark.parametrize("kind", _KINDS)
def test_getters_return_name_reference_id_and_resolved_remap_target(kind: str) -> None:
    choices = (_choice_item(kind, "memory_map", "map_a"), _choice_item(kind, "memory_remap", "window_a"))
    root = _parsed_component(
        _component(address_choices=choices if kind == "address" else (), data_choices=choices if kind == "data" else ())
    )
    owner = _owner_for(root, kind)
    owner_id = get_handle(owner)
    map_ref, remap_ref = getattr(owner, _CHOICE)
    map_ref_id, remap_ref_id = get_handle(map_ref), get_handle(remap_ref)
    target = root.memory_maps.memory_map[0].choice[0]
    target_id = get_handle(target)
    by_id, by_name, ref_id_getter, _ = _operations(kind)

    assert getattr(api, by_id)(owner_id) == target_id
    assert getattr(api, by_id)(owner_id) not in ("window_a", remap_ref_id)
    assert getattr(api, by_name)(owner_id) == "window_a"
    assert getattr(api, ref_id_getter)(owner_id) == remap_ref_id
    assert resolve_handle(target_id) is target
    assert resolve_handle(remap_ref_id) is remap_ref
    info = get_parent_info(remap_ref_id)
    assert info is not None and info.parent_handle == owner_id
    assert info.path == (_CHOICE,) and info.container == "list"
    assert getattr(owner, _CHOICE) == [map_ref, remap_ref]
    assert get_handle(map_ref) == map_ref_id


@pytest.mark.parametrize("kind", _KINDS)
def test_getters_return_none_for_absent_choice_without_changing_tuple(kind: str) -> None:
    owner = _owner(kind, ())
    original = ()
    setattr(owner, _CHOICE, original)
    owner_id = get_handle(owner)
    by_id, by_name, ref_id_getter, map_remover = _operations(kind)
    remap_remover = f"removeIndirect{'Address' if kind == 'address' else 'Data'}RefMemoryRemapRef"

    assert getattr(api, by_id)(owner_id) is None
    assert getattr(api, by_name)(owner_id) is None
    assert getattr(api, ref_id_getter)(owner_id) is None
    assert getattr(api, map_remover)(owner_id) is False
    assert getattr(api, remap_remover)(owner_id) is False
    assert getattr(owner, _CHOICE) is original


@pytest.mark.parametrize("kind", _KINDS)
def test_name_getter_rejects_invalid_xml_name_while_reference_id_is_repairable(kind: str) -> None:
    memory_map_ref = _choice_item(kind, "memory_map", "map_a")
    remap_ref = _choice_item(kind, "memory_remap", "bad name")
    choices = (memory_map_ref, remap_ref)
    root = _component(
        address_choices=choices if kind == "address" else (),
        data_choices=choices if kind == "data" else (),
    )
    owner_in_root = _owner_for(root, kind)
    setattr(owner_in_root, _CHOICE, choices)
    registry.register(root, (root.vendor, root.library, root.name, root.version))
    owner_id = get_handle(owner_in_root)
    _, by_name, ref_id_getter, _ = _operations(kind)

    reference_id = getattr(api, ref_id_getter)(owner_id)
    assert reference_id == get_handle(remap_ref)
    with pytest.raises(TgiError) as error:
        getattr(api, by_name)(owner_id)
    assert error.value.fault_code == TgiFaultCode.INVALID_ID
    assert remap_ref.memory_remap_ref == "bad name"
    assert getattr(owner_in_root, _CHOICE) is choices
    assert getattr(api, ref_id_getter)(owner_id) == reference_id
    remap_ref.memory_remap_ref = "window_a"
    assert getattr(api, by_name)(owner_id) == "window_a"


@pytest.mark.parametrize("kind", _KINDS)
def test_by_id_reports_missing_target_without_changing_reference(kind: str) -> None:
    choices = (_choice_item(kind, "memory_map", "map_a"), _choice_item(kind, "memory_remap", "missing_window"))
    root = _component(
        address_choices=choices if kind == "address" else (),
        data_choices=choices if kind == "data" else (),
    )
    registry.register(root, (root.vendor, root.library, root.name, root.version))
    owner = _owner_for(root, kind)
    owner_id = get_handle(owner)
    _, by_name, ref_id_getter, _ = _operations(kind)
    by_id = _operations(kind)[0]
    reference = getattr(owner, _CHOICE)[1]
    reference_id = getattr(api, ref_id_getter)(owner_id)

    assert getattr(api, by_name)(owner_id) == "missing_window"
    assert reference.memory_remap_ref == "missing_window"
    with pytest.raises(TgiError) as error:
        getattr(api, by_id)(owner_id)
    assert error.value.fault_code == TgiFaultCode.NOT_FOUND
    assert getattr(api, ref_id_getter)(owner_id) == reference_id
    assert reference.memory_remap_ref == "missing_window"


@pytest.mark.parametrize("kind", _KINDS)
def test_by_id_qualifies_duplicate_remap_names_with_memory_map(kind: str) -> None:
    choices = (_choice_item(kind, "memory_map", "map_a"), _choice_item(kind, "memory_remap", "window_a"))
    root = _component(
        address_choices=choices if kind == "address" else (),
        data_choices=choices if kind == "data" else (),
    )
    map_b = root.memory_maps.memory_map[1]
    duplicate_target = MemoryRemap(
        name="window_a",
        mode_ref=[ModeRef(value="mode_duplicate", priority=0)],
        choice=[_address_block("duplicate")],
    )
    map_b.choice = [*map_b.choice, duplicate_target]
    peer_owner = _owner_for(root, kind, index=1)
    peer_choices = getattr(peer_owner, _CHOICE)
    peer_choices[1].memory_remap_ref = "window_a"
    parsed = _parsed_component(root)

    primary = _owner_for(parsed, kind)
    peer = _owner_for(parsed, kind, index=1)
    primary_target = parsed.memory_maps.memory_map[0].choice[0]
    peer_target = parsed.memory_maps.memory_map[1].choice[1]
    by_id = _operations(kind)[0]

    assert getattr(api, by_id)(get_handle(primary)) == get_handle(primary_target)
    assert getattr(api, by_id)(get_handle(peer)) == get_handle(peer_target)
    assert getattr(api, by_id)(get_handle(primary)) != getattr(api, by_id)(get_handle(peer))


@pytest.mark.parametrize("kind", _KINDS)
@pytest.mark.parametrize("operation", _GETTERS + _REMOVERS)
def test_invalid_owner_handle_raises_without_mutating_component(kind: str, operation: str) -> None:
    choices = (_choice_item(kind, "memory_map", "map_a"), _choice_item(kind, "memory_remap", "window_a"))
    root = _component(
        address_choices=choices if kind == "address" else (),
        data_choices=choices if kind == "data" else (),
    )
    registry.register(root, (root.vendor, root.library, root.name, root.version))
    owner = _owner_for(root, kind)
    before = tuple(getattr(owner, _CHOICE))
    wrong_owner_id = get_handle(root)

    with pytest.raises(TgiError) as error:
        getattr(api, operation)(wrong_owner_id)
    assert error.value.fault_code == TgiFaultCode.INVALID_ID
    assert tuple(getattr(owner, _CHOICE)) == before


@pytest.mark.parametrize("kind", _KINDS)
@pytest.mark.parametrize(
    "invalid_choices",
    [
        (MemoryRemapRef(memory_remap_ref="window_a"),),
        (
            IndirectAddressRef.MemoryMapRef(memory_map_ref="map_a"),
            IndirectAddressRef.MemoryMapRef(memory_map_ref="map_b"),
        ),
        (
            MemoryRemapRef(memory_remap_ref="window_a"),
            IndirectAddressRef.MemoryMapRef(memory_map_ref="map_a"),
        ),
    ],
    ids=("remap-only", "multiple-maps", "reversed-order"),
)
def test_invalid_choice_shape_fails_atomically(kind: str, invalid_choices: tuple[object, ...]) -> None:
    owner_type = IndirectAddressRef if kind == "address" else IndirectDataRef
    invalid_choices = tuple(
        owner_type.MemoryMapRef(memory_map_ref=item.memory_map_ref)
        if isinstance(item, IndirectAddressRef.MemoryMapRef)
        else item
        for item in invalid_choices
    )
    root = _component()
    owner = _owner_for(root, kind)
    setattr(owner, _CHOICE, invalid_choices)
    registry.register(root, (root.vendor, root.library, root.name, root.version))
    owner_id = get_handle(owner)
    before = getattr(owner, _CHOICE)
    operations = _operations(kind)
    remap_remover = f"removeIndirect{'Address' if kind == 'address' else 'Data'}RefMemoryRemapRef"

    for operation in (*operations[:3], operations[3], remap_remover):
        with pytest.raises(TgiError) as error:
            getattr(api, operation)(owner_id)
        assert error.value.fault_code == TgiFaultCode.INVALID_ID
        assert getattr(owner, _CHOICE) is before


@pytest.mark.parametrize("kind", _KINDS)
def test_remove_map_reference_removes_companion_remap_and_invalidates_only_owned_children(kind: str) -> None:
    choices = (_choice_item(kind, "memory_map", "map_a"), _choice_item(kind, "memory_remap", "window_a"))
    root = _parsed_component(
        _component(address_choices=choices if kind == "address" else (), data_choices=choices if kind == "data" else ())
    )
    owner, peer = _owner_for(root, kind), _owner_for(root, kind, index=1)
    owner_id, peer_id = get_handle(owner), get_handle(peer)
    map_ref, remap_ref = getattr(owner, _CHOICE)
    map_ref_id, remap_ref_id = get_handle(map_ref), get_handle(remap_ref)
    peer_map_ref, peer_remap_ref = getattr(peer, _CHOICE)
    peer_map_id, peer_remap_id = get_handle(peer_map_ref), get_handle(peer_remap_ref)
    target = root.memory_maps.memory_map[0].choice[0]
    target_id = get_handle(target)
    map_remover = _operations(kind)[3]
    remap_remover = f"removeIndirect{'Address' if kind == 'address' else 'Data'}RefMemoryRemapRef"

    assert getattr(api, map_remover)(owner_id) is True
    assert getattr(owner, _CHOICE) == []
    assert resolve_handle(map_ref_id) is None
    assert resolve_handle(remap_ref_id) is None
    assert resolve_handle(owner_id) is owner
    assert resolve_handle(peer_id) is peer
    assert resolve_handle(peer_map_id) is peer_map_ref
    assert resolve_handle(peer_remap_id) is peer_remap_ref
    assert resolve_handle(target_id) is target
    assert getattr(api, map_remover)(owner_id) is False
    assert getattr(api, remap_remover)(owner_id) is False
    xml = XmlDocument.serializer().render(root)
    _SCHEMA.assertValid(etree.fromstring(xml.encode()))


@pytest.mark.parametrize("kind", _KINDS)
def test_remove_remap_reference_preserves_map_reference_and_invalidates_remap_handle(kind: str) -> None:
    choices = (_choice_item(kind, "memory_map", "map_a"), _choice_item(kind, "memory_remap", "window_a"))
    root = _parsed_component(
        _component(address_choices=choices if kind == "address" else (), data_choices=choices if kind == "data" else ())
    )
    owner = _owner_for(root, kind)
    owner_id = get_handle(owner)
    map_ref, remap_ref = getattr(owner, _CHOICE)
    map_ref_id, remap_ref_id = get_handle(map_ref), get_handle(remap_ref)
    target_id = get_handle(root.memory_maps.memory_map[0].choice[0])
    remover = f"removeIndirect{'Address' if kind == 'address' else 'Data'}RefMemoryRemapRef"

    assert getattr(api, remover)(owner_id) is True
    assert getattr(owner, _CHOICE) == [map_ref]
    assert resolve_handle(map_ref_id) is map_ref
    assert resolve_handle(remap_ref_id) is None
    assert resolve_handle(owner_id) is owner
    assert resolve_handle(target_id) is not None
    assert getattr(api, remover)(owner_id) is False
    xml = XmlDocument.serializer().render(root)
    _SCHEMA.assertValid(etree.fromstring(xml.encode()))

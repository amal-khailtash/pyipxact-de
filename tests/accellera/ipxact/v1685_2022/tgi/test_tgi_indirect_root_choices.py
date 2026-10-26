"""Address-space and memory-map reference choices on indirect references."""

import inspect
from collections.abc import Iterator, Sequence

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
    AddressSpaces,
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
type _ChoiceRef = (
    IndirectAddressRef.AddressSpaceRef
    | IndirectAddressRef.MemoryMapRef
    | IndirectDataRef.AddressSpaceRef
    | IndirectDataRef.MemoryMapRef
    | MemoryRemapRef
)

_CHOICE = "address_space_ref_or_memory_map_ref_or_memory_remap_ref"
_KINDS = ("address", "data")
_GETTERS = (
    "getIndirectAddressRefAddressSpaceRefByName",
    "getIndirectAddressRefAddressSpaceRefID",
    "getIndirectAddressRefMemoryMapRefByName",
    "getIndirectAddressRefMemoryMapRefID",
    "getIndirectDataRefAddressSpaceRefByName",
    "getIndirectDataRefAddressSpaceRefID",
    "getIndirectDataRefMemoryMapRefByName",
    "getIndirectDataRefMemoryMapRefID",
)
_REMOVERS = (
    "removeIndirectAddressRefAddressSpaceRef",
    "removeIndirectDataRefAddressSpaceRef",
)
_API_FUNCTIONS = (*_GETTERS, *_REMOVERS)


@pytest.fixture(autouse=True)
def clean_registry() -> Iterator[None]:
    registry.clear()
    yield
    registry.clear()


def _choice_item(kind: str, branch: str, value: str) -> _ChoiceRef:
    owner_type = IndirectAddressRef if kind == "address" else IndirectDataRef
    if branch == "address_space":
        return owner_type.AddressSpaceRef(address_space_ref=value)
    if branch == "memory_map":
        return owner_type.MemoryMapRef(memory_map_ref=value)
    return MemoryRemapRef(memory_remap_ref=value)


def _owner(kind: str, choices: object = ()) -> IndirectAddressRef | IndirectDataRef:
    owner_type = IndirectAddressRef if kind == "address" else IndirectDataRef
    return owner_type(
        address_space_ref_or_memory_map_ref_or_memory_remap_ref=choices,
        field_ref=FieldRef(field_ref=f"{kind}_field"),
    )


def _component(
    address_choices: object = (), data_choices: object = (), *, name: str = "indirect_root_choices"
) -> Component:
    return Component(
        vendor="acme",
        library="devices",
        name=name,
        version="1.0",
        address_spaces=AddressSpaces(
            address_space=[
                AddressSpaces.AddressSpace(
                    name=name,
                    range=UnsignedPositiveLongintExpression(value="4096"),
                    width=UnsignedPositiveIntExpression(value="32"),
                )
                for name in ("space_address", "space_data", "tuple_space", "parsed_space", "peer_space")
            ]
        ),
        memory_maps=MemoryMaps(
            memory_map=[
                MemoryMapType(
                    name="map_a",
                    choice=[MemoryRemap(name="window_a", mode_ref=[ModeRef(value="active", priority=0)])],
                ),
                MemoryMapType(name="map_peer"),
            ]
        ),
        modes=ComponentType.Modes(mode=[ComponentType.Modes.Mode(name="active")]),
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
                    indirect_address_ref=_owner("address", (_choice_item("address", "address_space", "peer_space"),)),
                    indirect_data_ref=_owner("data", (_choice_item("data", "memory_map", "map_peer"),)),
                    memory_map_ref_or_transparent_bridge=["map_peer"],
                ),
            ]
        ),
    )


def _xml_round_trip(root: Component) -> tuple[str, Component]:
    xml = XmlDocument.serializer().render(root)
    document = etree.fromstring(xml.encode())
    _SCHEMA.assertValid(document)
    reparsed = XmlDocument.parser().from_string(xml, Component)
    assert XmlDocument.serializer().render(reparsed) == xml
    return xml, reparsed


def _parsed_component(root: Component) -> Component:
    _, parsed = _xml_round_trip(root)
    registry.register(parsed, (parsed.vendor, parsed.library, parsed.name, parsed.version))
    return parsed


def _owner_for(root: Component, kind: str, index: int = 0) -> IndirectAddressRef | IndirectDataRef:
    interface = root.indirect_interfaces.indirect_interface[index]
    owner = interface.indirect_address_ref if kind == "address" else interface.indirect_data_ref
    assert owner is not None
    return owner


def _operation_names(kind: str) -> tuple[str, str, str, str]:
    prefix = "Address" if kind == "address" else "Data"
    return (
        f"getIndirect{prefix}RefAddressSpaceRefByName",
        f"getIndirect{prefix}RefAddressSpaceRefID",
        f"getIndirect{prefix}RefMemoryMapRefByName",
        f"getIndirect{prefix}RefMemoryMapRefID",
    )


def test_public_exports_native_signatures_and_annex_f_sections() -> None:
    expected = {
        "getIndirectAddressRefAddressSpaceRefByName": ("indirectAddressRefID", str | None, "F.7.53.3"),
        "getIndirectAddressRefAddressSpaceRefID": ("indirectAddressRefID", str | None, "F.7.53.4"),
        "getIndirectAddressRefMemoryMapRefByName": ("indirectAddressRefID", str | None, "F.7.53.11"),
        "getIndirectAddressRefMemoryMapRefID": ("indirectAddressRefID", str | None, "F.7.53.12"),
        "getIndirectDataRefAddressSpaceRefByName": ("indirectDataRefID", str | None, "F.7.53.22"),
        "getIndirectDataRefAddressSpaceRefID": ("indirectDataRefID", str | None, "F.7.53.23"),
        "getIndirectDataRefMemoryMapRefByName": ("indirectDataRefID", str | None, "F.7.53.30"),
        "getIndirectDataRefMemoryMapRefID": ("indirectDataRefID", str | None, "F.7.53.31"),
        "removeIndirectAddressRefAddressSpaceRef": ("indirectAddressRefID", bool, "F.7.54.9"),
        "removeIndirectDataRefAddressSpaceRef": ("indirectDataRefID", bool, "F.7.54.17"),
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
@pytest.mark.parametrize("branch", ("empty", "address_space", "memory_map", "map_remap"))
def test_valid_choice_states_round_trip_and_getters_return_owned_handles(kind: str, branch: str) -> None:
    choices: tuple[_ChoiceRef, ...]
    if branch == "empty":
        choices = ()
    elif branch == "address_space":
        choices = (_choice_item(kind, "address_space", f"space_{kind}"),)
    elif branch == "memory_map":
        choices = (_choice_item(kind, "memory_map", "map_a"),)
    else:
        choices = (
            _choice_item(kind, "memory_map", "map_a"),
            _choice_item(kind, "memory_remap", "window_a"),
        )

    root = _component(
        address_choices=choices if kind == "address" else (),
        data_choices=choices if kind == "data" else (),
    )
    parsed = _parsed_component(root)
    owner = _owner_for(parsed, kind)
    owner_id = get_handle(owner)
    collection = getattr(owner, _CHOICE)
    names = _operation_names(kind)
    before = tuple(collection)

    if branch == "address_space":
        child = collection[0]
        name, child_id = "space_" + kind, get_handle(child)
        assert getattr(api, names[0])(owner_id) == name
        assert getattr(api, names[1])(owner_id) == child_id
        assert getattr(api, names[2])(owner_id) is None
        assert getattr(api, names[3])(owner_id) is None
    elif branch == "memory_map":
        child = collection[0]
        child_id = get_handle(child)
        assert getattr(api, names[0])(owner_id) is None
        assert getattr(api, names[1])(owner_id) is None
        assert getattr(api, names[2])(owner_id) == "map_a"
        assert getattr(api, names[3])(owner_id) == child_id
    elif branch == "map_remap":
        map_ref, remap_ref = collection
        child_id = get_handle(map_ref)
        remap_id = get_handle(remap_ref)
        assert getattr(api, names[0])(owner_id) is None
        assert getattr(api, names[1])(owner_id) is None
        assert getattr(api, names[2])(owner_id) == "map_a"
        assert getattr(api, names[3])(owner_id) == child_id
        assert resolve_handle(remap_id) is remap_ref
        assert remap_ref.memory_remap_ref == "window_a"
    else:
        assert all(getattr(api, name)(owner_id) is None for name in names)

    assert getattr(owner, _CHOICE) is collection
    assert tuple(collection) == before
    child_info = get_parent_info(child_id) if branch != "empty" else None
    if child_info is not None:
        assert child_info.parent_handle == owner_id
        assert child_info.path == (_CHOICE,)
        assert child_info.container == "list"


@pytest.mark.parametrize("kind", _KINDS)
@pytest.mark.parametrize("branch", ("address_space", "memory_map", "map_remap"))
def test_choice_getters_preserve_tuple_collection_identity(kind: str, branch: str) -> None:
    if branch == "address_space":
        choices = (_choice_item(kind, "address_space", "tuple_space"),)
    elif branch == "memory_map":
        choices = (_choice_item(kind, "memory_map", "map_a"),)
    else:
        choices = (_choice_item(kind, "memory_map", "map_a"), _choice_item(kind, "memory_remap", "window_a"))
    root = _component(
        address_choices=choices if kind == "address" else (),
        data_choices=choices if kind == "data" else (),
    )
    owner = _owner_for(root, kind)
    collection = choices
    owner_id = get_handle(owner)

    for name in _operation_names(kind):
        getattr(api, name)(owner_id)

    assert getattr(owner, _CHOICE) is collection
    assert isinstance(getattr(owner, _CHOICE), tuple)


@pytest.mark.parametrize("kind", _KINDS)
@pytest.mark.parametrize("branch", ("address_space", "memory_map"))
@pytest.mark.parametrize("invalid", ("", "  ", "1invalid", "has space", "bad/name", "nul\x00name", None, 12))
def test_name_getters_validate_raw_values_while_id_getters_allow_repair(
    kind: str, branch: str, invalid: str | int | None
) -> None:
    child = _choice_item(kind, branch, "initial")
    value_attr = "address_space_ref" if branch == "address_space" else "memory_map_ref"
    setattr(child, value_attr, invalid)
    root = _component(
        address_choices=(child,) if kind == "address" else (),
        data_choices=(child,) if kind == "data" else (),
    )
    owner = _owner_for(root, kind)
    owner_id = get_handle(owner)
    collection = getattr(owner, _CHOICE)
    names = _operation_names(kind)
    name_getter, id_getter = names[0:2] if branch == "address_space" else names[2:4]

    child_id = getattr(api, id_getter)(owner_id)
    assert child_id == get_handle(child)
    info = get_parent_info(child_id)
    assert info is not None and info.parent_handle == owner_id
    assert info.path == (_CHOICE,) and info.container == "list"
    with pytest.raises(TgiError) as error:
        getattr(api, name_getter)(owner_id)
    assert error.value.fault_code == TgiFaultCode.INVALID_ID
    assert getattr(owner, _CHOICE) is collection
    assert getattr(child, value_attr) == invalid

    setattr(child, value_attr, "repaired_name")
    assert getattr(api, name_getter)(owner_id) == "repaired_name"


@pytest.mark.parametrize("kind", _KINDS)
@pytest.mark.parametrize(
    "malformed_case",
    (
        "none-collection",
        "scalar-collection",
        "scalar-child",
        "list-child",
        "unknown-child",
        "foreign-address",
        "foreign-map",
        "remap-alone",
        "remap-before-map",
        "mixed-address-map",
        "mixed-address-remap",
        "duplicate-map",
        "duplicate-remap",
        "too-many",
    ),
)
def test_all_choice_getters_and_remover_reject_malformed_collections_atomically(kind: str, malformed_case: str) -> None:
    address = _choice_item(kind, "address_space", "space_a")
    memory_map = _choice_item(kind, "memory_map", "map_a")
    remap = _choice_item(kind, "memory_remap", "window_a")
    malformed: dict[str, object] = {
        "none-collection": None,
        "scalar-collection": "not a choice collection",
        "scalar-child": ("text",),
        "list-child": ([memory_map],),
        "unknown-child": (object(),),
        "foreign-address": (_choice_item("data" if kind == "address" else "address", "address_space", "space_a"),),
        "foreign-map": (_choice_item("data" if kind == "address" else "address", "memory_map", "map_a"),),
        "remap-alone": (remap,),
        "remap-before-map": (remap, memory_map),
        "mixed-address-map": (address, memory_map),
        "mixed-address-remap": (address, remap),
        "duplicate-map": (memory_map, _choice_item(kind, "memory_map", "map_b")),
        "duplicate-remap": (memory_map, remap, _choice_item(kind, "memory_remap", "window_b")),
        "too-many": (address, memory_map, remap),
    }
    bad_collection = malformed[malformed_case]
    owner = _owner(kind, bad_collection if isinstance(bad_collection, tuple) else ())
    if not isinstance(bad_collection, tuple):
        setattr(owner, _CHOICE, bad_collection)
    before = getattr(owner, _CHOICE)
    before_contents = tuple(before) if isinstance(before, (list, tuple)) else before
    owner_id = get_handle(owner)

    for name in _operation_names(kind):
        with pytest.raises(TgiError) as error:
            getattr(api, name)(owner_id)
        assert error.value.fault_code == TgiFaultCode.INVALID_ID
        assert getattr(owner, _CHOICE) is before
        if isinstance(before, (list, tuple)):
            assert tuple(before) == before_contents
    remover = f"removeIndirect{kind.title()}RefAddressSpaceRef"
    with pytest.raises(TgiError) as error:
        getattr(api, remover)(owner_id)
    assert error.value.fault_code == TgiFaultCode.INVALID_ID
    assert getattr(owner, _CHOICE) is before


@pytest.mark.parametrize("kind", _KINDS)
def test_getters_and_removers_reject_wrong_handles_and_roles(kind: str) -> None:
    root = _parsed_component(_component())
    owner = _owner_for(root, kind)
    opposite = _owner_for(root, "data" if kind == "address" else "address")
    wrong_handles = ("missing-id", get_handle(opposite), get_handle(root.indirect_interfaces.indirect_interface[0]))
    operations = (*_operation_names(kind), f"removeIndirect{kind.title()}RefAddressSpaceRef")
    for operation in operations:
        for wrong_handle in wrong_handles:
            with pytest.raises(TgiError) as error:
                getattr(api, operation)(wrong_handle)
            assert error.value.fault_code == TgiFaultCode.INVALID_ID
    assert getattr(owner, _CHOICE) == []


@pytest.mark.parametrize("kind", _KINDS)
@pytest.mark.parametrize("storage", ("list", "tuple"))
def test_address_space_removers_detach_only_the_branch_and_invalidate_its_handle(kind: str, storage: str) -> None:
    choices: Sequence[_ChoiceRef] = [_choice_item(kind, "address_space", f"space_{kind}")]
    if storage == "tuple":
        choices = tuple(choices)
    root = _component(
        address_choices=choices if kind == "address" else (),
        data_choices=choices if kind == "data" else (),
    )
    registry.register(root, (root.vendor, root.library, root.name, root.version))
    owner = _owner_for(root, kind)
    peer = _owner_for(root, kind, 1)
    owner_id = get_handle(owner)
    peer_id = get_handle(peer)
    child = getattr(owner, _CHOICE)[0]
    child_id = get_handle(child)
    sibling_ids = tuple(get_handle(value) for value in (owner.field_ref, peer.field_ref))
    remover = f"removeIndirect{kind.title()}RefAddressSpaceRef"
    names = _operation_names(kind)

    assert getattr(api, remover)(owner_id) is True
    assert getattr(owner, _CHOICE) == []
    assert isinstance(getattr(owner, _CHOICE), list)
    assert resolve_handle(child_id) is None
    assert getattr(api, names[0])(owner_id) is None
    assert getattr(api, names[1])(owner_id) is None
    assert getattr(api, remover)(owner_id) is False
    assert get_handle(peer) == peer_id
    peer_names = _operation_names(kind)
    if kind == "address":
        assert getattr(api, peer_names[0])(peer_id) == "peer_space"
    else:
        assert getattr(api, peer_names[2])(peer_id) == "map_peer"
    assert all(resolve_handle(handle) is not None for handle in sibling_ids)
    _xml_round_trip(root)


@pytest.mark.parametrize("kind", _KINDS)
def test_absent_removal_preserves_map_remap_tuple_and_parsed_removal_needs_no_getter(kind: str) -> None:
    choices = (_choice_item(kind, "memory_map", "map_a"), _choice_item(kind, "memory_remap", "window_a"))
    root = _component(
        address_choices=choices if kind == "address" else (),
        data_choices=choices if kind == "data" else (),
    )
    _xml_round_trip(root)
    registry.register(root, (root.vendor, root.library, root.name, root.version))
    owner = _owner_for(root, kind)
    owner_id = get_handle(owner)
    collection = getattr(owner, _CHOICE)
    map_ref, remap_ref = collection
    map_id, remap_id = get_handle(map_ref), get_handle(remap_ref)
    remover = f"removeIndirect{kind.title()}RefAddressSpaceRef"
    names = _operation_names(kind)

    assert getattr(api, remover)(owner_id) is False
    assert getattr(owner, _CHOICE) is collection
    assert tuple(getattr(owner, _CHOICE)) == (map_ref, remap_ref)
    assert getattr(api, names[2])(owner_id) == "map_a"
    assert getattr(api, names[3])(owner_id) == map_id
    assert resolve_handle(remap_id) is remap_ref
    peer = _owner_for(root, kind, 1)
    peer_collection = getattr(peer, _CHOICE)
    peer_ids = tuple(get_handle(child) for child in peer_collection)
    assert getattr(peer, _CHOICE) is peer_collection
    assert tuple(get_handle(child) for child in peer_collection) == peer_ids

    # A parsed tree can be removed using only the owner handle; the child ID above
    # was created directly and no getter was needed to attach its ownership path.
    address_only = (_choice_item(kind, "address_space", "parsed_space"),)
    parsed_root = _parsed_component(
        _component(
            address_choices=address_only if kind == "address" else (),
            data_choices=address_only if kind == "data" else (),
            name="indirect_root_choices_removal",
        )
    )
    parsed_owner = _owner_for(parsed_root, kind)
    parsed_owner_id = get_handle(parsed_owner)
    parsed_child_id = get_handle(getattr(parsed_owner, _CHOICE)[0])
    assert getattr(api, remover)(parsed_owner_id) is True
    assert resolve_handle(parsed_child_id) is None
    assert getattr(api, names[0])(parsed_owner_id) is None
    assert getattr(api, names[1])(parsed_owner_id) is None
    _xml_round_trip(parsed_root)


@pytest.mark.parametrize("kind", _KINDS)
@pytest.mark.parametrize("branch", ("address_space", "memory_map"))
def test_name_getters_normalize_xml_whitespace_without_changing_reference(kind: str, branch: str) -> None:
    source = " \tδ:reference\r\n"
    child = _choice_item(kind, branch, source)
    owner = _owner(kind, (child,))
    owner_id = get_handle(owner)
    names = _operation_names(kind)
    name_getter, id_getter = names[0:2] if branch == "address_space" else names[2:4]
    collection = getattr(owner, _CHOICE)

    assert getattr(api, name_getter)(owner_id) == "δ:reference"
    assert getattr(api, id_getter)(owner_id) == get_handle(child)
    value_attr = "address_space_ref" if branch == "address_space" else "memory_map_ref"
    assert getattr(child, value_attr) == source
    assert getattr(owner, _CHOICE) is collection

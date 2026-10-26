"""Indirect interface bridge, enumeration and optional reference lifecycle contracts."""

from collections.abc import Callable, Iterator
from inspect import signature

import pytest
from lxml import etree
from xsdata.formats.dataclass.models.generics import AnyElement

from amal.eda.accellera.ipxact.v1685_2022 import tgi
from amal.eda.accellera.ipxact.v1685_2022.tgi import indirect_interface as api
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import (
    TgiError,
    TgiFaultCode,
    get_handle,
    register_parent,
    registry,
    resolve_handle,
)
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import (
    AddressBlock,
    BusInterface,
    BusInterfaces,
    BusInterfaceType,
    Component,
    ConfigurableLibraryRefType,
    EndianessType,
    FieldDefinitions,
    FieldRef,
    FieldType,
    IndirectAddressRef,
    IndirectDataRef,
    IndirectInterface,
    IndirectInterfaces,
    MemoryMaps,
    MemoryMapType,
    MemoryRemapRef,
    TransparentBridge,
    UnsignedLongintExpression,
    UnsignedPositiveIntExpression,
    UnsignedPositiveLongintExpression,
    VendorExtensions,
)

_CHOICE = "memory_map_ref_or_transparent_bridge"
_REFERENCE = "address_space_ref_or_memory_map_ref_or_memory_remap_ref"
_FieldBroadcast = FieldType.FieldAccessPolicies.FieldAccessPolicy.Broadcasts.BroadcastTo
_DefinitionBroadcast = FieldDefinitions.FieldDefinition.FieldAccessPolicies.FieldAccessPolicy.Broadcasts.BroadcastTo
type _Broadcast = _FieldBroadcast | _DefinitionBroadcast
type _ReferenceOwner = FieldType.AliasOf | _Broadcast
_BROADCASTS = (
    FieldType.FieldAccessPolicies.FieldAccessPolicy.Broadcasts.BroadcastTo,
    FieldDefinitions.FieldDefinition.FieldAccessPolicies.FieldAccessPolicy.Broadcasts.BroadcastTo,
)


@pytest.fixture(autouse=True)
def clear_registry() -> Iterator[None]:
    registry.clear()
    yield
    registry.clear()


def _interface() -> IndirectInterface:
    return IndirectInterface(
        name="indirect",
        indirect_address_ref=IndirectAddressRef(field_ref=FieldRef(field_ref="address")),
        indirect_data_ref=IndirectDataRef(field_ref=FieldRef(field_ref="data")),
        memory_map_ref_or_transparent_bridge=["indirect_map"],
    )


@pytest.mark.parametrize(
    ("name", "parameters", "section"),
    [
        ("getIndirectInterfaceTransparentBridgeIDs", ("indirectInterfaceID",), "F.7.53.46"),
        ("addIndirectInterfaceTransparentBridge", ("indirectInterfaceID", "initiatorRef"), "F.7.54.5"),
        ("removeAliasOfMemoryRemapRef", ("aliasOfID",), "F.7.54.6"),
        ("removeBroadcastToAddressSpaceRef", ("broadcastToID",), "F.7.54.7"),
        ("removeIndirectInterfaceEndianness", ("indirectInterfaceID",), "F.7.54.24"),
        ("removeIndirectInterfaceTransparentBridge", ("transparentBridgeID",), "F.7.54.25"),
        ("setIndirectInterfaceEndianness", ("indirectInterfaceID", "value"), "F.7.54.40"),
        ("setIndirectInterfaceMemoryMapRef", ("indirectInterfaceID", "memoryMapRef"), "F.7.54.41"),
    ],
)
def test_exact_signatures_exports_and_sections(name: str, parameters: tuple[str, ...], section: str) -> None:
    operation = getattr(api, name)
    contract = signature(operation)
    assert tuple(contract.parameters) == parameters
    assert all(parameter.annotation is str for parameter in contract.parameters.values())
    expected_return = list[str] if name.startswith("get") else str if name.startswith("add") else bool
    assert contract.return_annotation == expected_return
    assert getattr(tgi, name) is operation
    assert section in operation.__doc__


def test_bridge_creation_choice_switch_order_metadata_and_removal() -> None:
    owner = _interface()
    owner_id = get_handle(owner)
    assert api.getIndirectInterfaceTransparentBridgeIDs(owner_id) == []
    first_id = api.addIndirectInterfaceTransparentBridge(owner_id, "  master_a  ")
    first = resolve_handle(first_id)
    assert isinstance(first, TransparentBridge)
    first.vendor_extensions = VendorExtensions()
    extension_id = get_handle(first.vendor_extensions)
    second_id = api.addIndirectInterfaceTransparentBridge(owner_id, "master_b")
    assert first.initiator_ref == "master_a"
    assert api.getIndirectInterfaceTransparentBridgeIDs(owner_id) == [first_id, second_id]
    assert api.getIndirectInterfaceMemoryMapRefByName(owner_id) is None
    values = tuple(owner.memory_map_ref_or_transparent_bridge)
    owner.memory_map_ref_or_transparent_bridge = values
    assert api.getIndirectInterfaceTransparentBridgeIDs(owner_id) == [first_id, second_id]
    assert owner.memory_map_ref_or_transparent_bridge is values
    assert api.removeIndirectInterfaceTransparentBridge(first_id)
    assert resolve_handle(first_id) is None
    assert resolve_handle(extension_id) is None
    assert resolve_handle(second_id) is values[1]
    assert api.removeIndirectInterfaceTransparentBridge(second_id)
    assert owner.memory_map_ref_or_transparent_bridge == []
    assert api.getIndirectInterfaceTransparentBridgeIDs(owner_id) == []


@pytest.mark.parametrize("source", ["master_a", " master_a "])
def test_duplicate_bridge_rejected_without_tuple_normalization(source: str) -> None:
    owner = _interface()
    bridge = TransparentBridge(initiator_ref="master_a")
    values = (bridge,)
    owner.memory_map_ref_or_transparent_bridge = values
    with pytest.raises(TgiError) as error:
        api.addIndirectInterfaceTransparentBridge(get_handle(owner), source)
    assert error.value.fault_code == TgiFaultCode.ALREADY_EXISTS
    assert owner.memory_map_ref_or_transparent_bridge is values
    assert bridge.initiator_ref == "master_a"


@pytest.mark.parametrize("source", ["", "bad name", 3, None])
def test_bad_bridge_or_map_names_are_atomic(source: object) -> None:
    owner = _interface()
    values = (TransparentBridge(initiator_ref="master"),)
    owner.memory_map_ref_or_transparent_bridge = values
    for operation in (api.addIndirectInterfaceTransparentBridge, api.setIndirectInterfaceMemoryMapRef):
        with pytest.raises(TgiError) as error:
            operation(get_handle(owner), source)
        assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
        assert owner.memory_map_ref_or_transparent_bridge is values


def test_setting_memory_map_invalidates_bridges_and_descendants() -> None:
    owner = _interface()
    bridge = TransparentBridge(initiator_ref="master", vendor_extensions=VendorExtensions())
    owner.memory_map_ref_or_transparent_bridge = (bridge,)
    bridge_id = get_handle(bridge)
    extension_id = get_handle(bridge.vendor_extensions)
    data_id = get_handle(owner.indirect_data_ref)
    assert api.setIndirectInterfaceMemoryMapRef(get_handle(owner), "  indirect_map  ")
    assert owner.memory_map_ref_or_transparent_bridge == ["indirect_map"]
    assert resolve_handle(bridge_id) is None
    assert resolve_handle(extension_id) is None
    assert resolve_handle(data_id) is owner.indirect_data_ref


@pytest.mark.parametrize(
    "values",
    [42, ("map", "other"), ("map", TransparentBridge(initiator_ref="master")), (object(),)],
    ids=["noncollection", "two_maps", "mixed", "wrong_member"],
)
def test_malformed_interface_choices_are_atomic(values: object) -> None:
    owner = _interface()
    owner.memory_map_ref_or_transparent_bridge = values
    for operation, arguments in (
        (api.getIndirectInterfaceTransparentBridgeIDs, ()),
        (api.addIndirectInterfaceTransparentBridge, ("master",)),
        (api.setIndirectInterfaceMemoryMapRef, ("map",)),
    ):
        with pytest.raises(TgiError) as error:
            operation(get_handle(owner), *arguments)
        assert error.value.fault_code == TgiFaultCode.INVALID_ID
        assert owner.memory_map_ref_or_transparent_bridge is values


def test_orphan_stale_wrong_and_misleading_bridge_owners() -> None:
    owner = _interface()
    bridge = TransparentBridge(initiator_ref="master")
    bridge_id = get_handle(bridge)
    for handle in (bridge_id, get_handle(FieldRef(field_ref="wrong")), "stale"):
        with pytest.raises(TgiError) as error:
            api.removeIndirectInterfaceTransparentBridge(handle)
        assert error.value.fault_code == TgiFaultCode.INVALID_ID
    register_parent(bridge, owner, (_CHOICE,), "list")
    with pytest.raises(TgiError) as error:
        api.removeIndirectInterfaceTransparentBridge(bridge_id)
    assert error.value.fault_code == TgiFaultCode.INVALID_ID
    assert owner.memory_map_ref_or_transparent_bridge == ["indirect_map"]


@pytest.mark.parametrize("source", ["big", "little"])
def test_endianness_set_remove_and_default(source: str) -> None:
    owner = _interface()
    owner_id = get_handle(owner)
    assert api.getIndirectInterfaceEndianness(owner_id) == "little"
    assert not api.removeIndirectInterfaceEndianness(owner_id)
    assert api.setIndirectInterfaceEndianness(owner_id, source)
    assert owner.endianness is EndianessType(source)
    assert api.getIndirectInterfaceEndianness(owner_id) == source
    assert api.removeIndirectInterfaceEndianness(owner_id)
    assert api.getIndirectInterfaceEndianness(owner_id) == "little"


@pytest.mark.parametrize("source", ["BIG", " big ", "middle", 4, None])
def test_bad_endianness_is_atomic(source: object) -> None:
    owner = _interface()
    owner.endianness = EndianessType.BIG
    with pytest.raises(TgiError) as error:
        api.setIndirectInterfaceEndianness(get_handle(owner), source)
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert owner.endianness is EndianessType.BIG


def test_alias_remap_removal_preserves_map_field_and_tuple_on_noop() -> None:
    remap = MemoryRemapRef(memory_remap_ref="window")
    memory_map = FieldType.AliasOf.MemoryMapRef(memory_map_ref="map")
    field = FieldRef(field_ref="flag")
    owner = FieldType.AliasOf(
        field_ref=field, address_space_ref_or_memory_map_ref_or_memory_remap_ref=(memory_map, remap)
    )
    remap_id = get_handle(remap)
    field_id = get_handle(field)
    assert api.removeAliasOfMemoryRemapRef(get_handle(owner))
    assert resolve_handle(remap_id) is None
    assert owner.address_space_ref_or_memory_map_ref_or_memory_remap_ref == [memory_map]
    assert resolve_handle(field_id) is field
    values = (memory_map,)
    owner.address_space_ref_or_memory_map_ref_or_memory_remap_ref = values
    assert not api.removeAliasOfMemoryRemapRef(get_handle(owner))
    assert owner.address_space_ref_or_memory_map_ref_or_memory_remap_ref is values


@pytest.mark.parametrize("model", _BROADCASTS, ids=["field", "definition"])
def test_broadcast_address_space_removal_preserves_other_references(model: type[_Broadcast]) -> None:
    address = model.AddressSpaceRef(address_space_ref="space")
    field = FieldRef(field_ref="flag")
    owner = model(field_ref=field, address_space_ref_or_memory_map_ref_or_memory_remap_ref=(address,))
    child_id = get_handle(address)
    assert api.removeBroadcastToAddressSpaceRef(get_handle(owner))
    assert resolve_handle(child_id) is None
    assert owner.field_ref is field
    assert getattr(owner, _REFERENCE) == []
    values = (model.MemoryMapRef(memory_map_ref="map"), MemoryRemapRef(memory_remap_ref="window"))
    setattr(owner, _REFERENCE, values)
    assert not api.removeBroadcastToAddressSpaceRef(get_handle(owner))
    assert getattr(owner, _REFERENCE) is values


@pytest.mark.parametrize("model", [FieldType.AliasOf, *_BROADCASTS], ids=["alias", "field", "definition"])
def test_malformed_optional_reference_choices_rejected_atomically(model: type[_ReferenceOwner]) -> None:
    values = (MemoryRemapRef(memory_remap_ref="window"),)
    owner = model(field_ref=FieldRef(field_ref="flag"), address_space_ref_or_memory_map_ref_or_memory_remap_ref=values)
    operation = api.removeAliasOfMemoryRemapRef if model is FieldType.AliasOf else api.removeBroadcastToAddressSpaceRef
    with pytest.raises(TgiError) as error:
        operation(get_handle(owner))
    assert error.value.fault_code == TgiFaultCode.INVALID_ID
    assert getattr(owner, _REFERENCE) is values


@pytest.mark.parametrize(
    "operation",
    [api.removeAliasOfMemoryRemapRef, api.removeBroadcastToAddressSpaceRef, api.removeIndirectInterfaceEndianness],
)
def test_wrong_or_stale_owner_removals(operation: Callable[[str], bool]) -> None:
    for handle in ("stale", get_handle(FieldRef(field_ref="wrong"))):
        with pytest.raises(TgiError) as error:
            operation(handle)
        assert error.value.fault_code == TgiFaultCode.INVALID_ID


@pytest.mark.parametrize("mutation", ["remove", "map"])
def test_parsed_bridge_mutations_discover_ownership_before_getters(mutation: str) -> None:
    owner = _interface()
    owner.memory_map_ref_or_transparent_bridge = [
        TransparentBridge(
            initiator_ref="master_a",
            vendor_extensions=VendorExtensions(any_element=[AnyElement(qname="{urn:test}note", text="metadata")]),
        ),
        TransparentBridge(initiator_ref="master_b"),
    ]
    root = Component(
        vendor="example.org",
        library="devices",
        name="parsed_bridge",
        version="1.0",
        bus_interfaces=BusInterfaces(
            bus_interface=[
                BusInterface(
                    name=name,
                    bus_type=ConfigurableLibraryRefType(
                        vendor="example.org", library="bus", name="simple", version="1.0"
                    ),
                    choice=BusInterfaceType.Initiator(),
                )
                for name in ("master_a", "master_b")
            ]
        ),
        memory_maps=MemoryMaps(
            memory_map=[
                MemoryMapType(
                    name="map",
                    choice=[
                        AddressBlock(
                            name="registers",
                            base_address=UnsignedLongintExpression(value="0"),
                            choice=[
                                UnsignedPositiveLongintExpression(value="64"),
                                UnsignedPositiveIntExpression(value="32"),
                            ],
                        )
                    ],
                )
            ]
        ),
        indirect_interfaces=IndirectInterfaces(indirect_interface=[owner]),
    )
    schema = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))
    xml = XmlDocument.serializer().render(root)
    schema.assertValid(etree.fromstring(xml.encode()))
    parsed = XmlDocument.parser().from_string(xml, Component)
    registry.register(parsed, (parsed.vendor, parsed.library, parsed.name, parsed.version))
    interface = parsed.indirect_interfaces.indirect_interface[0]
    first, second = interface.memory_map_ref_or_transparent_bridge
    first_id = get_handle(first)
    second_id = get_handle(second)
    extension_id = get_handle(first.vendor_extensions)
    if mutation == "remove":
        assert api.removeIndirectInterfaceTransparentBridge(first_id)
        assert resolve_handle(second_id) is second
        schema.assertValid(etree.fromstring(XmlDocument.serializer().render(parsed).encode()))
    else:
        assert api.setIndirectInterfaceMemoryMapRef(get_handle(interface), "map")
        assert resolve_handle(second_id) is None
        assert interface.memory_map_ref_or_transparent_bridge == ["map"]
        schema.assertValid(etree.fromstring(XmlDocument.serializer().render(parsed).encode()))
    assert resolve_handle(first_id) is None
    assert resolve_handle(extension_id) is None

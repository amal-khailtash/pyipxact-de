"""Bus-interface mode transitions and remapping follow the generated schema."""

import pytest
from lxml import etree

from amal.eda.accellera.ipxact.v1685_2022.tgi import bus_interface as api
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import TgiError, get_handle, registry, resolve_handle
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import (
    AddressSpaces,
    BusInterface,
    BusInterfaces,
    Channels,
    Component,
    ComponentType,
    ConfigurableLibraryRefType,
    MemoryMaps,
    MemoryMapType,
    ModelType,
    UnsignedPositiveIntExpression,
    UnsignedPositiveLongintExpression,
)


def _root():
    interface = BusInterface(
        name="bus", bus_type=ConfigurableLibraryRefType(vendor="v", library="l", name="bus", version="1")
    )
    return Component(
        vendor="v",
        library="l",
        name="c",
        version="1",
        bus_interfaces=BusInterfaces(bus_interface=[interface]),
        memory_maps=MemoryMaps(memory_map=[MemoryMapType(name=name) for name in ["memory", "first", "second"]]),
        address_spaces=AddressSpaces(
            address_space=[
                AddressSpaces.AddressSpace(
                    name="space",
                    range=UnsignedPositiveLongintExpression(value="256"),
                    width=UnsignedPositiveIntExpression(value="32"),
                )
            ]
        ),
    ), interface


def _valid(root):
    schema = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))
    xml = XmlDocument.serializer().render(root)
    schema.assertValid(etree.fromstring(xml.encode()))
    return xml


def test_all_interface_modes_serialize_and_invalidate_replaced_children():
    root, interface = _root()
    handle = get_handle(interface)
    transitions = [
        ("Initiator", (), "initiator"),
        ("Target", ("memory",), "target"),
        ("System", ("control",), "system"),
        ("MirroredTarget", (), "mirroredTarget"),
        ("MirroredSystem", ("control",), "mirroredSystem"),
        ("Monitor", ("initiator",), "monitor"),
        ("MirroredInitiator", (), "mirroredInitiator"),
    ]
    previous = None
    for suffix, arguments, mode in transitions:
        assert getattr(api, f"setBusInterface{suffix}")(handle, *arguments)
        assert api.getBusInterfaceInterfaceMode(handle) == mode
        if previous is not None:
            assert resolve_handle(previous) is None
        previous = get_handle(interface.choice)
        parsed = XmlDocument.parser().from_string(_valid(root), Component)
        assert api.getBusInterfaceInterfaceMode(get_handle(parsed.bus_interfaces.bus_interface[0])) == mode


def test_setting_the_same_mode_updates_its_arguments_and_preserves_handles():
    root, interface = _root()
    handle = get_handle(interface)
    api.setBusInterfaceSystem(handle, "control")
    system_id = api.getBusInterfaceSystemID(handle)
    group = resolve_handle(system_id).group
    api.setBusInterfaceSystem(handle, "data")
    assert api.getBusInterfaceSystemID(handle) == system_id
    assert api.getSystemGroup(system_id) == "data"
    assert resolve_handle(system_id).group is group
    api.setBusInterfaceMonitor(handle, "initiator")
    monitor_id = api.getBusInterfaceMonitorID(handle)
    api.setBusInterfaceMonitor(handle, "target")
    assert api.getBusInterfaceMonitorID(handle) == monitor_id
    assert resolve_handle(monitor_id).interface_mode.value == "target"
    api.setBusInterfaceTarget(handle, "first")
    target_id = api.getBusInterfaceTargetID(handle)
    ref_id = api.getTargetMemoryMapRefID(target_id)
    api.setBusInterfaceTarget(handle, "second")
    assert api.getBusInterfaceTargetID(handle) == target_id
    assert api.getTargetMemoryMapRefID(target_id) == ref_id
    assert api.getTargetMemoryMapRefByName(target_id) == "second"
    _valid(root)


def test_remap_range_edits_are_atomic_and_keep_expression_handles():
    root, interface = _root()
    handle = get_handle(interface)
    api.setBusInterfaceMirroredTarget(handle)
    mirrored = api.getBusInterfaceMirroredTargetID(handle)
    assert api.setMirroredTargetBaseAddresses(mirrored, "0", "256")
    base = api.getMirroredTargetBaseAddressesID(mirrored)
    range_id = api.getBaseAddressesRangeID(base)
    api.setBaseAddressesRange(base, "1 << 10")
    assert api.getBaseAddressesRange(base) == 1024
    assert api.getBaseAddressesRangeExpression(base) == "1 << 10"
    assert api.getBaseAddressesRangeID(base) == range_id
    before = _valid(root)
    with pytest.raises(TgiError):
        api.setMirroredTargetBaseAddresses(mirrored, "-1", "0")
    assert _valid(root) == before
    assert api.removeMirroredTargetBaseAddresses(mirrored)
    assert resolve_handle(base) is None
    assert resolve_handle(range_id) is None
    _valid(root)


def test_expression_defaults_bounds_and_metadata_preservation():
    root, interface = _root()
    handle = get_handle(interface)
    api.setBusInterfaceInitiator(handle)
    assert api.getBusInterfaceBitsInLau(handle) == 8
    assert api.getBusInterfaceBitsInLauExpression(handle) is None
    assert api.getBusInterfaceBitsInLauID(handle) is None
    assert api.getBusInterfaceBitSteering(handle) is False
    assert api.getBusInterfaceConnectionRequired(handle) is False
    assert api.getBusInterfaceEndianness(handle) == "little"
    api.setBusInterfaceBitsInLau(handle, "8 * 4")
    bits_id = api.getBusInterfaceBitsInLauID(handle)
    bits = resolve_handle(bits_id)
    bits.other_attributes = {"{urn:test}label": "width"}
    api.setBusInterfaceBitsInLau(handle, "64'hFFFFFFFFFFFFFFFF")
    assert api.getBusInterfaceBitsInLau(handle) == (1 << 64) - 1
    assert api.getBusInterfaceBitsInLauID(handle) == bits_id
    assert bits.other_attributes == {"{urn:test}label": "width"}
    before = _valid(root)
    for invalid in ["0", "-1", str(1 << 64), "", True]:
        with pytest.raises(TgiError):
            api.setBusInterfaceBitsInLau(handle, invalid)
        assert _valid(root) == before
    bits.maximum = 32
    with pytest.raises(TgiError):
        api.setBusInterfaceBitsInLau(handle, "64")
    api.setBusInterfaceBitsInLau(handle, "32")
    assert api.getBusInterfaceBitsInLau(handle) == 32
    assert bits.maximum == 32
    api.setBusInterfaceBitSteering(handle, "1'b1")
    steering_id = api.getBusInterfaceBitSteeringID(handle)
    assert api.getBusInterfaceBitSteering(handle) is True
    assert api.getBusInterfaceBitSteeringExpression(handle) == "1'b1"
    with pytest.raises(TgiError):
        api.setBusInterfaceBitSteering(handle, "2")
    assert api.removeBusInterfaceBitSteering(handle)
    assert resolve_handle(steering_id) is None
    assert api.getBusInterfaceBitSteering(handle) is False
    _valid(root)


def test_address_space_mode_names_resolve_without_removing_targets():
    root, interface = _root()
    mode = ComponentType.Modes.Mode(name="active")
    root.modes = ComponentType.Modes(mode=[mode])
    registry.register(root, ("v", "l", "c", "1"), replace=True)
    api.setBusInterfaceInitiator(get_handle(interface))
    initiator = api.getBusInterfaceInitiatorID(get_handle(interface))
    api.setInitiatorAddressSpaceRef(initiator, "space")
    reference = api.getInitiatorAddressSpaceRefID(initiator)
    assert api.addAddressSpaceRefModeRef(reference, "active")
    assert api.getAddressSpaceRefModeRefByNames(reference) == ["active"]
    assert api.getAddressSpaceRefModeRefByID(reference, "active") == get_handle(mode)
    assert api.removeAddressSpaceRefModeRef(reference, "active")
    assert api.getAddressSpaceRefModeRefByNames(reference) == []
    assert resolve_handle(get_handle(mode)) is mode
    _valid(root)


def test_view_reference_resolution_is_scoped_to_owning_component():
    root, interface = _root()
    api.setBusInterfaceInitiator(get_handle(interface))
    view = ModelType.Views.View(name="rtl")
    root.model = ModelType(views=ModelType.Views(view=[view]))
    registry.register(root, ("v", "l", "c", "1"), replace=True)
    abstraction = api.addBusInterfaceAbstractionType(get_handle(interface), ["v", "l", "rtl", "1"])
    reference = api.addAbstractionTypeViewRef(abstraction, "rtl")
    assert api.getAbstractionTypeViewRefIDs(abstraction) == [reference]
    assert api.getAbstractionTypeViewRefByNames(abstraction) == ["rtl"]
    assert api.getAbstractionTypeViewRefByID(abstraction, reference) == get_handle(view)
    assert api.removeAbstractionTypeViewRef(reference)
    assert resolve_handle(reference) is None
    assert resolve_handle(get_handle(view)) is view
    _valid(root)


def test_channel_removal_keeps_required_two_references():
    root, interface = _root()
    api.setBusInterfaceMirroredInitiator(get_handle(interface))
    other = BusInterface(name="other", bus_type=interface.bus_type)
    root.bus_interfaces.bus_interface.append(other)
    api.setBusInterfaceMirroredInitiator(get_handle(other))
    channel = Channels.Channel(
        name="link",
        bus_interface_ref=[
            Channels.Channel.BusInterfaceRef(local_name="bus"),
            Channels.Channel.BusInterfaceRef(local_name="other"),
        ],
    )
    root.channels = Channels(channel=[channel])
    channel_id = get_handle(channel)
    original = api.getChannelBusInterfaceRefIDs(channel_id)
    assert api.removeChannelBusInterfaceRef(original[0]) is False
    assert resolve_handle(original[0]) is not None
    added = api.addChannelBusInterfaceRef(channel_id, "third")
    assert api.getChannelBusInterfaceRefIDs(channel_id) == [*original, added]
    assert api.removeChannelBusInterfaceRef(added)
    assert resolve_handle(added) is None
    assert api.getChannelBusInterfaceRefIDs(channel_id) == original
    _valid(root)

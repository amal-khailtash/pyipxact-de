"""Every IEEE 1685-2022 Bus Interface TGI operation executes on typed handles."""


import pytest

from amal.eda.accellera.ipxact.v1685_2022.tgi import bus_definition
from amal.eda.accellera.ipxact.v1685_2022.tgi import bus_interface as api
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import (
    TgiError,
    get_handle,
    register_parent,
    registry,
    resolve_handle,
)
from org.accellera.ipxact.v1685_2022.abstraction_definition import AbstractionDefinition
from org.accellera.ipxact.v1685_2022.abstraction_types import AbstractionTypes
from org.accellera.ipxact.v1685_2022.address_spaces import AddressSpaces
from org.accellera.ipxact.v1685_2022.bits_in_lau import BitsInLau
from org.accellera.ipxact.v1685_2022.bus_definition import BusDefinition
from org.accellera.ipxact.v1685_2022.bus_interface import BusInterface
from org.accellera.ipxact.v1685_2022.bus_interface_type import BusInterfaceType
from org.accellera.ipxact.v1685_2022.bus_interfaces import BusInterfaces
from org.accellera.ipxact.v1685_2022.channels import Channels
from org.accellera.ipxact.v1685_2022.component import Component
from org.accellera.ipxact.v1685_2022.component_type import ComponentType
from org.accellera.ipxact.v1685_2022.configurable_library_ref_type import ConfigurableLibraryRefType
from org.accellera.ipxact.v1685_2022.file_set_ref import FileSetRef
from org.accellera.ipxact.v1685_2022.indirect_address_ref import IndirectAddressRef
from org.accellera.ipxact.v1685_2022.indirect_data_ref import IndirectDataRef
from org.accellera.ipxact.v1685_2022.indirect_interface import IndirectInterface
from org.accellera.ipxact.v1685_2022.indirect_interfaces import IndirectInterfaces
from org.accellera.ipxact.v1685_2022.library_ref_type import LibraryRefType
from org.accellera.ipxact.v1685_2022.memory_map_ref import MemoryMapRef
from org.accellera.ipxact.v1685_2022.memory_map_ref_type import MemoryMapRefType
from org.accellera.ipxact.v1685_2022.memory_map_type import MemoryMapType
from org.accellera.ipxact.v1685_2022.memory_maps import MemoryMaps
from org.accellera.ipxact.v1685_2022.mode_ref import ModeRef
from org.accellera.ipxact.v1685_2022.model import Model
from org.accellera.ipxact.v1685_2022.model_type import ModelType
from org.accellera.ipxact.v1685_2022.monitor_interface_mode import MonitorInterfaceMode
from org.accellera.ipxact.v1685_2022.signed_longint_expression import SignedLongintExpression
from org.accellera.ipxact.v1685_2022.transparent_bridge import TransparentBridge
from org.accellera.ipxact.v1685_2022.unsigned_longint_expression import UnsignedLongintExpression
from org.accellera.ipxact.v1685_2022.unsigned_positive_int_expression import UnsignedPositiveIntExpression
from org.accellera.ipxact.v1685_2022.unsigned_positive_longint_expression import UnsignedPositiveLongintExpression
from org.accellera.ipxact.v1685_2022.view_ref import ViewRef


def _reference(vendor: str, library: str, name: str, version: str) -> ConfigurableLibraryRefType:
    return ConfigurableLibraryRefType(vendor=vendor, library=library, name=name, version=version)


def _interface(name: str, choice: object) -> BusInterface:
    return BusInterface(
        name=name,
        bus_type=_reference("acme", "buses", "control", "1.0"),
        choice=choice,
    )


def _operation_fixture():
    registry.clear()
    bus_vlnv = ("acme", "buses", "control", "1.0")
    abstraction_vlnv = ("acme", "abstractions", "control_rtl", "1.0")
    bus_definition = BusDefinition(
        vendor=bus_vlnv[0],
        library=bus_vlnv[1],
        name=bus_vlnv[2],
        version=bus_vlnv[3],
        direct_connection=False,
        is_addressable=True,
        system_group_names=BusDefinition.SystemGroupNames(
            system_group_name=[BusDefinition.SystemGroupNames.SystemGroupName(value="control")]
        ),
    )
    registry.register(bus_definition, bus_vlnv)
    system_group_name = bus_definition.system_group_names.system_group_name[0]
    bus_definition_id = get_handle(bus_definition)
    group_names_id = get_handle(system_group_name)
    register_parent(system_group_name, bus_definition, ("system_group_names", "system_group_name"), "list")

    abstraction_definition = AbstractionDefinition(
        vendor=abstraction_vlnv[0],
        library=abstraction_vlnv[1],
        name=abstraction_vlnv[2],
        version=abstraction_vlnv[3],
        bus_type=LibraryRefType(vendor=bus_vlnv[0], library=bus_vlnv[1], name=bus_vlnv[2], version=bus_vlnv[3]),
        ports=AbstractionDefinition.Ports(),
    )
    registry.register(abstraction_definition, abstraction_vlnv)
    abstraction_definition_id = get_handle(abstraction_definition)

    address_ref = BusInterfaceType.Initiator.AddressSpaceRef(
        address_space_ref="space",
        base_address=SignedLongintExpression(value="-4"),
        mode_ref=[BusInterfaceType.Initiator.AddressSpaceRef.ModeRef(value="active")],
    )
    address_expression = address_ref.base_address
    initiator_choice = BusInterfaceType.Initiator(address_space_ref=address_ref)
    interface = _interface("master", initiator_choice)
    view_ref = ViewRef(value="rtl")
    abstraction_type = AbstractionTypes.AbstractionType(
        abstraction_ref=_reference(*abstraction_vlnv),
        view_ref=[view_ref],
    )
    component_view = ModelType.Views.View(name="rtl")
    interface.abstraction_types = AbstractionTypes(abstraction_type=[abstraction_type])

    target_choice = BusInterfaceType.Target(
        memory_map_ref_or_transparent_bridge=[
            MemoryMapRef(
                memory_map_ref="map",
                mode_ref=[MemoryMapRefType.ModeRef(value="active")],
            )
        ],
        file_set_ref_group=[
            BusInterfaceType.Target.FileSetRefGroup(
                group="drivers",
                file_set_ref=[FileSetRef(local_name="rtl")],
            )
        ],
    )
    target_interface = _interface("target", target_choice)
    system_interface = _interface("system", BusInterfaceType.System(group=_group("control")))
    mirrored_system_interface = _interface("mirrored_system", BusInterfaceType.MirroredSystem(group=_group("mirrored")))
    mirrored_base = BusInterfaceType.MirroredTarget.BaseAddresses(
        remap_addresses=[
            BusInterfaceType.MirroredTarget.BaseAddresses.RemapAddresses(
                remap_address=UnsignedLongintExpression(value="0"),
                mode_ref=[ModeRef(value="active", priority=0)],
            ),
            BusInterfaceType.MirroredTarget.BaseAddresses.RemapAddresses(
                remap_address=UnsignedLongintExpression(value="32"), mode_ref=[]
            ),
        ],
        range=UnsignedPositiveLongintExpression(value="256"),
    )
    mirrored_target_choice = BusInterfaceType.MirroredTarget(base_addresses=mirrored_base)
    mirrored_target_interface = _interface("mirrored_target", mirrored_target_choice)
    monitor_interface = _interface(
        "monitor",
        BusInterfaceType.Monitor(interface_mode=MonitorInterfaceMode.SYSTEM, group=_group("monitored")),
    )
    switch_interface = _interface("switch", BusInterfaceType.Initiator())

    channel_ref_one = Channels.Channel.BusInterfaceRef(local_name="master")
    channel_ref_two = Channels.Channel.BusInterfaceRef(local_name="target")
    channel = Channels.Channel(name="paired", bus_interface_ref=[channel_ref_one, channel_ref_two])
    indirect = IndirectInterface(
        name="indirect",
        indirect_address_ref=IndirectAddressRef(field_ref=[]),
        indirect_data_ref=IndirectDataRef(field_ref=[]),
        bits_in_lau=BitsInLau(value="8"),
    )
    mode_active = ComponentType.Modes.Mode(name="active")
    component = Component(
        vendor="acme",
        library="components",
        name="operation_test",
        version="1.0",
        bus_interfaces=BusInterfaces(
            bus_interface=[
                interface,
                target_interface,
                system_interface,
                mirrored_system_interface,
                mirrored_target_interface,
                monitor_interface,
                switch_interface,
            ]
        ),
        channels=Channels(channel=[channel]),
        modes=ComponentType.Modes(mode=[mode_active]),
        address_spaces=AddressSpaces(
            address_space=[
                AddressSpaces.AddressSpace(
                    name="space",
                    range=UnsignedPositiveLongintExpression(value="256"),
                    width=UnsignedPositiveIntExpression(value="32"),
                )
            ]
        ),
        memory_maps=MemoryMaps(memory_map=[MemoryMapType(name="map")]),
        model=Model(views=ModelType.Views(view=[component_view])),
        indirect_interfaces=IndirectInterfaces(indirect_interface=[indirect]),
    )
    registry.register(component, (component.vendor, component.library, component.name, component.version))

    return {
        "component": component,
        "bus_definition": bus_definition,
        "bus_definition_id": bus_definition_id,
        "system_group_name_id": group_names_id,
        "abstraction_definition_id": abstraction_definition_id,
        "interface": interface,
        "interface_id": get_handle(interface),
        "target_interface": target_interface,
        "system_interface": system_interface,
        "mirrored_system_interface": mirrored_system_interface,
        "mirrored_target_interface": mirrored_target_interface,
        "monitor_interface": monitor_interface,
        "abstraction_type": abstraction_type,
        "abstraction_type_id": get_handle(abstraction_type),
        "view_ref": view_ref,
        "view_ref_id": get_handle(view_ref),
        "component_view_id": get_handle(component_view),
        "address_ref": address_ref,
        "address_ref_id": get_handle(address_ref),
        "address_expression_id": get_handle(address_expression),
        "target": target_choice,
        "target_id": get_handle(target_choice),
        "memory_ref": target_choice.memory_map_ref_or_transparent_bridge[0],
        "memory_ref_id": get_handle(target_choice.memory_map_ref_or_transparent_bridge[0]),
        "target_file_group": target_choice.file_set_ref_group[0],
        "target_file_group_id": get_handle(target_choice.file_set_ref_group[0]),
        "file_set_ref": target_choice.file_set_ref_group[0].file_set_ref[0],
        "file_set_ref_id": get_handle(target_choice.file_set_ref_group[0].file_set_ref[0]),
        "channel": channel,
        "channel_id": get_handle(channel),
        "channel_ref": channel_ref_one,
        "channel_ref_id": get_handle(channel_ref_one),
        "indirect": indirect,
        "indirect_id": get_handle(indirect),
        "initiator": initiator_choice,
        "initiator_id": get_handle(initiator_choice),
        "system": system_interface.choice,
        "system_id": get_handle(system_interface.choice),
        "mirrored_system": mirrored_system_interface.choice,
        "mirrored_system_id": get_handle(mirrored_system_interface.choice),
        "mirrored_target": mirrored_target_choice,
        "mirrored_target_id": get_handle(mirrored_target_choice),
        "base_addresses": mirrored_base,
        "base_addresses_id": get_handle(mirrored_base),
        "range_expression_id": get_handle(mirrored_base.range),
        "remap_record": mirrored_base.remap_addresses[0],
        "remap_record_id": get_handle(mirrored_base.remap_addresses[0]),
        "remap_expression": mirrored_base.remap_addresses[0].remap_address,
        "remap_expression_id": get_handle(mirrored_base.remap_addresses[0].remap_address),
        "remap_record_ids": [get_handle(item) for item in mirrored_base.remap_addresses],
        "monitor": monitor_interface.choice,
        "monitor_id": get_handle(monitor_interface.choice),
        "switch_id": get_handle(switch_interface),
        "mode_active": mode_active,
        "mode_active_id": get_handle(mode_active),
        "bridge": TransparentBridge(initiator_ref="master"),
    }


def _group(value: str):
    from org.accellera.ipxact.v1685_2022.group import Group

    return Group(value=value)


def test_every_base_operation_executes_against_its_schema_handle():
    data = _operation_fixture()
    seen: set[str] = set()

    def call(name: str, *args):
        seen.add(name)
        return getattr(api, name)(*args)

    at_id = data["abstraction_type_id"]
    address_id = data["address_ref_id"]
    base_id = data["base_addresses_id"]
    interface_id = data["interface_id"]
    target_id = data["target_id"]
    memory_ref_id = data["memory_ref_id"]
    record_id = data["remap_record_id"]
    assert call("getAbstractionTypeAbstractionRefByID", at_id) == data["abstraction_definition_id"]
    assert call("getAbstractionTypeAbstractionRefByVLNV", at_id) == ("acme", "abstractions", "control_rtl", "1.0")
    assert call("getAbstractionTypePortMapIDs", at_id) == []
    assert call("getAbstractionTypeViewRefByID", at_id, data["view_ref_id"]) == data["component_view_id"]
    assert call("getAbstractionTypeViewRefByNames", at_id) == ["rtl"]
    assert call("getAbstractionTypeViewRefIDs", at_id) == [data["view_ref_id"]]
    assert call("getAddressSpaceRefBaseAddress", address_id) == -4
    assert call("getAddressSpaceRefBaseAddressExpression", address_id) == "-4"
    assert call("getAddressSpaceRefBaseAddressID", address_id) == data["address_expression_id"]
    assert call("getAddressSpaceRefModeRefByID", address_id, "active") == data["mode_active_id"]
    assert call("getAddressSpaceRefModeRefByNames", address_id) == ["active"]
    assert call("getBaseAddressesRange", base_id) == 256
    assert call("getBaseAddressesRangeExpression", base_id) == "256"
    assert call("getBaseAddressesRangeID", base_id) == data["range_expression_id"]
    assert call("getBaseAddressesRemapAddressIDs", base_id) == data["remap_record_ids"]
    assert call("getBusInterfaceAbstractionTypeIDs", interface_id) == [at_id]
    assert call("getBusInterfaceBitSteering", interface_id) is False
    assert call("getBusInterfaceBitSteeringExpression", interface_id) is None
    assert call("getBusInterfaceBitSteeringID", interface_id) is None
    assert call("getBusInterfaceBitsInLau", interface_id) == 8
    assert call("getBusInterfaceBitsInLauExpression", interface_id) is None
    assert call("getBusInterfaceBitsInLauID", interface_id) is None
    assert call("getBusInterfaceBusTypeID", interface_id) == get_handle(data["interface"].bus_type)
    assert call("getBusInterfaceBusTypeRefByID", interface_id) == data["bus_definition_id"]
    assert call("getBusInterfaceBusTypeRefByVLNV", interface_id) == ("acme", "buses", "control", "1.0")
    assert call("getBusInterfaceConnectionRequired", interface_id) is False
    assert call("getBusInterfaceEndianness", interface_id) == "little"
    assert call("getBusInterfaceInitiatorID", interface_id) == data["initiator_id"]
    assert call("getBusInterfaceInterfaceMode", interface_id) == "initiator"
    assert (
        call("getBusInterfaceMirroredSystemID", get_handle(data["mirrored_system_interface"]))
        == data["mirrored_system_id"]
    )
    assert (
        call("getBusInterfaceMirroredTargetID", get_handle(data["mirrored_target_interface"]))
        == data["mirrored_target_id"]
    )
    assert call("getBusInterfaceMonitorID", get_handle(data["monitor_interface"])) == data["monitor_id"]
    assert call("getBusInterfaceRefLocalName", data["channel_ref_id"]) == "master"
    assert call("getBusInterfaceSystemID", get_handle(data["system_interface"])) == data["system_id"]
    assert call("getBusInterfaceTargetID", get_handle(data["target_interface"])) == data["target_id"]
    assert call("getChannelBusInterfaceRefByID", data["channel_ref_id"]) == interface_id
    assert call("getChannelBusInterfaceRefIDs", data["channel_id"]) == [
        data["channel_ref_id"],
        get_handle(data["channel"].bus_interface_ref[1]),
    ]
    assert call("getFileSetRefGroupGroup", data["target_file_group_id"]) == "drivers"
    assert call("getIndirectInterfaceBitsInLauID", data["indirect_id"]) == get_handle(data["indirect"].bits_in_lau)
    assert call("getInitiatorAddressSpaceRefByName", data["initiator_id"]) == "space"
    assert call("getInitiatorAddressSpaceRefID", data["initiator_id"]) == address_id
    assert call("getMemoryMapRefModeRefByID", memory_ref_id, "active") == data["mode_active_id"]
    assert call("getMemoryMapRefModeRefByNames", memory_ref_id) == ["active"]
    assert call("getMirroredSystemGroup", data["mirrored_system_id"]) == "mirrored"
    assert call("getMirroredTargetBaseAddressesID", data["mirrored_target_id"]) == base_id
    assert call("getMonitorGroup", data["monitor_id"]) == "monitored"
    assert call("getRemapAddressModeRefByID", data["remap_expression_id"]) == data["mode_active_id"]
    assert call("getRemapAddressesRemapAddressID", record_id) == data["remap_expression_id"]
    assert call("getSystemGroup", data["system_id"]) == "control"
    assert call("getTargetFileSetRefGroupIDs", target_id) == [data["target_file_group_id"]]
    assert call("getTargetMemoryMapRefByName", target_id) == "map"
    assert call("getTargetMemoryMapRefID", target_id) == memory_ref_id
    assert call("getTargetTransparentBridgeIDs", target_id) == []

    expected = {
        "getAbstractionTypeAbstractionRefByID",
        "getAbstractionTypeAbstractionRefByVLNV",
        "getAbstractionTypePortMapIDs",
        "getAbstractionTypeViewRefByID",
        "getAbstractionTypeViewRefByNames",
        "getAbstractionTypeViewRefIDs",
        "getAddressSpaceRefBaseAddress",
        "getAddressSpaceRefBaseAddressExpression",
        "getAddressSpaceRefBaseAddressID",
        "getAddressSpaceRefModeRefByID",
        "getAddressSpaceRefModeRefByNames",
        "getBaseAddressesRange",
        "getBaseAddressesRangeExpression",
        "getBaseAddressesRangeID",
        "getBaseAddressesRemapAddressIDs",
        "getBusInterfaceAbstractionTypeIDs",
        "getBusInterfaceBitSteering",
        "getBusInterfaceBitSteeringExpression",
        "getBusInterfaceBitSteeringID",
        "getBusInterfaceBitsInLau",
        "getBusInterfaceBitsInLauExpression",
        "getBusInterfaceBitsInLauID",
        "getBusInterfaceBusTypeID",
        "getBusInterfaceBusTypeRefByID",
        "getBusInterfaceBusTypeRefByVLNV",
        "getBusInterfaceConnectionRequired",
        "getBusInterfaceEndianness",
        "getBusInterfaceInitiatorID",
        "getBusInterfaceInterfaceMode",
        "getBusInterfaceMirroredSystemID",
        "getBusInterfaceMirroredTargetID",
        "getBusInterfaceMonitorID",
        "getBusInterfaceRefLocalName",
        "getBusInterfaceSystemID",
        "getBusInterfaceTargetID",
        "getChannelBusInterfaceRefByID",
        "getChannelBusInterfaceRefIDs",
        "getFileSetRefGroupGroup",
        "getIndirectInterfaceBitsInLauID",
        "getInitiatorAddressSpaceRefByName",
        "getInitiatorAddressSpaceRefID",
        "getMemoryMapRefModeRefByID",
        "getMemoryMapRefModeRefByNames",
        "getMirroredSystemGroup",
        "getMirroredTargetBaseAddressesID",
        "getMonitorGroup",
        "getRemapAddressModeRefByID",
        "getRemapAddressesRemapAddressID",
        "getSystemGroup",
        "getTargetFileSetRefGroupIDs",
        "getTargetMemoryMapRefByName",
        "getTargetMemoryMapRefID",
        "getTargetTransparentBridgeIDs",
    }
    assert seen == expected
    assert len(seen) == 53


def test_every_extended_operation_executes_and_removes_through_the_public_api():
    data = _operation_fixture()
    seen: set[str] = set()

    def call(name: str, *args):
        seen.add(name)
        return getattr(api, name)(*args)

    at_id = data["abstraction_type_id"]
    address_id = data["address_ref_id"]
    base_id = data["base_addresses_id"]
    interface_id = data["interface_id"]
    target_id = data["target_id"]
    record_id = data["remap_record_id"]
    channel_id = data["channel_id"]

    port_id = call("addAbstractionTypePortMap", at_id, "logical", "physical")
    view_ref_id = call("addAbstractionTypeViewRef", at_id, "extra")
    assert call("addAddressSpaceRefModeRef", address_id, "sleep")
    assert call("removeAddressSpaceRefModeRef", address_id, "sleep")
    call("addMemoryMapRefModeRef", data["memory_ref_id"], "sleep")
    assert call("removeMemoryMapRefModeRef", data["memory_ref_id"], "sleep")
    abstraction_type_id = call("addBusInterfaceAbstractionType", interface_id, ("acme", "abstractions", "new", "1"))
    channel_ref_id = call("addChannelBusInterfaceRef", channel_id, "extra")
    file_group_id = call("addTargetFileSetRefGroup", target_id)
    bridge_id = call("addTargetTransparentBridge", target_id, "master")

    assert call("setAddressSpaceRefBaseAddress", address_id, "16")
    assert call("setBaseAddressesRange", base_id, "128")
    assert call("setBusInterfaceBitSteering", interface_id, "1")
    assert call("setBusInterfaceBitsInLau", interface_id, "32")
    assert call("setBusInterfaceBusType", interface_id, ("acme", "buses", "control", "1.0"))
    assert call("setBusInterfaceConnectionRequired", interface_id, True)
    assert call("setBusInterfaceEndianness", interface_id, "little")
    assert call("setBusInterfaceRefLocalName", data["channel_ref_id"], "master")
    assert call("setFileSetRefGroupGroup", file_group_id, "drivers")
    assert call("setFileSetRefLocalName", data["file_set_ref_id"], "rtl")
    assert call("setIndirectInterfaceBitsInLau", data["indirect_id"], "16")
    assert call("setInitiatorAddressSpaceRef", data["initiator_id"], "space")
    assert call("setMirroredSystemGroup", data["mirrored_system_id"], "data")
    assert call("setMirroredTargetBaseAddresses", data["mirrored_target_id"], "8", "128")
    assert call("setMonitorGroup", data["monitor_id"], "observe")
    assert call("setRemapAddressesRemapAddress", record_id, "12")
    assert call("setSystemGroup", data["system_id"], "data")

    # Exercise every bus-interface mode setter, then the same-mode target edit.
    assert call("setBusInterfaceInitiator", data["switch_id"])
    assert call("setBusInterfaceMirroredInitiator", data["switch_id"])
    assert call("setBusInterfaceMirroredSystem", data["switch_id"], "mirror")
    assert call("setBusInterfaceMirroredTarget", data["switch_id"])
    assert call("setBusInterfaceMonitor", data["switch_id"], "target")
    assert call("setBusInterfaceSystem", data["switch_id"], "system")
    assert call("setBusInterfaceTarget", data["switch_id"], "map")
    switch_target_id = api.getBusInterfaceTargetID(data["switch_id"])
    assert call("removeTargetTransparentBridge", bridge_id)
    assert call("setTargetMemoryMapRef", target_id, "map")
    extra_record_id = call("addBaseAddressesRemapAddresses", base_id, "24")

    assert call("removeAbstractionTypePortMap", port_id)
    assert call("removeAbstractionTypeViewRef", view_ref_id)
    assert call("removeAddressSpaceRefBaseAddress", address_id)
    assert call("removeBaseAddressesRemapAddresses", extra_record_id)
    assert api.removeBusDefinitionSystemGroupName(data["system_group_name_id"])
    seen.add("removeBusDefinitionSystemGroupName")
    assert api.removeBusDefinitionSystemGroupName is bus_definition.removeBusDefinitionSystemGroupName
    assert call("removeBusInterfaceAbstractionType", abstraction_type_id)
    assert call("removeBusInterfaceBitSteering", interface_id)
    assert call("removeBusInterfaceBitsInLau", interface_id)
    assert call("removeBusInterfaceConnectionRequired", interface_id)
    assert call("removeBusInterfaceEndianness", interface_id)
    assert call("removeChannelBusInterfaceRef", channel_ref_id)
    assert call("removeFileSetRefGroupGroup", file_group_id)
    assert call("removeIndirectInterfaceBitsInLau", data["indirect_id"])
    assert call("removeInitiatorAddressSpaceRef", data["initiator_id"])
    assert call("removeMirroredTargetBaseAddresses", data["mirrored_target_id"])
    assert call("removeMonitorGroup", data["monitor_id"])
    assert call("removeTargetFileSetRefGroup", file_group_id)
    assert call("removeTargetMemoryMapRef", target_id)

    expected = {
        "addAbstractionTypePortMap",
        "addAbstractionTypeViewRef",
        "addAddressSpaceRefModeRef",
        "addBaseAddressesRemapAddresses",
        "addBusInterfaceAbstractionType",
        "addChannelBusInterfaceRef",
        "addMemoryMapRefModeRef",
        "addTargetFileSetRefGroup",
        "addTargetTransparentBridge",
        "removeAbstractionTypePortMap",
        "removeAbstractionTypeViewRef",
        "removeAddressSpaceRefBaseAddress",
        "removeAddressSpaceRefModeRef",
        "removeBaseAddressesRemapAddresses",
        "removeBusDefinitionSystemGroupName",
        "removeBusInterfaceAbstractionType",
        "removeBusInterfaceBitSteering",
        "removeBusInterfaceBitsInLau",
        "removeBusInterfaceConnectionRequired",
        "removeBusInterfaceEndianness",
        "removeChannelBusInterfaceRef",
        "removeFileSetRefGroupGroup",
        "removeIndirectInterfaceBitsInLau",
        "removeInitiatorAddressSpaceRef",
        "removeMemoryMapRefModeRef",
        "removeMirroredTargetBaseAddresses",
        "removeMonitorGroup",
        "removeTargetFileSetRefGroup",
        "removeTargetMemoryMapRef",
        "removeTargetTransparentBridge",
        "setAddressSpaceRefBaseAddress",
        "setBaseAddressesRange",
        "setBusInterfaceBitSteering",
        "setBusInterfaceBitsInLau",
        "setBusInterfaceBusType",
        "setBusInterfaceConnectionRequired",
        "setBusInterfaceEndianness",
        "setBusInterfaceInitiator",
        "setBusInterfaceMirroredInitiator",
        "setBusInterfaceMirroredSystem",
        "setBusInterfaceMirroredTarget",
        "setBusInterfaceMonitor",
        "setBusInterfaceRefLocalName",
        "setBusInterfaceSystem",
        "setBusInterfaceTarget",
        "setFileSetRefGroupGroup",
        "setFileSetRefLocalName",
        "setIndirectInterfaceBitsInLau",
        "setInitiatorAddressSpaceRef",
        "setMirroredSystemGroup",
        "setMirroredTargetBaseAddresses",
        "setMonitorGroup",
        "setRemapAddressesRemapAddress",
        "setSystemGroup",
        "setTargetMemoryMapRef",
    }
    assert seen == expected
    assert len(seen) == 55
    assert resolve_handle(switch_target_id) is not None


def test_completion_operations_reject_malformed_values_and_foreign_nested_handles():
    data = _operation_fixture()
    interface_id = data["interface_id"]
    current_choice = data["interface"].choice
    with pytest.raises(TgiError):
        api.setBusInterfaceTarget(interface_id, "invalid name")
    with pytest.raises(TgiError):
        api.setBusInterfaceBusType(interface_id, ("acme", "", "bus", "1"))
    with pytest.raises(TgiError):
        api.setBusInterfaceEndianness(interface_id, [])
    with pytest.raises(TgiError):
        api.setBusInterfaceMonitor(data["switch_id"], [])
    with pytest.raises(TgiError):
        api.setBusInterfaceBitsInLau(interface_id, "0")
    assert data["interface"].choice is current_choice

    foreign_abstraction_id = api.addBusInterfaceAbstractionType(interface_id, ("acme", "abstractions", "other", "1"))
    with pytest.raises(TgiError):
        api.getAbstractionTypeViewRefByID(foreign_abstraction_id, data["view_ref_id"])
    assert api.removeBusInterfaceAbstractionType(foreign_abstraction_id)

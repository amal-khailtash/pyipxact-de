"""Exercise the complete IEEE 1685-2022 Component BASE and EXTENDED API."""

import pytest

from amal.eda.accellera.ipxact.v1685_2022.tgi import component as api
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import (
    TgiError,
    get_handle,
    get_parent_info,
    registry,
    resolve_handle,
)
from org.accellera.ipxact.v1685_2022 import Component


@pytest.fixture
def component():
    registry.clear()
    root = Component(vendor="v", library="l", name="component", version="1")
    yield root, get_handle(root)
    registry.clear()


def test_all_78_annex_operations_execute_on_generated_component(component):
    root, root_id = component
    from org.accellera.ipxact.v1685_2022.always_on import AlwaysOn
    from org.accellera.ipxact.v1685_2022.component_type import ComponentType as CT

    root.power_domains = CT.PowerDomains(
        power_domain=[CT.PowerDomains.PowerDomain(name="power", always_on=AlwaysOn(value="1"))]
    )

    space = api.addComponentAddressSpace(root_id, "space", "4096", "32")
    initiator = api.addComponentInitiatorBusInterface(root_id, "initiator", ["v", "l", "bus", "1"])
    target = api.addComponentTargetBusInterface(root_id, "target", ["v", "l", "bus", "1"])
    channel = api.addComponentChannel(root_id, "channel", ["initiator", "target"])
    choice = api.addComponentChoice(root_id, "choice", ["off", "on"])
    clearbox = api.addComponentClearboxElement(root_id, "clearbox", "signal")
    generator = api.addComponentComponentGenerator(root_id, "generator", "generate.py")
    component_instantiation = api.addComponentComponentInstantiation(root_id, "componentInstance")
    cpu = api.addComponentCpu(root_id, "cpu", "map", "2048", "32")
    design_configuration = api.addComponentDesignConfigurationInstantiation(
        root_id, "configuration", ["v", "l", "configuration", "1"]
    )
    design = api.addComponentDesignInstantiation(root_id, "design", ["v", "l", "design", "1"])
    file_set = api.addComponentFileSet(root_id, "files")
    indirect = api.addComponentIndirectInterface(root_id, "indirect", "address", "data", "map")
    mirrored_initiator = api.addComponentMirroredInitiatorBusInterface(root_id, "mirrorI", ["v", "l", "bus", "1"])
    mirrored_system = api.addComponentMirroredSystemBusInterface(root_id, "mirrorS", ["v", "l", "bus", "1"], "group")
    mirrored_target = api.addComponentMirroredTargetBusInterface(root_id, "mirrorT", ["v", "l", "bus", "1"])
    mode = api.addComponentMode(root_id, "mode")
    monitor = api.addComponentMonitorBusInterface(root_id, "monitor", ["v", "l", "bus", "1"], "target")
    clock = api.addComponentOtherClockDriver(root_id, "clock", "10", "0", "1", "5")
    reset = api.addComponentResetType(root_id, "reset")
    structured_interface = api.addComponentStructuredInterfacePort(root_id, "interface", "TYPE")
    structured_struct = api.addComponentStructuredStructPort(root_id, "struct", "TYPE", "in")
    structured_union = api.addComponentStructuredUnionPort(root_id, "union", "TYPE", "member", "out")
    system = api.addComponentSystemBusInterface(root_id, "system", ["v", "l", "bus", "1"], "group")
    transactional = api.addComponentTransactionalPort(root_id, "transaction", "requires")
    view = api.addComponentView(root_id, "view")
    wire = api.addComponentWirePort(root_id, "wire", "inout")
    memory_map = api.addComponentMemoryMap(root_id, "map")

    # All 24 BASE functions run against the component and its created children.
    assert api.getComponentAddressSpaceIDs(root_id) == [space]
    assert set(api.getComponentBusInterfaceIDs(root_id)) == {
        initiator,
        target,
        mirrored_initiator,
        mirrored_system,
        mirrored_target,
        monitor,
        system,
    }
    assert api.getComponentChannelIDs(root_id) == [channel]
    assert api.getComponentChoiceIDs(root_id) == [choice]
    assert api.getComponentClearboxElementIDs(root_id) == [clearbox]
    assert api.getComponentComponentGeneratorIDs(root_id) == [generator]
    assert api.getComponentComponentInstantiationIDs(root_id) == [component_instantiation]
    assert api.getComponentCpuIDs(root_id) == [cpu]
    assert api.getComponentDesignConfigurationInstantiationIDs(root_id) == [design_configuration]
    assert api.getComponentDesignInstantiationIDs(root_id) == [design]
    assert api.getComponentExternalTypeDefinitionsIDs(root_id) == []
    assert api.getComponentFileSetIDs(root_id) == [file_set]
    assert api.getComponentIndirectInterfaceIDs(root_id) == [indirect]
    assert api.getComponentMemoryMapIDs(root_id) == [memory_map]
    assert api.getComponentModeIDs(root_id) == [mode]
    assert api.getComponentOtherClockDriverIDs(root_id) == [clock]
    assert set(api.getComponentPortIDs(root_id)) == {
        structured_interface,
        structured_struct,
        structured_union,
        transactional,
        wire,
    }
    power_domain = api.getComponentPowerDomainIDs(root_id)[0]
    assert api.removePowerDomainAlwaysOn(power_domain)
    assert api.getComponentResetTypeIDs(root_id) == [reset]
    assert api.getComponentSelectedViewIDs(root_id) == []
    assert api.getComponentViewIDs(root_id) == [view]
    assert api.getModeCondition(mode) is None
    assert api.getModeConditionExpression(mode) is None
    assert api.getModeName(mode) == "mode"

    # The remaining eight EXTENDED calls mutate existing owned schema nodes.
    assert api.setIndirectInterfaceIndirectAddressRef(indirect, "new_address")
    assert api.setIndirectInterfaceIndirectDataRef(indirect, "new_data")
    assert api.setMemoryMapAddressUnitBits(memory_map, "8")
    assert api.removeMemoryMapAddressUnitBits(memory_map)
    assert api.setModeCondition(mode, "1'b1")
    assert api.getModeCondition(mode) == "1"
    assert api.getModeConditionExpression(mode) == "1'b1"
    assert api.setModeName(mode, "enabled")
    assert api.getModeName(mode) == "enabled"
    assert api.removeModeCondition(mode)

    # The 18 component-child removers all accept only their child handles.
    for handle in api.getComponentBusInterfaceIDs(root_id):
        assert api.removeComponentBusInterface(handle)
    for operation, handle in (
        (api.removeComponentAddressSpace, space),
        (api.removeComponentChannel, channel),
        (api.removeComponentChoice, choice),
        (api.removeComponentClearboxElement, clearbox),
        (api.removeComponentComponentGenerator, generator),
        (api.removeComponentComponentInstantiation, component_instantiation),
        (api.removeComponentCpu, cpu),
        (api.removeComponentDesignConfigurationInstantiation, design_configuration),
        (api.removeComponentDesignInstantiation, design),
        (api.removeComponentFileSet, file_set),
        (api.removeComponentIndirectInterface, indirect),
        (api.removeComponentMemoryMap, memory_map),
        (api.removeComponentMode, mode),
        (api.removeComponentOtherClockDriver, clock),
        (api.removeComponentPort, structured_interface),
        (api.removeComponentPort, structured_struct),
        (api.removeComponentPort, structured_union),
        (api.removeComponentPort, transactional),
        (api.removeComponentPort, wire),
        (api.removeComponentResetType, reset),
        (api.removeComponentView, view),
    ):
        assert operation(handle)

    assert len(api.__all__) == 78
    assert resolve_handle(space) is None
    assert resolve_handle(memory_map) is None
    assert root.model is None


def test_component_bus_interface_modes_and_nested_ownership(component):
    root, root_id = component
    expected = (
        (api.addComponentInitiatorBusInterface, ["v", "l", "bus", "1"], "Initiator"),
        (api.addComponentTargetBusInterface, ["v", "l", "bus", "1"], "Target"),
        (api.addComponentSystemBusInterface, ["v", "l", "bus", "1"], "System", "g"),
        (api.addComponentMirroredInitiatorBusInterface, ["v", "l", "bus", "1"], "MirroredInitiator"),
        (api.addComponentMirroredSystemBusInterface, ["v", "l", "bus", "1"], "MirroredSystem", "g"),
        (api.addComponentMirroredTargetBusInterface, ["v", "l", "bus", "1"], "MirroredTarget"),
    )
    handles = []
    for item in expected:
        operation, vlnv, role, *extra = item
        handle = operation(root_id, role, vlnv, *extra)
        handles.append(handle)
        assert get_parent_info(handle).parent_handle == root_id
        assert resolve_handle(handle).choice is not None
    assert len(handles) == 6


@pytest.mark.parametrize(
    "operation",
    [
        lambda handle: api.addComponentAddressSpace(handle, "bad", "0", "32"),
        lambda handle: api.addComponentChoice(handle, "empty", []),
        lambda handle: api.addComponentChannel(handle, "short", ["one"]),
        lambda handle: api.addComponentClearboxElement(handle, "bad", "unknown"),
        lambda handle: api.addComponentComponentGenerator(handle, "bad", ""),
        lambda handle: api.addComponentInitiatorBusInterface(handle, "bad", ["v", "l", "bus"]),
        lambda handle: api.addComponentWirePort(handle, "bad", "sideways"),
        lambda handle: api.addComponentTransactionalPort(handle, "bad", "sideways"),
        lambda handle: api.addComponentStructuredStructPort(handle, "bad", "TYPE", "sideways"),
    ],
)
def test_invalid_add_inputs_leave_component_unchanged(component, operation):
    root, root_id = component
    before = root
    with pytest.raises(TgiError):
        operation(root_id)
    assert root is before
    assert root.address_spaces is None
    assert root.model is None
    assert root.bus_interfaces is None


def test_invalid_setters_and_remover_handles_do_not_change_owned_values(component):
    root, root_id = component
    mode = api.addComponentMode(root_id, "active")
    api.setModeCondition(mode, "1'b1")
    memory_map = api.addComponentMemoryMap(root_id, "map")
    api.setMemoryMapAddressUnitBits(memory_map, "8")
    condition = resolve_handle(mode).condition
    address_bits = next(item for item in resolve_handle(memory_map).choice if item.value == "8")

    for setter, args in (
        (api.setModeCondition, (mode, "2")),
        (api.setModeCondition, (mode, "-1")),
        (api.setMemoryMapAddressUnitBits, (memory_map, "0")),
        (api.setMemoryMapAddressUnitBits, (memory_map, "-1")),
        (api.setMemoryMapAddressUnitBits, (memory_map, None)),
    ):
        with pytest.raises(TgiError):
            setter(*args)

    assert resolve_handle(mode).condition is condition
    assert next(item for item in resolve_handle(memory_map).choice if item.value == "8") is address_bits
    with pytest.raises(TgiError):
        api.removeComponentMode(root_id)
    assert api.removeComponentMode(mode)
    assert not api.removeComponentMode(mode)
    assert not api.removeComponentAddressSpace("missing")

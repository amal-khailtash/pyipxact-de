"""Removed model subtrees cannot be edited through previously allocated handles."""

import pytest

from amal.eda.accellera.ipxact.v1685_2022.tgi import abstraction_definition as api
from amal.eda.accellera.ipxact.v1685_2022.tgi import top_element
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import (
    HandleManager,
    TgiError,
    get_handle,
    get_parent_info,
    registry,
    resolve_handle,
)
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import AbstractionDefinition


@pytest.fixture(autouse=True)
def clean_registry():
    registry.clear()
    yield
    registry.clear()


def make_port(parsed=False):
    root_id = top_element.createAbstractionDef(("v", "l", "a", "1"), ("v", "l", "b", "1"), "data", "wire")
    port_id = api.getAbstractionDefPortIDs(root_id)[0]
    packet_id = api.addAbstractionDefPortPacket(port_id, "packet", "field", "8")
    field_id = api.getPacketPacketFieldIDs(packet_id)[0]
    api.setPacketFieldValue(field_id, "1")
    if parsed:
        root = XmlDocument.parser().from_string(XmlDocument.serializer().render(resolve_handle(root_id)),
                                               AbstractionDefinition)
        root_id = get_handle(root)
        port_id = api.getAbstractionDefPortIDs(root_id)[0]
        packet_id = api.getAbstractionDefPortPacketIDs(port_id)[0]
        field_id = api.getPacketPacketFieldIDs(packet_id)[0]
    return root_id, port_id, packet_id, field_id


@pytest.mark.parametrize("parsed", [False, True])
@pytest.mark.parametrize("remove", ["field", "packet", "port"])
def test_nested_removal_invalidates_directly_allocated_children(parsed, remove):
    root_id, port_id, packet_id, field_id = make_port(parsed)
    field = resolve_handle(field_id)
    width_id = get_handle(field.width)
    value_id = get_handle(field.value)
    # Width/value handles intentionally allocated without getter ownership registration.
    sibling_id = api.addAbstractionDefPort(root_id, "sibling", "wire")
    operation, target = {
        "field": (api.removePacketPacketField, field_id),
        "packet": (api.removeAbstractionDefPortPacket, packet_id),
        "port": (api.removeAbstractionDefPort, port_id),
    }[remove]
    assert operation(target)
    for handle in (target, field_id, width_id, value_id):
        assert resolve_handle(handle) is None
        assert get_parent_info(handle) is None
    assert resolve_handle(sibling_id) is not None
    assert resolve_handle(root_id) is not None
    with pytest.raises(TgiError):
        api.setPacketFieldWidth(field_id, "16")


@pytest.mark.parametrize("conversion", [False, True])
def test_mode_removal_and_style_conversion_invalidate_width_and_constraints(conversion):
    _, port_id, packet_id, _ = make_port()
    api.setAbstractionDefPortWireOnInitiator(port_id)
    mode_id = api.getAbstractionDefPortWireOnInitiatorID(port_id)
    api.setAbstractionDefPortWireModeWidth(mode_id, "8")
    width_id = api.getAbstractionDefPortWireModeWidthID(mode_id)
    api.setAbstractionDefPortWireModeModeConstraints(mode_id, "clk")
    constraints_id = api.getAbstractionDefPortWireModeModeConstraintsID(mode_id)
    timing_id = api.getModeConstraintsTimingConstraintIDs(constraints_id)[0]
    if conversion:
        assert api.setAbstractionDefPortTransactional(port_id)
    else:
        assert api.removeAbstractionDefPortMode(mode_id)
    for handle in (mode_id, width_id, constraints_id, timing_id):
        assert resolve_handle(handle) is None
    assert resolve_handle(packet_id) is not None
    assert resolve_handle(port_id) is not None


def test_failed_detach_preserves_child_handles():
    manager = HandleManager()
    root = AbstractionDefinition.Ports.Port(logical_name="p")
    handle = manager.get(root)
    assert not manager.detach_child_by_handle(handle)
    assert manager.resolve(handle) is root


def test_forget_handles_cycles_without_invalidating_shared_scalar():
    manager = HandleManager()
    port = AbstractionDefinition.Ports.Port(logical_name="p")
    handle = manager.get(port)
    scalar_id = manager.get(port.logical_name)
    manager.register_parent(port, port, (), "single")
    assert manager.forget(handle)
    assert manager.resolve(handle) is None
    assert manager.resolve(scalar_id) == "p"
    assert not manager.forget(handle)


def test_choice_removal_invalidates_enumerations():
    root_id, _, _, _ = make_port()
    choice_id = api.addAbstractionDefChoice(root_id, "sizes", ["8", "16"])
    choice = resolve_handle(choice_id)
    enumeration_ids = [get_handle(item) for item in choice.enumeration]
    assert api.removeAbstractionDefChoice(choice_id)
    assert resolve_handle(choice_id) is None
    assert all(resolve_handle(handle) is None for handle in enumeration_ids)
    assert resolve_handle(root_id) is not None

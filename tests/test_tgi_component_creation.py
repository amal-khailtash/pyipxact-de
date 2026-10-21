"""Component factories create generated XML choices with standard signatures."""

import pytest
from lxml import etree

from amal.eda.ipxact_de.tgi.ipxact.v1685_2022 import component as api
from amal.eda.ipxact_de.tgi.ipxact.v1685_2022.core import TgiError, get_handle, get_parent_info, resolve_handle
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import Component


@pytest.fixture
def root():
    obj = Component(vendor="v", library="l", name="c", version="1")
    return get_handle(obj)


def check_xml(root):
    obj = resolve_handle(root)
    xml = XmlDocument.serializer().render(obj)
    schema = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))
    assert schema.validate(etree.fromstring(xml.encode())), schema.error_log
    assert XmlDocument.parser().from_string(xml, Component) == obj


@pytest.mark.parametrize("direction", ["in", "out", "inout", "phantom"])
def test_wire_creation_and_immediate_removal(root, direction):
    port_id = api.addComponentWirePort(root, "data", direction)
    child = resolve_handle(port_id)
    assert child.wire_or_transactional_or_structured.direction.value == direction
    assert get_parent_info(port_id).parent_handle == root
    check_xml(root)
    assert api.removeComponentPort(port_id)
    assert resolve_handle(port_id) is None


@pytest.mark.parametrize("initiative", ["requires", "provides", "both", "phantom"])
def test_transactional_creation_and_sibling_order(root, initiative):
    first = api.addComponentWirePort(root, "wire", "in")
    second = api.addComponentTransactionalPort(root, "transaction", initiative)
    assert api.getComponentPortIDs(root) == [first, second]
    assert resolve_handle(second).wire_or_transactional_or_structured.initiative.value.value == initiative
    check_xml(root)
    assert api.removeComponentPort(second)
    assert resolve_handle(first) is not None


def test_other_clock_expressions_xml_and_immediate_removal(root):
    clock_id = api.addComponentOtherClockDriver(root, "clock", "PERIOD", "OFFSET", "VALUE", "DURATION")
    clock = resolve_handle(clock_id)
    assert [clock.clock_period.value, clock.clock_pulse_offset.value, clock.clock_pulse_value.value,
            clock.clock_pulse_duration.value] == ["PERIOD", "OFFSET", "VALUE", "DURATION"]
    check_xml(root)
    child_id = get_handle(clock.clock_period)
    assert api.removeComponentOtherClockDriver(clock_id)
    assert resolve_handle(child_id) is None


def test_view_creation_identity_and_selective_removal(root):
    first = api.addComponentView(root, "first")
    second = api.addComponentView(root, "second")
    assert [v.name for v in resolve_handle(root).model.views.view] == ["first", "second"]
    assert get_parent_info(first).parent_handle == root
    check_xml(root)
    assert api.removeComponentView(first)
    assert not api.removeComponentView(first)
    assert resolve_handle(second) is not None
    check_xml(root)


@pytest.mark.parametrize("operation", [
    lambda root: api.addComponentWirePort(root, "p", "bad"),
    lambda root: api.addComponentTransactionalPort(root, "p", "bad"),
    lambda root: api.addComponentView(root, ""),
    lambda root: api.addComponentOtherClockDriver(root, "clock", "", "0", "1", "5"),
    lambda root: api.addComponentWirePort(root, None, "in"),
])
def test_invalid_arguments_before_scaffolding(root, operation):
    with pytest.raises(TgiError):
        operation(root)
    assert resolve_handle(root).model is None
    assert resolve_handle(root).other_clock_drivers is None


@pytest.mark.parametrize("operation", [
    lambda: api.addComponentWirePort("missing", "p", "in"),
    lambda: api.addComponentTransactionalPort("missing", "p", "requires"),
    lambda: api.addComponentView("missing", "v"),
    lambda: api.addComponentOtherClockDriver("missing", "c", "10", "0", "1", "5"),
])
def test_invalid_root_handles(operation):
    with pytest.raises(TgiError):
        operation()

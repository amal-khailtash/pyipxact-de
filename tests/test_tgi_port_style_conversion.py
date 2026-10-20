"""Logical style conversion preserves port metadata and independent packet content."""

import pytest

from amal.eda.ipxact_de.tgi.ipxact.v1685_2022 import abstraction_definition as api
from amal.eda.ipxact_de.tgi.ipxact.v1685_2022 import top_element
from amal.eda.ipxact_de.tgi.ipxact.v1685_2022.core import (
    TgiError,
    TgiFaultCode,
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


@pytest.mark.parametrize("source,target", [("wire", "transactional"), ("transactional", "wire")])
@pytest.mark.parametrize("parsed", [False, True])
def test_conversion_preserves_port_and_packet_contracts(source, target, parsed):
    root_id = top_element.createAbstractionDef(("v", "l", "a", "1"), ("v", "l", "b", "1"), "data", source)
    port_id = api.getAbstractionDefPortIDs(root_id)[0]
    api.addAbstractionDefPortPacket(port_id, "header", "tag", "8")
    root = resolve_handle(root_id)
    if parsed:
        root = XmlDocument.parser().from_string(XmlDocument.serializer().render(root), AbstractionDefinition)
        root_id = get_handle(root)
        port_id = api.getAbstractionDefPortIDs(root_id)[0]
    port = resolve_handle(port_id)
    port.match = False
    port.id = "logical-port"
    packet_ids = api.getAbstractionDefPortPacketIDs(port_id)
    packet = resolve_handle(packet_ids[0])
    packet_xml = XmlDocument.serializer().render(packet)
    old_style = port.wire_or_transactional
    old_handle = get_handle(old_style)
    setter = getattr(api, f"setAbstractionDefPort{target.title()}")
    assert setter(abstractionDefPortID=port_id)
    assert resolve_handle(old_handle) is None
    assert port.wire_or_transactional is not old_style
    assert api.getAbstractionDefPortStyle(port_id) == target
    assert api.getAbstractionDefPortLogicalName(port_id) == "data"
    assert api.getAbstractionDefPortMatch(port_id) is False
    assert port.id == "logical-port"
    assert api.getAbstractionDefPortIDs(root_id) == [port_id]
    assert api.getAbstractionDefPortPacketIDs(port_id) == packet_ids
    assert resolve_handle(packet_ids[0]) is packet
    assert XmlDocument.serializer().render(packet) == packet_xml
    new_style = port.wire_or_transactional
    new_handle = get_handle(new_style)
    if target == "wire":
        api.setAbstractionDefPortWireDefaultValue(port_id, "WIDTH + 1")
    else:
        api.setAbstractionDefPortTransactionalOnInitiator(port_id)
    before = XmlDocument.serializer().render(root)
    assert setter(port_id)
    assert port.wire_or_transactional is new_style
    assert get_handle(new_style) == new_handle
    assert XmlDocument.serializer().render(root) == before
    assert get_parent_info(new_handle).parent_handle == port_id
    assert get_parent_info(new_handle).path == ("wire_or_transactional",)
    loaded = XmlDocument.parser().from_string(before, AbstractionDefinition)
    assert loaded == root
    loaded_port_id = api.getAbstractionDefPortIDs(get_handle(loaded))[0]
    assert api.getAbstractionDefPortStyle(loaded_port_id) == target
    assert len(api.getAbstractionDefPortPacketIDs(loaded_port_id)) == 1


@pytest.mark.parametrize("setter", [api.setAbstractionDefPortWire, api.setAbstractionDefPortTransactional])
@pytest.mark.parametrize("wrong", ["missing", "root", "style"])
def test_invalid_handles_do_not_mutate(setter, wrong):
    root_id = top_element.createAbstractionDef(("v", "l", "a", "1"), ("v", "l", "b", "1"), "data", "wire")
    root = resolve_handle(root_id)
    port = resolve_handle(api.getAbstractionDefPortIDs(root_id)[0])
    handle = {"missing": "missing", "root": root_id, "style": get_handle(port.wire_or_transactional)}[wrong]
    before = XmlDocument.serializer().render(root)
    with pytest.raises(TgiError) as error:
        setter(handle)
    assert error.value.fault_code == TgiFaultCode.INVALID_ID
    assert XmlDocument.serializer().render(root) == before

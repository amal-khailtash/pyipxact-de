"""Packet edits remain atomic and preserve XML and handle identity."""

import pytest

from amal.eda.accellera.ipxact.v1685_2022.tgi import abstraction_definition as api
from amal.eda.accellera.ipxact.v1685_2022.tgi import top_element
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import (
    TgiError,
    TgiFaultCode,
    get_handle,
    registry,
    resolve_handle,
)
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import AbstractionDefinition


@pytest.fixture
def packet():
    registry.clear()
    root = top_element.createAbstractionDef(("v", "l", "a", "1"), ("v", "l", "b", "1"), "data", "wire")
    port = api.getAbstractionDefPortIDs(root)[0]
    yield port, api.addAbstractionDefPortPacket(port, "header", "tag", "8")
    registry.clear()


@pytest.mark.parametrize("parsed", [False, True])
def test_editing_and_selective_removal(packet, parsed):
    port, pkt = packet
    first = api.getPacketPacketFieldIDs(pkt)[0]
    added = api.addPacketPacketField(pkt, "payload", 32)
    assert api.getPacketPacketFieldIDs(pkt) == [first, added]
    assert api.getPacketFieldWidthExpression(added) == "32"
    width = api.getPacketFieldWidthID(added)
    assert api.setPacketFieldWidth(added, "WIDTH + 1")
    assert api.getPacketFieldWidthID(added) == width
    assert api.setPacketFieldValue(added, "VALUE")
    value = api.getPacketFieldValueID(added)
    resolve_handle(value).other_attributes = {"{urn:test}marker": "preserved"}
    assert api.setPacketFieldValue(added, "VALUE + 1")
    assert api.getPacketFieldValueID(added) == value
    assert resolve_handle(value).other_attributes == {"{urn:test}marker": "preserved"}
    assert api.setPacketEndianness(pkt, "big")
    assert api.setPacketFieldEndianness(added, "little")
    if parsed:
        obj = resolve_handle(port)
        xml = XmlDocument.serializer().render(obj)
        loaded = XmlDocument.parser().from_string(xml, AbstractionDefinition.Ports.Port)
        assert loaded == obj
        port = get_handle(loaded)
        pkt = api.getAbstractionDefPortPacketIDs(port)[0]
        first, added = api.getPacketPacketFieldIDs(pkt)
    assert api.getPacketEndianness(pkt) == "big"
    assert api.getPacketFieldEndianness(added) == "little"
    assert api.getPacketFieldValueExpression(added) == "VALUE + 1"
    assert api.getPacketFieldWidthExpression(added) == "WIDTH + 1"
    assert api.removePacketFieldEndianness(added)
    assert not api.removePacketFieldEndianness(added)
    assert resolve_handle(added).endianness is None
    assert api.removePacketEndianness(pkt)
    assert not api.removePacketEndianness(pkt)
    assert resolve_handle(pkt).endianness is None
    assert api.removePacketPacketField(added)
    assert not api.removePacketPacketField(added)
    assert api.getPacketPacketFieldIDs(pkt) == [first]
    assert resolve_handle(added) is None
    assert api.removeAbstractionDefPortPacket(pkt)
    assert not api.removeAbstractionDefPortPacket(pkt)
    assert api.getAbstractionDefPortPacketIDs(port) == []
    assert api.getAbstractionDefPortStyle(port) == "wire"


@pytest.mark.parametrize("name,width", [("", 8), (None, 8), ("x", 0), ("x", -1),
                                       ("x", True), ("x", "8"), ("x", 2.5)])
def test_invalid_field_creation(packet, name, width):
    _, pkt = packet
    before = list(resolve_handle(pkt).packet_fields.packet_field)
    with pytest.raises(TgiError) as error:
        api.addPacketPacketField(pkt, name, width)
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert resolve_handle(pkt).packet_fields.packet_field == before


@pytest.mark.parametrize("setter", [api.setPacketFieldWidth, api.setPacketFieldValue,
                                    api.setPacketFieldEndianness, api.setPacketEndianness])
@pytest.mark.parametrize("invalid", [None, "", "  ", 2])
def test_invalid_setter_is_atomic(packet, setter, invalid):
    _, pkt = packet
    handle = pkt if setter is api.setPacketEndianness else api.getPacketPacketFieldIDs(pkt)[0]
    before = XmlDocument.serializer().render(resolve_handle(packet[0]))
    with pytest.raises(TgiError) as error:
        setter(handle, invalid)
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert XmlDocument.serializer().render(resolve_handle(packet[0])) == before


@pytest.mark.parametrize("setter", [api.setPacketEndianness, api.setPacketFieldEndianness])
@pytest.mark.parametrize("invalid", ["BIG", "middle"])
def test_endianness_rejects_unknown_values(packet, setter, invalid):
    _, pkt = packet
    handle = pkt if setter is api.setPacketEndianness else api.getPacketPacketFieldIDs(pkt)[0]
    with pytest.raises(TgiError) as error:
        setter(handle, invalid)
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT


@pytest.mark.parametrize("operation,args", [
    (api.addPacketPacketField, ("field", 8)), (api.setPacketEndianness, ("big",)),
    (api.setPacketFieldEndianness, ("little",)), (api.setPacketFieldValue, ("VALUE",)),
    (api.setPacketFieldWidth, ("WIDTH",)),
])
@pytest.mark.parametrize("wrong_type", [False, True])
def test_invalid_edit_handle(operation, args, wrong_type):
    handle = get_handle(object()) if wrong_type else "missing"
    with pytest.raises(TgiError) as error:
        operation(handle, *args)
    assert error.value.fault_code == TgiFaultCode.INVALID_ID


@pytest.mark.parametrize("operation", [api.removePacketPacketField, api.removeAbstractionDefPortPacket,
                                      api.removePacketEndianness, api.removePacketFieldEndianness])
def test_invalid_removal(operation):
    assert not operation("missing")
    assert not operation(get_handle(object()))

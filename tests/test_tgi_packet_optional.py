"""Optional packet metadata retains explicit XML values and child identity."""

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
def test_qualifier_creation_preservation_and_optional_removal(packet, parsed):
    port, pkt = packet
    field = api.getPacketPacketFieldIDs(pkt)[0]
    assert not api.removePacketFieldQualifier(field)
    assert not api.removePacketFieldValue(field)
    assert api.setPacketFieldQualifier(field)
    qualifier = api.getPacketFieldQualifierID(field)
    obj = resolve_handle(qualifier)
    obj.is_address = True
    obj.is_data = False
    obj.id = "qualifier-id"
    assert api.setPacketFieldQualifier(field)
    assert api.getPacketFieldQualifierID(field) == qualifier
    assert obj.is_address is True and obj.is_data is False
    assert obj.id == "qualifier-id"
    assert api.setPacketFieldValue(field, "VALUE + 1")
    if parsed:
        original = resolve_handle(port)
        loaded = XmlDocument.parser().from_string(
            XmlDocument.serializer().render(original), AbstractionDefinition.Ports.Port)
        assert loaded == original
        port = get_handle(loaded)
        pkt = api.getAbstractionDefPortPacketIDs(port)[0]
        # Exercise removal before traversing/registering the optional children.
        field = get_handle(resolve_handle(pkt).packet_fields.packet_field[0])
        qualifier = get_handle(resolve_handle(field).qualifier)
    value = get_handle(resolve_handle(field).value)
    width = api.getPacketFieldWidthID(field)
    assert api.removePacketFieldQualifier(field)
    assert resolve_handle(qualifier) is None
    assert api.getPacketFieldQualifierID(field) is None
    assert not api.removePacketFieldQualifier(field)
    assert api.removePacketFieldValue(field)
    assert resolve_handle(value) is None
    assert api.getPacketFieldValueID(field) is None
    assert not api.removePacketFieldValue(field)
    assert api.getPacketFieldWidthID(field) == width
    assert api.setPacketFieldQualifier(field)
    assert api.getPacketFieldQualifierID(field) != qualifier
    assert api.setPacketFieldValue(field, "2")
    assert api.getPacketFieldValueID(field) != value


@pytest.mark.parametrize("packet_end", [None, "big", "little"])
@pytest.mark.parametrize("field_end", [None, "big", "little"])
def test_endianness_getters_preserve_explicit_values(packet, packet_end, field_end):
    port, pkt = packet
    field = api.getPacketPacketFieldIDs(pkt)[0]
    if packet_end is not None:
        api.setPacketEndianness(pkt, packet_end)
    if field_end is not None:
        api.setPacketFieldEndianness(field, field_end)
    assert api.getPacketEndianness(pkt) == packet_end
    assert api.getPacketFieldEndianness(field) == field_end
    original = resolve_handle(port)
    loaded = XmlDocument.parser().from_string(
        XmlDocument.serializer().render(original), AbstractionDefinition.Ports.Port)
    assert loaded == original
    pkt = api.getAbstractionDefPortPacketIDs(get_handle(loaded))[0]
    field = api.getPacketPacketFieldIDs(pkt)[0]
    assert api.getPacketEndianness(pkt) == packet_end
    assert api.getPacketFieldEndianness(field) == field_end


@pytest.mark.parametrize("operation", [api.setPacketFieldQualifier, api.getPacketEndianness,
                                      api.getPacketFieldEndianness])
@pytest.mark.parametrize("wrong_type", [False, True])
def test_invalid_handles(operation, wrong_type):
    handle = get_handle(object()) if wrong_type else "missing"
    with pytest.raises(TgiError) as error:
        operation(handle)
    assert error.value.fault_code == TgiFaultCode.INVALID_ID


@pytest.mark.parametrize("operation", [api.removePacketFieldQualifier, api.removePacketFieldValue])
def test_invalid_removal(operation):
    assert not operation("missing")
    assert not operation(get_handle(object()))

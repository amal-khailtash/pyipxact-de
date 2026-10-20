"""Packet metadata preserves expressions, ordering and parsed child ownership."""

import pytest

from amal.eda.ipxact_de.tgi.ipxact.v1685_2022 import abstraction_definition as api
from amal.eda.ipxact_de.tgi.ipxact.v1685_2022 import top_element
from amal.eda.ipxact_de.tgi.ipxact.v1685_2022.core import (
    TgiError,
    TgiFaultCode,
    detach_child_by_handle,
    get_handle,
    get_parent_info,
    registry,
    resolve_handle,
)
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import (
    AbstractionDefinition,
    PortPacketFieldType,
    QualifierType,
    UnresolvedUnsignedPositiveIntExpression,
    UnsignedBitVectorExpression,
)


@pytest.fixture
def port():
    registry.clear()
    root = top_element.createAbstractionDef(("v", "l", "a", "1"), ("v", "l", "b", "1"), "data", "wire")
    yield api.getAbstractionDefPortIDs(root)[0]
    registry.clear()


@pytest.mark.parametrize("parsed", [False, True])
def test_packet_traversal_expressions_and_identity(port, parsed):
    assert api.getAbstractionDefPortPacketIDs(port) == []
    first = api.addAbstractionDefPortPacket(port, "header", "tag", "WIDTH + 1")
    second = api.addAbstractionDefPortPacket(port, "body", "payload", "8")
    packet = resolve_handle(first)
    field = packet.packet_fields.packet_field[0]
    field.value = UnsignedBitVectorExpression(value="VALUE")
    field.qualifier = QualifierType()
    packet.packet_fields.packet_field.append(PortPacketFieldType(
        name="other", width=UnresolvedUnsignedPositiveIntExpression(value="2")))
    if parsed:
        obj = resolve_handle(port)
        loaded = XmlDocument.parser().from_string(
            XmlDocument.serializer().render(obj), AbstractionDefinition.Ports.Port)
        assert loaded == obj
        port = get_handle(loaded)
    ids = api.getAbstractionDefPortPacketIDs(port)
    assert ids == api.getAbstractionDefPortPacketIDs(port)
    if not parsed:
        assert ids == [first, second]
    assert [resolve_handle(i).name for i in ids] == ["header", "body"]
    fields = api.getPacketPacketFieldIDs(ids[0])
    assert [resolve_handle(i).name for i in fields] == ["tag", "other"]
    assert api.getAbstractionDefPortStyle(port) == "wire"
    assert api.getPacketFieldWidthExpression(fields[0]) == "WIDTH + 1"
    assert api.getPacketFieldValueExpression(fields[0]) == "VALUE"
    for getter, attr in [(api.getPacketFieldWidthID, "width"), (api.getPacketFieldValueID, "value"),
                         (api.getPacketFieldQualifierID, "qualifier")]:
        handle = getter(fields[0])
        assert handle == getter(fields[0])
        assert resolve_handle(handle) is getattr(resolve_handle(fields[0]), attr)
        assert get_parent_info(handle).path == (attr,)
        if attr != "width":
            assert detach_child_by_handle(handle)
            assert getattr(resolve_handle(fields[0]), attr) is None
    assert api.getPacketFieldValueID(fields[1]) is None
    assert api.getPacketFieldValueExpression(fields[1]) is None
    assert api.getPacketFieldQualifierID(fields[1]) is None
    assert detach_child_by_handle(fields[1])
    assert api.getPacketPacketFieldIDs(ids[0]) == [fields[0]]
    assert detach_child_by_handle(ids[0])
    assert api.getAbstractionDefPortPacketIDs(port) == [ids[1]]


@pytest.mark.parametrize("index", [0, 1, 2])
@pytest.mark.parametrize("invalid", [None, 2, "", "  "])
@pytest.mark.parametrize("existing", [False, True])
def test_creation_failure_is_atomic(port, index, invalid, existing):
    if existing:
        api.addAbstractionDefPortPacket(port, "initial", "field", "8")
    obj = resolve_handle(port)
    before = XmlDocument.serializer().render(obj)
    args = ["packet", "field", "WIDTH"]
    args[index] = invalid
    with pytest.raises(TgiError) as error:
        api.addAbstractionDefPortPacket(port, *args)
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert XmlDocument.serializer().render(obj) == before


@pytest.mark.parametrize("getter", [api.getAbstractionDefPortPacketIDs, api.getPacketPacketFieldIDs,
                                    api.getPacketFieldWidthExpression, api.getPacketFieldWidthID,
                                    api.getPacketFieldValueExpression, api.getPacketFieldValueID,
                                    api.getPacketFieldQualifierID])
@pytest.mark.parametrize("wrong_type", [False, True])
def test_invalid_getter_handles(port, getter, wrong_type):
    handle = get_handle(object()) if wrong_type else "missing"
    with pytest.raises(TgiError) as error:
        getter(handle)
    assert error.value.fault_code == TgiFaultCode.INVALID_ID


def test_invalid_creation_handle(port):
    with pytest.raises(TgiError) as error:
        api.addAbstractionDefPortPacket("missing", "packet", "field", "8")
    assert error.value.fault_code == TgiFaultCode.INVALID_ID

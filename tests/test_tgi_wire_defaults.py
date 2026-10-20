"""Wire default expressions use the generated defaultValue/requiresDriver choice."""

import pytest

from amal.eda.ipxact_de.tgi.ipxact.v1685_2022 import abstraction_definition as api
from amal.eda.ipxact_de.tgi.ipxact.v1685_2022 import top_element
from amal.eda.ipxact_de.tgi.ipxact.v1685_2022.core import (
    TgiError,
    TgiFaultCode,
    get_handle,
    get_parent_info,
    register_parent,
    registry,
    resolve_handle,
)
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import AbstractionDefinition
from org.accellera.ipxact.v1685_2022.requires_driver import RequiresDriver
from org.accellera.ipxact.v1685_2022.requires_driver_driver_type import RequiresDriverDriverType
from org.accellera.ipxact.v1685_2022.unsigned_bit_vector_expression import (
    UnsignedBitVectorExpression,
)


@pytest.fixture(autouse=True)
def clean_registry():
    registry.clear()
    yield
    registry.clear()


def make_port(style="wire"):
    root = top_element.createAbstractionDef(
        ("vendor", "library", f"abstraction-{style}", "1.0"),
        ("vendor", "library", "bus", "1.0"),
        "data",
        style,
    )
    return root, api.getAbstractionDefPortIDs(root)[0]


def get_wire(port_id):
    return resolve_handle(port_id).wire_or_transactional


def test_default_expression_identity_metadata_and_packet_xml_are_preserved():
    root, port_id = make_port()
    wire = get_wire(port_id)
    assert api.getAbstractionDefPortWireDefaultValueExpression(port_id) is None
    assert api.getAbstractionDefPortWireDefaultValueID(port_id) is None

    packet_id = api.addAbstractionDefPortPacket(port_id, "header", "tag", "8")
    packet = resolve_handle(packet_id)
    field_id = api.getPacketPacketFieldIDs(packet_id)[0]
    assert api.setPacketFieldValue(field_id, "TAG_VALUE")
    assert api.setPacketFieldEndianness(field_id, "big")
    packet_xml = XmlDocument.serializer().render(packet)
    packet_ids = api.getAbstractionDefPortPacketIDs(port_id)

    assert api.setAbstractionDefPortWireDefaultValue(port_id, " 1 + WIDTH ")
    expression_id = api.getAbstractionDefPortWireDefaultValueID(port_id)
    expression = resolve_handle(expression_id)
    expression.other_attributes = {"{urn:test}marker": "retain"}
    assert api.getAbstractionDefPortWireDefaultValueExpression(port_id) == " 1 + WIDTH "
    parent_info = get_parent_info(expression_id)
    assert parent_info.parent_handle == get_handle(wire)
    assert parent_info.path == ("default_value_or_requires_driver",)
    assert parent_info.container == "single"

    assert api.setAbstractionDefPortWireDefaultValue(port_id, "NEXT_WIDTH + 2")
    assert api.getAbstractionDefPortWireDefaultValueID(port_id) == expression_id
    assert resolve_handle(expression_id) is expression
    assert expression.other_attributes == {"{urn:test}marker": "retain"}
    assert api.getAbstractionDefPortWireDefaultValueExpression(port_id) == "NEXT_WIDTH + 2"
    assert api.getAbstractionDefPortPacketIDs(port_id) == packet_ids
    assert resolve_handle(packet_id) is packet
    assert XmlDocument.serializer().render(packet) == packet_xml

    rendered = XmlDocument.serializer().render(resolve_handle(root))
    parsed = XmlDocument.parser().from_string(rendered, AbstractionDefinition)
    assert parsed == resolve_handle(root)
    parsed_port_id = get_handle(parsed.ports.port[0])
    assert api.getAbstractionDefPortWireDefaultValueExpression(parsed_port_id) == "NEXT_WIDTH + 2"
    parsed_packet_id = api.getAbstractionDefPortPacketIDs(parsed_port_id)[0]
    parsed_field_id = api.getPacketPacketFieldIDs(parsed_packet_id)[0]
    assert api.getPacketFieldValueExpression(parsed_field_id) == "TAG_VALUE"
    assert api.getPacketFieldEndianness(parsed_field_id) == "big"


def test_default_expression_switches_choice_and_removes_only_expression():
    _, port_id = make_port()
    wire = get_wire(port_id)
    driver = RequiresDriver(value=True, driver_type=RequiresDriverDriverType.SINGLE_SHOT)
    wire.default_value_or_requires_driver = driver
    register_parent(driver, wire, ("default_value_or_requires_driver",), "single")
    driver_id = get_handle(driver)

    assert api.getAbstractionDefPortWireDefaultValueExpression(port_id) is None
    assert api.getAbstractionDefPortWireDefaultValueID(port_id) is None
    assert api.setAbstractionDefPortWireDefaultValue(port_id, "DATA")
    assert resolve_handle(driver_id) is None
    assert isinstance(wire.default_value_or_requires_driver, UnsignedBitVectorExpression)
    expression_id = api.getAbstractionDefPortWireDefaultValueID(port_id)
    assert api.getAbstractionDefPortWireDefaultValueExpression(port_id) == "DATA"

    assert api.removeAbstractionDefPortWireDefaultValue(port_id)
    assert resolve_handle(expression_id) is None
    assert wire.default_value_or_requires_driver is None
    assert not api.removeAbstractionDefPortWireDefaultValue(port_id)

    preserved_driver = RequiresDriver(value=False)
    wire.default_value_or_requires_driver = preserved_driver
    register_parent(preserved_driver, wire, ("default_value_or_requires_driver",), "single")
    preserved_driver_id = get_handle(preserved_driver)
    assert not api.removeAbstractionDefPortWireDefaultValue(port_id)
    assert wire.default_value_or_requires_driver is preserved_driver
    assert resolve_handle(preserved_driver_id) is preserved_driver


@pytest.mark.parametrize("invalid", [None, "", " \t ", 7])
def test_default_setter_rejects_invalid_values_atomically(invalid):
    root, port_id = make_port()
    before = XmlDocument.serializer().render(resolve_handle(root))
    with pytest.raises(TgiError) as error:
        api.setAbstractionDefPortWireDefaultValue(port_id, invalid)
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert XmlDocument.serializer().render(resolve_handle(root)) == before


def test_default_operations_distinguish_invalid_handles_from_wrong_style():
    _, wire_port_id = make_port("wire")
    _, transactional_port_id = make_port("transactional")

    assert api.getAbstractionDefPortWireDefaultValueExpression(transactional_port_id) is None
    assert api.getAbstractionDefPortWireDefaultValueID(transactional_port_id) is None
    assert not api.removeAbstractionDefPortWireDefaultValue(transactional_port_id)
    with pytest.raises(TgiError) as error:
        api.setAbstractionDefPortWireDefaultValue(transactional_port_id, "8")
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT

    arbitrary_handle = get_handle(object())
    for invalid_handle in ("missing", arbitrary_handle):
        for getter in (
            api.getAbstractionDefPortWireDefaultValueExpression,
            api.getAbstractionDefPortWireDefaultValueID,
        ):
            with pytest.raises(TgiError) as error:
                getter(invalid_handle)
            assert error.value.fault_code == TgiFaultCode.INVALID_ID
        with pytest.raises(TgiError) as error:
            api.setAbstractionDefPortWireDefaultValue(invalid_handle, "8")
        assert error.value.fault_code == TgiFaultCode.INVALID_ID
        assert not api.removeAbstractionDefPortWireDefaultValue(invalid_handle)

    assert api.getAbstractionDefPortWireDefaultValueExpression(wire_port_id) is None

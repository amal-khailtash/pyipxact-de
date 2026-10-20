"""Mode initiative and expression/protocol editing preserve selective identity."""

import pytest

from amal.eda.ipxact_de.tgi.ipxact.v1685_2022 import abstraction_definition as api
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
    OnInitiatorInitiative,
    OnSystemInitiative,
    OnTargetInitiative,
    Payload,
    PayloadType,
    Protocol,
    ProtocolTypeType,
    UnsignedPositiveIntExpression,
    Wire,
)

LOCI = ["onInitiator", "onTarget", "onSystem"]


@pytest.fixture(autouse=True)
def clean_registry():
    registry.clear()
    yield
    registry.clear()


def modes(style):
    container = Wire if style == "wire" else AbstractionDefinition.Ports.Port.Transactional
    return [container.OnInitiator(), container.OnTarget(), container.OnSystem(group="system")]


def port_with_modes(style, mode_objects):
    container = Wire if style == "wire" else AbstractionDefinition.Ports.Port.Transactional
    return AbstractionDefinition.Ports.Port(
        logical_name="p",
        wire_or_transactional=container(
            on_initiator=mode_objects[0], on_target=mode_objects[1], on_system=[mode_objects[2]]
        ),
    )


def assert_round_trip(port):
    text = XmlDocument.serializer().render(port)
    assert XmlDocument.parser().from_string(text, AbstractionDefinition.Ports.Port) == port


@pytest.mark.parametrize("index", range(3), ids=LOCI)
def test_initiative_uses_mode_enum_and_preserves_siblings(index):
    mode_objects = modes("transactional")
    port = port_with_modes("transactional", mode_objects)
    selected = mode_objects[index]
    enum_type = [OnInitiatorInitiative, OnTargetInitiative, OnSystemInitiative][index]
    handle = get_handle(selected)
    for value in ["requires", "provides", "both", "both"]:
        assert api.setAbstractionDefPortTransactionalModeInitiative(abstractionDefPortModeID=handle, initiative=value)
        assert selected.initiative is enum_type(value)
        assert all(other.initiative is None for other in mode_objects if other is not selected)
        assert_round_trip(port)


@pytest.mark.parametrize("index", range(3), ids=LOCI)
@pytest.mark.parametrize("invalid", [None, 8, "", "  ", "unknown", "requires "])
def test_invalid_initiative_is_atomic(index, invalid):
    mode_objects = modes("transactional")
    port = port_with_modes("transactional", mode_objects)
    handle = get_handle(mode_objects[index])
    api.setAbstractionDefPortTransactionalModeInitiative(handle, "both")
    before = XmlDocument.serializer().render(port)
    with pytest.raises(TgiError) as error:
        api.setAbstractionDefPortTransactionalModeInitiative(handle, invalid)
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert XmlDocument.serializer().render(port) == before


def test_initiative_and_width_id_reject_wrong_handles():
    for style, operation in [
        ("transactional", lambda handle: api.setAbstractionDefPortTransactionalModeInitiative(handle, "requires")),
        ("wire", api.getAbstractionDefPortWireModeWidthID),
    ]:
        other = "wire" if style == "transactional" else "transactional"
        for handle in [
            "missing",
            get_handle(object()),
            get_handle(port_with_modes(style, modes(style))),
            get_handle(modes(other)[0]),
            get_handle(UnsignedPositiveIntExpression(value="8")),
        ]:
            with pytest.raises(TgiError) as error:
                operation(handle)
            assert error.value.fault_code == TgiFaultCode.INVALID_ID


@pytest.mark.parametrize("index", range(3), ids=LOCI)
def test_width_id_absence_parsed_ownership_and_selective_detach(index):
    mode_objects = modes("wire")
    assert api.getAbstractionDefPortWireModeWidthID(get_handle(mode_objects[index])) is None
    for mode in mode_objects:
        mode.width = type(mode).Width(value="WIDTH + 1", all_bits=True)
    port = port_with_modes("wire", mode_objects)
    parsed = XmlDocument.parser().from_string(XmlDocument.serializer().render(port), AbstractionDefinition.Ports.Port)
    wire = parsed.wire_or_transactional
    parsed_modes = [wire.on_initiator, wire.on_target, wire.on_system[0]]
    selected = parsed_modes[index]
    mode_handle = get_handle(selected)
    expected = get_handle(selected.width)
    assert api.getAbstractionDefPortWireModeWidthID(mode_handle) == expected
    assert api.getAbstractionDefPortWireModeWidthID(mode_handle) == expected
    owner = get_parent_info(expected)
    assert (owner.parent_handle, owner.path, owner.container) == (mode_handle, ("width",), "single")
    assert detach_child_by_handle(expected)
    assert not detach_child_by_handle(expected)
    assert selected.width is None
    assert resolve_handle(expected) is None
    assert all(other.width is not None for other in parsed_modes if other is not selected)
    assert_round_trip(parsed)


@pytest.mark.parametrize("style,attr", [("wire", "width"), ("transactional", "bus_width")])
@pytest.mark.parametrize("index", range(3), ids=LOCI)
def test_expression_setter_preserves_attributes_identity_and_siblings(style, attr, index):
    mode_objects = modes(style)
    selected = mode_objects[index]
    model = type(selected).Width if style == "wire" else UnsignedPositiveIntExpression
    kwargs = {"all_bits": True} if style == "wire" else {}
    selected_child = model(
        value="8", minimum=1, maximum=1024, other_attributes={"{urn:custom}tag": "kept"}, **kwargs
    )
    setattr(selected, attr, selected_child)
    original = get_handle(selected_child)
    setter = (
        api.setAbstractionDefPortWireModeWidth
        if style == "wire"
        else api.setAbstractionDefPortTransactionalModeBusWidth
    )
    for expression in ["WIDTH + 1", "  OTHER_WIDTH  "]:
        assert setter(get_handle(selected), expression)
        child = getattr(selected, attr)
        assert child is selected_child
        assert get_handle(child) == original
        assert child.value == expression
        assert (child.minimum, child.maximum, child.other_attributes) == (1, 1024, {"{urn:custom}tag": "kept"})
        if style == "wire":
            assert child.all_bits is True
        assert all(getattr(other, attr) is None for other in mode_objects if other is not selected)
        assert_round_trip(port_with_modes(style, mode_objects))


@pytest.mark.parametrize("index", range(3), ids=LOCI)
def test_protocol_setter_preserves_children_payload_custom_and_siblings(index):
    mode_objects = modes("transactional")
    selected = mode_objects[index]
    payload = Payload(
        type_value=PayloadType.SPECIFIC,
        name="data",
        extension=Payload.Extension(value="extension", mandatory=True),
    )
    protocol_type = Protocol.ProtocolType(value=ProtocolTypeType.CUSTOM, custom="retained_protocol")
    protocol = Protocol(protocol_type=protocol_type, payload=payload)
    selected.protocol = protocol
    handles = [get_handle(child) for child in [protocol, protocol_type, payload, payload.extension]]
    for value in ["tlm", "custom", "custom"]:
        assert api.setAbstractionDefPortTransactionalModeProtocol(get_handle(selected), value)
        assert selected.protocol is protocol
        assert protocol.protocol_type is protocol_type
        assert protocol.payload is payload
        assert protocol_type.value is ProtocolTypeType(value)
        assert protocol_type.custom == "retained_protocol"
        assert [get_handle(child) for child in [protocol, protocol_type, payload, payload.extension]] == handles
        assert all(other.protocol is None for other in mode_objects if other is not selected)
        assert_round_trip(port_with_modes("transactional", mode_objects))

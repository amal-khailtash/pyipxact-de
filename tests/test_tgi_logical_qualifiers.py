"""Logical style qualifiers use generated optional models and owned handles."""

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
from org.accellera.ipxact.v1685_2022 import AbstractionDefinition, IsResetLevel, QualifierType


@pytest.fixture(autouse=True)
def clean_registry():
    registry.clear()
    yield
    registry.clear()


def operations(style):
    label = style.title()
    return (
        getattr(api, f"getAbstractionDefPort{label}QualifierID"),
        getattr(api, f"setAbstractionDefPort{label}Qualifier"),
        getattr(api, f"removeAbstractionDefPort{label}Qualifier"),
    )


def create(style):
    root = top_element.createAbstractionDef(("v", "l", "a", "1"), ("v", "l", "b", "1"), "p", style)
    return api.getAbstractionDefPortIDs(root)[0]


def round_trip(port):
    return XmlDocument.parser().from_string(XmlDocument.serializer().render(port), AbstractionDefinition.Ports.Port)


def populated_qualifier():
    return QualifierType(
        is_address=True,
        is_data=False,
        is_reset=QualifierType.IsReset(value=True, level=IsResetLevel.LOW),
        is_user=QualifierType.IsUser(value=True, user="retained"),
        id="qualifier_id",
    )


@pytest.mark.parametrize("style", ["wire", "transactional"])
def test_absent_creation_repeated_identity_and_removal(style):
    port_handle = create(style)
    port = resolve_handle(port_handle)
    getter, setter, remover = operations(style)
    assert getter(port_handle) is None
    assert not remover(port_handle)
    keyword = "abstractionDefPortID" if style == "wire" else "portID"
    assert setter(**{keyword: port_handle})
    qualifier = port.wire_or_transactional.qualifier
    assert qualifier == QualifierType()
    child_handle = getter(port_handle)
    assert setter(**{keyword: port_handle})
    assert getter(port_handle) == child_handle
    assert resolve_handle(child_handle) is qualifier
    owner = get_parent_info(child_handle)
    assert (owner.parent_handle, owner.path, owner.container) == (
        get_handle(port.wire_or_transactional), ("qualifier",), "single"
    )
    assert round_trip(port) == port
    assert remover(port_handle)
    assert resolve_handle(child_handle) is None
    assert getter(port_handle) is None
    assert not remover(port_handle)
    assert setter(port_handle)
    assert getter(port_handle) != child_handle


@pytest.mark.parametrize("style", ["wire", "transactional"])
@pytest.mark.parametrize("parsed", [False, True], ids=["created", "parsed"])
def test_existing_content_identity_ownership_and_optional_removal(style, parsed):
    port_handle = create(style)
    mode_handles = [
        api.addAbstractionDefPortMode(port_handle, locus) for locus in ["onInitiator", "onTarget", "onSystem"]
    ]
    api.setOnSystemGroup(mode_handles[2], "system")
    packet_handle = api.addAbstractionDefPortPacket(port_handle, "packet", "field", "8")
    port = resolve_handle(port_handle)
    port.wire_or_transactional.qualifier = populated_qualifier()
    if parsed:
        port = round_trip(port)
        port_handle = get_handle(port)
    container = port.wire_or_transactional
    qualifier = container.qualifier
    packet = port.packets.packet[0]
    modes = [container.on_initiator, container.on_target, container.on_system[0]]
    identities = [get_handle(obj) for obj in [packet, *modes]]
    if not parsed:
        assert identities == [packet_handle, *mode_handles]
    getter, setter, remover = operations(style)
    qualifier_handle = get_handle(qualifier)
    assert getter(port_handle) == qualifier_handle
    assert setter(port_handle)
    assert setter(port_handle)
    assert container.qualifier is qualifier
    assert getter(port_handle) == qualifier_handle
    assert qualifier == populated_qualifier()
    assert round_trip(port) == port
    assert remover(port_handle)
    assert not remover(port_handle)
    assert container.qualifier is None
    assert resolve_handle(qualifier_handle) is None
    assert [get_handle(obj) for obj in [port.packets.packet[0], container.on_initiator,
                                     container.on_target, container.on_system[0]]] == identities
    assert round_trip(port) == port


@pytest.mark.parametrize("style", ["wire", "transactional"])
def test_wrong_style_is_atomic(style):
    getter, setter, remover = operations(style)
    other_handle = create("transactional" if style == "wire" else "wire")
    other = resolve_handle(other_handle)
    other.wire_or_transactional.qualifier = populated_qualifier()
    before = XmlDocument.serializer().render(other)
    assert getter(other_handle) is None
    assert not remover(other_handle)
    with pytest.raises(TgiError) as error:
        setter(other_handle)
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert XmlDocument.serializer().render(other) == before


@pytest.mark.parametrize("style", ["wire", "transactional"])
def test_invalid_handles_have_operation_faults(style):
    getter, setter, remover = operations(style)
    port = resolve_handle(create(style))
    for handle in ["missing", get_handle(object()), get_handle(port.wire_or_transactional),
                   get_handle(QualifierType())]:
        for operation in [getter, setter]:
            with pytest.raises(TgiError) as error:
                operation(handle)
            assert error.value.fault_code == TgiFaultCode.INVALID_ID
        assert not remover(handle)

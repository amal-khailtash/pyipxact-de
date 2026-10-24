"""Logical mode traversal and removal respect generated style and ownership."""

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


@pytest.fixture(params=["wire", "transactional"])
def port(request):
    registry.clear()
    root = top_element.createAbstractionDef(("v", "l", "a", "1"), ("v", "l", "b", "1"), "data", request.param)
    yield api.getAbstractionDefPortIDs(root)[0], request.param.title()
    registry.clear()


def populate(handle):
    api.addAbstractionDefPortMode(handle, "onInitiator")
    api.addAbstractionDefPortMode(handle, "onTarget")
    for group in ["a", "b"]:
        mode = api.addAbstractionDefPortMode(handle, "onSystem")
        resolve_handle(mode).group = group


@pytest.mark.parametrize("parsed", [False, True])
@pytest.mark.parametrize("generic", [False, True])
def test_ordered_mode_traversal_and_removal(port, parsed, generic):
    handle, style = port
    populate(handle)
    if parsed:
        obj = resolve_handle(handle)
        loaded = XmlDocument.parser().from_string(
            XmlDocument.serializer().render(obj), AbstractionDefinition.Ports.Port)
        assert loaded == obj
        handle = get_handle(loaded)
    prefix = "getAbstractionDefPort" + style
    initiator = getattr(api, prefix + "OnInitiatorID")(handle)
    target = getattr(api, prefix + "OnTargetID")(handle)
    systems = getattr(api, prefix + "OnSystemIDs")(handle)
    from amal.eda.accellera.ipxact.v1685_2022.tgi.core import get_parent_info

    assert all(get_parent_info(mode) is not None for mode in systems)
    assert systems == api.getAbstractionDefPortOnSystemIDs(handle)
    assert [resolve_handle(i).group for i in systems] == ["a", "b"]
    other = "Wire" if style == "Transactional" else "Transactional"
    assert not getattr(api, "removeAbstractionDefPort" + other + "OnSystem")(systems[0])
    remover = api.removeAbstractionDefPortMode if generic else getattr(
        api, "removeAbstractionDefPort" + style + "OnSystem")
    assert remover(systems[0])
    assert not remover(systems[0])
    assert resolve_handle(systems[0]) is None
    assert api.getAbstractionDefPortOnSystemIDs(handle) == [systems[1]]
    for locus, mode in [("Initiator", initiator), ("Target", target)]:
        if generic:
            assert api.removeAbstractionDefPortMode(mode)
        else:
            remove = getattr(api, "removeAbstractionDefPort" + style + "On" + locus)
            assert remove(handle)
            assert not remove(handle)
        assert resolve_handle(mode) is None
        assert getattr(api, prefix + "On" + locus + "ID")(handle) is None


@pytest.mark.parametrize("locus", ["Initiator", "Target"])
def test_port_removal_without_child_traversal(port, locus):
    handle, style = port
    populate(handle)
    obj = resolve_handle(handle)
    loaded = XmlDocument.parser().from_string(
        XmlDocument.serializer().render(obj), AbstractionDefinition.Ports.Port)
    handle = get_handle(loaded)
    other = "Wire" if style == "Transactional" else "Transactional"
    assert not getattr(api, "removeAbstractionDefPort" + other + "On" + locus)(handle)
    assert getattr(api, "removeAbstractionDefPort" + style + "On" + locus)(handle)
    assert getattr(loaded.wire_or_transactional, "on_" + locus.lower()) is None


def test_mode_removers_reject_other_registered_children(port):
    handle, _ = port
    packet = api.addAbstractionDefPortPacket(handle, "packet", "field", "8")
    for remove in [api.removeAbstractionDefPortMode, api.removeAbstractionDefPortWireOnSystem,
                   api.removeAbstractionDefPortTransactionalOnSystem]:
        assert not remove(packet)
    assert api.getAbstractionDefPortPacketIDs(handle) == [packet]
    assert api.getAbstractionDefPortOnSystemIDs(handle) == []


@pytest.mark.parametrize("remove", [api.removeAbstractionDefPortMode, api.removeAbstractionDefPortWireOnSystem,
                                   api.removeAbstractionDefPortTransactionalOnSystem,
                                   api.removeAbstractionDefPortWireOnInitiator,
                                   api.removeAbstractionDefPortWireOnTarget,
                                   api.removeAbstractionDefPortTransactionalOnInitiator,
                                   api.removeAbstractionDefPortTransactionalOnTarget])
def test_invalid_removal(remove):
    assert not remove("missing")
    assert not remove(get_handle(object()))


def test_invalid_system_traversal():
    with pytest.raises(TgiError) as error:
        api.getAbstractionDefPortOnSystemIDs("missing")
    assert error.value.fault_code == TgiFaultCode.INVALID_ID

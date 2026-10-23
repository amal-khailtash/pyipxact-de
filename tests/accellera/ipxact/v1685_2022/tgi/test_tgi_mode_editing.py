"""Mode setters preserve identity and complete logical system groups."""

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


@pytest.fixture(params=["Wire", "Transactional"])
def port(request):
    registry.clear()
    root = top_element.createAbstractionDef(("v", "l", "a", "1"), ("v", "l", "b", "1"), "p", request.param.lower())
    yield api.getAbstractionDefPortIDs(root)[0], request.param
    registry.clear()


@pytest.mark.parametrize("parsed", [False, True])
def test_setters_identity_groups_and_roundtrip(port, parsed):
    handle, style = port
    for locus in ["Initiator", "Target"]:
        setter = getattr(api, "setAbstractionDefPort" + style + "On" + locus)
        assert setter(handle)
        mode = api.setAbstractionDefPortMode(handle, "on" + locus)
        assert setter(handle)
        assert api.setAbstractionDefPortMode(handle, "on" + locus) == mode
        # Creation must register ownership without needing a getter.
        assert api.removeAbstractionDefPortMode(mode)
        assert setter(handle)
    first = api.setAbstractionDefPortMode(handle, "onSystem")
    second = api.setAbstractionDefPortMode(handle, "onSystem")
    assert first != second
    assert api.setOnSystemGroup(first, "control")
    assert api.setOnSystemGroup(second, "data")
    assert api.setOnSystemGroup(first, "changed")
    assert api.getOnSystemGroup(first) == "changed"
    if parsed:
        obj = resolve_handle(handle)
        loaded = XmlDocument.parser().from_string(
            XmlDocument.serializer().render(obj), AbstractionDefinition.Ports.Port)
        assert loaded == obj
        handle = get_handle(loaded)
    systems = api.getAbstractionDefPortOnSystemIDs(handle)
    assert [api.getOnSystemGroup(i) for i in systems] == ["changed", "data"]
    assert api.setOnSystemGroup(systems[0], "updated")
    assert api.getAbstractionDefPortOnSystemIDs(handle) == systems
    assert api.getOnSystemGroup(systems[0]) == "updated"


@pytest.mark.parametrize("invalid", [None, "", "  ", 2])
def test_invalid_group_is_atomic(port, invalid):
    handle, _ = port
    mode = api.setAbstractionDefPortMode(handle, "onSystem")
    api.setOnSystemGroup(mode, "original")
    with pytest.raises(TgiError) as error:
        api.setOnSystemGroup(mode, invalid)
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert api.getOnSystemGroup(mode) == "original"


@pytest.mark.parametrize("invalid", [None, "", "initiator", "target", "system", 2])
def test_invalid_mode_is_atomic(port, invalid):
    handle, _ = port
    before = XmlDocument.serializer().render(resolve_handle(handle))
    with pytest.raises(TgiError) as error:
        api.setAbstractionDefPortMode(handle, invalid)
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert XmlDocument.serializer().render(resolve_handle(handle)) == before


@pytest.mark.parametrize("locus", ["Initiator", "Target"])
def test_wrong_style_setter_is_atomic(port, locus):
    handle, style = port
    other = "Wire" if style == "Transactional" else "Transactional"
    with pytest.raises(TgiError) as error:
        getattr(api, "setAbstractionDefPort" + other + "On" + locus)(handle)
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert getattr(resolve_handle(handle).wire_or_transactional, "on_" + locus.lower()) is None


@pytest.mark.parametrize("operation,args", [
    (api.setAbstractionDefPortMode, ("onInitiator",)), (api.setOnSystemGroup, ("group",)),
    (api.getOnSystemGroup, ()), (api.setAbstractionDefPortWireOnInitiator, ()),
    (api.setAbstractionDefPortWireOnTarget, ()), (api.setAbstractionDefPortTransactionalOnInitiator, ()),
    (api.setAbstractionDefPortTransactionalOnTarget, ()),
])
def test_invalid_handle(operation, args):
    for handle in ["missing", get_handle(object())]:
        with pytest.raises(TgiError) as error:
            operation(handle, *args)
        assert error.value.fault_code == TgiFaultCode.INVALID_ID

"""Logical port modes use generated style choices and standard mode names."""

import pytest

from amal.eda.ipxact_de.tgi.ipxact.v1685_2022 import abstraction_definition as api
from amal.eda.ipxact_de.tgi.ipxact.v1685_2022 import top_element
from amal.eda.ipxact_de.tgi.ipxact.v1685_2022.core import TgiError, TgiFaultCode, registry, resolve_handle
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import AbstractionDefinition


@pytest.fixture(params=["wire", "transactional"])
def port(request):
    """Provide a logical port for each style."""
    registry.clear()
    root = top_element.createAbstractionDef(("v", "l", "a", "1"), ("v", "l", "b", "1"), "p", request.param)
    yield root, api.getAbstractionDefPortIDs(root)[0], request.param
    registry.clear()


def test_modes_and_grouped_systems(port):
    """Creation and six getters preserve identity, order and XML contents."""
    root, handle, style = port
    prefix = "getAbstractionDefPort" + style.title()
    initiator = api.addAbstractionDefPortMode(handle, "onInitiator")
    target = api.addAbstractionDefPortMode(handle, "onTarget")
    assert api.addAbstractionDefPortMode(handle, "onInitiator") == initiator
    assert getattr(api, prefix + "OnInitiatorID")(handle) == initiator
    assert getattr(api, prefix + "OnTargetID")(handle) == target
    system = api.addAbstractionDefPortMode(handle, "onSystem")
    resolve_handle(system).group = "default"
    add = getattr(api, "addAbstractionDefPort" + style.title() + "OnSystem")
    grouped = add(handle, "control")
    assert getattr(api, prefix + "OnSystemIDs")(handle) == [system, grouped]
    other = "Wire" if style == "transactional" else "Transactional"
    assert getattr(api, "getAbstractionDefPort" + other + "OnInitiatorID")(handle) is None
    assert getattr(api, "getAbstractionDefPort" + other + "OnTargetID")(handle) is None
    assert getattr(api, "getAbstractionDefPort" + other + "OnSystemIDs")(handle) == []
    obj = resolve_handle(root)
    assert XmlDocument.parser().from_string(XmlDocument.serializer().render(obj), AbstractionDefinition) == obj


@pytest.mark.parametrize("mode", ["initiator", "target", "bad", None])
def test_invalid_modes_are_atomic(port, mode):
    """Nonstandard mode names fail without changing the style."""
    _, handle, _ = port
    with pytest.raises(TgiError) as error:
        api.addAbstractionDefPortMode(handle, mode)
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert resolve_handle(handle).wire_or_transactional.on_initiator is None


@pytest.mark.parametrize("group", ["", None, 1])
def test_invalid_system_groups_are_atomic(port, group):
    """Group validation precedes append."""
    _, handle, style = port
    add = getattr(api, "addAbstractionDefPort" + style.title() + "OnSystem")
    with pytest.raises(TgiError) as error:
        add(handle, group)
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert resolve_handle(handle).wire_or_transactional.on_system == []


def test_invalid_handle():
    """Mode creation rejects missing port handles."""
    with pytest.raises(TgiError) as error:
        api.addAbstractionDefPortMode("missing", "onInitiator")
    assert error.value.fault_code == TgiFaultCode.INVALID_ID

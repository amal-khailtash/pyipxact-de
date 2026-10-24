"""Mode properties edit only the supplied generated mode and retain identity."""

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

CASES = [
    ("transactional", "BusWidth", "bus_width", ["8", "WIDTH + 1"]),
    ("transactional", "Kind", "kind", ["tlm_port", "tlm_socket", "simple_socket", "multi_socket", "custom"]),
    ("transactional", "Presence", "presence", ["required", "optional", "illegal"]),
    ("transactional", "Protocol", "protocol", ["tlm", "custom"]),
    ("wire", "Width", "width", ["8", "WIDTH + 1"]),
    ("wire", "Direction", "direction", ["in", "out", "inout"]),
    ("wire", "Presence", "presence", ["required", "optional", "illegal"]),
]


@pytest.fixture(autouse=True)
def clean_registry():
    registry.clear()
    yield
    registry.clear()


def create(style):
    root = top_element.createAbstractionDef(("v", "l", "a", "1"), ("v", "l", "b", "1"), "p", style)
    return api.getAbstractionDefPortIDs(root)[0]


@pytest.mark.parametrize("style,suffix,attr,values", CASES)
@pytest.mark.parametrize("locus", ["onInitiator", "onTarget", "onSystem"])
def test_property_identity_selectivity_and_xml(style, suffix, attr, values, locus):
    port = create(style)
    modes = [api.addAbstractionDefPortMode(port, name) for name in ["onInitiator", "onTarget", "onSystem"]]
    api.setOnSystemGroup(modes[2], "system")
    mode = modes[["onInitiator", "onTarget", "onSystem"].index(locus)]
    setter = getattr(api, "setAbstractionDefPort" + style.title() + "Mode" + suffix)
    first = None
    for value in values:
        assert setter(mode, value)
        child = getattr(resolve_handle(mode), attr)
        if attr == "direction":
            assert child.value == value
        else:
            if first is None:
                first = get_handle(child)
            assert get_handle(child) == first
            actual = child.protocol_type.value.value if attr == "protocol" else child.value
            assert getattr(actual, "value", actual) == value
        assert all(getattr(resolve_handle(other), attr) is None for other in modes if other != mode)
        obj = resolve_handle(port)
        assert XmlDocument.parser().from_string(XmlDocument.serializer().render(obj),
                                               AbstractionDefinition.Ports.Port) == obj


@pytest.mark.parametrize("style,suffix,attr,values", CASES)
@pytest.mark.parametrize("invalid", [None, "", "  ", 8])
def test_invalid_property_is_atomic(style, suffix, attr, values, invalid):
    port = create(style)
    mode = api.addAbstractionDefPortMode(port, "onInitiator")
    setter = getattr(api, "setAbstractionDefPort" + style.title() + "Mode" + suffix)
    setter(mode, values[0])
    before = XmlDocument.serializer().render(resolve_handle(port))
    with pytest.raises(TgiError) as error:
        setter(mode, invalid)
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert XmlDocument.serializer().render(resolve_handle(port)) == before


@pytest.mark.parametrize("style,suffix,attr,values", [case for case in CASES if case[2] not in ("width", "bus_width")])
def test_unknown_enum_is_atomic(style, suffix, attr, values):
    port = create(style)
    mode = api.addAbstractionDefPortMode(port, "onTarget")
    with pytest.raises(TgiError) as error:
        getattr(api, "setAbstractionDefPort" + style.title() + "Mode" + suffix)(mode, "unknown")
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert getattr(resolve_handle(mode), attr) is None


@pytest.mark.parametrize("style,suffix,attr,values", CASES)
def test_rejects_port_and_wrong_style_handles(style, suffix, attr, values):
    port = create(style)
    other_root = top_element.createAbstractionDef(("v", "l", "other", "1"), ("v", "l", "b", "1"),
                                                 "p", "wire" if style == "transactional" else "transactional")
    other = api.addAbstractionDefPortMode(api.getAbstractionDefPortIDs(other_root)[0], "onInitiator")
    setter = getattr(api, "setAbstractionDefPort" + style.title() + "Mode" + suffix)
    for handle in [port, other, "missing"]:
        with pytest.raises(TgiError) as error:
            setter(handle, values[0])
        assert error.value.fault_code == TgiFaultCode.INVALID_ID

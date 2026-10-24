"""Transactional property getters follow the supplied generated mode handle."""

import pytest

from amal.eda.accellera.ipxact.v1685_2022.tgi import abstraction_definition as api
from amal.eda.accellera.ipxact.v1685_2022.tgi import top_element
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import (
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
    Kind,
    KindType,
    OnInitiatorInitiative,
    OnSystemInitiative,
    OnTargetInitiative,
    Presence,
    PresenceType,
    Protocol,
    ProtocolTypeType,
    UnsignedPositiveIntExpression,
    Wire,
)

GETTERS = ["BusWidthExpression", "BusWidthID", "Initiative", "KindID", "Presence", "ProtocolID"]
LOCI = ["onInitiator", "onTarget", "onSystem"]
INITIATIVES = [OnInitiatorInitiative.REQUIRES, OnTargetInitiative.PROVIDES, OnSystemInitiative.BOTH]


@pytest.fixture(autouse=True)
def clean_registry():
    registry.clear()
    yield
    registry.clear()


def getter(suffix):
    return getattr(api, "getAbstractionDefPortTransactionalMode" + suffix)


def populated_modes():
    tr = AbstractionDefinition.Ports.Port.Transactional
    return [
        mode_type(
            **({"group": "system"} if mode_type is tr.OnSystem else {}),
            bus_width=UnsignedPositiveIntExpression(value=expression, minimum=1, maximum=64),
            initiative=INITIATIVES[index],
            presence=Presence(value=presence),
            kind=Kind(value=KindType.CUSTOM, custom=f"kind{index}"),
            protocol=Protocol(
                protocol_type=Protocol.ProtocolType(value=ProtocolTypeType.CUSTOM, custom=f"protocol{index}")
            ),
        )
        for index, (mode_type, expression, presence) in enumerate(
            zip(
                [tr.OnInitiator, tr.OnTarget, tr.OnSystem],
                ["WIDTH + 1", "16", "  SYS_WIDTH  "],
                [PresenceType.REQUIRED, PresenceType.ILLEGAL, PresenceType.OPTIONAL],
                strict=True,
            )
        )
    ]


@pytest.mark.parametrize("index", range(3), ids=LOCI)
def test_scalar_getters_select_mode_and_preserve_expression(index):
    modes = populated_modes()
    handle = get_handle(modes[index])
    assert getter("BusWidthExpression")(handle) == ["WIDTH + 1", "16", "  SYS_WIDTH  "][index]
    assert getter("Initiative")(handle) == ["requires", "provides", "both"][index]
    assert getter("Presence")(handle) == ["required", "illegal", "optional"][index]
    assert modes == populated_modes()


@pytest.mark.parametrize("suffix,attr", [("BusWidthID", "bus_width"), ("KindID", "kind"), ("ProtocolID", "protocol")])
@pytest.mark.parametrize("index", range(3), ids=LOCI)
def test_id_getters_register_parsed_ownership_and_preserve_identity(suffix, attr, index):
    modes = populated_modes()
    port = AbstractionDefinition.Ports.Port(
        logical_name="p",
        wire_or_transactional=AbstractionDefinition.Ports.Port.Transactional(
            on_initiator=modes[0], on_target=modes[1], on_system=[modes[2]]
        ),
    )
    parsed = XmlDocument.parser().from_string(XmlDocument.serializer().render(port), AbstractionDefinition.Ports.Port)
    transactional = parsed.wire_or_transactional
    parsed_modes = [transactional.on_initiator, transactional.on_target, transactional.on_system[0]]
    mode = parsed_modes[index]
    mode_handle = get_handle(mode)
    child = getattr(mode, attr)
    existing_handle = get_handle(child)
    before = XmlDocument.serializer().render(parsed)
    assert getter(suffix)(mode_handle) == existing_handle
    assert getter(suffix)(mode_handle) == existing_handle
    assert resolve_handle(existing_handle) is child
    parent = get_parent_info(existing_handle)
    assert (parent.parent_handle, parent.path, parent.container) == (mode_handle, (attr,), "single")
    assert XmlDocument.serializer().render(parsed) == before
    assert detach_child_by_handle(existing_handle)
    assert getattr(mode, attr) is None
    assert resolve_handle(existing_handle) is None
    assert not detach_child_by_handle(existing_handle)
    assert getter(suffix)(mode_handle) is None
    assert all(getattr(other, attr) is not None for other in parsed_modes if other is not mode)


@pytest.mark.parametrize("suffix", GETTERS)
@pytest.mark.parametrize("index", range(3), ids=LOCI)
def test_absent_property_returns_none(suffix, index):
    tr = AbstractionDefinition.Ports.Port.Transactional
    mode = [tr.OnInitiator(), tr.OnTarget(), tr.OnSystem(group="system")][index]
    assert getter(suffix)(get_handle(mode)) is None


@pytest.mark.parametrize("suffix", GETTERS)
def test_rejects_missing_port_style_container_wire_mode_and_child_handles(suffix):
    root = top_element.createAbstractionDef(("v", "l", "a", "1"), ("v", "l", "b", "1"), "p", "transactional")
    port_handle = api.getAbstractionDefPortIDs(root)[0]
    port = resolve_handle(port_handle)
    invalid_handles = [
        "missing",
        get_handle(object()),
        root,
        port_handle,
        get_handle(port.wire_or_transactional),
        get_handle(Wire.OnInitiator()),
        get_handle(UnsignedPositiveIntExpression(value="8")),
    ]
    for handle in invalid_handles:
        with pytest.raises(TgiError) as error:
            getter(suffix)(handle)
        assert error.value.fault_code == TgiFaultCode.INVALID_ID

"""Transactional mode removers target one standard mode handle and property."""

import pytest

from amal.eda.accellera.ipxact.v1685_2022.tgi import abstraction_definition as api
from amal.eda.accellera.ipxact.v1685_2022.tgi import top_element
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import (
    get_handle,
    registry,
    resolve_handle,
)
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import AbstractionDefinition
from org.accellera.ipxact.v1685_2022.on_initiator_initiative import OnInitiatorInitiative
from org.accellera.ipxact.v1685_2022.on_system_initiative import OnSystemInitiative
from org.accellera.ipxact.v1685_2022.on_target_initiative import OnTargetInitiative

LOCUS_NAMES = ("onInitiator", "onTarget", "onSystem")
PROPERTY_CASES = (
    ("BusWidth", "bus_width", "WIDTH + 1"),
    ("Initiative", "initiative", None),
    ("Kind", "kind", "tlm_port"),
    ("Presence", "presence", "required"),
    ("Protocol", "protocol", "tlm"),
)


@pytest.fixture(autouse=True)
def clean_registry():
    registry.clear()
    yield
    registry.clear()


def _make_port():
    root = top_element.createAbstractionDef(("v", "l", "a", "1"), ("v", "l", "b", "1"), "p", "transactional")
    port_handle = api.getAbstractionDefPortIDs(root)[0]
    mode_handles = [api.addAbstractionDefPortMode(port_handle, name) for name in LOCUS_NAMES]
    api.setOnSystemGroup(mode_handles[2], "system")
    initiative_types = (OnInitiatorInitiative, OnTargetInitiative, OnSystemInitiative)
    for index, mode_handle in enumerate(mode_handles):
        for suffix, _attr, value in PROPERTY_CASES:
            if suffix == "Initiative":
                resolve_handle(mode_handle).initiative = initiative_types[index].REQUIRES
            else:
                setter = getattr(api, "setAbstractionDefPortTransactionalMode" + suffix)
                assert setter(mode_handle, value)
    return port_handle, mode_handles


def _parsed_modes(port_handle):
    port = resolve_handle(port_handle)
    loaded = XmlDocument.parser().from_string(
        XmlDocument.serializer().render(port), AbstractionDefinition.Ports.Port
    )
    loaded_handle = get_handle(loaded)
    transactional = loaded.wire_or_transactional
    mode_handles = [
        get_handle(transactional.on_initiator),
        get_handle(transactional.on_target),
        get_handle(transactional.on_system[0]),
    ]
    return loaded_handle, mode_handles, loaded


@pytest.mark.parametrize("parsed", [False, True])
@pytest.mark.parametrize("locus_index", range(3), ids=LOCUS_NAMES)
@pytest.mark.parametrize("suffix,attr,value", PROPERTY_CASES)
def test_remover_clears_only_supplied_locus_and_invalidates_child_handle(parsed, locus_index, suffix, attr, value):
    port_handle, mode_handles = _make_port()
    if parsed:
        port_handle, mode_handles, port = _parsed_modes(port_handle)
    else:
        port = resolve_handle(port_handle)

    modes = [resolve_handle(mode_handle) for mode_handle in mode_handles]
    selected = modes[locus_index]
    child = getattr(selected, attr)
    child_handle = get_handle(child) if child is not None and suffix != "Initiative" else None
    assert all(getattr(mode, attr) is not None for mode in modes)

    remover = getattr(api, "removeAbstractionDefPortTransactionalMode" + suffix)
    assert remover(mode_handles[locus_index])
    assert getattr(selected, attr) is None
    assert all(getattr(mode, attr) is not None for index, mode in enumerate(modes) if index != locus_index)
    if child_handle is not None:
        assert resolve_handle(child_handle) is None

    round_tripped = XmlDocument.parser().from_string(
        XmlDocument.serializer().render(port), AbstractionDefinition.Ports.Port
    )
    assert round_tripped == port


@pytest.mark.parametrize("suffix,attr,value", PROPERTY_CASES)
@pytest.mark.parametrize("locus_index", range(3), ids=LOCUS_NAMES)
def test_absent_property_and_wrong_handles_return_false(suffix, attr, value, locus_index):
    root = top_element.createAbstractionDef(("v", "l", "empty", "1"), ("v", "l", "b", "1"), "p", "transactional")
    port_handle = api.getAbstractionDefPortIDs(root)[0]
    mode_handles = [api.addAbstractionDefPortMode(port_handle, name) for name in LOCUS_NAMES]
    api.setOnSystemGroup(mode_handles[2], "system")
    remover = getattr(api, "removeAbstractionDefPortTransactionalMode" + suffix)
    assert not remover(mode_handles[locus_index])

    wire_root = top_element.createAbstractionDef(("v", "l", "wire", "1"), ("v", "l", "b", "1"), "p", "wire")
    wire_port_handle = api.getAbstractionDefPortIDs(wire_root)[0]
    wire_mode = api.addAbstractionDefPortMode(wire_port_handle, "onInitiator")
    for wrong_handle in ("missing", get_handle(object()), port_handle, wire_mode):
        assert not remover(wrong_handle)

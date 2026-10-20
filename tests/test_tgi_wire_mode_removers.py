"""Wire mode removers mutate only the supplied generated mode locus."""

import pytest

from amal.eda.ipxact_de.tgi.ipxact.v1685_2022 import abstraction_definition as api
from amal.eda.ipxact_de.tgi.ipxact.v1685_2022 import top_element
from amal.eda.ipxact_de.tgi.ipxact.v1685_2022.core import get_handle, registry, resolve_handle
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import AbstractionDefinition
from org.accellera.ipxact.v1685_2022.abstraction_def_port_constraints_type import (
    AbstractionDefPortConstraintsType,
)

LOCUS_NAMES = ("onInitiator", "onTarget", "onSystem")
PROPERTY_CASES = (
    ("Direction", "direction", "out"),
    ("MirroredModeConstraints", "mirrored_mode_constraints", None),
    ("ModeConstraints", "mode_constraints", None),
    ("Presence", "presence", "required"),
    ("Width", "width", "WIDTH + 1"),
)


@pytest.fixture(autouse=True)
def clean_registry():
    registry.clear()
    yield
    registry.clear()


def _make_wire_port(populate=True):
    root = top_element.createAbstractionDef(
        ("v", "l", "abstraction", "1"), ("v", "l", "bus", "1"), "data", "wire"
    )
    port_handle = api.getAbstractionDefPortIDs(root)[0]
    mode_handles = [api.addAbstractionDefPortMode(port_handle, name) for name in LOCUS_NAMES]
    api.setOnSystemGroup(mode_handles[2], "system")

    if populate:
        for mode_handle in mode_handles:
            assert api.setAbstractionDefPortWireModeDirection(mode_handle, "out")
            assert api.setAbstractionDefPortWireModePresence(mode_handle, "required")
            assert api.setAbstractionDefPortWireModeWidth(mode_handle, "WIDTH + 1")
            mode = resolve_handle(mode_handle)
            mode.mode_constraints = AbstractionDefPortConstraintsType()
            mode.mirrored_mode_constraints = AbstractionDefPortConstraintsType()
    return root, mode_handles


def _parsed_root_and_modes(root):
    parsed = XmlDocument.parser().from_string(
        XmlDocument.serializer().render(resolve_handle(root)), AbstractionDefinition
    )
    wire = parsed.ports.port[0].wire_or_transactional
    mode_handles = [get_handle(wire.on_initiator), get_handle(wire.on_target), get_handle(wire.on_system[0])]
    return parsed, mode_handles


@pytest.mark.parametrize("parsed", [False, True])
@pytest.mark.parametrize("locus_index", range(3), ids=LOCUS_NAMES)
@pytest.mark.parametrize("suffix,attr,value", PROPERTY_CASES)
def test_remover_clears_only_supplied_locus_and_invalidates_child(parsed, locus_index, suffix, attr, value):
    root_handle, mode_handles = _make_wire_port()
    if parsed:
        root, mode_handles = _parsed_root_and_modes(root_handle)
    else:
        root = resolve_handle(root_handle)
    modes = [resolve_handle(mode_handle) for mode_handle in mode_handles]
    selected = modes[locus_index]
    child = getattr(selected, attr)
    child_handle = get_handle(child) if child is not None and suffix != "Direction" else None
    sibling_children = [getattr(mode, attr) for index, mode in enumerate(modes) if index != locus_index]
    assert all(getattr(mode, attr) is not None for mode in modes)
    if attr == "width":
        assert all(mode.width.value == "WIDTH + 1" for mode in modes)

    remover = getattr(api, "removeAbstractionDefPortWireMode" + suffix)
    assert remover(mode_handles[locus_index])
    assert getattr(selected, attr) is None
    assert not remover(mode_handles[locus_index])
    remaining_modes = [mode for index, mode in enumerate(modes) if index != locus_index]
    assert all(getattr(mode, attr) is child for mode, child in zip(remaining_modes, sibling_children, strict=True))
    if child_handle is not None:
        assert resolve_handle(child_handle) is None
        assert all(resolve_handle(get_handle(child)) is child for child in sibling_children)

    round_tripped = XmlDocument.parser().from_string(
        XmlDocument.serializer().render(root), AbstractionDefinition
    )
    assert round_tripped == root


@pytest.mark.parametrize("suffix,attr,value", PROPERTY_CASES)
@pytest.mark.parametrize("locus_index", range(3), ids=LOCUS_NAMES)
def test_absent_property_and_wrong_handles_return_false(suffix, attr, value, locus_index):
    root_handle, mode_handles = _make_wire_port(populate=False)
    remover = getattr(api, "removeAbstractionDefPortWireMode" + suffix)
    assert not remover(mode_handles[locus_index])

    transactional_root = top_element.createAbstractionDef(
        ("v", "l", "transactional", "1"), ("v", "l", "bus", "1"), "data", "transactional"
    )
    transactional_port_handle = api.getAbstractionDefPortIDs(transactional_root)[0]
    transactional_mode = api.addAbstractionDefPortMode(transactional_port_handle, "onInitiator")
    wire_port_handle = api.getAbstractionDefPortIDs(root_handle)[0]
    for wrong_handle in ("missing", get_handle(object()), root_handle, wire_port_handle, transactional_mode):
        assert not remover(wrong_handle)

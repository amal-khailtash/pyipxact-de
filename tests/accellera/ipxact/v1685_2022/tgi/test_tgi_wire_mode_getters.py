"""Wire mode getters resolve the standard per-locus wire mode handles."""

import pytest

from amal.eda.accellera.ipxact.v1685_2022.tgi import abstraction_definition as api
from amal.eda.accellera.ipxact.v1685_2022.tgi import top_element
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import (
    TgiError,
    TgiFaultCode,
    get_handle,
    get_parent_info,
    registry,
    resolve_handle,
)
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import AbstractionDefinition
from org.accellera.ipxact.v1685_2022.abstraction_def_port_constraints_type import (
    AbstractionDefPortConstraintsType,
)

LOCUS_NAMES = ("onInitiator", "onTarget", "onSystem")


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


def make_wire_modes(port_id):
    modes = {name: api.addAbstractionDefPortMode(port_id, name) for name in LOCUS_NAMES}
    api.setOnSystemGroup(modes["onSystem"], "default")
    return modes


def test_wire_mode_getters_cover_each_locus_and_preserve_child_ownership():
    root, port_id = make_port()
    modes = make_wire_modes(port_id)
    expected = {
        "onInitiator": ("in", "required", "WIDTH_I + 1"),
        "onTarget": ("out", "optional", "WIDTH_T + 2"),
        "onSystem": ("inout", "illegal", "WIDTH_S + 3"),
    }

    for mode_id in modes.values():
        assert api.getAbstractionDefPortWireModeDirection(mode_id) is None
        assert api.getAbstractionDefPortWireModeMirroredModeConstraintsID(mode_id) is None
        assert api.getAbstractionDefPortWireModeModeConstraintsID(mode_id) is None
        assert api.getAbstractionDefPortWireModePresence(mode_id) is None
        assert api.getAbstractionDefPortWireModeWidthExpression(mode_id) is None

    for locus, mode_id in modes.items():
        direction, presence, width_expression = expected[locus]
        assert api.setAbstractionDefPortWireModeDirection(mode_id, direction)
        assert api.setAbstractionDefPortWireModePresence(mode_id, presence)
        assert api.setAbstractionDefPortWireModeWidth(mode_id, width_expression)
        mode = resolve_handle(mode_id)
        mode.mode_constraints = AbstractionDefPortConstraintsType()
        mode.mirrored_mode_constraints = AbstractionDefPortConstraintsType()

        assert api.getAbstractionDefPortWireModeDirection(mode_id) == direction
        assert api.getAbstractionDefPortWireModePresence(mode_id) == presence
        # Preserve expression text; this getter does not evaluate expressions.
        assert api.getAbstractionDefPortWireModeWidthExpression(mode_id) == width_expression

        for getter, attr in (
            (api.getAbstractionDefPortWireModeModeConstraintsID, "mode_constraints"),
            (api.getAbstractionDefPortWireModeMirroredModeConstraintsID, "mirrored_mode_constraints"),
        ):
            child_id = getter(mode_id)
            child = getattr(mode, attr)
            assert child_id == getter(mode_id)
            assert resolve_handle(child_id) is child
            parent_info = get_parent_info(child_id)
            assert parent_info.parent_handle == mode_id
            assert parent_info.path == (attr,)
            assert parent_info.container == "single"

    # The getters' values and child placement survive generated-model XML I/O.
    rendered = XmlDocument.serializer().render(resolve_handle(root))
    parsed = XmlDocument.parser().from_string(rendered, AbstractionDefinition)
    assert parsed == resolve_handle(root)
    parsed_wire = parsed.ports.port[0].wire_or_transactional
    parsed_modes = {
        "onInitiator": parsed_wire.on_initiator,
        "onTarget": parsed_wire.on_target,
        "onSystem": parsed_wire.on_system[0],
    }
    for locus, mode in parsed_modes.items():
        mode_id = get_handle(mode)
        direction, presence, width_expression = expected[locus]
        assert api.getAbstractionDefPortWireModeDirection(mode_id) == direction
        assert api.getAbstractionDefPortWireModePresence(mode_id) == presence
        assert api.getAbstractionDefPortWireModeWidthExpression(mode_id) == width_expression
        assert api.getAbstractionDefPortWireModeModeConstraintsID(mode_id) is not None
        assert api.getAbstractionDefPortWireModeMirroredModeConstraintsID(mode_id) is not None


@pytest.mark.parametrize(
    "getter",
    [
        api.getAbstractionDefPortWireModeDirection,
        api.getAbstractionDefPortWireModeMirroredModeConstraintsID,
        api.getAbstractionDefPortWireModeModeConstraintsID,
        api.getAbstractionDefPortWireModePresence,
        api.getAbstractionDefPortWireModeWidthExpression,
    ],
)
def test_wire_mode_getters_reject_invalid_port_and_wrong_style_handles(getter):
    _, wire_port_id = make_port("wire")
    _, transactional_port_id = make_port("transactional")
    transactional_mode_id = api.addAbstractionDefPortMode(transactional_port_id, "onInitiator")
    arbitrary_object_id = get_handle(object())

    for handle in ("missing", wire_port_id, transactional_mode_id, arbitrary_object_id):
        with pytest.raises(TgiError) as error:
            getter(handle)
        assert error.value.fault_code == TgiFaultCode.INVALID_ID


def test_wire_mode_constraints_are_distinct_between_loci():
    _, port_id = make_port()
    modes = make_wire_modes(port_id)

    mode_constraint_ids = []
    mirrored_constraint_ids = []
    for mode_id in modes.values():
        mode = resolve_handle(mode_id)
        mode.mode_constraints = AbstractionDefPortConstraintsType()
        mode.mirrored_mode_constraints = AbstractionDefPortConstraintsType()
        mode_constraint_ids.append(api.getAbstractionDefPortWireModeModeConstraintsID(mode_id))
        mirrored_constraint_ids.append(
            api.getAbstractionDefPortWireModeMirroredModeConstraintsID(mode_id)
        )

    assert len(set(mode_constraint_ids)) == len(LOCUS_NAMES)
    assert len(set(mirrored_constraint_ids)) == len(LOCUS_NAMES)

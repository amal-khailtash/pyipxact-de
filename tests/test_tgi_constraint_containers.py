"""Wire constraint ensure operations preserve each mode and container identity."""

import pytest

from amal.eda.ipxact_de.tgi.ipxact.v1685_2022 import abstraction_definition as api
from amal.eda.ipxact_de.tgi.ipxact.v1685_2022.core import (
    TgiError,
    TgiFaultCode,
    get_handle,
    get_parent_info,
    registry,
    resolve_handle,
)
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import (
    AbstractionDefinition,
    AbstractionDefPortConstraintsType,
    DelayValueType,
    EdgeValueType,
    TimingConstraint,
    Wire,
)

CASES = [("ModeConstraints", "mode_constraints"), ("MirroredModeConstraints", "mirrored_mode_constraints")]
LOCI = ["onInitiator", "onTarget", "onSystem"]


@pytest.fixture(autouse=True)
def clean_registry():
    registry.clear()
    yield
    registry.clear()


def modes():
    return [Wire.OnInitiator(), Wire.OnTarget(), Wire.OnSystem(group="system")]


def port_with_modes(mode_objects):
    return AbstractionDefinition.Ports.Port(
        logical_name="p",
        wire_or_transactional=Wire(
            on_initiator=mode_objects[0], on_target=mode_objects[1], on_system=[mode_objects[2]]
        ),
    )


def parse(port):
    return XmlDocument.parser().from_string(XmlDocument.serializer().render(port), AbstractionDefinition.Ports.Port)


def setter(suffix):
    return getattr(api, "setAbstractionDefPortWireMode" + suffix)


def getter(suffix):
    return getattr(api, "getAbstractionDefPortWireMode" + suffix + "ID")


def populated(clock):
    return AbstractionDefPortConstraintsType(
        timing_constraint=[
            TimingConstraint(value=25.0, clock_name=clock, clock_edge=EdgeValueType.FALL,
                             delay_type=DelayValueType.MIN, id="timing_id")
        ]
    )


@pytest.mark.parametrize("suffix,attr", CASES)
@pytest.mark.parametrize("index", range(3), ids=LOCI)
def test_creation_idempotence_ownership_and_selective_modes(suffix, attr, index):
    mode_objects = modes()
    selected = mode_objects[index]
    handle = get_handle(selected)
    assert getter(suffix)(handle) is None
    assert setter(suffix)(abstractionDefPortModeID=handle, timingConstraintClockName="  supplied_clock  ")
    constraints = getattr(selected, attr)
    child = constraints.timing_constraint[0]
    assert child.value == 0.0
    assert child.clock_name == "  supplied_clock  "
    assert len(constraints.timing_constraint) == 1
    constraints_handle = getter(suffix)(handle)
    owner = get_parent_info(constraints_handle)
    assert (owner.parent_handle, owner.path, owner.container) == (handle, (attr,), "single")
    timing_owner = get_parent_info(get_handle(child))
    assert (timing_owner.parent_handle, timing_owner.path, timing_owner.container) == (
        constraints_handle, ("timing_constraint",), "list"
    )
    assert setter(suffix)(handle, "different_clock")
    assert getter(suffix)(handle) == constraints_handle
    assert constraints.timing_constraint == [child]
    assert child.clock_name == "  supplied_clock  "
    assert all(getattr(other, attr) is None for other in mode_objects if other is not selected)
    port = port_with_modes(mode_objects)
    assert parse(port) == port


@pytest.mark.parametrize("index", range(3), ids=LOCI)
@pytest.mark.parametrize("parsed", [False, True], ids=["created", "parsed"])
def test_existing_distinct_containers_preserved_and_normal_removal(index, parsed):
    mode_objects = modes()
    for mode in mode_objects:
        mode.mode_constraints = populated("normal_clock")
        mode.mirrored_mode_constraints = populated("mirrored_clock")
    port = port_with_modes(mode_objects)
    if parsed:
        port = parse(port)
        wire = port.wire_or_transactional
        mode_objects = [wire.on_initiator, wire.on_target, wire.on_system[0]]
    selected = mode_objects[index]
    handle = get_handle(selected)
    normal = selected.mode_constraints
    mirrored = selected.mirrored_mode_constraints
    normal_id = getter("ModeConstraints")(handle)
    mirrored_id = getter("MirroredModeConstraints")(handle)
    assert normal_id != mirrored_id
    before = XmlDocument.serializer().render(port)
    for suffix, _attr in CASES:
        assert setter(suffix)(handle, "replacement_clock")
        assert setter(suffix)(handle, "replacement_clock")
    assert XmlDocument.serializer().render(port) == before
    assert selected.mode_constraints is normal
    assert selected.mirrored_mode_constraints is mirrored
    assert getter("ModeConstraints")(handle) == normal_id
    assert getter("MirroredModeConstraints")(handle) == mirrored_id
    assert api.removeAbstractionDefPortWireModeModeConstraints(handle)
    assert not api.removeAbstractionDefPortWireModeModeConstraints(handle)
    assert selected.mode_constraints is None
    assert resolve_handle(normal_id) is None
    assert selected.mirrored_mode_constraints is mirrored
    assert resolve_handle(mirrored_id) is mirrored
    assert all(other.mode_constraints is not None for other in mode_objects if other is not selected)
    assert parse(port) == port


@pytest.mark.parametrize("suffix,attr", CASES)
@pytest.mark.parametrize("invalid", [None, 5, "", "  "])
@pytest.mark.parametrize("existing", [False, True])
def test_clock_validation_is_atomic(suffix, attr, invalid, existing):
    selected = modes()[0]
    if existing:
        setattr(selected, attr, populated("existing_clock"))
    before = XmlDocument.serializer().render(selected)
    with pytest.raises(TgiError) as error:
        setter(suffix)(get_handle(selected), invalid)
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert XmlDocument.serializer().render(selected) == before


@pytest.mark.parametrize("suffix,attr", CASES)
def test_invalid_and_wrong_style_handles(suffix, attr):
    for handle in [
        "missing", get_handle(object()), get_handle(port_with_modes(modes())),
        get_handle(AbstractionDefinition.Ports.Port.Transactional.OnInitiator()),
        get_handle(AbstractionDefPortConstraintsType()),
    ]:
        for operation in [getter(suffix), lambda identifier: setter(suffix)(identifier, "clock")]:
            with pytest.raises(TgiError) as error:
                operation(handle)
            assert error.value.fault_code == TgiFaultCode.INVALID_ID
        assert not api.removeAbstractionDefPortWireModeModeConstraints(handle)

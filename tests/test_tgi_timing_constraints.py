"""Timing constraint lifecycle keeps ownership, order, and numeric values typed."""

import pytest

from amal.eda.accellera.ipxact.v1685_2022.tgi import abstraction_definition as abstraction_api
from amal.eda.accellera.ipxact.v1685_2022.tgi import constraint as constraint_api
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
from org.accellera.ipxact.v1685_2022.cell_specification import CellSpecification
from org.accellera.ipxact.v1685_2022.drive_constraint import DriveConstraint
from org.accellera.ipxact.v1685_2022.load_constraint import LoadConstraint
from org.accellera.ipxact.v1685_2022.timing_constraint import TimingConstraint


@pytest.fixture(autouse=True)
def clean_registry():
    registry.clear()
    yield
    registry.clear()


def _make_constraints():
    root_handle = top_element.createAbstractionDef(
        ("v", "l", "abstraction", "1"), ("v", "l", "bus", "1"), "data", "wire"
    )
    port_handle = abstraction_api.getAbstractionDefPortIDs(root_handle)[0]
    mode_handle = abstraction_api.addAbstractionDefPortMode(port_handle, "onInitiator")
    mode = resolve_handle(mode_handle)
    container = AbstractionDefPortConstraintsType(
        drive_constraint_or_load_constraint=[
            DriveConstraint(cell_specification=CellSpecification()),
            LoadConstraint(cell_specification=CellSpecification()),
        ]
    )
    mode.mode_constraints = container
    return root_handle, get_handle(container)


def _parse_root(root_handle):
    return XmlDocument.parser().from_string(
        XmlDocument.serializer().render(resolve_handle(root_handle)), AbstractionDefinition
    )


def test_timing_lifecycle_order_ownership_selective_removal_and_xml():
    root_handle, constraints_handle = _make_constraints()
    add = abstraction_api.addModeConstraintsTimingConstraint
    remove = abstraction_api.removeModeConstraintsTimingConstraint

    first = add(constraints_handle, 0, "clk_a")
    second = add(constraints_handle, 23.5, "clk_b")
    third = add(constraints_handle, 100, " clk_c ")
    ids = abstraction_api.getModeConstraintsTimingConstraintIDs(constraints_handle)
    assert ids == [first, second, third]
    assert abstraction_api.getModeConstraintsTimingConstraintIDs(constraints_handle) == ids
    container = resolve_handle(constraints_handle)
    assert [resolve_handle(timing_id).clock_name for timing_id in ids] == ["clk_a", "clk_b", " clk_c "]
    assert [constraint_api.getTimingConstraintValue(timing_id) for timing_id in ids] == [0.0, 23.5, 100.0]
    for timing_id in ids:
        parent = get_parent_info(timing_id)
        assert parent.parent_handle == constraints_handle
        assert parent.path == ("timing_constraint",)
        assert parent.container == "list"

    parsed = _parse_root(root_handle)
    assert parsed == resolve_handle(root_handle)
    parsed_container = parsed.ports.port[0].wire_or_transactional.on_initiator.mode_constraints
    parsed_container_id = get_handle(parsed_container)
    parsed_ids = abstraction_api.getModeConstraintsTimingConstraintIDs(parsed_container_id)
    assert [resolve_handle(timing_id).clock_name for timing_id in parsed_ids] == [
        "clk_a", "clk_b", " clk_c "
    ]
    assert [resolve_handle(timing_id).value for timing_id in parsed_ids] == [0.0, 23.5, 100.0]

    mixed_constraints = container.drive_constraint_or_load_constraint
    assert isinstance(mixed_constraints[0], DriveConstraint)
    assert isinstance(mixed_constraints[1], LoadConstraint)
    assert remove(second)
    assert resolve_handle(second) is None
    assert not remove(second)
    assert abstraction_api.getModeConstraintsTimingConstraintIDs(constraints_handle) == [first, third]
    assert container.drive_constraint_or_load_constraint is mixed_constraints
    assert len(container.drive_constraint_or_load_constraint) == 2
    assert XmlDocument.parser().from_string(
        XmlDocument.serializer().render(resolve_handle(root_handle)), AbstractionDefinition
    ) == resolve_handle(root_handle)


@pytest.mark.parametrize("value", [True, False, "1", None, -0.01, 100.01, float("nan"), float("inf"), float("-inf")])
def test_add_timing_constraint_rejects_bad_values_atomically(value):
    _root_handle, constraints_handle = _make_constraints()
    add = abstraction_api.addModeConstraintsTimingConstraint
    with pytest.raises(TgiError) as error:
        add(constraints_handle, value, "clk")
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert resolve_handle(constraints_handle).timing_constraint == []


@pytest.mark.parametrize("clock_name", [None, 1, "", "   "])
def test_add_timing_constraint_rejects_bad_clock_atomically(clock_name):
    _root_handle, constraints_handle = _make_constraints()
    with pytest.raises(TgiError) as error:
        abstraction_api.addModeConstraintsTimingConstraint(constraints_handle, 5, clock_name)
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert resolve_handle(constraints_handle).timing_constraint == []


def test_timing_lifecycle_rejects_invalid_containers_and_unowned_removal():
    for handle in ("missing", get_handle(object())):
        with pytest.raises(TgiError) as add_error:
            abstraction_api.addModeConstraintsTimingConstraint(handle, 1, "clk")
        assert add_error.value.fault_code == TgiFaultCode.INVALID_ID
        with pytest.raises(TgiError) as get_error:
            abstraction_api.getModeConstraintsTimingConstraintIDs(handle)
        assert get_error.value.fault_code == TgiFaultCode.INVALID_ID
        assert not abstraction_api.removeModeConstraintsTimingConstraint(handle)
    unowned = get_handle(TimingConstraint(value=1.0, clock_name="clk"))
    assert not abstraction_api.removeModeConstraintsTimingConstraint(unowned)


@pytest.mark.parametrize("value", ["", " ", "clock", "1 + 1", "nan", "inf", "-1", "100.01", 1, True, None])
def test_timing_value_setter_rejects_bad_input_atomically(value):
    timing_id = get_handle(TimingConstraint(value=20.0, clock_name="clk"))
    with pytest.raises(TgiError) as error:
        constraint_api.setTimingConstraintValue(timing_id, value)
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert constraint_api.getTimingConstraintValue(timing_id) == 20.0


def test_timing_value_setter_uses_numeric_string_and_isolates_target():
    first = get_handle(TimingConstraint(value=20.0, clock_name="clk_a"))
    second = get_handle(TimingConstraint(value=30.0, clock_name="clk_b"))
    assert constraint_api.setTimingConstraintValue(first, "0")
    assert constraint_api.getTimingConstraintValue(first) == 0.0
    assert constraint_api.getTimingConstraintValue(second) == 30.0
    assert constraint_api.setTimingConstraintValue(first, "100.0")
    assert constraint_api.getTimingConstraintValue(first) == 100.0

    for invalid_handle in ("missing", get_handle(object())):
        with pytest.raises(TgiError) as error:
            constraint_api.setTimingConstraintValue(invalid_handle, "1")
        assert error.value.fault_code == TgiFaultCode.INVALID_ID
        with pytest.raises(TgiError) as error:
            constraint_api.getTimingConstraintValue(invalid_handle)
        assert error.value.fault_code == TgiFaultCode.INVALID_ID

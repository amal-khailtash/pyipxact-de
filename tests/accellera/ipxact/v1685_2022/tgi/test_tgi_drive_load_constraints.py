"""Drive and load constraints traverse and remove from the generated mixed list."""

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
from org.accellera.ipxact.v1685_2022.cell_function_value_type import CellFunctionValueType
from org.accellera.ipxact.v1685_2022.cell_specification import CellSpecification
from org.accellera.ipxact.v1685_2022.drive_constraint import DriveConstraint
from org.accellera.ipxact.v1685_2022.load_constraint import LoadConstraint
from org.accellera.ipxact.v1685_2022.timing_constraint import TimingConstraint
from org.accellera.ipxact.v1685_2022.unsigned_positive_int_expression import (
    UnsignedPositiveIntExpression,
)


@pytest.fixture(autouse=True)
def clean_registry():
    registry.clear()
    yield
    registry.clear()


def cell(name):
    """Build a valid cellSpecification with a distinguishable cellFunction."""
    return CellSpecification(
        cell_function_or_cell_class=CellSpecification.CellFunction(
            value=CellFunctionValueType.BUF,
            other=name,
        )
    )


def make_constraints(multiple=True):
    drive_first = DriveConstraint(cell_specification=cell("drive-first"))
    load_first = LoadConstraint(
        cell_specification=cell("load-first"),
        count=UnsignedPositiveIntExpression(value="3"),
    )
    drive_second = DriveConstraint(cell_specification=cell("drive-second"))
    load_second = LoadConstraint(
        cell_specification=cell("load-second"),
        count=UnsignedPositiveIntExpression(value="5"),
    )
    timing = TimingConstraint(value=2.5, clock_name="clk")
    mixed_constraints = [drive_first, load_first]
    if multiple:
        mixed_constraints.extend([drive_second, load_second])
    constraints = AbstractionDefPortConstraintsType(
        timing_constraint=[timing],
        drive_constraint_or_load_constraint=mixed_constraints,
    )
    return constraints, drive_first, load_first, drive_second, load_second, timing


def make_mode_with_constraints(multiple=True):
    root = top_element.createAbstractionDef(
        ("vendor", "library", "abstraction-wire", "1.0"),
        ("vendor", "library", "bus", "1.0"),
        "data",
        "wire",
    )
    port_id = api.getAbstractionDefPortIDs(root)[0]
    mode_id = api.addAbstractionDefPortMode(port_id, "onInitiator")
    mode = resolve_handle(mode_id)
    constraints, *rest = make_constraints(multiple)
    mode.mode_constraints = constraints
    return root, port_id, mode_id, mode, constraints, rest


def test_getters_scan_mixed_constraints_in_order_and_register_ownership():
    _, _, _, _, constraints, items = make_mode_with_constraints()
    drive_first, load_first, drive_second, load_second, timing = items
    constraints_id = get_handle(constraints)

    drive_cell_id = api.getModeConstraintsDriveConstraintCellSpecificationID(constraints_id)
    assert drive_cell_id == get_handle(drive_first.cell_specification)
    assert api.getModeConstraintsDriveConstraintCellSpecificationID(constraints_id) == drive_cell_id
    assert resolve_handle(drive_cell_id) is drive_first.cell_specification
    drive_owner = get_parent_info(get_handle(drive_first))
    assert drive_owner.parent_handle == constraints_id
    assert drive_owner.path == ("drive_constraint_or_load_constraint",)
    assert drive_owner.container == "list"
    cell_owner = get_parent_info(drive_cell_id)
    assert cell_owner.parent_handle == get_handle(drive_first)
    assert cell_owner.path == ("cell_specification",)
    assert cell_owner.container == "single"

    load_id = api.getModeConstraintsLoadConstraintID(constraints_id)
    assert load_id == get_handle(load_first)
    assert api.getModeConstraintsLoadConstraintID(constraints_id) == load_id
    assert resolve_handle(load_id) is load_first
    load_owner = get_parent_info(load_id)
    assert load_owner.parent_handle == constraints_id
    assert load_owner.path == ("drive_constraint_or_load_constraint",)
    assert load_owner.container == "list"

    assert drive_second is not drive_first
    assert load_second is not load_first
    assert constraints.timing_constraint == [timing]


def test_removers_delete_all_matching_entries_and_preserve_opposite_type_and_timing():
    _, _, _, _, constraints, items = make_mode_with_constraints()
    drive_first, load_first, drive_second, load_second, timing = items
    constraints_id = get_handle(constraints)
    drive_ids = [get_handle(drive_first), get_handle(drive_second)]
    load_ids = [get_handle(load_first), get_handle(load_second)]
    timing_id = get_handle(timing)

    assert api.removeModeConstraintsDriveConstraint(constraints_id)
    assert constraints.drive_constraint_or_load_constraint == [load_first, load_second]
    assert all(resolve_handle(child_id) is None for child_id in drive_ids)
    assert api.getModeConstraintsDriveConstraintCellSpecificationID(constraints_id) is None
    assert api.getModeConstraintsLoadConstraintID(constraints_id) == load_ids[0]
    assert constraints.timing_constraint == [timing]
    assert resolve_handle(timing_id) is timing
    assert not api.removeModeConstraintsDriveConstraint(constraints_id)

    assert api.removeModeConstraintsLoadConstraint(constraints_id)
    assert constraints.drive_constraint_or_load_constraint == []
    assert all(resolve_handle(child_id) is None for child_id in load_ids)
    assert constraints.timing_constraint == [timing]
    assert resolve_handle(timing_id) is timing
    assert api.getModeConstraintsLoadConstraintID(constraints_id) is None
    assert not api.removeModeConstraintsLoadConstraint(constraints_id)


def test_empty_and_invalid_constraint_handles():
    empty_id = get_handle(AbstractionDefPortConstraintsType())
    assert api.getModeConstraintsDriveConstraintCellSpecificationID(empty_id) is None
    assert api.getModeConstraintsLoadConstraintID(empty_id) is None
    assert not api.removeModeConstraintsDriveConstraint(empty_id)
    assert not api.removeModeConstraintsLoadConstraint(empty_id)

    invalid_ids = ["missing", get_handle(object()), get_handle(cell("unrelated"))]
    for invalid_id in invalid_ids:
        for getter in (
            api.getModeConstraintsDriveConstraintCellSpecificationID,
            api.getModeConstraintsLoadConstraintID,
        ):
            with pytest.raises(TgiError) as error:
                getter(invalid_id)
            assert error.value.fault_code == TgiFaultCode.INVALID_ID
        assert not api.removeModeConstraintsDriveConstraint(invalid_id)
        assert not api.removeModeConstraintsLoadConstraint(invalid_id)


def test_mode_constraints_id_traversal_survives_xml_with_mixed_children():
    root, _, _, mode, constraints, items = make_mode_with_constraints(multiple=False)
    drive_first, load_first, _, _, timing = items
    rendered = XmlDocument.serializer().render(resolve_handle(root))
    parsed = XmlDocument.parser().from_string(rendered, AbstractionDefinition)
    assert parsed == resolve_handle(root)

    parsed_mode = parsed.ports.port[0].wire_or_transactional.on_initiator
    parsed_mode_id = get_handle(parsed_mode)
    parsed_constraints_id = api.getAbstractionDefPortWireModeModeConstraintsID(parsed_mode_id)
    assert parsed_constraints_id == get_handle(parsed_mode.mode_constraints)
    assert api.getModeConstraintsDriveConstraintCellSpecificationID(parsed_constraints_id) is not None
    assert api.getModeConstraintsLoadConstraintID(parsed_constraints_id) is not None

    # The parser retains the generated combined choice list order and identities.
    parsed_items = parsed_mode.mode_constraints.drive_constraint_or_load_constraint
    assert [type(item) for item in parsed_items] == [type(drive_first), type(load_first)]
    assert parsed_mode.mode_constraints.timing_constraint[0].value == timing.value
    assert mode.mode_constraints is constraints

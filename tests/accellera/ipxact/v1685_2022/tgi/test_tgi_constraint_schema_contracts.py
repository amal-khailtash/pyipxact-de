"""Constraint TGI contracts follow the generated IP-XACT 1685-2022 schema model."""

import pytest
from lxml import etree

from amal.eda.accellera.ipxact.v1685_2022.tgi import constraint as api
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import (
    TgiError,
    get_handle,
    get_parent_info,
    registry,
    resolve_handle,
)
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import (
    CellClassValueType,
    CellFunctionValueType,
    CellStrengthValueType,
    Component,
    ComponentPortDirectionType,
    ConstraintSet,
    ConstraintSets,
    DelayValueType,
    EdgeValueType,
    LoadConstraint,
    Model,
    Port,
    PortWireType,
    TimingConstraint,
    UnsignedIntExpression,
    UnsignedPositiveIntExpression,
)
from org.accellera.ipxact.v1685_2022.cell_specification import CellSpecification
from org.accellera.ipxact.v1685_2022.drive_constraint import DriveConstraint

_SCHEMA = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))


@pytest.fixture(autouse=True)
def clean_registry():
    registry.clear()
    yield
    registry.clear()


def component_with_constraints(constraint_sets):
    wire = PortWireType(
        direction=ComponentPortDirectionType.IN,
        constraint_sets=ConstraintSets(constraint_set=constraint_sets),
    )
    return Component(
        vendor="example.org",
        library="contracts",
        name="constraint_component",
        version="1.0",
        model=Model(
            ports=Model.Ports(
                port=[Port(name="data", wire_or_transactional_or_structured=wire)],
            ),
        ),
    )


def schema_round_trip(root):
    xml = XmlDocument.serializer().render(root)
    _SCHEMA.assertValid(etree.fromstring(xml.encode()))
    parsed = XmlDocument.parser().from_string(xml, Component)
    assert parsed == root
    return parsed


def test_constraint_choices_wrappers_defaults_and_vector_endpoints_round_trip():
    function_spec = CellSpecification(
        cell_function_or_cell_class=CellSpecification.CellFunction(
            value=CellFunctionValueType.OTHER,
            other="vendor_cell",
        ),
        cell_strength=CellStrengthValueType.HIGH,
    )
    class_spec = CellSpecification(
        cell_function_or_cell_class=CellClassValueType.SEQUENTIAL,
        cell_strength=CellStrengthValueType.MEDIAN,
    )
    first = ConstraintSet(
        constraint_set_id="data_slice",
        vector=ConstraintSet.Vector(
            left=UnsignedIntExpression(value="WIDTH - 1"),
            right=UnsignedIntExpression(value="0"),
        ),
        drive_constraint=DriveConstraint(cell_specification=function_spec),
        load_constraint=LoadConstraint(
            cell_specification=class_spec,
            count=UnsignedPositiveIntExpression(value="5"),
        ),
        timing_constraint=[
            TimingConstraint(
                value=25.0,
                clock_name="clk",
                clock_edge=EdgeValueType.FALL,
                delay_type=DelayValueType.MAX,
            ),
        ],
    )
    omitted_count = ConstraintSet(
        constraint_set_id="default_count",
        load_constraint=LoadConstraint(
            cell_specification=CellSpecification(
                cell_function_or_cell_class=CellSpecification.CellFunction(value=CellFunctionValueType.BUF),
            ),
        ),
    )
    root = component_with_constraints([first, omitted_count])

    parsed = schema_round_trip(root)
    parsed_sets = parsed.model.ports.port[0].wire_or_transactional_or_structured.constraint_sets
    parsed_first, parsed_default = parsed_sets.constraint_set
    first_id = get_handle(parsed_first)
    default_id = get_handle(parsed_default)

    drive_spec_id = api.getConstraintSetDriveConstraintCellSpecificationID(first_id)
    drive_spec = resolve_handle(drive_spec_id)
    assert drive_spec.cell_function_or_cell_class.value is CellFunctionValueType.OTHER
    assert api.getCellSpecificationCellFunction(drive_spec_id) == "other"
    assert api.getCellSpecificationCellClass(drive_spec_id) is None
    function_id = api.getCellSpecificationCellFunctionID(drive_spec_id)
    assert resolve_handle(function_id).other == "vendor_cell"
    drive_id = get_parent_info(drive_spec_id).parent_handle
    assert api.getDriveConstraintType(drive_id) == "other"
    assert api.getDriveConstraintOther(drive_id) == "vendor_cell"
    assert api.getDriveConstraintValue(drive_id) == "high"

    load_id = api.getConstraintSetLoadConstraintID(first_id)
    load = resolve_handle(load_id)
    assert load.cell_specification.cell_function_or_cell_class is CellClassValueType.SEQUENTIAL
    assert api.getLoadConstraintType(load_id) == "sequential"
    count_id = api.getLoadConstraintCountID(load_id)
    assert isinstance(resolve_handle(count_id), UnsignedPositiveIntExpression)
    assert api.getLoadConstraintCount(load_id) == 5
    assert api.getLoadConstraintCountExpression(load_id) == "5"
    assert get_parent_info(count_id).parent_handle == load_id
    assert get_parent_info(count_id).path == ("count",)

    assert api.getLoadConstraintCountID(api.getConstraintSetLoadConstraintID(default_id)) is None
    assert api.getLoadConstraintCount(api.getConstraintSetLoadConstraintID(default_id)) == 3

    left_id = api.getConstraintSetVectorLeftID(first_id)
    right_id = api.getConstraintSetVectorRightID(first_id)
    vector_id = get_handle(parsed_first.vector)
    assert isinstance(resolve_handle(left_id), UnsignedIntExpression)
    assert isinstance(resolve_handle(right_id), UnsignedIntExpression)
    assert get_parent_info(left_id).parent_handle == vector_id
    assert get_parent_info(right_id).parent_handle == vector_id
    with pytest.raises(TgiError):
        api.getConstraintSetVector(first_id)
    assert api.getConstraintSetVectorExpression(first_id) == ["WIDTH - 1", "0"]
    assert api.getConstraintSetTimingConstraintIDs(first_id)
    timing_id = api.getConstraintSetTimingConstraintIDs(first_id)[0]
    assert api.getTimingConstraintValue(timing_id) == 25.0
    assert resolve_handle(timing_id).clock_edge is EdgeValueType.FALL
    assert resolve_handle(timing_id).delay_type is DelayValueType.MAX


def test_constraint_mutations_preserve_choice_and_wrapper_identity_then_invalidate_removed_subtrees():
    root = component_with_constraints([ConstraintSet(constraint_set_id="editable")])
    constraint_set = root.model.ports.port[0].wire_or_transactional_or_structured.constraint_sets.constraint_set[0]
    constraint_set_id = get_handle(constraint_set)

    assert api.setConstraintSetDriveConstraint(constraint_set_id, "buf")
    drive_spec_id = api.getConstraintSetDriveConstraintCellSpecificationID(constraint_set_id)
    drive_spec = resolve_handle(drive_spec_id)
    drive_id = get_parent_info(drive_spec_id).parent_handle
    function_id = api.getCellSpecificationCellFunctionID(drive_spec_id)
    function = resolve_handle(function_id)
    assert api.setCellSpecificationCellFunction(drive_spec_id, "inv")
    assert api.getCellSpecificationCellFunctionID(drive_spec_id) == function_id
    assert resolve_handle(function_id) is function
    assert api.getCellSpecificationCellFunction(drive_spec_id) == "inv"
    assert api.setDriveConstraintValue(drive_id, "high")
    assert api.getDriveConstraintValue(drive_id) == "high"

    assert api.setCellSpecificationCellClass(drive_spec_id, "sequential")
    assert resolve_handle(function_id) is None
    assert api.getCellSpecificationCellFunctionID(drive_spec_id) is None
    assert api.getCellSpecificationCellFunction(drive_spec_id) is None
    assert api.getCellSpecificationCellClass(drive_spec_id) == "sequential"
    assert drive_spec.cell_function_or_cell_class is CellClassValueType.SEQUENTIAL
    assert api.setCellSpecificationCellFunction(drive_spec_id, "nand2")
    assert api.getCellSpecificationCellClass(drive_spec_id) is None
    assert api.getCellSpecificationCellFunction(drive_spec_id) == "nand2"

    assert api.setConstraintSetLoadConstraint(constraint_set_id, "other")
    load_id = api.getConstraintSetLoadConstraintID(constraint_set_id)
    assert api.getLoadConstraintCount(load_id) == 3
    assert api.getLoadConstraintCountID(load_id) is None
    assert api.setLoadConstraintCount(load_id, "LOADS + 1")
    count_id = api.getLoadConstraintCountID(load_id)
    count = resolve_handle(count_id)
    assert isinstance(count, UnsignedPositiveIntExpression)
    assert get_parent_info(count_id).parent_handle == load_id
    assert api.getLoadConstraintCountExpression(load_id) == "LOADS + 1"
    assert api.setLoadConstraintCount(load_id, "7")
    assert api.getLoadConstraintCountID(load_id) == count_id
    assert resolve_handle(count_id) is count
    assert api.getLoadConstraintCount(load_id) == 7
    assert api.removeLoadConstraintCount(load_id)
    assert resolve_handle(count_id) is None
    assert api.getLoadConstraintCount(load_id) == 3
    load_spec_id = api.getLoadConstraintCellSpecificationID(load_id)

    assert api.setConstraintSetVector(constraint_set_id, ["WIDTH - 1", "0"])
    vector = constraint_set.vector
    vector_id = get_handle(vector)
    left_id = api.getConstraintSetVectorLeftID(constraint_set_id)
    right_id = api.getConstraintSetVectorRightID(constraint_set_id)
    left = resolve_handle(left_id)
    right = resolve_handle(right_id)
    assert api.setConstraintSetVector(constraint_set_id, ["8", "4"])
    assert constraint_set.vector is vector
    assert get_handle(constraint_set.vector) == vector_id
    assert api.getConstraintSetVectorLeftID(constraint_set_id) == left_id
    assert api.getConstraintSetVectorRightID(constraint_set_id) == right_id
    assert resolve_handle(left_id) is left and left.value == "8"
    assert resolve_handle(right_id) is right and right.value == "4"
    assert api.getConstraintSetVector(constraint_set_id) == [8, 4]

    timing_id = api.getConstraintSetTimingConstraintIDs(constraint_set_id)
    assert timing_id == []
    timing = TimingConstraint(value=0.0, clock_name="clk")
    constraint_set.timing_constraint.append(timing)
    timing_id = api.getConstraintSetTimingConstraintIDs(constraint_set_id)[0]
    assert get_parent_info(timing_id).parent_handle == constraint_set_id

    assert schema_round_trip(root) == root
    assert api.removeConstraintSetTimingConstraint(timing_id)
    assert resolve_handle(timing_id) is None
    assert api.removeConstraintSetVector(constraint_set_id)
    assert resolve_handle(vector_id) is None
    assert resolve_handle(left_id) is None
    assert resolve_handle(right_id) is None
    assert api.removeConstraintSetLoadConstraint(constraint_set_id)
    assert resolve_handle(load_id) is None
    assert resolve_handle(count_id) is None
    assert resolve_handle(load_spec_id) is None
    assert api.removeConstraintSetDriveConstraint(constraint_set_id)
    assert resolve_handle(drive_id) is None
    assert resolve_handle(drive_spec_id) is None
    assert api.getConstraintSetDriveConstraintCellSpecificationID(constraint_set_id) is None
    assert schema_round_trip(root) == root

"""Constraint Annex signatures, enums, source expressions and owned mutations."""

import inspect

import pytest

from amal.eda.accellera.ipxact.v1685_2022 import tgi
from amal.eda.accellera.ipxact.v1685_2022.tgi import constraint as api
from amal.eda.accellera.ipxact.v1685_2022.tgi.component import _register_graph
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import TgiError, get_handle, registry, resolve_handle
from org.accellera.ipxact.v1685_2022 import (
    CellClassValueType,
    ConstraintSet,
    ConstraintSetRef,
    ConstraintSets,
    TimingConstraint,
)

_BASE = [
    ("getCellSpecificationCellClass", "cellSpecificationID"),
    ("getCellSpecificationCellFunction", "cellSpecificationID"),
    ("getCellSpecificationCellFunctionID", "cellSpecificationID"),
    ("getConstraintSetDriveConstraintCellSpecificationID", "constraintSetID"),
    ("getConstraintSetLoadConstraintID", "constraintSetID"),
    ("getConstraintSetRefLocalName", "constraintSetRefID"),
    ("getConstraintSetReferenceName", "constraintSetID"),
    ("getConstraintSetTimingConstraintIDs", "constraintSetID"),
    ("getConstraintSetVector", "constraitSetID"),
    ("getConstraintSetVectorExpression", "constraintSetID"),
    ("getConstraintSetVectorLeftID", "constraintSetID"),
    ("getConstraintSetVectorRightID", "constraintSetID"),
    ("getDriveConstraintOther", "driveConstraintID"),
    ("getDriveConstraintType", "driveConstraintID"),
    ("getDriveConstraintValue", "driveConstraintID"),
    ("getLoadConstraintCellSpecificationID", "loadConstraintID"),
    ("getLoadConstraintCount", "loadConstraintID"),
    ("getLoadConstraintCountExpression", "loadConstraintID"),
    ("getLoadConstraintCountID", "loadConstraintID"),
    ("getLoadConstraintOther", "loadConstraintID"),
    ("getLoadConstraintType", "loadConstraintID"),
    ("getLoadConstraintValue", "loadConstraintID"),
    ("getTimingConstraintValue", "timingConstraintID"),
]
_EXTENDED = [
    ("removeConstraintSetDriveConstraint", "constraintSetID"),
    ("removeConstraintSetLoadConstraint", "constraintSetID"),
    ("removeConstraintSetTimingConstraint", "timingConstraintID"),
    ("removeConstraintSetVector", "constraintSetID"),
    ("removeLoadConstraintCount", "loadConstraintID"),
    ("setCellSpecificationCellClass", "cellSpecificationID,cellClass"),
    ("setCellSpecificationCellFunction", "cellSpecificationID,cellFunction"),
    ("setConstraintSetDriveConstraint", "constraintSetID,cellFunctionOrCellClass"),
    ("setConstraintSetLoadConstraint", "constraintSetID,cellFuntionOrCellClass"),
    ("setConstraintSetReferenceName", "constraintSetID,referenceName"),
    ("setConstraintSetVector", "constraintSetID,vector"),
    ("setDriveConstraintOtherValue", "driveConstraintID,other"),
    ("setDriveConstraintValue", "driveConstraintID,value"),
    ("setLoadConstraintCellSpecification", "loadConstraintID,cellFunctionOrCellClass"),
    ("setLoadConstraintCount", "loadConstraintID,count"),
    ("setLoadConstraintOtherValue", "loadConstraintID,other"),
    ("setTimingConstraintValue", "timingConstraintID,value"),
]


@pytest.fixture(autouse=True)
def clean_registry():
    registry.clear()
    yield
    registry.clear()


@pytest.mark.parametrize(
    "name,args,section",
    [
        *[(name, args, f"F.7.33.{i}") for i, (name, args) in enumerate(_BASE, 1)],
        *[(name, args, f"F.7.34.{i}") for i, (name, args) in enumerate(_EXTENDED, 1)],
    ],
)
def test_signatures_exports_and_static_docs(name, args, section):
    function = getattr(api, name)
    assert list(inspect.signature(function).parameters) == args.split(",")
    assert getattr(tgi, name) is function and name in api.__all__
    assert "Args:" in function.__doc__ and "Returns:" in function.__doc__
    assert f"Section: {section}." in function.__doc__


@pytest.mark.parametrize("name,args", _BASE)
def test_getters_reject_wrong_handles(name, args):
    with pytest.raises(TgiError):
        getattr(api, name)(get_handle(object()))


def _constraints():
    parent = ConstraintSet()
    handle = get_handle(parent)
    api.setConstraintSetDriveConstraint(handle, "buf")
    api.setConstraintSetLoadConstraint(handle, "sequential")
    return parent, handle, get_handle(parent.drive_constraint), get_handle(parent.load_constraint)


def test_choice_edits_preserve_identity_strength_and_invalidate_removed_function():
    parent, handle, drive_id, load_id = _constraints()
    spec_id = api.getConstraintSetDriveConstraintCellSpecificationID(handle)
    function_id = api.getCellSpecificationCellFunctionID(spec_id)
    api.setDriveConstraintValue(drive_id, "high")
    api.setDriveConstraintOtherValue(drive_id, "  custom\tcell  ")
    api.setConstraintSetDriveConstraint(handle, "other")
    assert api.getCellSpecificationCellFunctionID(spec_id) == function_id
    assert api.getDriveConstraintOther(drive_id) == "custom cell"
    assert api.getDriveConstraintValue(drive_id) == "high"
    api.setCellSpecificationCellClass(spec_id, "combinational")
    assert resolve_handle(function_id) is None
    assert api.getCellSpecificationCellClass(spec_id) == "combinational"
    assert api.getDriveConstraintOther(drive_id) is None
    assert api.setDriveConstraintOtherValue(drive_id, "anything") is False
    assert parent.drive_constraint.cell_specification.cell_function_or_cell_class is CellClassValueType.COMBINATIONAL
    assert api.getLoadConstraintType(load_id) == "sequential"


@pytest.mark.parametrize("invalid", ["bad", "", "combinational extra", None, True, 4, "buf\x00"])
def test_invalid_cell_choices_are_atomic(invalid):
    parent, handle, drive_id, load_id = _constraints()
    before = parent.drive_constraint.cell_specification.cell_function_or_cell_class
    for action in [
        lambda: api.setConstraintSetDriveConstraint(handle, invalid),
        lambda: api.setConstraintSetLoadConstraint(handle, invalid),
        lambda: api.setDriveConstraintValue(drive_id, invalid),
    ]:
        with pytest.raises(TgiError):
            action()
    assert parent.drive_constraint.cell_specification.cell_function_or_cell_class is before
    assert api.getLoadConstraintType(load_id) == "sequential"


def test_count_default_source_and_wrapper_bounds_lifecycle():
    parent, handle, drive_id, load_id = _constraints()
    assert api.getLoadConstraintCount(load_id) == 3
    assert api.getLoadConstraintCountExpression(load_id) is None
    assert api.getLoadConstraintCountID(load_id) is None
    api.setLoadConstraintCount(load_id, "2 + 3")
    count_id = api.getLoadConstraintCountID(load_id)
    count = resolve_handle(count_id)
    count.minimum, count.maximum = 2, 7
    count.other_attributes = {"{urn:test}source": "kept"}
    for source in ["0", "1", "8", "-1", str(1 << 32), "1 +", "1'bx", None]:
        with pytest.raises(TgiError):
            api.setLoadConstraintCount(load_id, source)
        assert count.value == "2 + 3"
    api.setLoadConstraintCount(load_id, "COUNT")
    assert api.getLoadConstraintCountID(load_id) == count_id
    assert count.other_attributes
    with pytest.raises(TgiError):
        api.getLoadConstraintCount(load_id)
    assert api.getLoadConstraintCountExpression(load_id) == "COUNT"
    assert api.removeLoadConstraintCount(load_id)
    assert resolve_handle(count_id) is None
    assert api.getLoadConstraintCount(load_id) == 3
    assert not api.removeLoadConstraintCount(load_id)


def test_vector_source_atomicity_metadata_and_subtree_removal():
    parent = ConstraintSet()
    handle = get_handle(parent)
    assert api.getConstraintSetVector(handle) is None
    api.setConstraintSetVector(handle, ["4 + 3", "0"])
    vector_id = get_handle(parent.vector)
    left_id = api.getConstraintSetVectorLeftID(handle)
    right_id = api.getConstraintSetVectorRightID(handle)
    left = resolve_handle(left_id)
    left.other_attributes = {"{urn:test}source": "kept"}
    for values in [["8", "-1"], ["8", str(1 << 32)], ["8", "1 +"], "70", [], [None, "0"]]:
        with pytest.raises(TgiError):
            api.setConstraintSetVector(handle, values)
        assert api.getConstraintSetVectorExpression(handle) == ["4 + 3", "0"]
    api.setConstraintSetVector(handle, ("WIDTH - 1", "0"))
    assert api.getConstraintSetVectorLeftID(handle) == left_id and left.other_attributes
    with pytest.raises(TgiError):
        api.getConstraintSetVector(handle)
    assert api.removeConstraintSetVector(handle)
    assert all(resolve_handle(h) is None for h in [vector_id, left_id, right_id])


def test_constraint_removal_invalidates_descendants_and_timing_ownership():
    parent, handle, drive_id, load_id = _constraints()
    spec_id = api.getConstraintSetDriveConstraintCellSpecificationID(handle)
    function_id = api.getCellSpecificationCellFunctionID(spec_id)
    assert api.removeConstraintSetDriveConstraint(handle)
    assert all(resolve_handle(h) is None for h in [drive_id, spec_id, function_id])
    assert not api.removeConstraintSetDriveConstraint(handle)
    parent.timing_constraint = (TimingConstraint(value=12, clock_name="clk"),)
    timing_id = api.getConstraintSetTimingConstraintIDs(handle)[0]
    assert api.removeConstraintSetTimingConstraint(timing_id)
    assert parent.timing_constraint == [] and resolve_handle(timing_id) is None
    orphan_id = get_handle(TimingConstraint(value=20, clock_name="clk"))
    with pytest.raises(TgiError):
        api.removeConstraintSetTimingConstraint(orphan_id)


def test_reference_source_and_nmtoken_uniqueness():
    ref = ConstraintSetRef(local_name="named-set")
    assert api.getConstraintSetRefLocalName(get_handle(ref)) == "named-set"
    first, second = ConstraintSet(constraint_set_id="first"), ConstraintSet(constraint_set_id="second")
    holder = ConstraintSets(constraint_set=[first, second])
    _register_graph(holder)
    with pytest.raises(TgiError):
        api.setConstraintSetReferenceName(get_handle(first), "second")
    assert first.constraint_set_id == "first"
    api.setConstraintSetReferenceName(get_handle(first), "  1:valid-token  ")
    assert first.constraint_set_id == "1:valid-token"

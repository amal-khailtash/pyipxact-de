# ruff: noqa: I001
"""Constraint category TGI functions (IEEE 1685-2022).

Implements BASE (F.7.33) and EXTENDED (F.7.34) functions providing read and
write access to constraint related schema elements: ``constraintSet``,
``constraintSetRef``, ``driveConstraint``, ``loadConstraint`` and
``timingConstraint`` along with the nested ``cellSpecification`` and vector
range expressions.

Only the public functions defined in sections F.7.33 and F.7.34 are exported;
no convenience helpers. Invalid handles raise :class:`TgiError` with
``TgiFaultCode.INVALID_ID``. Operations that cannot be performed because of
schema state raise ``TgiFaultCode.INVALID_ARGUMENT``.
"""

import re
from collections.abc import Sequence
from enum import Enum

from org.accellera.ipxact.v1685_2022 import Component, CellClassValueType, CellFunctionValueType, CellStrengthValueType

from ._attribute_references import _root_for
from .address_space import _register_owned_child, _walk_model
from .component import _list_attr, _register_graph
from .constraint_set import _timing_value
from .cpu import _xml_text
from .port_map import _integer, _name, _remove_child, _source

from org.accellera.ipxact.v1685_2022.cell_specification import CellSpecification
from org.accellera.ipxact.v1685_2022.constraint_set import ConstraintSet
from org.accellera.ipxact.v1685_2022.constraint_set_ref import ConstraintSetRef
from org.accellera.ipxact.v1685_2022.drive_constraint import DriveConstraint
from org.accellera.ipxact.v1685_2022.load_constraint import LoadConstraint
from org.accellera.ipxact.v1685_2022.timing_constraint import TimingConstraint
from org.accellera.ipxact.v1685_2022.unsigned_int_expression import UnsignedIntExpression
from org.accellera.ipxact.v1685_2022.unsigned_positive_int_expression import UnsignedPositiveIntExpression

from .core import (
    TgiError,
    TgiFaultCode,
    get_handle,
    resolve_handle,
    register_parent,
    detach_child_by_handle,
)

__all__ = [
    # BASE (F.7.33)
    "getCellSpecificationCellClass",
    "getCellSpecificationCellFunction",
    "getCellSpecificationCellFunctionID",
    "getConstraintSetDriveConstraintCellSpecificationID",
    "getConstraintSetLoadConstraintID",
    "getConstraintSetRefLocalName",
    "getConstraintSetReferenceName",
    "getConstraintSetTimingConstraintIDs",
    "getConstraintSetVector",
    "getConstraintSetVectorExpression",
    "getConstraintSetVectorLeftID",
    "getConstraintSetVectorRightID",
    "getDriveConstraintOther",
    "getDriveConstraintType",
    "getDriveConstraintValue",
    "getLoadConstraintCellSpecificationID",
    "getLoadConstraintCount",
    "getLoadConstraintCountExpression",
    "getLoadConstraintCountID",
    "getLoadConstraintOther",
    "getLoadConstraintType",
    "getLoadConstraintValue",
    "getTimingConstraintValue",
    # EXTENDED (F.7.34)
    "removeConstraintSetDriveConstraint",
    "removeConstraintSetLoadConstraint",
    "removeConstraintSetTimingConstraint",
    "removeConstraintSetVector",
    "removeLoadConstraintCount",
    "setCellSpecificationCellClass",
    "setCellSpecificationCellFunction",
    "setConstraintSetDriveConstraint",
    "setConstraintSetLoadConstraint",
    "setConstraintSetReferenceName",
    "setConstraintSetVector",
    "setDriveConstraintOtherValue",
    "setDriveConstraintValue",
    "setLoadConstraintCellSpecification",
    "setLoadConstraintCount",
    "setLoadConstraintOtherValue",
    "setTimingConstraintValue",
]


# ---------------------------------------------------------------------------
# Internal helpers (non-spec)
# ---------------------------------------------------------------------------


def _as_cell_specification(handle: str) -> CellSpecification:
    return _require(handle, CellSpecification)


def _as_constraint_set(handle: str) -> ConstraintSet:
    return _require(handle, ConstraintSet)


def _as_drive_constraint(handle: str) -> DriveConstraint:
    return _require(handle, DriveConstraint)


def _as_load_constraint(handle: str) -> LoadConstraint:
    return _require(handle, LoadConstraint)


def _as_timing_constraint(handle: str) -> TimingConstraint:
    return _require(handle, TimingConstraint)


def _as_constraint_set_ref(handle: str) -> ConstraintSetRef:
    return _require(handle, ConstraintSetRef)


_UINT_MAX = (1 << 32) - 1


def _require[T](handle: str, model: type[T]) -> T:
    value = resolve_handle(handle) if isinstance(handle, str) else None
    if not isinstance(value, model):
        raise TgiError(f"Invalid {model.__name__} handle", TgiFaultCode.INVALID_ID)
    _register_graph(value)
    return value


def _token(value: str) -> str:
    _xml_text(value)
    return re.sub(r"[ \t\r\n]+", " ", value).strip(" ")


def _enumeration[T: Enum](value: str, model: type[T]) -> T:
    source = _token(value)
    try:
        return model(source)
    except ValueError as error:
        raise TgiError("Invalid cell enumeration", TgiFaultCode.INVALID_ARGUMENT) from error


def _function(spec: CellSpecification) -> CellSpecification.CellFunction | None:
    value = spec.cell_function_or_cell_class
    return value if isinstance(value, CellSpecification.CellFunction) else None


def _spec(parent: DriveConstraint | LoadConstraint) -> CellSpecification:
    value = parent.cell_specification
    if not isinstance(value, CellSpecification):
        raise TgiError("Invalid cellSpecification model", TgiFaultCode.INVALID_ID)
    return value


def _choice(value: str) -> CellSpecification.CellFunction | CellClassValueType:
    source = _token(value)
    try:
        return CellSpecification.CellFunction(value=CellFunctionValueType(source))
    except ValueError:
        return _enumeration(source, CellClassValueType)


def _set_choice(spec: CellSpecification, value: CellSpecification.CellFunction | CellClassValueType) -> None:
    current = _function(spec)
    if current is not None and isinstance(value, CellSpecification.CellFunction):
        current.value = value.value
    else:
        if current is not None:
            register_parent(current, spec, ("cell_function_or_cell_class",), "single")
            detach_child_by_handle(get_handle(current))
        spec.cell_function_or_cell_class = value
    _register_graph(spec)


def _type(parent: DriveConstraint | LoadConstraint) -> str | None:
    value = _spec(parent).cell_function_or_cell_class
    if isinstance(value, CellSpecification.CellFunction):
        return value.value.value
    return value.value if isinstance(value, CellClassValueType) else None


def _strength(parent: DriveConstraint | LoadConstraint) -> str | None:
    value = _spec(parent).cell_strength
    return value.value if value is not None else None


def _other(parent: DriveConstraint | LoadConstraint) -> str | None:
    value = _function(_spec(parent))
    return value.other if value is not None else None


def _set_other(parent: DriveConstraint | LoadConstraint, source: str) -> bool:
    source = _token(source)
    value = _function(_spec(parent))
    if value is None:
        return False
    value.other = source
    return True


def _set_constraint(parent: ConstraintSet, kind: type[DriveConstraint] | type[LoadConstraint], source: str) -> bool:
    value = _choice(source)
    if kind is DriveConstraint:
        current = parent.drive_constraint
        if current is None:
            parent.drive_constraint = DriveConstraint(
                cell_specification=CellSpecification(cell_function_or_cell_class=value)
            )
        else:
            _set_choice(_spec(current), value)
    else:
        current = parent.load_constraint
        if current is None:
            parent.load_constraint = LoadConstraint(
                cell_specification=CellSpecification(cell_function_or_cell_class=value)
            )
        else:
            _set_choice(_spec(current), value)
    _register_graph(parent)
    return True


def _vector(parent: ConstraintSet) -> ConstraintSet.Vector | None:
    value = parent.vector
    if value is not None and (
        not isinstance(value, ConstraintSet.Vector)
        or not isinstance(value.left, UnsignedIntExpression)
        or not isinstance(value.right, UnsignedIntExpression)
    ):
        raise TgiError("Invalid constraint vector model", TgiFaultCode.INVALID_ID)
    return value


def _number(value: UnsignedIntExpression | UnsignedPositiveIntExpression, *, positive: bool = False) -> int:
    result = _integer(value.value, _UINT_MAX)
    if result is None or (positive and result == 0):
        raise TgiError("Invalid unsigned constraint expression", TgiFaultCode.INVALID_ARGUMENT)
    if (value.minimum is not None and result < value.minimum) or (value.maximum is not None and result > value.maximum):
        raise TgiError("Constraint expression outside declared bounds", TgiFaultCode.INVALID_ARGUMENT)
    return result


def _count_source(source: str, current: UnsignedPositiveIntExpression | None) -> str:
    source = _source(source, current, _UINT_MAX)
    if _integer(source, _UINT_MAX, True) == 0:
        raise TgiError("Load count must be positive", TgiFaultCode.INVALID_ARGUMENT)
    return source


def _child_id(parent: object, child: object | None, attr: str) -> str | None:
    if child is None:
        return None
    register_parent(child, parent, (attr,), "single")
    _register_graph(child)
    return get_handle(child)


# ---------------------------------------------------------------------------
# BASE (F.7.33)
# ---------------------------------------------------------------------------


def getCellSpecificationCellClass(cellSpecificationID: str) -> str | None:
    """Return the ``cellClass`` enumeration value of a cellSpecification.

    Section: F.7.33.1.


    Args:
        cellSpecificationID: Handle to the specified schema element.

    Returns:
        Stored source value, or None when optional content is absent.
    """
    spec = _as_cell_specification(cellSpecificationID)
    value = spec.cell_function_or_cell_class
    return value.value if isinstance(value, CellClassValueType) else None


def getCellSpecificationCellFunction(cellSpecificationID: str) -> str | None:
    """Return the ``cellFunction`` enumeration value of a cellSpecification.

    Section: F.7.33.2.


    Args:
        cellSpecificationID: Handle to the specified schema element.

    Returns:
        Stored source value, or None when optional content is absent.
    """
    value = _function(_as_cell_specification(cellSpecificationID))
    return value.value.value if value is not None else None


def getCellSpecificationCellFunctionID(cellSpecificationID: str) -> str | None:
    """Return handle of the ``cellFunction`` element of a cellSpecification.

    Section: F.7.33.3.


    Args:
        cellSpecificationID: Handle to the specified schema element.

    Returns:
        Owned child handle, or None when absent.
    """
    spec = _as_cell_specification(cellSpecificationID)
    return _child_id(spec, _function(spec), "cell_function_or_cell_class")


def getConstraintSetDriveConstraintCellSpecificationID(constraintSetID: str) -> str | None:
    """Return handle of ``cellSpecification`` inside the driveConstraint.

    Section: F.7.33.4.


    Args:
        constraintSetID: Handle to the specified schema element.

    Returns:
        Owned child handle, or None when absent.
    """
    parent = _as_constraint_set(constraintSetID)
    value = parent.drive_constraint
    return _child_id(value, _spec(value), "cell_specification") if value is not None else None


def getConstraintSetLoadConstraintID(constraintSetID: str) -> str | None:
    """Return handle of the ``loadConstraint`` element.

    Section: F.7.33.5.


    Args:
        constraintSetID: Handle to the specified schema element.

    Returns:
        Owned child handle, or None when absent.
    """
    parent = _as_constraint_set(constraintSetID)
    return _child_id(parent, parent.load_constraint, "load_constraint")


def getConstraintSetRefLocalName(constraintSetRefID: str) -> str | None:
    """Return the local name value of a constraintSetRef.

    Section: F.7.33.6.


    Args:
        constraintSetRefID: Handle to the specified schema element.

    Returns:
        Stored source value, or None when optional content is absent.
    """
    return _as_constraint_set_ref(constraintSetRefID).local_name


def getConstraintSetReferenceName(constraintSetID: str) -> str | None:
    """Return the ``constraintSetId`` attribute of a constraintSet.

    Section: F.7.33.7.


    Args:
        constraintSetID: Handle to the specified schema element.

    Returns:
        Stored source value, or None when optional content is absent.
    """
    return _as_constraint_set(constraintSetID).constraint_set_id


def getConstraintSetTimingConstraintIDs(constraintSetID: str) -> list[str]:
    """Return handles of all ``timingConstraint`` children of a constraintSet.

    Section: F.7.33.8.


    Args:
        constraintSetID: Handle to the specified schema element.

    Returns:
        Owned handles in source order.
    """
    parent = _as_constraint_set(constraintSetID)
    return [get_handle(_require(get_handle(value), TimingConstraint)) for value in parent.timing_constraint]


def getConstraintSetVector(constraitSetID: str) -> list[int] | None:
    """Return [left, right] evaluated integer values of constraintSet vector.

    Section: F.7.33.9.


    Args:
        constraitSetID: Handle to the specified schema element.

    Returns:
        Evaluated unsigned [left, right] values, or None when absent. Unresolved expressions fault.
    """
    value = _vector(_as_constraint_set(constraitSetID))
    return [_number(value.left), _number(value.right)] if value is not None else None


def getConstraintSetVectorExpression(constraintSetID: str) -> list[str] | None:
    """Return [leftExpr, rightExpr] textual expressions of vector bounds.

    Section: F.7.33.10.


    Args:
        constraintSetID: Handle to the specified schema element.

    Returns:
        Stored [left, right] expression sources, or None when absent.
    """
    value = _vector(_as_constraint_set(constraintSetID))
    return [value.left.value, value.right.value] if value is not None else None


def getConstraintSetVectorLeftID(constraintSetID: str) -> str | None:
    """Return handle of left side expression element of vector.

    Section: F.7.33.11.


    Args:
        constraintSetID: Handle to the specified schema element.

    Returns:
        Owned child handle, or None when absent.
    """
    parent = _as_constraint_set(constraintSetID)
    value = _vector(parent)
    return _child_id(value, value.left, "left") if value is not None else None


def getConstraintSetVectorRightID(constraintSetID: str) -> str | None:
    """Return handle of right side expression element of vector.

    Section: F.7.33.12.


    Args:
        constraintSetID: Handle to the specified schema element.

    Returns:
        Owned child handle, or None when absent.
    """
    parent = _as_constraint_set(constraintSetID)
    value = _vector(parent)
    return _child_id(value, value.right, "right") if value is not None else None


def getDriveConstraintOther(driveConstraintID: str) -> str | None:
    """Return the ``other`` attribute of driveConstraint.cellSpecification.cellFunction.

    Section: F.7.33.13.


    Args:
        driveConstraintID: Handle to the specified schema element.

    Returns:
        Stored source value, or None when optional content is absent.
    """
    return _other(_as_drive_constraint(driveConstraintID))


def getDriveConstraintType(driveConstraintID: str) -> str | None:
    """Return type of driveConstraint (cellFunction value or cellClass value).

    Section: F.7.33.14.


    Args:
        driveConstraintID: Handle to the specified schema element.

    Returns:
        Stored source value, or None when optional content is absent.
    """
    return _type(_as_drive_constraint(driveConstraintID))


def getDriveConstraintValue(driveConstraintID: str) -> str | None:
    """Return the drive constraint strength value (cellStrength attribute).

    Section: F.7.33.15.


    Args:
        driveConstraintID: Handle to the specified schema element.

    Returns:
        Stored source value, or None when optional content is absent.
    """
    return _strength(_as_drive_constraint(driveConstraintID))


def getLoadConstraintCellSpecificationID(loadConstraintID: str) -> str | None:
    """Return handle of the ``cellSpecification`` of a loadConstraint.

    Section: F.7.33.16.


    Args:
        loadConstraintID: Handle to the specified schema element.

    Returns:
        Owned child handle, or None when absent.
    """
    parent = _as_load_constraint(loadConstraintID)
    return _child_id(parent, _spec(parent), "cell_specification")


def getLoadConstraintCount(loadConstraintID: str) -> int | None:
    """Return numeric count of a loadConstraint.

    Section: F.7.33.17.


    Args:
        loadConstraintID: Handle to the specified schema element.

    Returns:
        Evaluated positive unsigned count; 3 when the count element is absent.
    """
    value = _as_load_constraint(loadConstraintID).count
    return _number(value, positive=True) if value is not None else 3


def getLoadConstraintCountExpression(loadConstraintID: str) -> str | None:
    """Return textual count expression of a loadConstraint.

    Section: F.7.33.18.


    Args:
        loadConstraintID: Handle to the specified schema element.

    Returns:
        Stored source value, or None when optional content is absent.
    """
    value = _as_load_constraint(loadConstraintID).count
    return value.value if value is not None else None


def getLoadConstraintCountID(loadConstraintID: str) -> str | None:
    """Return handle of the ``count`` expression element.

    Section: F.7.33.19.


    Args:
        loadConstraintID: Handle to the specified schema element.

    Returns:
        Owned child handle, or None when absent.
    """
    parent = _as_load_constraint(loadConstraintID)
    return _child_id(parent, parent.count, "count")


def getLoadConstraintOther(loadConstraintID: str) -> str | None:
    """Return the ``other`` attribute (cellFunction based specification only).

    Section: F.7.33.20.


    Args:
        loadConstraintID: Handle to the specified schema element.

    Returns:
        Stored source value, or None when optional content is absent.
    """
    return _other(_as_load_constraint(loadConstraintID))


def getLoadConstraintType(loadConstraintID: str) -> str | None:
    """Return type of a loadConstraint (cellFunction value or cellClass value).

    Section: F.7.33.21.


    Args:
        loadConstraintID: Handle to the specified schema element.

    Returns:
        Stored source value, or None when optional content is absent.
    """
    return _type(_as_load_constraint(loadConstraintID))


def getLoadConstraintValue(loadConstraintID: str) -> str | None:
    """Return the load constraint strength value (cellStrength attribute).

    Section: F.7.33.22.


    Args:
        loadConstraintID: Handle to the specified schema element.

    Returns:
        Stored source value, or None when optional content is absent.
    """
    return _strength(_as_load_constraint(loadConstraintID))


def getTimingConstraintValue(timingConstraintID: str) -> float:
    """Return a timingConstraint's finite numeric percentage.

    Section: F.7.33.23.

    Args:
        timingConstraintID: Handle to the specified schema element.

    Returns:
        Finite percentage from 0 through 100.
    """
    return _timing_value(_as_timing_constraint(timingConstraintID).value)


def removeConstraintSetDriveConstraint(constraintSetID: str) -> bool:
    """Remove the driveConstraint child from a constraintSet.

    Section: F.7.34.1.


    Args:
        constraintSetID: Handle to the specified schema element.

    Returns:
        True on success; False when optional content or the requested choice is absent.
    """
    return _remove_child(_as_constraint_set(constraintSetID), "drive_constraint")


def removeConstraintSetLoadConstraint(constraintSetID: str) -> bool:
    """Remove the loadConstraint child from a constraintSet.

    Section: F.7.34.2.


    Args:
        constraintSetID: Handle to the specified schema element.

    Returns:
        True on success; False when optional content or the requested choice is absent.
    """
    return _remove_child(_as_constraint_set(constraintSetID), "load_constraint")


def removeConstraintSetTimingConstraint(timingConstraintID: str) -> bool:
    """Remove a timingConstraint element.

    Section: F.7.34.3.


    Args:
        timingConstraintID: Handle to the specified schema element.

    Returns:
        True on success; False when optional content or the requested choice is absent.
    """
    value = _as_timing_constraint(timingConstraintID)
    owner = _register_owned_child(value, ConstraintSet)
    if owner is None or not any(item is value for item in owner.timing_constraint):
        raise TgiError("Timing constraint lacks an owning constraintSet", TgiFaultCode.INVALID_ID)
    _list_attr(owner, "timing_constraint")
    _register_graph(owner)
    return detach_child_by_handle(timingConstraintID)


def removeConstraintSetVector(constraintSetID: str) -> bool:
    """Remove vector element from a constraintSet.

    Section: F.7.34.4.


    Args:
        constraintSetID: Handle to the specified schema element.

    Returns:
        True on success; False when optional content or the requested choice is absent.
    """
    return _remove_child(_as_constraint_set(constraintSetID), "vector")


def removeLoadConstraintCount(loadConstraintID: str) -> bool:
    """Remove ``count`` element from a loadConstraint.

    Section: F.7.34.5.


    Args:
        loadConstraintID: Handle to the specified schema element.

    Returns:
        True on success; False when optional content or the requested choice is absent.
    """
    return _remove_child(_as_load_constraint(loadConstraintID), "count")


def setCellSpecificationCellClass(cellSpecificationID: str, cellClass: str) -> bool:
    """Set ``cellClass`` enumeration of a cellSpecification (clears cellFunction).

    Section: F.7.34.6.


    Args:
        cellSpecificationID: Handle to the specified schema element.
        cellClass: Source value to assign.

    Returns:
        True on success; False when optional content or the requested choice is absent.
    """
    spec = _as_cell_specification(cellSpecificationID)
    value = _enumeration(cellClass, CellClassValueType)
    _set_choice(spec, value)
    return True


def setCellSpecificationCellFunction(cellSpecificationID: str, cellFunction: str) -> bool:
    """Set ``cellFunction`` enumeration of a cellSpecification (clears cellClass).

    Section: F.7.34.7.


    Args:
        cellSpecificationID: Handle to the specified schema element.
        cellFunction: Source value to assign.

    Returns:
        True on success; False when optional content or the requested choice is absent.
    """
    spec = _as_cell_specification(cellSpecificationID)
    value = _enumeration(cellFunction, CellFunctionValueType)
    _set_choice(spec, CellSpecification.CellFunction(value=value))
    return True


def setConstraintSetDriveConstraint(constraintSetID: str, cellFunctionOrCellClass: str) -> bool:
    """Create/replace driveConstraint with given type (function or class).

    Section: F.7.34.8. Strength remains unspecified when creating a constraint.


    Args:
        constraintSetID: Handle to the specified schema element.
        cellFunctionOrCellClass: Source value to assign.

    Returns:
        True on success; False when optional content or the requested choice is absent.
    """
    return _set_constraint(_as_constraint_set(constraintSetID), DriveConstraint, cellFunctionOrCellClass)


def setConstraintSetLoadConstraint(constraintSetID: str, cellFuntionOrCellClass: str) -> bool:
    """Create/replace loadConstraint with given type (function or class).

    Section: F.7.34.9.


    Args:
        constraintSetID: Handle to the specified schema element.
        cellFuntionOrCellClass: Source value to assign.

    Returns:
        True on success; False when optional content or the requested choice is absent.
    """
    return _set_constraint(_as_constraint_set(constraintSetID), LoadConstraint, cellFuntionOrCellClass)


def setConstraintSetReferenceName(constraintSetID: str, referenceName: str) -> bool:
    """Set the ``constraintSetId`` attribute of a constraintSet.

    Section: F.7.34.10.


    Args:
        constraintSetID: Handle to the specified schema element.
        referenceName: Source value to assign.

    Returns:
        True on success; False when optional content or the requested choice is absent.
    """
    parent = _as_constraint_set(constraintSetID)
    source = _name(referenceName, "NMTOKEN")
    root = _root_for(parent)
    scope = root.model if isinstance(root, Component) else root
    if scope is not None:
        for value, _, _, _ in _walk_model(scope):
            if (
                isinstance(value, ConstraintSet)
                and value is not parent
                and _name(value.constraint_set_id, "NMTOKEN") == source
            ):
                raise TgiError("Duplicate constraintSetId", TgiFaultCode.ALREADY_EXISTS)
    parent.constraint_set_id = source
    return True


def setConstraintSetVector(constraintSetID: str, vector: Sequence[str]) -> bool:
    """Set vector left/right expression values for a constraintSet.

    Section: F.7.34.11. Expects list/tuple of two strings.


    Args:
        constraintSetID: Handle to the specified schema element.
        vector: Source value to assign.

    Returns:
        True on success; False when optional content or the requested choice is absent.
    """
    parent = _as_constraint_set(constraintSetID)
    if not isinstance(vector, Sequence) or isinstance(vector, (str, bytes)) or len(vector) != 2:
        raise TgiError("Vector requires two expression sources", TgiFaultCode.INVALID_ARGUMENT)
    current = _vector(parent)
    left = _source(vector[0], current.left if current is not None else None, _UINT_MAX)
    right = _source(vector[1], current.right if current is not None else None, _UINT_MAX)
    if current is None:
        parent.vector = ConstraintSet.Vector(
            left=UnsignedIntExpression(value=left), right=UnsignedIntExpression(value=right)
        )
    else:
        current.left.value, current.right.value = left, right
    _register_graph(parent)
    return True


def setDriveConstraintOtherValue(driveConstraintID: str, other: str) -> bool:
    """Set ``other`` attribute for driveConstraint cellFunction variant.

    Section: F.7.34.12.


    Args:
        driveConstraintID: Handle to the specified schema element.
        other: Source value to assign.

    Returns:
        True on success; False when optional content or the requested choice is absent.
    """
    return _set_other(_as_drive_constraint(driveConstraintID), other)


def setDriveConstraintValue(driveConstraintID: str, value: str) -> bool:
    """Set cellStrength (value) for driveConstraint cellSpecification.

    Section: F.7.34.13.


    Args:
        driveConstraintID: Handle to the specified schema element.
        value: Source value to assign.

    Returns:
        True on success; False when optional content or the requested choice is absent.
    """
    parent = _as_drive_constraint(driveConstraintID)
    strength = _enumeration(value, CellStrengthValueType)
    _spec(parent).cell_strength = strength
    return True


def setLoadConstraintCellSpecification(loadConstraintID: str, cellFunctionOrCellClass: str) -> bool:
    """Replace loadConstraint cellSpecification definition.

    Section: F.7.34.14.


    Args:
        loadConstraintID: Handle to the specified schema element.
        cellFunctionOrCellClass: Source value to assign.

    Returns:
        True on success; False when optional content or the requested choice is absent.
    """
    parent = _as_load_constraint(loadConstraintID)
    value = _choice(cellFunctionOrCellClass)
    _set_choice(_spec(parent), value)
    return True


def setLoadConstraintCount(loadConstraintID: str, count: str) -> bool:
    """Set numeric count (expression) of loadConstraint.

    Section: F.7.34.15.


    Args:
        loadConstraintID: Handle to the specified schema element.
        count: Source value to assign.

    Returns:
        True on success; False when optional content or the requested choice is absent.
    """
    parent = _as_load_constraint(loadConstraintID)
    current = parent.count
    if current is not None and not isinstance(current, UnsignedPositiveIntExpression):
        raise TgiError("Invalid count model", TgiFaultCode.INVALID_ID)
    source = _count_source(count, current)
    if current is None:
        parent.count = UnsignedPositiveIntExpression(value=source)
    else:
        current.value = source
    _register_graph(parent)
    return True


def setLoadConstraintOtherValue(loadConstraintID: str, other: str) -> bool:
    """Set ``other`` attribute for loadConstraint cellFunction variant.

    Section: F.7.34.16.


    Args:
        loadConstraintID: Handle to the specified schema element.
        other: Source value to assign.

    Returns:
        True on success; False when optional content or the requested choice is absent.
    """
    return _set_other(_as_load_constraint(loadConstraintID), other)


def setTimingConstraintValue(timingConstraintID: str, value: str) -> bool:
    """Set a finite numeric timing value from its WSDL string input.

    Section: F.7.34.17.

    Args:
        timingConstraintID: Handle to the specified schema element.
        value: Source value to assign.

    Returns:
        True on success; False when optional content or the requested choice is absent.
    """
    import math

    tc = _as_timing_constraint(timingConstraintID)
    if tc is None:
        raise TgiError("Invalid timingConstraint handle", TgiFaultCode.INVALID_ID)
    if not isinstance(value, str):
        raise TgiError("Timing value must be a numeric string from 0 through 100", TgiFaultCode.INVALID_ARGUMENT)
    try:
        numeric_value = float(value)
    except (ValueError, OverflowError) as error:
        raise TgiError(
            "Timing value must be a numeric string from 0 through 100", TgiFaultCode.INVALID_ARGUMENT
        ) from error
    if not math.isfinite(numeric_value) or not 0.0 <= numeric_value <= 100.0:
        raise TgiError("Timing value must be a numeric string from 0 through 100", TgiFaultCode.INVALID_ARGUMENT)
    tc.value = numeric_value
    return True

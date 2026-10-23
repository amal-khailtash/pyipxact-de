"""Constraint Set category TGI functions (IEEE 1685-2022).

Implements only the public API defined in Annex F sections:

* F.7.35 Constraint Set (BASE)
* F.7.36 Constraint Set (EXTENDED)

Per the 2022 specification these sections currently define exactly two
functions:

* getConstraintSetTimingConstraints (F.7.35.1)
* addConstraintSetTimingConstraint (F.7.36.1)

Timing constraints express delay as a percentage from 0 through 100 relative
to a named clock. The optional clockEdge and delayType attributes retain their
source values; adding a constraint leaves them unspecified. Nested constraints
use handle ownership and never enter the top-level document VLNV registry.

Invalid handles raise :class:`TgiError` with ``TgiFaultCode.INVALID_ID``.
Invalid percentages and clock names raise INVALID_ARGUMENT before mutation.
The BASE operation returns numeric values; the EXTENDED operation returns the
new timingConstraint handle. Clock-reference consistency is checked separately
by component semantic validation.
"""

import math
import re
import unicodedata

from org.accellera.ipxact.v1685_2022.constraint_set import ConstraintSet
from org.accellera.ipxact.v1685_2022.timing_constraint import TimingConstraint

from .core import TgiError, TgiFaultCode, get_handle, register_parent, resolve_handle

__all__ = [
    "getConstraintSetTimingConstraints",  # F.7.35.1 (BASE)
    "addConstraintSetTimingConstraint",  # F.7.36.1 (EXTENDED)
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _resolve_constraint_set(csID: str) -> ConstraintSet:
    """Resolve a typed constraintSet handle or raise INVALID_ID."""
    obj = resolve_handle(csID) if isinstance(csID, str) else None
    if not isinstance(obj, ConstraintSet):
        raise TgiError("Invalid constraintSet handle", TgiFaultCode.INVALID_ID)
    return obj


# ---------------------------------------------------------------------------
# Traversal
# ---------------------------------------------------------------------------


def getConstraintSetTimingConstraints(constraintSetID: str) -> list[float]:
    """Return all timingConstraint values for the given constraintSet.

    Section: F.7.35.1.

    Args:
        constraintSetID: Handle referencing a ``constraintSet`` element.

    Returns:
        list[float]: A copied, source-ordered list of finite percentages (empty if none).
            Traversal establishes ownership for parsed timingConstraint children.

    Raises:
        TgiError: INVALID_ID for a wrong parent handle; INVALID_ARGUMENT for
            malformed timingConstraint children or percentage values.
    """
    cs = _resolve_constraint_set(constraintSetID)
    values: list[float] = []
    for constraint in cs.timing_constraint:
        if not isinstance(constraint, TimingConstraint):
            raise TgiError("Invalid timingConstraint model", TgiFaultCode.INVALID_ARGUMENT)
        values.append(_timing_value(constraint.value))
        register_parent(constraint, cs, ("timing_constraint",), "list")
    return values


# ---------------------------------------------------------------------------
# Getters
# ---------------------------------------------------------------------------


def addConstraintSetTimingConstraint(constraintSetID: str, value: float, clockName: str) -> str:
    """Add a new timingConstraint to the given constraintSet.

    Section: F.7.36.1.

    Args:
        constraintSetID: Handle referencing a ``constraintSet`` element.
        value: Finite numeric timing percentage, from 0.0 through 100.0 inclusive.
            Boolean and string inputs are rejected.
        clockName: Associated clock portName; XML whitespace is collapsed and
            the schema character rules are checked before mutation.

    Returns:
        str: Handle of the newly created ``timingConstraint`` element.

    Raises:
        TgiError: If the parent handle is invalid or value cannot be applied.
    """
    cs = _resolve_constraint_set(constraintSetID)
    numeric_value = _timing_value(value)
    clock_name = _clock_name(clockName)
    tc = TimingConstraint(value=numeric_value, clock_name=clock_name)
    # The timing_constraint field is an iterable list (list default factory in schema)
    cs.timing_constraint = [*cs.timing_constraint, tc]
    register_parent(tc, cs, ("timing_constraint",), "list")
    return get_handle(tc)


def _timing_value(value: float) -> float:
    """Validate the delayPercentageType finite inclusive percentage range."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TgiError("Timing value must be numeric", TgiFaultCode.INVALID_ARGUMENT)
    try:
        numeric = float(value)
    except (OverflowError, ValueError) as error:
        raise TgiError("Invalid timing percentage", TgiFaultCode.INVALID_ARGUMENT) from error
    if not math.isfinite(numeric) or not 0.0 <= numeric <= 100.0:
        raise TgiError("Timing value must be finite and between 0 and 100", TgiFaultCode.INVALID_ARGUMENT)
    return numeric


def _clock_name(value: str) -> str:
    """Apply XML whitespace collapse and the IP-XACT portName character rules."""
    if not isinstance(value, str):
        raise TgiError("clockName must be a port name", TgiFaultCode.INVALID_ARGUMENT)
    name = re.sub(r"[ \t\r\n]+", " ", value).strip(" ")
    # XML NameStartChar includes Unicode ranges beyond letters (XML 1.0, fifth edition).
    initial = re.compile(
        r"[:A-Z_a-z\u00c0-\u00d6\u00d8-\u00f6\u00f8-\u02ff\u0370-\u037d"
        r"\u037f-\u1fff\u200c-\u200d\u2070-\u218f\u2c00-\u2fef\u3001-\ud7ff"
        r"\uf900-\ufdcf\ufdf0-\ufffd\U00010000-\U000effff]"
    )
    if (
        not name
        or initial.fullmatch(name[0]) is None
        or any(char not in ".-:_" and unicodedata.category(char)[0] not in "LN" for char in name[1:])
    ):
        raise TgiError("clockName must match the IP-XACT portName type", TgiFaultCode.INVALID_ARGUMENT)
    return name

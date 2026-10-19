from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from org.accellera.spirit.v1685_2009.ve.constraint_set import ConstraintSet

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009"


@dataclass(slots=True, kw_only=True)
class ConstraintSets:
    """
    List of constraintSet elements for a component port.
    """

    class Meta:
        name = "constraintSets"
        namespace = (
            "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009"
        )

    constraint_set: Sequence[ConstraintSet] = field(
        default_factory=list,
        metadata={
            "name": "constraintSet",
            "type": "Element",
            "min_occurs": 1,
        },
    )

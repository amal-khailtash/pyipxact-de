from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from org.accellera.spirit.v1_2.bus_def_signal_constraints import (
    BusDefSignalConstraints,
)

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2"


@dataclass(slots=True, kw_only=True)
class BusDefSignalConstraintSets:
    """
    List of busDefSignalConstraints elements for a bus definition signal.
    """

    class Meta:
        name = "busDefSignalConstraintSets"
        namespace = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2"

    bus_def_signal_constraints: Sequence[BusDefSignalConstraints] = field(
        default_factory=list,
        metadata={
            "name": "busDefSignalConstraints",
            "type": "Element",
            "min_occurs": 1,
        },
    )

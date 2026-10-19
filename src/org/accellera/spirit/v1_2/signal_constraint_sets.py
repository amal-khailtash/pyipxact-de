from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from org.accellera.spirit.v1_2.signal_constraints import SignalConstraints

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2"


@dataclass(slots=True, kw_only=True)
class SignalConstraintSets:
    """
    List of signalConstraints elements for a component signal.
    """

    class Meta:
        name = "signalConstraintSets"
        namespace = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2"

    signal_constraints: Sequence[SignalConstraints] = field(
        default_factory=list,
        metadata={
            "name": "signalConstraints",
            "type": "Element",
            "min_occurs": 1,
        },
    )

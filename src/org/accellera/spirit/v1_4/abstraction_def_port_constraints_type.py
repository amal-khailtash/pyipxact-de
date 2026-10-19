from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from org.accellera.spirit.v1_4.drive_constraint import DriveConstraint
from org.accellera.spirit.v1_4.load_constraint import LoadConstraint
from org.accellera.spirit.v1_4.timing_constraint import TimingConstraint

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4"


@dataclass(slots=True, kw_only=True)
class AbstractionDefPortConstraintsType:
    """
    Defines constraints that apply to a wire type port in an abstraction
    definition.
    """

    class Meta:
        name = "abstractionDefPortConstraintsType"

    timing_constraint: Sequence[TimingConstraint] = field(
        default_factory=list,
        metadata={
            "name": "timingConstraint",
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
        },
    )
    drive_constraint: None | DriveConstraint = field(
        default=None,
        metadata={
            "name": "driveConstraint",
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
        },
    )
    load_constraint: None | LoadConstraint = field(
        default=None,
        metadata={
            "name": "loadConstraint",
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
        },
    )

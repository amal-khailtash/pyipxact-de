from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from org.accellera.ipxact.v1685_2022.drive_constraint import DriveConstraint
from org.accellera.ipxact.v1685_2022.load_constraint import LoadConstraint
from org.accellera.ipxact.v1685_2022.timing_constraint import TimingConstraint

__NAMESPACE__ = "http://www.accellera.org/XMLSchema/IPXACT/1685-2022"


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
            "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
        },
    )
    drive_constraint_or_load_constraint: Sequence[
        DriveConstraint | LoadConstraint
    ] = field(
        default_factory=list,
        metadata={
            "type": "Elements",
            "choices": (
                {
                    "name": "driveConstraint",
                    "type": DriveConstraint,
                    "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
                    "max_occurs": 2,
                },
                {
                    "name": "loadConstraint",
                    "type": LoadConstraint,
                    "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
                    "max_occurs": 3,
                },
            ),
            "max_occurs": 5,
        },
    )

from __future__ import annotations

from dataclasses import dataclass, field

from org.accellera.ipxact.v1685_2014.real_expression import RealExpression
from org.accellera.ipxact.v1685_2014.unsigned_bit_vector_expression import (
    UnsignedBitVectorExpression,
)

__NAMESPACE__ = "http://www.accellera.org/XMLSchema/IPXACT/1685-2014"


@dataclass(slots=True, kw_only=True)
class SingleShotDriver:
    """
    Describes a driven one-shot port.

    :ivar single_shot_offset: Time in nanoseconds until start of one-
        shot.
    :ivar single_shot_value: Value of port after first  edge of one-
        shot.
    :ivar single_shot_duration: Duration in nanoseconds of the one shot.
    """

    class Meta:
        name = "singleShotDriver"
        namespace = "http://www.accellera.org/XMLSchema/IPXACT/1685-2014"

    single_shot_offset: RealExpression = field(
        metadata={
            "name": "singleShotOffset",
            "type": "Element",
        }
    )
    single_shot_value: UnsignedBitVectorExpression = field(
        metadata={
            "name": "singleShotValue",
            "type": "Element",
        }
    )
    single_shot_duration: RealExpression = field(
        metadata={
            "name": "singleShotDuration",
            "type": "Element",
        }
    )

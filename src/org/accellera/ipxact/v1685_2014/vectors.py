from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from org.accellera.ipxact.v1685_2014.vector import Vector

__NAMESPACE__ = "http://www.accellera.org/XMLSchema/IPXACT/1685-2014"


@dataclass(slots=True, kw_only=True)
class Vectors:
    """
    Vectored information.
    """

    class Meta:
        name = "vectors"
        namespace = "http://www.accellera.org/XMLSchema/IPXACT/1685-2014"

    vector: Sequence[Vector] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "min_occurs": 1,
        },
    )

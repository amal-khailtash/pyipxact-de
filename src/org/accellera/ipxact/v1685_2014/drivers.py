from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from org.accellera.ipxact.v1685_2014.driver import Driver

__NAMESPACE__ = "http://www.accellera.org/XMLSchema/IPXACT/1685-2014"


@dataclass(slots=True, kw_only=True)
class Drivers:
    """
    Container for wire port driver elements.

    :ivar driver: Wire port driver element. If no range is specified,
        default value applies to the entire range.
    """

    class Meta:
        name = "drivers"
        namespace = "http://www.accellera.org/XMLSchema/IPXACT/1685-2014"

    driver: Sequence[Driver] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "min_occurs": 1,
        },
    )

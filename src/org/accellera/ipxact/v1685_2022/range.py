from __future__ import annotations

from dataclasses import dataclass, field

from org.accellera.ipxact.v1685_2022.left import Left
from org.accellera.ipxact.v1685_2022.right import Right

__NAMESPACE__ = "http://www.accellera.org/XMLSchema/IPXACT/1685-2022"


@dataclass(slots=True, kw_only=True)
class Range:
    """
    Left and right bound of a reference into a vector.
    """

    class Meta:
        name = "range"
        namespace = "http://www.accellera.org/XMLSchema/IPXACT/1685-2022"

    left: Left = field(
        metadata={
            "type": "Element",
        }
    )
    right: Right = field(
        metadata={
            "type": "Element",
        }
    )

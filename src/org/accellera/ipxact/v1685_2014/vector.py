from __future__ import annotations

from dataclasses import dataclass, field

from org.accellera.ipxact.v1685_2014.left import Left
from org.accellera.ipxact.v1685_2014.right import Right

__NAMESPACE__ = "http://www.accellera.org/XMLSchema/IPXACT/1685-2014"


@dataclass(slots=True, kw_only=True)
class Vector:
    """
    Left and right ranges of the vector.
    """

    class Meta:
        name = "vector"
        namespace = "http://www.accellera.org/XMLSchema/IPXACT/1685-2014"

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

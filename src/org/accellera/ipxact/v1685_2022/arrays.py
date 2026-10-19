from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from org.accellera.ipxact.v1685_2022.left import Left
from org.accellera.ipxact.v1685_2022.right import Right

__NAMESPACE__ = "http://www.accellera.org/XMLSchema/IPXACT/1685-2022"


@dataclass(slots=True, kw_only=True)
class Arrays:
    """
    :ivar array: Specific left and right array bounds.
    """

    class Meta:
        name = "arrays"
        namespace = "http://www.accellera.org/XMLSchema/IPXACT/1685-2022"

    array: Sequence[Arrays.Array] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "min_occurs": 1,
        },
    )

    @dataclass(slots=True, kw_only=True)
    class Array:
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
        array_id: None | str = field(
            default=None,
            metadata={
                "name": "arrayId",
                "type": "Attribute",
            },
        )
        id: None | str = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.w3.org/XML/1998/namespace",
            },
        )

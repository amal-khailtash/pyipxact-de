from __future__ import annotations

from dataclasses import dataclass, field

from org.accellera.ipxact.v1685_2022.indices import Indices
from org.accellera.ipxact.v1685_2022.range import Range

__NAMESPACE__ = "http://www.accellera.org/XMLSchema/IPXACT/1685-2022"


@dataclass(slots=True, kw_only=True)
class PartSelect:
    """
    Bit range definition.
    """

    class Meta:
        name = "partSelect"
        namespace = "http://www.accellera.org/XMLSchema/IPXACT/1685-2022"

    range_or_indices: None | Range | Indices = field(
        default=None,
        metadata={
            "type": "Elements",
            "choices": (
                {
                    "name": "range",
                    "type": Range,
                },
                {
                    "name": "indices",
                    "type": Indices,
                },
            ),
        },
    )
    id: None | str = field(
        default=None,
        metadata={
            "type": "Attribute",
            "namespace": "http://www.w3.org/XML/1998/namespace",
        },
    )

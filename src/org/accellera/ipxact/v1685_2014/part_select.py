from __future__ import annotations

from dataclasses import dataclass, field

from org.accellera.ipxact.v1685_2014.indices_type import IndicesType
from org.accellera.ipxact.v1685_2014.range import Range

__NAMESPACE__ = "http://www.accellera.org/XMLSchema/IPXACT/1685-2014"


@dataclass(slots=True, kw_only=True)
class PartSelect:
    """
    Bit range definition.
    """

    class Meta:
        name = "partSelect"
        namespace = "http://www.accellera.org/XMLSchema/IPXACT/1685-2014"

    range_or_indices: None | Range | IndicesType = field(
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
                    "type": IndicesType,
                },
            ),
        },
    )

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from org.accellera.ipxact.v1685_2014.unsigned_int_expression import (
    UnsignedIntExpression,
)

__NAMESPACE__ = "http://www.accellera.org/XMLSchema/IPXACT/1685-2014"


@dataclass(slots=True, kw_only=True)
class IndicesType:
    """
    :ivar index: An index into an object in the referenced view.
    """

    class Meta:
        name = "indicesType"

    index: Sequence[UnsignedIntExpression] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2014",
            "min_occurs": 1,
        },
    )

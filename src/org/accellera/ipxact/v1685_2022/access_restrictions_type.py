from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from org.accellera.ipxact.v1685_2022.access_restriction_type import (
    AccessRestrictionType,
)

__NAMESPACE__ = "http://www.accellera.org/XMLSchema/IPXACT/1685-2022"


@dataclass(slots=True, kw_only=True)
class AccessRestrictionsType:
    """
    :ivar access_restriction: Access mode.
    """

    class Meta:
        name = "accessRestrictionsType"

    access_restriction: Sequence[AccessRestrictionType] = field(
        default_factory=list,
        metadata={
            "name": "accessRestriction",
            "type": "Element",
            "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
            "min_occurs": 1,
        },
    )

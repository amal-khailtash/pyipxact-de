from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from org.accellera.ipxact.v1685_2022.trans_type_def import TransTypeDef

__NAMESPACE__ = "http://www.accellera.org/XMLSchema/IPXACT/1685-2022"


@dataclass(slots=True, kw_only=True)
class TransTypeDefs:
    """
    The group of transactional type definitions.

    If no match to a viewName is found then the default language types are
    to be used. See the User Guide for these default types.
    """

    class Meta:
        name = "transTypeDefs"
        namespace = "http://www.accellera.org/XMLSchema/IPXACT/1685-2022"

    trans_type_def: Sequence[TransTypeDef] = field(
        default_factory=list,
        metadata={
            "name": "transTypeDef",
            "type": "Element",
            "min_occurs": 1,
        },
    )

from __future__ import annotations

from dataclasses import dataclass, field

from org.accellera.spirit.v1685_2009.ve.power.name_ref_vector_pairs import (
    NameRefVectorPairs,
)
from org.accellera.spirit.v1685_2009.ve.power.vector import Vector

__NAMESPACE__ = (
    "http://www.accellera.org/XMLSchema/SPIRIT/1685-2009-VE/PDP-1.0"
)


@dataclass(slots=True, kw_only=True)
class CombinationalPathDef:
    class Meta:
        name = "combinationalPathDef"

    vector: None | Vector = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
        },
    )
    sources: NameRefVectorPairs = field(
        metadata={
            "type": "Element",
            "namespace": "http://www.accellera.org/XMLSchema/SPIRIT/1685-2009-VE/PDP-1.0",
        }
    )

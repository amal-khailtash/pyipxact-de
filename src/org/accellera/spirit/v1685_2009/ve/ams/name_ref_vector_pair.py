from __future__ import annotations

from dataclasses import dataclass, field

from org.accellera.spirit.v1685_2009.ve.ams.name_ref import NameRef
from org.accellera.spirit.v1685_2009.ve.ams.vector import Vector

__NAMESPACE__ = (
    "http://www.accellera.org/XMLSchema/SPIRIT/1685-2009-VE/PDP-1.0"
)


@dataclass(slots=True, kw_only=True)
class NameRefVectorPair:
    class Meta:
        name = "nameRefVectorPair"

    name_ref: NameRef = field(
        metadata={
            "name": "nameRef",
            "type": "Element",
            "namespace": "http://www.accellera.org/XMLSchema/SPIRIT/1685-2009-VE",
        }
    )
    vector: None | Vector = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
        },
    )

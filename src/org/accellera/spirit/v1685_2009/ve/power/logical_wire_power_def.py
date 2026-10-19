from __future__ import annotations

from dataclasses import dataclass, field

from org.accellera.spirit.v1685_2009.ve.power.domain import Domain
from org.accellera.spirit.v1685_2009.ve.power.idle import Idle
from org.accellera.spirit.v1685_2009.ve.power.isolation import Isolation
from org.accellera.spirit.v1685_2009.ve.power.reset import Reset
from org.accellera.spirit.v1685_2009.ve.power.vector import Vector

__NAMESPACE__ = (
    "http://www.accellera.org/XMLSchema/SPIRIT/1685-2009-VE/POWER-1.0"
)


@dataclass(slots=True, kw_only=True)
class LogicalWirePowerDef:
    """
    Logical wire port power definition.
    """

    class Meta:
        name = "logicalWirePowerDef"
        namespace = (
            "http://www.accellera.org/XMLSchema/SPIRIT/1685-2009-VE/POWER-1.0"
        )

    domain: None | Domain = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    isolation: None | Isolation = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    idle: None | Idle = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    reset: None | Reset = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    vector: None | Vector = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
        },
    )

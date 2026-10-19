from __future__ import annotations

from dataclasses import dataclass, field

from org.accellera.spirit.v1685_2009.ve.ams.domain import Domain
from org.accellera.spirit.v1685_2009.ve.ams.has_isolation import HasIsolation
from org.accellera.spirit.v1685_2009.ve.ams.has_level_shifter import (
    HasLevelShifter,
)
from org.accellera.spirit.v1685_2009.ve.ams.idle import Idle
from org.accellera.spirit.v1685_2009.ve.ams.isolation import Isolation
from org.accellera.spirit.v1685_2009.ve.ams.name_ref import NameRef
from org.accellera.spirit.v1685_2009.ve.ams.reset import Reset
from org.accellera.spirit.v1685_2009.ve.ams.vector import Vector

__NAMESPACE__ = (
    "http://www.accellera.org/XMLSchema/SPIRIT/1685-2009-VE/POWER-1.0"
)


@dataclass(slots=True, kw_only=True)
class WireInstancePowerDef:
    """
    Component instance wire port power definition.
    """

    class Meta:
        name = "wireInstancePowerDef"
        namespace = (
            "http://www.accellera.org/XMLSchema/SPIRIT/1685-2009-VE/POWER-1.0"
        )

    name_ref: NameRef = field(
        metadata={
            "name": "nameRef",
            "type": "Element",
            "namespace": "http://www.accellera.org/XMLSchema/SPIRIT/1685-2009-VE",
        }
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
    has_isolation: None | HasIsolation = field(
        default=None,
        metadata={
            "name": "hasIsolation",
            "type": "Element",
        },
    )
    has_level_shifter: None | HasLevelShifter = field(
        default=None,
        metadata={
            "name": "hasLevelShifter",
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

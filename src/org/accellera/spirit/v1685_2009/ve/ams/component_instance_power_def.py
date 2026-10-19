from __future__ import annotations

from dataclasses import dataclass, field

from org.accellera.spirit.v1685_2009.ve.ams.always_powered import AlwaysPowered
from org.accellera.spirit.v1685_2009.ve.ams.domain import Domain
from org.accellera.spirit.v1685_2009.ve.ams.has_isolation import HasIsolation
from org.accellera.spirit.v1685_2009.ve.ams.has_level_shifter import (
    HasLevelShifter,
)
from org.accellera.spirit.v1685_2009.ve.ams.idle import Idle
from org.accellera.spirit.v1685_2009.ve.ams.isolation import Isolation
from org.accellera.spirit.v1685_2009.ve.ams.reset import Reset
from org.accellera.spirit.v1685_2009.ve.ams.retention_mode import RetentionMode

__NAMESPACE__ = (
    "http://www.accellera.org/XMLSchema/SPIRIT/1685-2009-VE/POWER-1.0"
)


@dataclass(slots=True, kw_only=True)
class ComponentInstancePowerDef:
    """
    Component instance power definition.
    """

    class Meta:
        name = "componentInstancePowerDef"
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
    retention_mode: None | RetentionMode = field(
        default=None,
        metadata={
            "name": "retentionMode",
            "type": "Element",
        },
    )
    always_powered: None | AlwaysPowered = field(
        default=None,
        metadata={
            "name": "alwaysPowered",
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

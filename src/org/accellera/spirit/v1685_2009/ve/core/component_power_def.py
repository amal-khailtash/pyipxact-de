from __future__ import annotations

from dataclasses import dataclass, field

from org.accellera.spirit.v1685_2009.ve.core.always_powered import (
    AlwaysPowered,
)
from org.accellera.spirit.v1685_2009.ve.core.domain import Domain
from org.accellera.spirit.v1685_2009.ve.core.has_isolation import HasIsolation
from org.accellera.spirit.v1685_2009.ve.core.has_level_shifter import (
    HasLevelShifter,
)
from org.accellera.spirit.v1685_2009.ve.core.idle import Idle
from org.accellera.spirit.v1685_2009.ve.core.isolation import Isolation
from org.accellera.spirit.v1685_2009.ve.core.reset import Reset
from org.accellera.spirit.v1685_2009.ve.core.retention_mode import (
    RetentionMode,
)

__NAMESPACE__ = (
    "http://www.accellera.org/XMLSchema/SPIRIT/1685-2009-VE/POWER-1.0"
)


@dataclass(slots=True, kw_only=True)
class ComponentPowerDef:
    """
    Power definition of a component.
    """

    class Meta:
        name = "componentPowerDef"
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

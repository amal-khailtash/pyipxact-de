from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from org.accellera.spirit.v1685_2009.ve.pdp.wire_instance_power_def import (
    WireInstancePowerDef,
)

__NAMESPACE__ = (
    "http://www.accellera.org/XMLSchema/SPIRIT/1685-2009-VE/POWER-1.0"
)


@dataclass(slots=True, kw_only=True)
class WireInstancePowerDefs:
    """
    Component instance wire port power definitions.

    :ivar wire_instance_power_def: Single wire port power definition.
    """

    class Meta:
        name = "wireInstancePowerDefs"
        namespace = (
            "http://www.accellera.org/XMLSchema/SPIRIT/1685-2009-VE/POWER-1.0"
        )

    wire_instance_power_def: Sequence[WireInstancePowerDef] = field(
        default_factory=list,
        metadata={
            "name": "wireInstancePowerDef",
            "type": "Element",
            "min_occurs": 1,
        },
    )

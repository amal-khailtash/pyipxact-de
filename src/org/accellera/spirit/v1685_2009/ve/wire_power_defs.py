from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from org.accellera.spirit.v1685_2009.ve.wire_power_def import WirePowerDef

__NAMESPACE__ = (
    "http://www.accellera.org/XMLSchema/SPIRIT/1685-2009-VE/POWER-1.0"
)


@dataclass(slots=True, kw_only=True)
class WirePowerDefs:
    """
    Wire port power definitions.

    :ivar wire_power_def: Single wire port power definition.
    """

    class Meta:
        name = "wirePowerDefs"
        namespace = (
            "http://www.accellera.org/XMLSchema/SPIRIT/1685-2009-VE/POWER-1.0"
        )

    wire_power_def: Sequence[WirePowerDef] = field(
        default_factory=list,
        metadata={
            "name": "wirePowerDef",
            "type": "Element",
            "min_occurs": 1,
        },
    )

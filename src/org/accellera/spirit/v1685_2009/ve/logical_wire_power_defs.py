from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from org.accellera.spirit.v1685_2009.ve.logical_wire_power_def import (
    LogicalWirePowerDef,
)

__NAMESPACE__ = (
    "http://www.accellera.org/XMLSchema/SPIRIT/1685-2009-VE/POWER-1.0"
)


@dataclass(slots=True, kw_only=True)
class LogicalWirePowerDefs:
    """
    Logical wire port power definitions.

    :ivar logical_wire_power_def: Single logical wire port power
        definition.
    """

    class Meta:
        name = "logicalWirePowerDefs"
        namespace = (
            "http://www.accellera.org/XMLSchema/SPIRIT/1685-2009-VE/POWER-1.0"
        )

    logical_wire_power_def: Sequence[LogicalWirePowerDef] = field(
        default_factory=list,
        metadata={
            "name": "logicalWirePowerDef",
            "type": "Element",
            "min_occurs": 1,
        },
    )

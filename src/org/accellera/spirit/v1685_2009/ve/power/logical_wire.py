from __future__ import annotations

from dataclasses import dataclass, field

from org.accellera.spirit.v1685_2009.ve.power.logical_wire_power_defs import (
    LogicalWirePowerDefs,
)

__NAMESPACE__ = "http://www.accellera.org/XMLSchema/SPIRIT/1685-2009-VE"


@dataclass(slots=True, kw_only=True)
class LogicalWire:
    """
    Logical wire extension.
    """

    class Meta:
        name = "logicalWire"
        namespace = "http://www.accellera.org/XMLSchema/SPIRIT/1685-2009-VE"

    logical_wire_power_defs: None | LogicalWirePowerDefs = field(
        default=None,
        metadata={
            "name": "logicalWirePowerDefs",
            "type": "Element",
            "namespace": "http://www.accellera.org/XMLSchema/SPIRIT/1685-2009-VE/POWER-1.0",
        },
    )

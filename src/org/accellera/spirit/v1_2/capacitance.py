from __future__ import annotations

from dataclasses import dataclass, field

from org.accellera.spirit.v1_2.capacitance_value_unit_type import (
    CapacitanceValueUnitType,
)

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2"


@dataclass(slots=True, kw_only=True)
class Capacitance:
    """
    Represents a simple capacitance value with optional units.
    """

    class Meta:
        name = "capacitance"

    value: float = field(
        metadata={
            "min_inclusive": 0.0,
        }
    )
    units: None | CapacitanceValueUnitType = field(
        default=None,
        metadata={
            "type": "Attribute",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2",
        },
    )

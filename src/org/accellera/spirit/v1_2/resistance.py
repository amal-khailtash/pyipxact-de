from __future__ import annotations

from dataclasses import dataclass, field

from org.accellera.spirit.v1_2.resistance_value_unit_type import (
    ResistanceValueUnitType,
)

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2"


@dataclass(slots=True, kw_only=True)
class Resistance:
    """
    Represents a simple resistance value with optional units.
    """

    class Meta:
        name = "resistance"

    value: float = field(
        metadata={
            "min_inclusive": 0.0,
        }
    )
    units: None | ResistanceValueUnitType = field(
        default=None,
        metadata={
            "type": "Attribute",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2",
        },
    )

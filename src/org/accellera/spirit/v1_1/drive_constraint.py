from __future__ import annotations

from dataclasses import dataclass, field

from org.accellera.spirit.v1_1.cell_specification import CellSpecification
from org.accellera.spirit.v1_1.resistance import Resistance

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.1"


@dataclass(slots=True, kw_only=True)
class DriveConstraint:
    """
    Defines a constraint indicating how an input is to be driven.

    The preferred methodology is to specify a library cell in technology
    independent fashion. The implemention tool should assume that the
    associated signal is driven by the specified cell, or that the drive
    strength of the input signal is indicated by the specified resistance
    value.
    """

    class Meta:
        name = "driveConstraint"
        namespace = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.1"

    cell_specification_or_resistance: None | CellSpecification | Resistance = (
        field(
            default=None,
            metadata={
                "type": "Elements",
                "choices": (
                    {
                        "name": "cellSpecification",
                        "type": CellSpecification,
                    },
                    {
                        "name": "resistance",
                        "type": Resistance,
                    },
                ),
            },
        )
    )

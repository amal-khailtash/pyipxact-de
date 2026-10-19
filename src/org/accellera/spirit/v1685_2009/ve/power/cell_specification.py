from __future__ import annotations

from dataclasses import dataclass, field
from typing import ForwardRef

from org.accellera.spirit.v1685_2009.ve.power.cell_class_value_type import (
    CellClassValueType,
)
from org.accellera.spirit.v1685_2009.ve.power.cell_function_value_type import (
    CellFunctionValueType,
)
from org.accellera.spirit.v1685_2009.ve.power.cell_strength_value_type import (
    CellStrengthValueType,
)

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009"


@dataclass(slots=True, kw_only=True)
class CellSpecification:
    """
    Used to provide a generic description of a technology library cell.
    """

    class Meta:
        name = "cellSpecification"
        namespace = (
            "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009"
        )

    cell_function_or_cell_class: (
        None | CellSpecification.CellFunction | CellSpecification.CellClass
    ) = field(
        default=None,
        metadata={
            "type": "Elements",
            "choices": (
                {
                    "name": "cellFunction",
                    "type": ForwardRef("CellSpecification.CellFunction"),
                },
                {
                    "name": "cellClass",
                    "type": ForwardRef("CellSpecification.CellClass"),
                },
            ),
        },
    )

    @dataclass(slots=True, kw_only=True)
    class CellFunction:
        value: CellFunctionValueType = field()
        cell_strength: None | CellStrengthValueType = field(
            default=None,
            metadata={
                "name": "cellStrength",
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
            },
        )

    @dataclass(slots=True, kw_only=True)
    class CellClass:
        value: CellClassValueType = field()
        cell_strength: None | CellStrengthValueType = field(
            default=None,
            metadata={
                "name": "cellStrength",
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
            },
        )

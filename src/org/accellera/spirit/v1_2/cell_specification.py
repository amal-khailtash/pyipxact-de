from __future__ import annotations

from dataclasses import dataclass, field
from typing import ForwardRef

from org.accellera.spirit.v1_2.cell_class_value_type import CellClassValueType
from org.accellera.spirit.v1_2.cell_function_value_type import (
    CellFunctionValueType,
)
from org.accellera.spirit.v1_2.cell_strength_value_type import (
    CellStrengthValueType,
)

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2"


@dataclass(slots=True, kw_only=True)
class CellSpecification:
    """
    Used to indicate a particular technology library cell.

    Use of cellName is discouraged since it is technology dependent.
    """

    class Meta:
        name = "cellSpecification"
        namespace = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2"

    cell_function_or_cell_class_or_cell_name: (
        None
        | CellSpecification.CellFunction
        | CellSpecification.CellClass
        | CellSpecification.CellName
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
                {
                    "name": "cellName",
                    "type": ForwardRef("CellSpecification.CellName"),
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
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2",
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
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2",
            },
        )

    @dataclass(slots=True, kw_only=True)
    class CellName:
        lib_cell_name: str = field(
            metadata={
                "name": "libCellName",
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2",
            }
        )
        lib_pin_name: None | str = field(
            default=None,
            metadata={
                "name": "libPinName",
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2",
            },
        )

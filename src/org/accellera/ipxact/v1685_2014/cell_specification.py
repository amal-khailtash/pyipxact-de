from __future__ import annotations

from dataclasses import dataclass, field
from typing import ForwardRef

from org.accellera.ipxact.v1685_2014.cell_class_value_type import (
    CellClassValueType,
)
from org.accellera.ipxact.v1685_2014.cell_function_value_type import (
    CellFunctionValueType,
)
from org.accellera.ipxact.v1685_2014.cell_strength_value_type import (
    CellStrengthValueType,
)

__NAMESPACE__ = "http://www.accellera.org/XMLSchema/IPXACT/1685-2014"


@dataclass(slots=True, kw_only=True)
class CellSpecification:
    """
    Used to provide a generic description of a technology library cell.

    :ivar cell_function_or_cell_class:
    :ivar cell_strength: Indicates the desired strength of the specified
        cell.
    """

    class Meta:
        name = "cellSpecification"
        namespace = "http://www.accellera.org/XMLSchema/IPXACT/1685-2014"

    cell_function_or_cell_class: (
        None | CellSpecification.CellFunction | CellClassValueType
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
                    "type": CellClassValueType,
                },
            ),
        },
    )
    cell_strength: None | CellStrengthValueType = field(
        default=None,
        metadata={
            "name": "cellStrength",
            "type": "Attribute",
        },
    )

    @dataclass(slots=True, kw_only=True)
    class CellFunction:
        value: CellFunctionValueType = field()
        other: None | str = field(
            default=None,
            metadata={
                "type": "Attribute",
            },
        )

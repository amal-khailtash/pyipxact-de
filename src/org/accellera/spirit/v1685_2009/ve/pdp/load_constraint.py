from __future__ import annotations

from dataclasses import dataclass, field

from org.accellera.spirit.v1685_2009.ve.pdp.cell_specification import (
    CellSpecification,
)

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009"


@dataclass(slots=True, kw_only=True)
class LoadConstraint:
    """
    Defines a constraint indicating the type of load on an output port.

    :ivar cell_specification:
    :ivar count: Indicates how many loads of the specified cell are
        connected. If not present, 3 is assumed.
    """

    class Meta:
        name = "loadConstraint"
        namespace = (
            "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009"
        )

    cell_specification: CellSpecification = field(
        metadata={
            "name": "cellSpecification",
            "type": "Element",
        }
    )
    count: None | int = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )

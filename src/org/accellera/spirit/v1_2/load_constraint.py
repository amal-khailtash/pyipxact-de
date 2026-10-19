from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from org.accellera.spirit.v1_2.capacitance import Capacitance
from org.accellera.spirit.v1_2.cell_specification import CellSpecification

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2"


@dataclass(slots=True, kw_only=True)
class LoadConstraint:
    """
    Defines a constraint indicating the type of load on an output signal.
    """

    class Meta:
        name = "loadConstraint"
        namespace = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2"

    cell_specification_or_count_or_capacitance: Sequence[
        CellSpecification | int | Capacitance
    ] = field(
        default_factory=list,
        metadata={
            "type": "Elements",
            "choices": (
                {
                    "name": "cellSpecification",
                    "type": CellSpecification,
                },
                {
                    "name": "count",
                    "type": int,
                },
                {
                    "name": "capacitance",
                    "type": Capacitance,
                },
            ),
            "max_occurs": 2,
        },
    )

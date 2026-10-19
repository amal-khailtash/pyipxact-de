from __future__ import annotations

from dataclasses import dataclass, field

from org.accellera.spirit.v1685_2009.ve.ams.delay_value_type import (
    DelayValueType,
)
from org.accellera.spirit.v1685_2009.ve.ams.edge_value_type import (
    EdgeValueType,
)

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009"


@dataclass(slots=True, kw_only=True)
class TimingConstraint:
    """
    Defines a timing constraint for the associated port.

    The constraint is relative to the clock specified by the clockName
    attribute. The clockEdge indicates which clock edge the constraint is
    associated with (default is rising edge). The delayType attribute can
    be specified to further refine the constraint.

    :ivar value:
    :ivar clock_edge:
    :ivar delay_type:
    :ivar clock_name: Indicates the name of the clock to which this
        constraint applies.
    """

    class Meta:
        name = "timingConstraint"
        namespace = (
            "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009"
        )

    value: float = field(
        metadata={
            "min_inclusive": 0.0,
            "max_inclusive": 100.0,
        }
    )
    clock_edge: EdgeValueType = field(
        default=EdgeValueType.RISE,
        metadata={
            "name": "clockEdge",
            "type": "Attribute",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
        },
    )
    delay_type: None | DelayValueType = field(
        default=None,
        metadata={
            "name": "delayType",
            "type": "Attribute",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
        },
    )
    clock_name: str = field(
        metadata={
            "name": "clockName",
            "type": "Attribute",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
            "white_space": "collapse",
            "pattern": r"\i[\p{L}\p{N}\.\-:_]*",
        }
    )

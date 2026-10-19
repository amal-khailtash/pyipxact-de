from __future__ import annotations

from dataclasses import dataclass, field

from org.accellera.spirit.v1_2.delay import Delay
from org.accellera.spirit.v1_2.delay_value_type import DelayValueType
from org.accellera.spirit.v1_2.edge_value_type import EdgeValueType

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2"


@dataclass(slots=True, kw_only=True)
class TimingConstraint:
    """
    Defines a timing constraint for the associated signal.

    The constraint is relative to the clock specified by the clockName
    attribute. The clockEdge indicates which clock edge the constraint is
    associated with (default is rising edge). The delayType attribute can
    be specified to further refine the constraint.
    """

    class Meta:
        name = "timingConstraint"
        namespace = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2"

    percent_of_period_or_delay: None | float | Delay = field(
        default=None,
        metadata={
            "type": "Elements",
            "choices": (
                {
                    "name": "percentOfPeriod",
                    "type": float,
                    "min_inclusive": 0.0,
                    "max_inclusive": 100.0,
                },
                {
                    "name": "delay",
                    "type": Delay,
                },
            ),
        },
    )
    clock_edge: None | EdgeValueType = field(
        default=None,
        metadata={
            "name": "clockEdge",
            "type": "Attribute",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2",
        },
    )
    delay_type: None | DelayValueType = field(
        default=None,
        metadata={
            "name": "delayType",
            "type": "Attribute",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2",
        },
    )
    clock_name: str = field(
        metadata={
            "name": "clockName",
            "type": "Attribute",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2",
        }
    )

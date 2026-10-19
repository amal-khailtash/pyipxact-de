from __future__ import annotations

from dataclasses import dataclass, field

from org.accellera.spirit.v1_2.delay import Delay
from org.accellera.spirit.v1_2.delay_value_type import DelayValueType
from org.accellera.spirit.v1_2.edge_value_type import EdgeValueType
from org.accellera.spirit.v1_2.path_specifier import PathSpecifier

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2"


@dataclass(slots=True, kw_only=True)
class TimedPath:
    """
    Defines a point-to-point timing exception.

    The pathEdge attribute can be used to restrict the constraint to rising
    or falling edges, and the delayType attribute can be used to restrict
    the constraint to imply a minimum path constraint or a maximum path
    constraint.
    """

    class Meta:
        name = "timedPath"
        namespace = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2"

    path_specifier: PathSpecifier = field(
        metadata={
            "name": "pathSpecifier",
            "type": "Element",
        }
    )
    delay: Delay = field(
        metadata={
            "type": "Element",
        }
    )
    path_edge: None | EdgeValueType = field(
        default=None,
        metadata={
            "name": "pathEdge",
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

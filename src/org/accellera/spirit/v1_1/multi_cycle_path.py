from __future__ import annotations

from dataclasses import dataclass, field

from org.accellera.spirit.v1_1.check_value_type import CheckValueType
from org.accellera.spirit.v1_1.edge_value_type import EdgeValueType
from org.accellera.spirit.v1_1.path_specifier import PathSpecifier
from org.accellera.spirit.v1_1.relative_clock_type import RelativeClockType

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.1"


@dataclass(slots=True, kw_only=True)
class MultiCyclePath:
    """
    Defines a multi-cycle path timing exception.
    """

    class Meta:
        name = "multiCyclePath"
        namespace = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.1"

    path_specifier: PathSpecifier = field(
        metadata={
            "name": "pathSpecifier",
            "type": "Element",
        }
    )
    cycles: int = field(
        metadata={
            "type": "Element",
        }
    )
    path_edge: None | EdgeValueType = field(
        default=None,
        metadata={
            "name": "pathEdge",
            "type": "Attribute",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.1",
        },
    )
    path_type: None | CheckValueType = field(
        default=None,
        metadata={
            "name": "pathType",
            "type": "Attribute",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.1",
        },
    )
    relative_clock: None | RelativeClockType = field(
        default=None,
        metadata={
            "name": "relativeClock",
            "type": "Attribute",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.1",
        },
    )

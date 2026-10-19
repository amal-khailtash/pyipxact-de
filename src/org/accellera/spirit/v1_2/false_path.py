from __future__ import annotations

from dataclasses import dataclass, field

from org.accellera.spirit.v1_2.check_value_type import CheckValueType
from org.accellera.spirit.v1_2.edge_value_type import EdgeValueType
from org.accellera.spirit.v1_2.path_specifier import PathSpecifier

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2"


@dataclass(slots=True, kw_only=True)
class FalsePath:
    """
    Defines a false path timing exception.
    """

    class Meta:
        name = "falsePath"
        namespace = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2"

    path_specifier: PathSpecifier = field(
        metadata={
            "name": "pathSpecifier",
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
    path_type: None | CheckValueType = field(
        default=None,
        metadata={
            "name": "pathType",
            "type": "Attribute",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2",
        },
    )

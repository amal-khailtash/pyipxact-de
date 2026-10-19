from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from org.accellera.spirit.v1685_2009.ve.power.wire_type_def import WireTypeDef

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009"


@dataclass(slots=True, kw_only=True)
class WireTypeDefs:
    """
    The group of wire type definitions.

    If no match to a viewName is found then the default language types are
    to be used. See the User Guide for these default types.
    """

    class Meta:
        name = "wireTypeDefs"
        namespace = (
            "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009"
        )

    wire_type_def: Sequence[WireTypeDef] = field(
        default_factory=list,
        metadata={
            "name": "wireTypeDef",
            "type": "Element",
            "min_occurs": 1,
        },
    )

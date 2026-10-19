from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from org.accellera.spirit.v1_0.interconnection import Interconnection

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0"


@dataclass(slots=True, kw_only=True)
class Interconnections:
    """
    Connections between internal sub components.
    """

    class Meta:
        name = "interconnections"
        namespace = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0"

    interconnection: Sequence[Interconnection] = field(
        default_factory=list,
        metadata={
            "type": "Element",
        },
    )

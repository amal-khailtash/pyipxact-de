from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from org.accellera.spirit.v1685_2009.interconnection import Interconnection
from org.accellera.spirit.v1685_2009.monitor_interconnection import (
    MonitorInterconnection,
)

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009"


@dataclass(slots=True, kw_only=True)
class Interconnections:
    """
    Connections between internal sub components.
    """

    class Meta:
        name = "interconnections"
        namespace = (
            "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009"
        )

    interconnection: Sequence[Interconnection] = field(
        default_factory=list,
        metadata={
            "type": "Element",
        },
    )
    monitor_interconnection: Sequence[MonitorInterconnection] = field(
        default_factory=list,
        metadata={
            "name": "monitorInterconnection",
            "type": "Element",
        },
    )

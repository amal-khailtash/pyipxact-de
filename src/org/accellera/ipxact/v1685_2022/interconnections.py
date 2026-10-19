from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from org.accellera.ipxact.v1685_2022.interconnection import Interconnection
from org.accellera.ipxact.v1685_2022.monitor_interconnection import (
    MonitorInterconnection,
)

__NAMESPACE__ = "http://www.accellera.org/XMLSchema/IPXACT/1685-2022"


@dataclass(slots=True, kw_only=True)
class Interconnections:
    """
    Connections between internal sub components.
    """

    class Meta:
        name = "interconnections"
        namespace = "http://www.accellera.org/XMLSchema/IPXACT/1685-2022"

    interconnection_or_monitor_interconnection: Sequence[
        Interconnection | MonitorInterconnection
    ] = field(
        default_factory=list,
        metadata={
            "type": "Elements",
            "choices": (
                {
                    "name": "interconnection",
                    "type": Interconnection,
                },
                {
                    "name": "monitorInterconnection",
                    "type": MonitorInterconnection,
                },
            ),
        },
    )

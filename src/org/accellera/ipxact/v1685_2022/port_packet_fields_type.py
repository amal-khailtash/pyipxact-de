from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from org.accellera.ipxact.v1685_2022.port_packet_field_type import (
    PortPacketFieldType,
)

__NAMESPACE__ = "http://www.accellera.org/XMLSchema/IPXACT/1685-2022"


@dataclass(slots=True, kw_only=True)
class PortPacketFieldsType:
    class Meta:
        name = "portPacketFieldsType"

    packet_field: Sequence[PortPacketFieldType] = field(
        default_factory=list,
        metadata={
            "name": "packetField",
            "type": "Element",
            "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
            "min_occurs": 1,
        },
    )

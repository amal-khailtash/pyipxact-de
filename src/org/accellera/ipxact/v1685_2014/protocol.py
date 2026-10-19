from __future__ import annotations

from dataclasses import dataclass, field

from org.accellera.ipxact.v1685_2014.payload import Payload
from org.accellera.ipxact.v1685_2014.protocol_type_type import ProtocolTypeType

__NAMESPACE__ = "http://www.accellera.org/XMLSchema/IPXACT/1685-2014"


@dataclass(slots=True, kw_only=True)
class Protocol:
    """
    defines the protocol type.

    Defaults to tlm_base_protocol_type for TLM sockets.
    """

    class Meta:
        name = "protocol"
        namespace = "http://www.accellera.org/XMLSchema/IPXACT/1685-2014"

    protocol_type: Protocol.ProtocolType = field(
        metadata={
            "name": "protocolType",
            "type": "Element",
        }
    )
    payload: None | Payload = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )

    @dataclass(slots=True, kw_only=True)
    class ProtocolType:
        value: ProtocolTypeType = field()
        custom: None | str = field(
            default=None,
            metadata={
                "type": "Attribute",
            },
        )

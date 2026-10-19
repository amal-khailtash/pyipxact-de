from __future__ import annotations

from dataclasses import dataclass, field

from org.accellera.ipxact.v1685_2022.kind_type import KindType

__NAMESPACE__ = "http://www.accellera.org/XMLSchema/IPXACT/1685-2022"


@dataclass(slots=True, kw_only=True)
class Kind:
    """
    Defines the protocol type.

    Defaults to tlm_base_protocol_type for TLM sockets.
    """

    class Meta:
        name = "kind"
        namespace = "http://www.accellera.org/XMLSchema/IPXACT/1685-2022"

    value: KindType = field()
    custom: None | str = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )

from __future__ import annotations

from dataclasses import dataclass, field

from org.accellera.spirit.v1_5.description import Description
from org.accellera.spirit.v1_5.display_name import DisplayName
from org.accellera.spirit.v1_5.port_access_type_1 import PortAccessType1
from org.accellera.spirit.v1_5.port_transactional_type import (
    PortTransactionalType,
)
from org.accellera.spirit.v1_5.port_wire_type import PortWireType

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5"


@dataclass(slots=True, kw_only=True)
class PortDeclarationType:
    """
    Basic port declarations.

    :ivar name: Unique name
    :ivar display_name:
    :ivar description:
    :ivar wire_or_transactional:
    :ivar access: Port access characteristics.
    """

    class Meta:
        name = "portDeclarationType"

    name: str = field(
        metadata={
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
            "white_space": "collapse",
            "pattern": r"\i[\p{L}\p{N}\.\-:_]*",
        }
    )
    display_name: None | DisplayName = field(
        default=None,
        metadata={
            "name": "displayName",
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
        },
    )
    description: None | Description = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
        },
    )
    wire_or_transactional: None | PortWireType | PortTransactionalType = field(
        default=None,
        metadata={
            "type": "Elements",
            "choices": (
                {
                    "name": "wire",
                    "type": PortWireType,
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                },
                {
                    "name": "transactional",
                    "type": PortTransactionalType,
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                },
            ),
        },
    )
    access: None | PortAccessType1 = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
        },
    )

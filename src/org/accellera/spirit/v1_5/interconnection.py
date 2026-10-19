from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from org.accellera.spirit.v1_5.description import Description
from org.accellera.spirit.v1_5.display_name import DisplayName
from org.accellera.spirit.v1_5.interface import Interface

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5"


@dataclass(slots=True, kw_only=True)
class Interconnection:
    """
    Describes a connection between two active (not monitor) busInterfaces.

    :ivar name: Unique name
    :ivar display_name:
    :ivar description:
    :ivar active_interface: Describes one interface of the
        interconnection. The componentRef and busRef attributes indicate
        the instance name and bus interface name of one end of the
        connection.
    """

    class Meta:
        name = "interconnection"
        namespace = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5"

    name: str = field(
        metadata={
            "type": "Element",
        }
    )
    display_name: None | DisplayName = field(
        default=None,
        metadata={
            "name": "displayName",
            "type": "Element",
        },
    )
    description: None | Description = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    active_interface: Sequence[Interface] = field(
        default_factory=list,
        metadata={
            "name": "activeInterface",
            "type": "Element",
            "min_occurs": 2,
            "max_occurs": 2,
        },
    )

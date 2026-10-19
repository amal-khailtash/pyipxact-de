from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from org.accellera.spirit.v1_4.interface import Interface

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4"


@dataclass(slots=True, kw_only=True)
class Interconnection:
    """
    Describes a connection between two active (not monitor) busInterfaces.

    :ivar name: Unique name
    :ivar display_name: Element name for display purposes. Typically a
        few words providing a more detailed and/or user-friendly name
        than the spirit:name.
    :ivar description: Full description string, typically for
        documentation
    :ivar active_interface: Describes one interface of the
        interconnection. The componentRef and busRef attributes indicate
        the instance name and bus interface name of one end of the
        connection.
    """

    class Meta:
        name = "interconnection"
        namespace = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4"

    name: str = field(
        metadata={
            "type": "Element",
        }
    )
    display_name: None | str = field(
        default=None,
        metadata={
            "name": "displayName",
            "type": "Element",
        },
    )
    description: None | str = field(
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

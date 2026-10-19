from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4"


@dataclass(slots=True, kw_only=True)
class Channels:
    """
    Lists all channel connections between mirror interfaces of this
    component.

    :ivar channel: Defines a set of mirrored interfaces of this
        component that are connected to one another.
    """

    class Meta:
        name = "channels"
        namespace = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4"

    channel: Sequence[Channels.Channel] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "min_occurs": 1,
        },
    )

    @dataclass(slots=True, kw_only=True)
    class Channel:
        """
        :ivar name: Unique name
        :ivar display_name: Element name for display purposes. Typically
            a few words providing a more detailed and/or user-friendly
            name than the spirit:name.
        :ivar description: Full description string, typically for
            documentation
        :ivar bus_interface_ref: Contains the name of one of the bus
            interfaces that is part of this channel. The ordering of the
            references may be important to the design environment.
        """

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
        bus_interface_ref: Sequence[str] = field(
            default_factory=list,
            metadata={
                "name": "busInterfaceRef",
                "type": "Element",
                "min_occurs": 2,
            },
        )

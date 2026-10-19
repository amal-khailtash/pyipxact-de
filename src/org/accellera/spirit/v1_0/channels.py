from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0"


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
        namespace = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0"

    channel: Sequence[Channels.Channel] = field(
        default_factory=list,
        metadata={
            "type": "Element",
        },
    )

    @dataclass(slots=True, kw_only=True)
    class Channel:
        """
        :ivar max_masters: Overrides the maxMasters value in the bus
            definition if this number is more restrictive.
        :ivar max_slaves: Overrides the maxSlaves value in the bus
            definition if this number is more restrictive.
        :ivar bus_interface_ref: Contains the name of one of the bus
            interfaces that is part of this channel.
        """

        max_masters: None | int = field(
            default=None,
            metadata={
                "name": "maxMasters",
                "type": "Element",
            },
        )
        max_slaves: None | int = field(
            default=None,
            metadata={
                "name": "maxSlaves",
                "type": "Element",
            },
        )
        bus_interface_ref: Sequence[str] = field(
            default_factory=list,
            metadata={
                "name": "busInterfaceRef",
                "type": "Element",
            },
        )

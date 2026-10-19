from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from org.accellera.spirit.v1685_2009.ve.power.description import Description
from org.accellera.spirit.v1685_2009.ve.power.display_name import DisplayName

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009"


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
        namespace = (
            "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009"
        )

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
        :ivar display_name:
        :ivar description:
        :ivar bus_interface_ref: Contains the name of one of the bus
            interfaces that is part of this channel. The ordering of the
            references may be important to the design environment.
        """

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
        bus_interface_ref: Sequence[str] = field(
            default_factory=list,
            metadata={
                "name": "busInterfaceRef",
                "type": "Element",
                "min_occurs": 2,
            },
        )

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from org.accellera.ipxact.v1685_2014.description import Description
from org.accellera.ipxact.v1685_2014.display_name import DisplayName
from org.accellera.ipxact.v1685_2014.is_present import IsPresent

__NAMESPACE__ = "http://www.accellera.org/XMLSchema/IPXACT/1685-2014"


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
        namespace = "http://www.accellera.org/XMLSchema/IPXACT/1685-2014"

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
        :ivar is_present:
        :ivar bus_interface_ref: Contains the name of one of the bus
            interfaces that is part of this channel. The ordering of the
            references may be important to the design environment.
        :ivar id:
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
        is_present: None | IsPresent = field(
            default=None,
            metadata={
                "name": "isPresent",
                "type": "Element",
            },
        )
        bus_interface_ref: Sequence[Channels.Channel.BusInterfaceRef] = field(
            default_factory=list,
            metadata={
                "name": "busInterfaceRef",
                "type": "Element",
                "min_occurs": 2,
            },
        )
        id: None | str = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.w3.org/XML/1998/namespace",
            },
        )

        @dataclass(slots=True, kw_only=True)
        class BusInterfaceRef:
            local_name: str = field(
                metadata={
                    "name": "localName",
                    "type": "Element",
                }
            )
            is_present: None | IsPresent = field(
                default=None,
                metadata={
                    "name": "isPresent",
                    "type": "Element",
                },
            )
            id: None | str = field(
                default=None,
                metadata={
                    "type": "Attribute",
                    "namespace": "http://www.w3.org/XML/1998/namespace",
                },
            )

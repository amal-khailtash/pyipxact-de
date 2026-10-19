from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from org.accellera.spirit.v1_2.interface import Interface

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2"


@dataclass(slots=True, kw_only=True)
class MonitorInterconnection:
    """
    Describes a connection from the interface of one component to any
    number of monitor interfaces in the design through its child elements'
    attributes.

    The componentRef and busInterfaceRef attributes of each child interface
    element indicate the instance name and bus interface name of one end of
    the connection. An active interface can be connected to unlimited
    number of monitor interfaces.

    :ivar name: name of the connection
    :ivar active_interface:
    :ivar monitor_interface:
    """

    class Meta:
        name = "monitorInterconnection"
        namespace = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2"

    name: None | object = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    active_interface: Interface = field(
        metadata={
            "name": "activeInterface",
            "type": "Element",
        }
    )
    monitor_interface: Sequence[Interface] = field(
        default_factory=list,
        metadata={
            "name": "monitorInterface",
            "type": "Element",
            "min_occurs": 1,
        },
    )

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from org.accellera.ipxact.v1685_2014.description import Description
from org.accellera.ipxact.v1685_2014.display_name import DisplayName
from org.accellera.ipxact.v1685_2014.is_present import IsPresent
from org.accellera.ipxact.v1685_2014.monitor_interface_type import (
    MonitorInterfaceType,
)

__NAMESPACE__ = "http://www.accellera.org/XMLSchema/IPXACT/1685-2014"


@dataclass(slots=True, kw_only=True)
class MonitorInterconnection:
    """
    Describes a connection from the interface of one component to any
    number of monitor interfaces in the design.

    An active interface can be connected to unlimited number of monitor
    interfaces.

    :ivar name: Unique name
    :ivar display_name:
    :ivar description:
    :ivar is_present:
    :ivar monitored_active_interface: Describes an active interface of
        the design that all the monitors will be connected to. The
        componentRef and busRef attributes indicate the instance name
        and bus interface name. The optional path attribute indicates
        the hierarchical instance name path to the component.
    :ivar monitor_interface: Describes a list of monitor interfaces that
        are connected to the single active interface. The componentRef
        and busRef attributes indicate the instance name and bus
        interface name. The optional path attribute indicates the
        hierarchical instance name path to the component.
    """

    class Meta:
        name = "monitorInterconnection"
        namespace = "http://www.accellera.org/XMLSchema/IPXACT/1685-2014"

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
    monitored_active_interface: MonitorInterfaceType = field(
        metadata={
            "name": "monitoredActiveInterface",
            "type": "Element",
        }
    )
    monitor_interface: Sequence[MonitorInterconnection.MonitorInterface] = (
        field(
            default_factory=list,
            metadata={
                "name": "monitorInterface",
                "type": "Element",
                "min_occurs": 1,
            },
        )
    )

    @dataclass(slots=True, kw_only=True)
    class MonitorInterface(MonitorInterfaceType):
        is_present: None | IsPresent = field(
            default=None,
            metadata={
                "name": "isPresent",
                "type": "Element",
            },
        )

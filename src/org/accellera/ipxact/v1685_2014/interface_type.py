from __future__ import annotations

from dataclasses import dataclass, field

__NAMESPACE__ = "http://www.accellera.org/XMLSchema/IPXACT/1685-2014"


@dataclass(slots=True, kw_only=True)
class InterfaceType:
    """
    A representation of a component/bus interface relation; i.e. a bus
    interface belonging to a certain component.

    :ivar component_ref: Reference to a component instance name.
    :ivar bus_ref: Reference to the components  bus interface
    :ivar id:
    """

    class Meta:
        name = "interfaceType"

    component_ref: str = field(
        metadata={
            "name": "componentRef",
            "type": "Attribute",
        }
    )
    bus_ref: str = field(
        metadata={
            "name": "busRef",
            "type": "Attribute",
        }
    )
    id: None | str = field(
        default=None,
        metadata={
            "type": "Attribute",
            "namespace": "http://www.w3.org/XML/1998/namespace",
        },
    )

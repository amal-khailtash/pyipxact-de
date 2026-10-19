from __future__ import annotations

from dataclasses import dataclass, field

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009"


@dataclass(slots=True, kw_only=True)
class Interface:
    """
    A representation of a component/bus interface relation; i.e. a bus
    interface belonging to a certain component.

    :ivar component_ref: Reference to a component instance name.
    :ivar bus_ref: Reference to the components  bus interface
    """

    class Meta:
        name = "interface"

    component_ref: str = field(
        metadata={
            "name": "componentRef",
            "type": "Attribute",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
        }
    )
    bus_ref: str = field(
        metadata={
            "name": "busRef",
            "type": "Attribute",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
        }
    )

from __future__ import annotations

from dataclasses import dataclass, field

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2"


@dataclass(slots=True, kw_only=True)
class Interface:
    """
    A representation of a component/bus interface relation; i.e. a bus
    interface belonging to a certain component.
    """

    class Meta:
        name = "interface"

    component_ref: object = field(
        metadata={
            "name": "componentRef",
            "type": "Attribute",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2",
        }
    )
    bus_ref: object = field(
        metadata={
            "name": "busRef",
            "type": "Attribute",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2",
        }
    )

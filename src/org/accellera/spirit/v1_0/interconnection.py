from __future__ import annotations

from dataclasses import dataclass, field

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0"


@dataclass(slots=True, kw_only=True)
class Interconnection:
    """
    Describes a connection from the interace of one comonent to the
    interface of another component through its attributes.

    The component1Ref and busInterface1Ref attributes indicate the instance
    name and bus interface name of one end of the connection. The
    component2Ref and busInterface2Ref attributes indicate the instance
    name and bus interface name of the other end of he connection.
    """

    class Meta:
        name = "interconnection"
        namespace = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0"

    component1_ref: str = field(
        metadata={
            "name": "component1Ref",
            "type": "Attribute",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
        }
    )
    bus_interface1_ref: str = field(
        metadata={
            "name": "busInterface1Ref",
            "type": "Attribute",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
        }
    )
    component2_ref: str = field(
        metadata={
            "name": "component2Ref",
            "type": "Attribute",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
        }
    )
    bus_interface2_ref: str = field(
        metadata={
            "name": "busInterface2Ref",
            "type": "Attribute",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
        }
    )

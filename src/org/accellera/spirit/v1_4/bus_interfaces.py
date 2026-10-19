from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from org.accellera.spirit.v1_4.bus_interface import BusInterface

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4"


@dataclass(slots=True, kw_only=True)
class BusInterfaces:
    """
    A list of bus interfaces supported by this component.
    """

    class Meta:
        name = "busInterfaces"
        namespace = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4"

    bus_interface: Sequence[BusInterface] = field(
        default_factory=list,
        metadata={
            "name": "busInterface",
            "type": "Element",
            "min_occurs": 1,
        },
    )

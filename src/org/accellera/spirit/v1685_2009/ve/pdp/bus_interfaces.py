from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from org.accellera.spirit.v1685_2009.ve.pdp.bus_interface import BusInterface

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009"


@dataclass(slots=True, kw_only=True)
class BusInterfaces:
    """
    A list of bus interfaces supported by this component.
    """

    class Meta:
        name = "busInterfaces"
        namespace = (
            "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009"
        )

    bus_interface: Sequence[BusInterface] = field(
        default_factory=list,
        metadata={
            "name": "busInterface",
            "type": "Element",
            "min_occurs": 1,
        },
    )

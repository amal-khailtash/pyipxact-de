from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from org.accellera.ipxact.v1685_2022.bus_interface import BusInterface

__NAMESPACE__ = "http://www.accellera.org/XMLSchema/IPXACT/1685-2022"


@dataclass(slots=True, kw_only=True)
class BusInterfaces:
    """
    A list of bus interfaces supported by this component.
    """

    class Meta:
        name = "busInterfaces"
        namespace = "http://www.accellera.org/XMLSchema/IPXACT/1685-2022"

    bus_interface: Sequence[BusInterface] = field(
        default_factory=list,
        metadata={
            "name": "busInterface",
            "type": "Element",
            "min_occurs": 1,
        },
    )

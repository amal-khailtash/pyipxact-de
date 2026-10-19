from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from org.accellera.spirit.v1685_2009.ve.pdp.port_parameter import PortParameter

__NAMESPACE__ = (
    "http://www.accellera.org/XMLSchema/SPIRIT/1685-2009-VE/CORE-1.0"
)


@dataclass(slots=True, kw_only=True)
class PortParameters:
    """
    A collection of parameters.
    """

    class Meta:
        name = "portParameters"
        namespace = (
            "http://www.accellera.org/XMLSchema/SPIRIT/1685-2009-VE/CORE-1.0"
        )

    port_parameter: Sequence[PortParameter] = field(
        default_factory=list,
        metadata={
            "name": "portParameter",
            "type": "Element",
            "min_occurs": 1,
        },
    )

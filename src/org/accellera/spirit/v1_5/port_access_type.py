from __future__ import annotations

from dataclasses import dataclass, field

from org.accellera.spirit.v1_5.port_access_type_value import (
    PortAccessTypeValue,
)

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5"


@dataclass(slots=True, kw_only=True)
class PortAccessType:
    """
    Indicates how a netlister accesses a port. 'ref' means accessed by
    reference (default) and 'ptr' means accessed by pointer.
    """

    class Meta:
        name = "portAccessType"
        namespace = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5"

    value: PortAccessTypeValue = field()

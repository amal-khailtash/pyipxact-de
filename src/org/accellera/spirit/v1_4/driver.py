from __future__ import annotations

from dataclasses import dataclass

from org.accellera.spirit.v1_4.driver_type import DriverType

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4"


@dataclass(slots=True, kw_only=True)
class Driver(DriverType):
    """
    Wire port driver element.
    """

    class Meta:
        name = "driver"
        namespace = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4"

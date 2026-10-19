from __future__ import annotations

from dataclasses import dataclass

from org.accellera.spirit.v1685_2009.ve.driver_type import DriverType

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009"


@dataclass(slots=True, kw_only=True)
class Driver1(DriverType):
    """
    Wire port driver element.
    """

    class Meta:
        name = "driver"
        namespace = (
            "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009"
        )

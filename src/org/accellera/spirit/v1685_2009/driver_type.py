from __future__ import annotations

from dataclasses import dataclass, field

from org.accellera.spirit.v1685_2009.clock_driver import ClockDriver
from org.accellera.spirit.v1685_2009.default_value import DefaultValue
from org.accellera.spirit.v1685_2009.single_shot_driver import SingleShotDriver

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009"


@dataclass(slots=True, kw_only=True)
class DriverType:
    """
    Wire port driver type.
    """

    class Meta:
        name = "driverType"

    default_value_or_clock_driver_or_single_shot_driver: (
        None | DefaultValue | ClockDriver | SingleShotDriver
    ) = field(
        default=None,
        metadata={
            "type": "Elements",
            "choices": (
                {
                    "name": "defaultValue",
                    "type": DefaultValue,
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
                },
                {
                    "name": "clockDriver",
                    "type": ClockDriver,
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
                },
                {
                    "name": "singleShotDriver",
                    "type": SingleShotDriver,
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
                },
            ),
        },
    )

from __future__ import annotations

from dataclasses import dataclass, field

from org.accellera.ipxact.v1685_2014.clock_driver import ClockDriver
from org.accellera.ipxact.v1685_2014.default_value import DefaultValue
from org.accellera.ipxact.v1685_2014.range import Range
from org.accellera.ipxact.v1685_2014.single_shot_driver import SingleShotDriver

__NAMESPACE__ = "http://www.accellera.org/XMLSchema/IPXACT/1685-2014"


@dataclass(slots=True, kw_only=True)
class DriverType:
    """
    Wire port driver type.
    """

    class Meta:
        name = "driverType"

    range: None | Range = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2014",
        },
    )
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
                    "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2014",
                },
                {
                    "name": "clockDriver",
                    "type": ClockDriver,
                    "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2014",
                },
                {
                    "name": "singleShotDriver",
                    "type": SingleShotDriver,
                    "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2014",
                },
            ),
        },
    )

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from org.accellera.ipxact.v1685_2022.clock_driver import ClockDriver
from org.accellera.ipxact.v1685_2022.default_value import DefaultValue
from org.accellera.ipxact.v1685_2022.range import Range
from org.accellera.ipxact.v1685_2022.single_shot_driver import SingleShotDriver

__NAMESPACE__ = "http://www.accellera.org/XMLSchema/IPXACT/1685-2022"


@dataclass(slots=True, kw_only=True)
class DriverType:
    """
    Wire port driver type.

    :ivar range:
    :ivar view_ref: A reference to a view in the file for which this
        type applies.
    :ivar default_value_or_clock_driver_or_single_shot_driver:
    :ivar id:
    """

    class Meta:
        name = "driverType"

    range: None | Range = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
        },
    )
    view_ref: Sequence[DriverType.ViewRef] = field(
        default_factory=list,
        metadata={
            "name": "viewRef",
            "type": "Element",
            "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
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
                    "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
                },
                {
                    "name": "clockDriver",
                    "type": ClockDriver,
                    "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
                },
                {
                    "name": "singleShotDriver",
                    "type": SingleShotDriver,
                    "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
                },
            ),
        },
    )
    id: None | str = field(
        default=None,
        metadata={
            "type": "Attribute",
            "namespace": "http://www.w3.org/XML/1998/namespace",
        },
    )

    @dataclass(slots=True, kw_only=True)
    class ViewRef:
        value: str = field(default="")
        id: None | str = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.w3.org/XML/1998/namespace",
            },
        )

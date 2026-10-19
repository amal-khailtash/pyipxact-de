from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from org.accellera.spirit.v1685_2009.ve.core.combinational_paths import (
    CombinationalPaths,
)
from org.accellera.spirit.v1685_2009.ve.core.domain_type_defs import (
    DomainTypeDefs,
)
from org.accellera.spirit.v1685_2009.ve.core.driver_2 import Driver2
from org.accellera.spirit.v1685_2009.ve.core.register_count import (
    RegisterCount,
)
from org.accellera.spirit.v1685_2009.ve.core.signal_type_defs import (
    SignalTypeDefs,
)
from org.accellera.spirit.v1685_2009.ve.core.wire_power_defs import (
    WirePowerDefs,
)

__NAMESPACE__ = "http://www.accellera.org/XMLSchema/SPIRIT/1685-2009-VE"


@dataclass(slots=True, kw_only=True)
class Wire:
    """
    Wire port extension.
    """

    class Meta:
        name = "wire"
        namespace = "http://www.accellera.org/XMLSchema/SPIRIT/1685-2009-VE"

    driver: Sequence[Driver2] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.accellera.org/XMLSchema/SPIRIT/1685-2009-VE/CORE-1.0",
        },
    )
    domain_type_defs: None | DomainTypeDefs = field(
        default=None,
        metadata={
            "name": "domainTypeDefs",
            "type": "Element",
            "namespace": "http://www.accellera.org/XMLSchema/SPIRIT/1685-2009-VE/AMS-1.0",
        },
    )
    signal_type_defs: None | SignalTypeDefs = field(
        default=None,
        metadata={
            "name": "signalTypeDefs",
            "type": "Element",
            "namespace": "http://www.accellera.org/XMLSchema/SPIRIT/1685-2009-VE/AMS-1.0",
        },
    )
    register_count: None | RegisterCount = field(
        default=None,
        metadata={
            "name": "registerCount",
            "type": "Element",
            "namespace": "http://www.accellera.org/XMLSchema/SPIRIT/1685-2009-VE/PDP-1.0",
        },
    )
    combinational_paths: None | CombinationalPaths = field(
        default=None,
        metadata={
            "name": "combinationalPaths",
            "type": "Element",
            "namespace": "http://www.accellera.org/XMLSchema/SPIRIT/1685-2009-VE/PDP-1.0",
        },
    )
    wire_power_defs: None | WirePowerDefs = field(
        default=None,
        metadata={
            "name": "wirePowerDefs",
            "type": "Element",
            "namespace": "http://www.accellera.org/XMLSchema/SPIRIT/1685-2009-VE/POWER-1.0",
        },
    )

from __future__ import annotations

from dataclasses import dataclass, field

from org.accellera.ipxact.v1685_2022.ve.is_present import IsPresent

__NAMESPACE__ = "http://www.accellera.org/XMLSchema/IPXACT/1685-2022-VE"


@dataclass(slots=True, kw_only=True)
class HierInterface:
    """
    HierInterface isPresent extension.
    """

    class Meta:
        name = "hierInterface"
        namespace = "http://www.accellera.org/XMLSchema/IPXACT/1685-2022-VE"

    is_present: IsPresent = field(
        metadata={
            "name": "isPresent",
            "type": "Element",
            "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022-VE/COND-1.0",
        }
    )

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from org.accellera.ipxact.v1685_2014.leaf_access_handle import LeafAccessHandle
from org.accellera.ipxact.v1685_2014.port_access_type import PortAccessType

__NAMESPACE__ = "http://www.accellera.org/XMLSchema/IPXACT/1685-2014"


@dataclass(slots=True, kw_only=True)
class PortAccessType1:
    """
    :ivar port_access_type: Indicates how a netlister accesses a port.
        'ref' means accessed by reference (default) and 'ptr' means
        accessed through a pointer.
    :ivar access_handles:
    """

    class Meta:
        name = "portAccessType"

    port_access_type: None | PortAccessType = field(
        default=None,
        metadata={
            "name": "portAccessType",
            "type": "Element",
            "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2014",
        },
    )
    access_handles: None | PortAccessType1.AccessHandles = field(
        default=None,
        metadata={
            "name": "accessHandles",
            "type": "Element",
            "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2014",
        },
    )

    @dataclass(slots=True, kw_only=True)
    class AccessHandles:
        access_handle: Sequence[LeafAccessHandle] = field(
            default_factory=list,
            metadata={
                "name": "accessHandle",
                "type": "Element",
                "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2014",
                "min_occurs": 1,
            },
        )

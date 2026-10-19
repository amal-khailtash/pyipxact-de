from __future__ import annotations

from dataclasses import dataclass, field

from org.accellera.ipxact.v1685_2014.is_present import IsPresent
from org.accellera.ipxact.v1685_2014.part_select import PartSelect

__NAMESPACE__ = "http://www.accellera.org/XMLSchema/IPXACT/1685-2014"


@dataclass(slots=True, kw_only=True)
class ExternalPortReference:
    """
    :ivar is_present:
    :ivar part_select:
    :ivar port_ref: A port on the on the referenced component from
        componentRef.
    :ivar id:
    """

    class Meta:
        name = "externalPortReference"
        namespace = "http://www.accellera.org/XMLSchema/IPXACT/1685-2014"

    is_present: None | IsPresent = field(
        default=None,
        metadata={
            "name": "isPresent",
            "type": "Element",
        },
    )
    part_select: None | PartSelect = field(
        default=None,
        metadata={
            "name": "partSelect",
            "type": "Element",
        },
    )
    port_ref: str = field(
        metadata={
            "name": "portRef",
            "type": "Attribute",
            "white_space": "collapse",
            "pattern": r"\i[\p{L}\p{N}\.\-:_]*",
        }
    )
    id: None | str = field(
        default=None,
        metadata={
            "type": "Attribute",
            "namespace": "http://www.w3.org/XML/1998/namespace",
        },
    )

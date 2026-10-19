from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from org.accellera.ipxact.v1685_2022.part_select import PartSelect
from org.accellera.ipxact.v1685_2022.sub_port_reference import SubPortReference
from org.accellera.ipxact.v1685_2022.vendor_extensions import VendorExtensions

__NAMESPACE__ = "http://www.accellera.org/XMLSchema/IPXACT/1685-2022"


@dataclass(slots=True, kw_only=True)
class ExternalPortReference:
    """
    :ivar sub_port_reference:
    :ivar part_select:
    :ivar vendor_extensions:
    :ivar port_ref: A port on the on the referenced component from
        componentInterfaceRef.
    :ivar id:
    """

    class Meta:
        name = "externalPortReference"
        namespace = "http://www.accellera.org/XMLSchema/IPXACT/1685-2022"

    sub_port_reference: Sequence[SubPortReference] = field(
        default_factory=list,
        metadata={
            "name": "subPortReference",
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
    vendor_extensions: None | VendorExtensions = field(
        default=None,
        metadata={
            "name": "vendorExtensions",
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

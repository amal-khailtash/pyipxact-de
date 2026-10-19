from __future__ import annotations

from dataclasses import dataclass, field

from org.accellera.ipxact.v1685_2014.description import Description
from org.accellera.ipxact.v1685_2014.is_present import IsPresent
from org.accellera.ipxact.v1685_2014.vendor_extensions import VendorExtensions

__NAMESPACE__ = "http://www.accellera.org/XMLSchema/IPXACT/1685-2014"


@dataclass(slots=True, kw_only=True)
class HierInterfaceType:
    """
    A representation of an exported interface.

    The busRef indicates the name of the interface in the containing
    component.

    :ivar is_present:
    :ivar description:
    :ivar vendor_extensions:
    :ivar bus_ref: Reference to the components  bus interface
    :ivar id:
    """

    class Meta:
        name = "hierInterfaceType"

    is_present: None | IsPresent = field(
        default=None,
        metadata={
            "name": "isPresent",
            "type": "Element",
            "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2014",
        },
    )
    description: None | Description = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2014",
        },
    )
    vendor_extensions: None | VendorExtensions = field(
        default=None,
        metadata={
            "name": "vendorExtensions",
            "type": "Element",
            "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2014",
        },
    )
    bus_ref: str = field(
        metadata={
            "name": "busRef",
            "type": "Attribute",
        }
    )
    id: None | str = field(
        default=None,
        metadata={
            "type": "Attribute",
            "namespace": "http://www.w3.org/XML/1998/namespace",
        },
    )

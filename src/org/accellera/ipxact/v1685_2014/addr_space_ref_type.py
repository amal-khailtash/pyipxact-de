from __future__ import annotations

from dataclasses import dataclass, field

from org.accellera.ipxact.v1685_2014.is_present import IsPresent

__NAMESPACE__ = "http://www.accellera.org/XMLSchema/IPXACT/1685-2014"


@dataclass(slots=True, kw_only=True)
class AddrSpaceRefType:
    """
    Base type for an element which references an address space.

    Reference is kept in an attribute rather than the text value, so that
    the type may be extended with child elements if necessary.

    :ivar is_present:
    :ivar address_space_ref: A reference to a unique address space.
    :ivar id:
    """

    class Meta:
        name = "addrSpaceRefType"

    is_present: None | IsPresent = field(
        default=None,
        metadata={
            "name": "isPresent",
            "type": "Element",
            "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2014",
        },
    )
    address_space_ref: str = field(
        metadata={
            "name": "addressSpaceRef",
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

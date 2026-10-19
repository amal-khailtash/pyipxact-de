from __future__ import annotations

from dataclasses import dataclass, field

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4"


@dataclass(slots=True, kw_only=True)
class AddrSpaceRefType:
    """
    Base type for an element which references an address space.

    Reference is kept in an attribute rather than the text value, so that
    the type may be extended with child elements if necessary.
    """

    class Meta:
        name = "addrSpaceRefType"

    address_space_ref: str = field(
        metadata={
            "name": "addressSpaceRef",
            "type": "Attribute",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
        }
    )

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from org.accellera.ipxact.v1685_2014.address_block import AddressBlock
from org.accellera.ipxact.v1685_2014.description import Description
from org.accellera.ipxact.v1685_2014.display_name import DisplayName
from org.accellera.ipxact.v1685_2014.is_present import IsPresent
from org.accellera.ipxact.v1685_2014.local_address_bank_type import (
    LocalAddressBankType,
)

__NAMESPACE__ = "http://www.accellera.org/XMLSchema/IPXACT/1685-2014"


@dataclass(slots=True, kw_only=True)
class LocalMemoryMapType:
    """
    Map of address space blocks on the local memory map of a master bus
    interface.

    :ivar name: Unique name
    :ivar display_name:
    :ivar description:
    :ivar is_present:
    :ivar address_block_or_bank:
    :ivar id:
    """

    class Meta:
        name = "localMemoryMapType"

    name: str = field(
        metadata={
            "type": "Element",
            "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2014",
        }
    )
    display_name: None | DisplayName = field(
        default=None,
        metadata={
            "name": "displayName",
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
    is_present: None | IsPresent = field(
        default=None,
        metadata={
            "name": "isPresent",
            "type": "Element",
            "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2014",
        },
    )
    address_block_or_bank: Sequence[AddressBlock | LocalAddressBankType] = (
        field(
            default_factory=list,
            metadata={
                "type": "Elements",
                "choices": (
                    {
                        "name": "addressBlock",
                        "type": AddressBlock,
                        "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2014",
                    },
                    {
                        "name": "bank",
                        "type": LocalAddressBankType,
                        "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2014",
                    },
                ),
            },
        )
    )
    id: None | str = field(
        default=None,
        metadata={
            "type": "Attribute",
            "namespace": "http://www.w3.org/XML/1998/namespace",
        },
    )

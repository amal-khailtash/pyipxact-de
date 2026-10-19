from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from org.accellera.ipxact.v1685_2022.address_bank_definition_type import (
    AddressBankDefinitionType,
)
from org.accellera.ipxact.v1685_2022.address_block import AddressBlock
from org.accellera.ipxact.v1685_2022.address_unit_bits import AddressUnitBits
from org.accellera.ipxact.v1685_2022.description import Description
from org.accellera.ipxact.v1685_2022.display_name import DisplayName
from org.accellera.ipxact.v1685_2022.short_description import ShortDescription
from org.accellera.ipxact.v1685_2022.vendor_extensions import VendorExtensions

__NAMESPACE__ = "http://www.accellera.org/XMLSchema/IPXACT/1685-2022"


@dataclass(slots=True, kw_only=True)
class MemoryRemapDefinitions:
    class Meta:
        name = "memoryRemapDefinitions"
        namespace = "http://www.accellera.org/XMLSchema/IPXACT/1685-2022"

    memory_remap_definition: Sequence[
        MemoryRemapDefinitions.MemoryRemapDefinition
    ] = field(
        default_factory=list,
        metadata={
            "name": "memoryRemapDefinition",
            "type": "Element",
            "min_occurs": 1,
        },
    )

    @dataclass(slots=True, kw_only=True)
    class MemoryRemapDefinition:
        """
        :ivar name: Unique name
        :ivar display_name:
        :ivar short_description:
        :ivar description:
        :ivar address_block_or_bank:
        :ivar address_unit_bits:
        :ivar vendor_extensions:
        :ivar id:
        """

        name: str = field(
            metadata={
                "type": "Element",
            }
        )
        display_name: None | DisplayName = field(
            default=None,
            metadata={
                "name": "displayName",
                "type": "Element",
            },
        )
        short_description: None | ShortDescription = field(
            default=None,
            metadata={
                "name": "shortDescription",
                "type": "Element",
            },
        )
        description: None | Description = field(
            default=None,
            metadata={
                "type": "Element",
            },
        )
        address_block_or_bank: Sequence[
            AddressBlock | AddressBankDefinitionType
        ] = field(
            default_factory=list,
            metadata={
                "type": "Elements",
                "choices": (
                    {
                        "name": "addressBlock",
                        "type": AddressBlock,
                    },
                    {
                        "name": "bank",
                        "type": AddressBankDefinitionType,
                    },
                ),
            },
        )
        address_unit_bits: None | AddressUnitBits = field(
            default=None,
            metadata={
                "name": "addressUnitBits",
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
        id: None | str = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.w3.org/XML/1998/namespace",
            },
        )

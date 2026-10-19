from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import ForwardRef

from org.accellera.ipxact.v1685_2022.address_block import AddressBlock
from org.accellera.ipxact.v1685_2022.address_unit_bits import AddressUnitBits
from org.accellera.ipxact.v1685_2022.bank import Bank
from org.accellera.ipxact.v1685_2022.description import Description
from org.accellera.ipxact.v1685_2022.display_name import DisplayName
from org.accellera.ipxact.v1685_2022.memory_remap import MemoryRemap
from org.accellera.ipxact.v1685_2022.shared_type import SharedType
from org.accellera.ipxact.v1685_2022.short_description import ShortDescription
from org.accellera.ipxact.v1685_2022.subspace_map import SubspaceMap
from org.accellera.ipxact.v1685_2022.vendor_extensions import VendorExtensions

__NAMESPACE__ = "http://www.accellera.org/XMLSchema/IPXACT/1685-2022"


@dataclass(slots=True, kw_only=True)
class MemoryMapType:
    """
    Map of address space blocks on target target bus interface.

    :ivar name: Unique name
    :ivar display_name:
    :ivar short_description:
    :ivar description:
    :ivar choice:
    :ivar vendor_extensions:
    :ivar id:
    """

    class Meta:
        name = "memoryMapType"

    name: str = field(
        metadata={
            "type": "Element",
            "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
        }
    )
    display_name: None | DisplayName = field(
        default=None,
        metadata={
            "name": "displayName",
            "type": "Element",
            "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
        },
    )
    short_description: None | ShortDescription = field(
        default=None,
        metadata={
            "name": "shortDescription",
            "type": "Element",
            "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
        },
    )
    description: None | Description = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
        },
    )
    choice: Sequence[
        MemoryMapType.MemoryMapDefinitionRef
        | AddressBlock
        | Bank
        | SubspaceMap
        | MemoryRemap
        | AddressUnitBits
        | SharedType
    ] = field(
        default_factory=list,
        metadata={
            "type": "Elements",
            "choices": (
                {
                    "name": "memoryMapDefinitionRef",
                    "type": ForwardRef("MemoryMapType.MemoryMapDefinitionRef"),
                    "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
                },
                {
                    "name": "addressBlock",
                    "type": AddressBlock,
                    "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
                },
                {
                    "name": "bank",
                    "type": Bank,
                    "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
                },
                {
                    "name": "subspaceMap",
                    "type": SubspaceMap,
                    "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
                },
                {
                    "name": "memoryRemap",
                    "type": MemoryRemap,
                    "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
                },
                {
                    "name": "addressUnitBits",
                    "type": AddressUnitBits,
                    "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
                },
                {
                    "name": "shared",
                    "type": SharedType,
                    "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
                },
            ),
        },
    )
    vendor_extensions: None | VendorExtensions = field(
        default=None,
        metadata={
            "name": "vendorExtensions",
            "type": "Element",
            "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
        },
    )
    id: None | str = field(
        default=None,
        metadata={
            "type": "Attribute",
            "namespace": "http://www.w3.org/XML/1998/namespace",
        },
    )

    @dataclass(slots=True, kw_only=True)
    class MemoryMapDefinitionRef:
        value: str = field(default="")
        type_definitions: str = field(
            metadata={
                "name": "typeDefinitions",
                "type": "Attribute",
            }
        )

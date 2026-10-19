from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from org.accellera.ipxact.v1685_2014.address_block import AddressBlock
from org.accellera.ipxact.v1685_2014.address_unit_bits import AddressUnitBits
from org.accellera.ipxact.v1685_2014.bank import Bank
from org.accellera.ipxact.v1685_2014.description import Description
from org.accellera.ipxact.v1685_2014.display_name import DisplayName
from org.accellera.ipxact.v1685_2014.is_present import IsPresent
from org.accellera.ipxact.v1685_2014.memory_remap_type import MemoryRemapType
from org.accellera.ipxact.v1685_2014.shared_type import SharedType
from org.accellera.ipxact.v1685_2014.subspace_ref_type import SubspaceRefType
from org.accellera.ipxact.v1685_2014.vendor_extensions import VendorExtensions

__NAMESPACE__ = "http://www.accellera.org/XMLSchema/IPXACT/1685-2014"


@dataclass(slots=True, kw_only=True)
class MemoryMapType:
    """
    Map of address space blocks on slave slave bus interface.

    :ivar name: Unique name
    :ivar display_name:
    :ivar description:
    :ivar is_present:
    :ivar address_block_or_bank_or_subspace_map:
    :ivar memory_remap: Additional memory map elements that are
        dependent on the component state.
    :ivar address_unit_bits:
    :ivar shared: When the value is 'yes', the contents of the memoryMap
        are shared by all the references to this memoryMap, when the
        value is 'no' the contents of the memoryMap is not shared and
        when the value is 'undefined' (default) the sharing of the
        memoryMap is undefined.
    :ivar vendor_extensions:
    :ivar id:
    """

    class Meta:
        name = "memoryMapType"

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
    address_block_or_bank_or_subspace_map: Sequence[
        AddressBlock | Bank | SubspaceRefType
    ] = field(
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
                    "type": Bank,
                    "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2014",
                },
                {
                    "name": "subspaceMap",
                    "type": SubspaceRefType,
                    "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2014",
                },
            ),
        },
    )
    memory_remap: Sequence[MemoryRemapType] = field(
        default_factory=list,
        metadata={
            "name": "memoryRemap",
            "type": "Element",
            "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2014",
        },
    )
    address_unit_bits: None | AddressUnitBits = field(
        default=None,
        metadata={
            "name": "addressUnitBits",
            "type": "Element",
            "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2014",
        },
    )
    shared: None | SharedType = field(
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
    id: None | str = field(
        default=None,
        metadata={
            "type": "Attribute",
            "namespace": "http://www.w3.org/XML/1998/namespace",
        },
    )

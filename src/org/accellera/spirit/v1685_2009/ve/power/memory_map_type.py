from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from org.accellera.spirit.v1685_2009.ve.power.address_block import AddressBlock
from org.accellera.spirit.v1685_2009.ve.power.address_unit_bits import (
    AddressUnitBits,
)
from org.accellera.spirit.v1685_2009.ve.power.bank import Bank
from org.accellera.spirit.v1685_2009.ve.power.description import Description
from org.accellera.spirit.v1685_2009.ve.power.display_name import DisplayName
from org.accellera.spirit.v1685_2009.ve.power.memory_remap_type import (
    MemoryRemapType,
)
from org.accellera.spirit.v1685_2009.ve.power.subspace_ref_type import (
    SubspaceRefType,
)
from org.accellera.spirit.v1685_2009.ve.power.vendor_extensions import (
    VendorExtensions,
)

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009"


@dataclass(slots=True, kw_only=True)
class MemoryMapType:
    """
    Map of address space blocks on slave slave bus interface.

    :ivar name: Unique name
    :ivar display_name:
    :ivar description:
    :ivar address_block_or_bank_or_subspace_map:
    :ivar memory_remap: Additional memory map elements that are
        dependent on the component state.
    :ivar address_unit_bits:
    :ivar vendor_extensions:
    :ivar id:
    """

    class Meta:
        name = "memoryMapType"

    name: str = field(
        metadata={
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
        }
    )
    display_name: None | DisplayName = field(
        default=None,
        metadata={
            "name": "displayName",
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
        },
    )
    description: None | Description = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
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
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
                },
                {
                    "name": "bank",
                    "type": Bank,
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
                },
                {
                    "name": "subspaceMap",
                    "type": SubspaceRefType,
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
                },
            ),
        },
    )
    memory_remap: Sequence[MemoryRemapType] = field(
        default_factory=list,
        metadata={
            "name": "memoryRemap",
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
        },
    )
    address_unit_bits: None | AddressUnitBits = field(
        default=None,
        metadata={
            "name": "addressUnitBits",
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
        },
    )
    vendor_extensions: None | VendorExtensions = field(
        default=None,
        metadata={
            "name": "vendorExtensions",
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
        },
    )
    id: None | str = field(
        default=None,
        metadata={
            "type": "Attribute",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
        },
    )

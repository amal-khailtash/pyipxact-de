from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from org.accellera.spirit.v1_0.address_block import AddressBlock
from org.accellera.spirit.v1_0.bank import Bank
from org.accellera.spirit.v1_0.memory_remap_type import MemoryRemapType
from org.accellera.spirit.v1_0.subspace_ref_type import SubspaceRefType

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0"


@dataclass(slots=True, kw_only=True)
class MemoryMapType:
    """
    Map of address space blocks on slave slave bus interface.

    :ivar name: Memory map name, unique within the component. Put into a
        group to avoid making it a top level element
    :ivar address_block_or_bank_or_subspace_map:
    :ivar memory_remap:
    """

    class Meta:
        name = "memoryMapType"

    name: str = field(
        metadata={
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
        }
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
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
                },
                {
                    "name": "bank",
                    "type": Bank,
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
                },
                {
                    "name": "subspaceMap",
                    "type": SubspaceRefType,
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
                },
            ),
        },
    )
    memory_remap: Sequence[MemoryRemapType] = field(
        default_factory=list,
        metadata={
            "name": "memoryRemap",
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
        },
    )

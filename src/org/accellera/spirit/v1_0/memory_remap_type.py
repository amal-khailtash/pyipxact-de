from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from org.accellera.spirit.v1_0.address_block import AddressBlock
from org.accellera.spirit.v1_0.bank import Bank
from org.accellera.spirit.v1_0.subspace_ref_type import SubspaceRefType

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0"


@dataclass(slots=True, kw_only=True)
class MemoryRemapType:
    """
    Map of address space blocks on a slave bus interface in a specific
    remap state.

    :ivar address_block_or_bank_or_subspace_map:
    :ivar state: State of the component in which the memory map is
        active.
    """

    class Meta:
        name = "memoryRemapType"

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
    state: str = field(
        metadata={
            "type": "Attribute",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
        }
    )

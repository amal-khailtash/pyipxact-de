from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from org.accellera.spirit.v1_2.address_block import AddressBlock
from org.accellera.spirit.v1_2.bank import Bank
from org.accellera.spirit.v1_2.subspace_ref_type import SubspaceRefType

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2"


@dataclass(slots=True, kw_only=True)
class LocalMemoryMapType:
    """
    Map of address space blocks on the local memory map of a master bus
    interface.
    """

    class Meta:
        name = "localMemoryMapType"

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
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2",
                },
                {
                    "name": "bank",
                    "type": Bank,
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2",
                },
                {
                    "name": "subspaceMap",
                    "type": SubspaceRefType,
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2",
                },
            ),
        },
    )

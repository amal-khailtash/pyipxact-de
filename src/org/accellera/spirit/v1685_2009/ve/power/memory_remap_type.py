from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from org.accellera.spirit.v1685_2009.ve.power.address_block import AddressBlock
from org.accellera.spirit.v1685_2009.ve.power.bank import Bank
from org.accellera.spirit.v1685_2009.ve.power.description import Description
from org.accellera.spirit.v1685_2009.ve.power.display_name import DisplayName
from org.accellera.spirit.v1685_2009.ve.power.subspace_ref_type import (
    SubspaceRefType,
)

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009"


@dataclass(slots=True, kw_only=True)
class MemoryRemapType:
    """
    Map of address space blocks on a slave bus interface in a specific
    remap state.

    :ivar name: Unique name
    :ivar display_name:
    :ivar description:
    :ivar address_block_or_bank_or_subspace_map:
    :ivar state: State of the component in which the memory map is
        active.
    :ivar id:
    """

    class Meta:
        name = "memoryRemapType"

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
    state: str = field(
        metadata={
            "type": "Attribute",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
        }
    )
    id: None | str = field(
        default=None,
        metadata={
            "type": "Attribute",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
        },
    )

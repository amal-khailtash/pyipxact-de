from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import ForwardRef

from org.accellera.ipxact.v1685_2022.address_block_ref import AddressBlockRef
from org.accellera.ipxact.v1685_2022.alternate_register_ref import (
    AlternateRegisterRef,
)
from org.accellera.ipxact.v1685_2022.bank_ref import BankRef
from org.accellera.ipxact.v1685_2022.field_ref import FieldRef
from org.accellera.ipxact.v1685_2022.memory_remap_ref import MemoryRemapRef
from org.accellera.ipxact.v1685_2022.register_file_ref import RegisterFileRef
from org.accellera.ipxact.v1685_2022.register_ref import RegisterRef

__NAMESPACE__ = "http://www.accellera.org/XMLSchema/IPXACT/1685-2022"


@dataclass(slots=True, kw_only=True)
class IndirectAddressRef:
    """
    A reference to a field used for addressing the indirectly accessible
    memoryMap.
    """

    class Meta:
        name = "indirectAddressRef"
        namespace = "http://www.accellera.org/XMLSchema/IPXACT/1685-2022"

    address_space_ref_or_memory_map_ref_or_memory_remap_ref: Sequence[
        IndirectAddressRef.AddressSpaceRef
        | IndirectAddressRef.MemoryMapRef
        | MemoryRemapRef
    ] = field(
        default_factory=list,
        metadata={
            "type": "Elements",
            "choices": (
                {
                    "name": "addressSpaceRef",
                    "type": ForwardRef("IndirectAddressRef.AddressSpaceRef"),
                },
                {
                    "name": "memoryMapRef",
                    "type": ForwardRef("IndirectAddressRef.MemoryMapRef"),
                },
                {
                    "name": "memoryRemapRef",
                    "type": MemoryRemapRef,
                },
            ),
            "max_occurs": 2,
        },
    )
    bank_ref: Sequence[BankRef] = field(
        default_factory=list,
        metadata={
            "name": "bankRef",
            "type": "Element",
        },
    )
    address_block_ref: None | AddressBlockRef = field(
        default=None,
        metadata={
            "name": "addressBlockRef",
            "type": "Element",
        },
    )
    register_file_ref: Sequence[RegisterFileRef] = field(
        default_factory=list,
        metadata={
            "name": "registerFileRef",
            "type": "Element",
        },
    )
    register_ref: None | RegisterRef = field(
        default=None,
        metadata={
            "name": "registerRef",
            "type": "Element",
        },
    )
    alternate_register_ref: None | AlternateRegisterRef = field(
        default=None,
        metadata={
            "name": "alternateRegisterRef",
            "type": "Element",
        },
    )
    field_ref: FieldRef = field(
        metadata={
            "name": "fieldRef",
            "type": "Element",
        }
    )

    @dataclass(slots=True, kw_only=True)
    class AddressSpaceRef:
        address_space_ref: str = field(
            metadata={
                "name": "addressSpaceRef",
                "type": "Attribute",
            }
        )

    @dataclass(slots=True, kw_only=True)
    class MemoryMapRef:
        memory_map_ref: str = field(
            metadata={
                "name": "memoryMapRef",
                "type": "Attribute",
            }
        )

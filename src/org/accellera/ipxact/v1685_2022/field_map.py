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
from org.accellera.ipxact.v1685_2022.part_select import PartSelect
from org.accellera.ipxact.v1685_2022.range import Range
from org.accellera.ipxact.v1685_2022.register_file_ref import RegisterFileRef
from org.accellera.ipxact.v1685_2022.register_ref import RegisterRef
from org.accellera.ipxact.v1685_2022.sub_port_reference import SubPortReference

__NAMESPACE__ = "http://www.accellera.org/XMLSchema/IPXACT/1685-2022"


@dataclass(slots=True, kw_only=True)
class FieldMap:
    """
    Maps slices of this port to component field slices.

    :ivar field_slice: Reference to a register field slice
    :ivar sub_port_reference:
    :ivar part_select:
    :ivar mode_ref: A reference to a mode.
    :ivar id:
    """

    class Meta:
        name = "fieldMap"
        namespace = "http://www.accellera.org/XMLSchema/IPXACT/1685-2022"

    field_slice: FieldMap.FieldSlice = field(
        metadata={
            "name": "fieldSlice",
            "type": "Element",
        }
    )
    sub_port_reference: Sequence[SubPortReference] = field(
        default_factory=list,
        metadata={
            "name": "subPortReference",
            "type": "Element",
        },
    )
    part_select: None | PartSelect = field(
        default=None,
        metadata={
            "name": "partSelect",
            "type": "Element",
        },
    )
    mode_ref: Sequence[FieldMap.ModeRef] = field(
        default_factory=list,
        metadata={
            "name": "modeRef",
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

    @dataclass(slots=True, kw_only=True)
    class FieldSlice:
        address_space_ref_or_memory_map_ref_or_memory_remap_ref: Sequence[
            FieldMap.FieldSlice.AddressSpaceRef
            | FieldMap.FieldSlice.MemoryMapRef
            | MemoryRemapRef
        ] = field(
            default_factory=list,
            metadata={
                "type": "Elements",
                "choices": (
                    {
                        "name": "addressSpaceRef",
                        "type": ForwardRef(
                            "FieldMap.FieldSlice.AddressSpaceRef"
                        ),
                    },
                    {
                        "name": "memoryMapRef",
                        "type": ForwardRef("FieldMap.FieldSlice.MemoryMapRef"),
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
        address_block_ref: AddressBlockRef = field(
            metadata={
                "name": "addressBlockRef",
                "type": "Element",
            }
        )
        register_file_ref: Sequence[RegisterFileRef] = field(
            default_factory=list,
            metadata={
                "name": "registerFileRef",
                "type": "Element",
            },
        )
        register_ref: RegisterRef = field(
            metadata={
                "name": "registerRef",
                "type": "Element",
            }
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
        range: None | Range = field(
            default=None,
            metadata={
                "type": "Element",
            },
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

    @dataclass(slots=True, kw_only=True)
    class ModeRef:
        value: str = field(default="")
        priority: int = field(
            metadata={
                "type": "Attribute",
            }
        )
        id: None | str = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.w3.org/XML/1998/namespace",
            },
        )

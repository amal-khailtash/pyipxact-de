from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import ForwardRef

from org.accellera.ipxact.v1685_2014.access import Access
from org.accellera.ipxact.v1685_2014.alternate_registers import (
    AlternateRegisters,
)
from org.accellera.ipxact.v1685_2014.description import Description
from org.accellera.ipxact.v1685_2014.display_name import DisplayName
from org.accellera.ipxact.v1685_2014.field_type import FieldType
from org.accellera.ipxact.v1685_2014.indexed_access_handle import (
    IndexedAccessHandle,
)
from org.accellera.ipxact.v1685_2014.is_present import IsPresent
from org.accellera.ipxact.v1685_2014.parameters import Parameters
from org.accellera.ipxact.v1685_2014.unsigned_longint_expression import (
    UnsignedLongintExpression,
)
from org.accellera.ipxact.v1685_2014.unsigned_positive_int_expression import (
    UnsignedPositiveIntExpression,
)
from org.accellera.ipxact.v1685_2014.unsigned_positive_longint_expression import (
    UnsignedPositiveLongintExpression,
)
from org.accellera.ipxact.v1685_2014.vendor_extensions import VendorExtensions
from org.accellera.ipxact.v1685_2014.volatile import Volatile

__NAMESPACE__ = "http://www.accellera.org/XMLSchema/IPXACT/1685-2014"


@dataclass(slots=True, kw_only=True)
class RegisterFile:
    """
    A structure of registers and register files.

    :ivar name: Unique name
    :ivar display_name:
    :ivar description:
    :ivar access_handles:
    :ivar is_present:
    :ivar dim: Dimensions a register array, the semantics for dim
        elements are the same as the C language standard for the  layout
        of memory in multidimensional arrays.
    :ivar address_offset: Offset from the address block's baseAddress or
        the containing register file's addressOffset, expressed as the
        number of addressUnitBits from the containing memoryMap or
        localMemoryMap.
    :ivar type_identifier: Identifier name used to indicate that
        multiple registerFile elements contain the exact same
        information except for the elements in the
        registerFileInstanceGroup.
    :ivar range: The range of a register file.  Expressed as the number
        of addressable units accessible to the block. Specified in units
        of addressUnitBits.
    :ivar register_or_register_file:
    :ivar parameters:
    :ivar vendor_extensions:
    :ivar id:
    """

    class Meta:
        name = "registerFile"
        namespace = "http://www.accellera.org/XMLSchema/IPXACT/1685-2014"

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
    description: None | Description = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    access_handles: None | RegisterFile.AccessHandles = field(
        default=None,
        metadata={
            "name": "accessHandles",
            "type": "Element",
        },
    )
    is_present: None | IsPresent = field(
        default=None,
        metadata={
            "name": "isPresent",
            "type": "Element",
        },
    )
    dim: Sequence[RegisterFile.Dim] = field(
        default_factory=list,
        metadata={
            "type": "Element",
        },
    )
    address_offset: UnsignedLongintExpression = field(
        metadata={
            "name": "addressOffset",
            "type": "Element",
        }
    )
    type_identifier: None | str = field(
        default=None,
        metadata={
            "name": "typeIdentifier",
            "type": "Element",
        },
    )
    range: UnsignedPositiveLongintExpression = field(
        metadata={
            "type": "Element",
        }
    )
    register_or_register_file: Sequence[
        RegisterFile.Register | RegisterFile
    ] = field(
        default_factory=list,
        metadata={
            "type": "Elements",
            "choices": (
                {
                    "name": "register",
                    "type": ForwardRef("RegisterFile.Register"),
                },
                {
                    "name": "registerFile",
                    "type": ForwardRef("RegisterFile"),
                },
            ),
        },
    )
    parameters: None | Parameters = field(
        default=None,
        metadata={
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

    @dataclass(slots=True, kw_only=True)
    class AccessHandles:
        access_handle: Sequence[IndexedAccessHandle] = field(
            default_factory=list,
            metadata={
                "name": "accessHandle",
                "type": "Element",
                "min_occurs": 1,
            },
        )

    @dataclass(slots=True, kw_only=True)
    class Dim(UnsignedLongintExpression):
        id: None | str = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.w3.org/XML/1998/namespace",
            },
        )

    @dataclass(slots=True, kw_only=True)
    class Register:
        """
        :ivar name: Unique name
        :ivar display_name:
        :ivar description:
        :ivar access_handles:
        :ivar is_present:
        :ivar dim: Dimensions a register array, the semantics for dim
            elements are the same as the C language standard for the
            layout of memory in multidimensional arrays.
        :ivar address_offset: Offset from the address block's
            baseAddress or the containing register file's addressOffset,
            expressed as the number of addressUnitBits from the
            containing memoryMap or localMemoryMap.
        :ivar type_identifier: Identifier name used to indicate that
            multiple register elements contain the exact same
            information for the elements in the registerDefinitionGroup.
        :ivar size: Width of the register in bits.
        :ivar volatile:
        :ivar access:
        :ivar field_value: Describes individual bit fields within the
            register.
        :ivar alternate_registers:
        :ivar parameters:
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
        description: None | Description = field(
            default=None,
            metadata={
                "type": "Element",
            },
        )
        access_handles: None | RegisterFile.Register.AccessHandles = field(
            default=None,
            metadata={
                "name": "accessHandles",
                "type": "Element",
            },
        )
        is_present: None | IsPresent = field(
            default=None,
            metadata={
                "name": "isPresent",
                "type": "Element",
            },
        )
        dim: Sequence[RegisterFile.Register.Dim] = field(
            default_factory=list,
            metadata={
                "type": "Element",
            },
        )
        address_offset: UnsignedLongintExpression = field(
            metadata={
                "name": "addressOffset",
                "type": "Element",
            }
        )
        type_identifier: None | str = field(
            default=None,
            metadata={
                "name": "typeIdentifier",
                "type": "Element",
            },
        )
        size: UnsignedPositiveIntExpression = field(
            metadata={
                "type": "Element",
            }
        )
        volatile: None | Volatile = field(
            default=None,
            metadata={
                "type": "Element",
            },
        )
        access: None | Access = field(
            default=None,
            metadata={
                "type": "Element",
            },
        )
        field_value: Sequence[FieldType] = field(
            default_factory=list,
            metadata={
                "name": "field",
                "type": "Element",
                "min_occurs": 1,
            },
        )
        alternate_registers: None | AlternateRegisters = field(
            default=None,
            metadata={
                "name": "alternateRegisters",
                "type": "Element",
            },
        )
        parameters: None | Parameters = field(
            default=None,
            metadata={
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

        @dataclass(slots=True, kw_only=True)
        class AccessHandles:
            access_handle: Sequence[IndexedAccessHandle] = field(
                default_factory=list,
                metadata={
                    "name": "accessHandle",
                    "type": "Element",
                    "min_occurs": 1,
                },
            )

        @dataclass(slots=True, kw_only=True)
        class Dim(UnsignedLongintExpression):
            id: None | str = field(
                default=None,
                metadata={
                    "type": "Attribute",
                    "namespace": "http://www.w3.org/XML/1998/namespace",
                },
            )

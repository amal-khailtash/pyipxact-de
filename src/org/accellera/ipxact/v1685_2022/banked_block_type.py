from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import ForwardRef

from org.accellera.ipxact.v1685_2022.access_policies import AccessPolicies
from org.accellera.ipxact.v1685_2022.alternate_registers import (
    AlternateRegisters,
)
from org.accellera.ipxact.v1685_2022.array import Array
from org.accellera.ipxact.v1685_2022.description import Description
from org.accellera.ipxact.v1685_2022.display_name import DisplayName
from org.accellera.ipxact.v1685_2022.field_type import FieldType
from org.accellera.ipxact.v1685_2022.parameters import Parameters
from org.accellera.ipxact.v1685_2022.register_file import RegisterFile
from org.accellera.ipxact.v1685_2022.short_description import ShortDescription
from org.accellera.ipxact.v1685_2022.simple_access_handle import (
    SimpleAccessHandle,
)
from org.accellera.ipxact.v1685_2022.sliced_access_handle import (
    SlicedAccessHandle,
)
from org.accellera.ipxact.v1685_2022.unsigned_longint_expression import (
    UnsignedLongintExpression,
)
from org.accellera.ipxact.v1685_2022.unsigned_positive_int_expression import (
    UnsignedPositiveIntExpression,
)
from org.accellera.ipxact.v1685_2022.unsigned_positive_longint_expression import (
    UnsignedPositiveLongintExpression,
)
from org.accellera.ipxact.v1685_2022.usage_type import UsageType
from org.accellera.ipxact.v1685_2022.vendor_extensions import VendorExtensions
from org.accellera.ipxact.v1685_2022.volatile import Volatile

__NAMESPACE__ = "http://www.accellera.org/XMLSchema/IPXACT/1685-2022"


@dataclass(slots=True, kw_only=True)
class BankedBlockType:
    """
    Address blocks inside a bank do not specify address.

    :ivar name: Unique name
    :ivar display_name:
    :ivar short_description:
    :ivar description:
    :ivar access_handles:
    :ivar range: The address range of an address block.  Expressed as
        the number of addressable units accessible to the block. The
        range and the width are related by the following formulas:
        number_of_bits_in_block = ipxact:addressUnitBits * ipxact:range
        number_of_rows_in_block = number_of_bits_in_block / ipxact:width
    :ivar width: The bit width of a row in the address block. The range
        and the width are related by the following formulas:
        number_of_bits_in_block = ipxact:addressUnitBits * ipxact:range
        number_of_rows_in_block = number_of_bits_in_block / ipxact:width
    :ivar usage: Indicates the usage of this block.  Possible values are
        'memory', 'register' and 'reserved'.
    :ivar volatile:
    :ivar access_policies:
    :ivar parameters: Any additional parameters needed to describe this
        address block to the generators.
    :ivar register_or_register_file:
    :ivar vendor_extensions:
    :ivar id:
    """

    class Meta:
        name = "bankedBlockType"

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
    access_handles: None | BankedBlockType.AccessHandles = field(
        default=None,
        metadata={
            "name": "accessHandles",
            "type": "Element",
            "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
        },
    )
    range: UnsignedPositiveLongintExpression = field(
        metadata={
            "type": "Element",
            "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
        }
    )
    width: UnsignedPositiveIntExpression = field(
        metadata={
            "type": "Element",
            "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
        }
    )
    usage: None | UsageType = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
        },
    )
    volatile: None | Volatile = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
        },
    )
    access_policies: None | AccessPolicies = field(
        default=None,
        metadata={
            "name": "accessPolicies",
            "type": "Element",
            "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
        },
    )
    parameters: None | Parameters = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
        },
    )
    register_or_register_file: Sequence[
        BankedBlockType.Register | RegisterFile
    ] = field(
        default_factory=list,
        metadata={
            "type": "Elements",
            "choices": (
                {
                    "name": "register",
                    "type": ForwardRef("BankedBlockType.Register"),
                    "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
                },
                {
                    "name": "registerFile",
                    "type": RegisterFile,
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
    class AccessHandles:
        access_handle: Sequence[SlicedAccessHandle] = field(
            default_factory=list,
            metadata={
                "name": "accessHandle",
                "type": "Element",
                "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
                "min_occurs": 1,
            },
        )

    @dataclass(slots=True, kw_only=True)
    class Register:
        """
        :ivar name: Unique name
        :ivar display_name:
        :ivar short_description:
        :ivar description:
        :ivar access_handles:
        :ivar array:
        :ivar address_offset: Offset from the address block's
            baseAddress or the containing register file's addressOffset,
            expressed as the number of addressUnitBits from the
            containing memoryMap or localMemoryMap.
        :ivar choice:
        :ivar alternate_registers:
        :ivar parameters:
        :ivar vendor_extensions:
        :ivar id:
        """

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
        access_handles: None | BankedBlockType.Register.AccessHandles = field(
            default=None,
            metadata={
                "name": "accessHandles",
                "type": "Element",
                "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
            },
        )
        array: None | Array = field(
            default=None,
            metadata={
                "type": "Element",
                "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
            },
        )
        address_offset: UnsignedLongintExpression = field(
            metadata={
                "name": "addressOffset",
                "type": "Element",
                "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
            }
        )
        choice: Sequence[
            BankedBlockType.Register.RegisterDefinitionRef
            | str
            | UnsignedPositiveIntExpression
            | Volatile
            | AccessPolicies
            | FieldType
        ] = field(
            default_factory=list,
            metadata={
                "type": "Elements",
                "choices": (
                    {
                        "name": "registerDefinitionRef",
                        "type": ForwardRef(
                            "BankedBlockType.Register.RegisterDefinitionRef"
                        ),
                        "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
                    },
                    {
                        "name": "typeIdentifier",
                        "type": str,
                        "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
                    },
                    {
                        "name": "size",
                        "type": UnsignedPositiveIntExpression,
                        "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
                    },
                    {
                        "name": "volatile",
                        "type": Volatile,
                        "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
                    },
                    {
                        "name": "accessPolicies",
                        "type": AccessPolicies,
                        "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
                    },
                    {
                        "name": "field",
                        "type": FieldType,
                        "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
                    },
                ),
            },
        )
        alternate_registers: None | AlternateRegisters = field(
            default=None,
            metadata={
                "name": "alternateRegisters",
                "type": "Element",
                "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
            },
        )
        parameters: None | Parameters = field(
            default=None,
            metadata={
                "type": "Element",
                "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
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
        class AccessHandles:
            access_handle: Sequence[SimpleAccessHandle] = field(
                default_factory=list,
                metadata={
                    "name": "accessHandle",
                    "type": "Element",
                    "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
                    "min_occurs": 1,
                },
            )

        @dataclass(slots=True, kw_only=True)
        class RegisterDefinitionRef:
            value: str = field(default="")
            type_definitions: str = field(
                metadata={
                    "name": "typeDefinitions",
                    "type": "Attribute",
                }
            )

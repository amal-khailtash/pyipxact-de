from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import ForwardRef

from org.accellera.ipxact.v1685_2022.access_policies import AccessPolicies
from org.accellera.ipxact.v1685_2022.address_unit_bits import AddressUnitBits
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
class AddressBlockDefinitions:
    class Meta:
        name = "addressBlockDefinitions"
        namespace = "http://www.accellera.org/XMLSchema/IPXACT/1685-2022"

    address_block_definition: Sequence[
        AddressBlockDefinitions.AddressBlockDefinition
    ] = field(
        default_factory=list,
        metadata={
            "name": "addressBlockDefinition",
            "type": "Element",
            "min_occurs": 1,
        },
    )

    @dataclass(slots=True, kw_only=True)
    class AddressBlockDefinition:
        """
        :ivar name: Unique name
        :ivar display_name:
        :ivar short_description:
        :ivar description:
        :ivar type_identifier: Identifier name used to indicate that
            multiple addressBlock elements contain the exact same
            information except for the elements in the
            addressBlockInstanceGroup.
        :ivar range: The address range of an address block.  Expressed
            as the number of addressable units accessible to the block.
            The range and the width are related by the following
            formulas: number_of_bits_in_block = ipxact:addressUnitBits *
            ipxact:range number_of_rows_in_block =
            number_of_bits_in_block / ipxact:width
        :ivar width: The bit width of a row in the address block. The
            range and the width are related by the following formulas:
            number_of_bits_in_block = ipxact:addressUnitBits *
            ipxact:range number_of_rows_in_block =
            number_of_bits_in_block / ipxact:width
        :ivar usage: Indicates the usage of this block.  Possible values
            are 'memory', 'register' and 'reserved'.
        :ivar volatile:
        :ivar access_policies:
        :ivar parameters: Any additional parameters needed to describe
            this address block to the generators.
        :ivar register_or_register_file:
        :ivar address_unit_bits:
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
        short_description: None | ShortDescription = field(
            default=None,
            metadata={
                "name": "shortDescription",
                "type": "Element",
            },
        )
        description: None | Description = field(
            default=None,
            metadata={
                "type": "Element",
            },
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
        width: UnsignedPositiveIntExpression = field(
            metadata={
                "type": "Element",
            }
        )
        usage: None | UsageType = field(
            default=None,
            metadata={
                "type": "Element",
            },
        )
        volatile: None | Volatile = field(
            default=None,
            metadata={
                "type": "Element",
            },
        )
        access_policies: None | AccessPolicies = field(
            default=None,
            metadata={
                "name": "accessPolicies",
                "type": "Element",
            },
        )
        parameters: None | Parameters = field(
            default=None,
            metadata={
                "type": "Element",
            },
        )
        register_or_register_file: Sequence[
            AddressBlockDefinitions.AddressBlockDefinition.Register
            | RegisterFile
        ] = field(
            default_factory=list,
            metadata={
                "type": "Elements",
                "choices": (
                    {
                        "name": "register",
                        "type": ForwardRef(
                            "AddressBlockDefinitions.AddressBlockDefinition.Register"
                        ),
                    },
                    {
                        "name": "registerFile",
                        "type": RegisterFile,
                    },
                ),
            },
        )
        address_unit_bits: None | AddressUnitBits = field(
            default=None,
            metadata={
                "name": "addressUnitBits",
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
        class Register:
            """
            :ivar name: Unique name
            :ivar display_name:
            :ivar short_description:
            :ivar description:
            :ivar access_handles:
            :ivar array:
            :ivar address_offset: Offset from the address block's
                baseAddress or the containing register file's
                addressOffset, expressed as the number of
                addressUnitBits from the containing memoryMap or
                localMemoryMap.
            :ivar choice:
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
            short_description: None | ShortDescription = field(
                default=None,
                metadata={
                    "name": "shortDescription",
                    "type": "Element",
                },
            )
            description: None | Description = field(
                default=None,
                metadata={
                    "type": "Element",
                },
            )
            access_handles: (
                None
                | AddressBlockDefinitions.AddressBlockDefinition.Register.AccessHandles
            ) = field(
                default=None,
                metadata={
                    "name": "accessHandles",
                    "type": "Element",
                },
            )
            array: None | Array = field(
                default=None,
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
            choice: Sequence[
                AddressBlockDefinitions.AddressBlockDefinition.Register.RegisterDefinitionRef
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
                                "AddressBlockDefinitions.AddressBlockDefinition.Register.RegisterDefinitionRef"
                            ),
                        },
                        {
                            "name": "typeIdentifier",
                            "type": str,
                        },
                        {
                            "name": "size",
                            "type": UnsignedPositiveIntExpression,
                        },
                        {
                            "name": "volatile",
                            "type": Volatile,
                        },
                        {
                            "name": "accessPolicies",
                            "type": AccessPolicies,
                        },
                        {
                            "name": "field",
                            "type": FieldType,
                        },
                    ),
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
                access_handle: Sequence[SimpleAccessHandle] = field(
                    default_factory=list,
                    metadata={
                        "name": "accessHandle",
                        "type": "Element",
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

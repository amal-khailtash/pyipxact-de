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
from org.accellera.ipxact.v1685_2022.vendor_extensions import VendorExtensions
from org.accellera.ipxact.v1685_2022.volatile import Volatile

__NAMESPACE__ = "http://www.accellera.org/XMLSchema/IPXACT/1685-2022"


@dataclass(slots=True, kw_only=True)
class RegisterFile:
    """
    A structure of registers and register files.

    :ivar name: Unique name
    :ivar display_name:
    :ivar short_description:
    :ivar description:
    :ivar access_handles:
    :ivar array:
    :ivar address_offset: Offset from the address block's baseAddress or
        the containing register file's addressOffset, expressed as the
        number of addressUnitBits from the containing memoryMap or
        localMemoryMap.
    :ivar choice:
    :ivar parameters:
    :ivar vendor_extensions:
    :ivar id:
    """

    class Meta:
        name = "registerFile"
        namespace = "http://www.accellera.org/XMLSchema/IPXACT/1685-2022"

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
    access_handles: None | RegisterFile.AccessHandles = field(
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
        RegisterFile.RegisterFileDefinitionRef
        | str
        | UnsignedPositiveLongintExpression
        | AccessPolicies
        | RegisterFile.Register
        | RegisterFile
    ] = field(
        default_factory=list,
        metadata={
            "type": "Elements",
            "choices": (
                {
                    "name": "registerFileDefinitionRef",
                    "type": ForwardRef(
                        "RegisterFile.RegisterFileDefinitionRef"
                    ),
                },
                {
                    "name": "typeIdentifier",
                    "type": str,
                },
                {
                    "name": "range",
                    "type": UnsignedPositiveLongintExpression,
                },
                {
                    "name": "accessPolicies",
                    "type": AccessPolicies,
                },
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
        access_handle: Sequence[SimpleAccessHandle] = field(
            default_factory=list,
            metadata={
                "name": "accessHandle",
                "type": "Element",
                "min_occurs": 1,
            },
        )

    @dataclass(slots=True, kw_only=True)
    class RegisterFileDefinitionRef:
        value: str = field(default="")
        type_definitions: str = field(
            metadata={
                "name": "typeDefinitions",
                "type": "Attribute",
            }
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
        access_handles: None | RegisterFile.Register.AccessHandles = field(
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
            RegisterFile.Register.RegisterDefinitionRef
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
                            "RegisterFile.Register.RegisterDefinitionRef"
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

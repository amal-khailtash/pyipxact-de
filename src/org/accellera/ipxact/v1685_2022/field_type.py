from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import ForwardRef

from org.accellera.ipxact.v1685_2022.access import Access
from org.accellera.ipxact.v1685_2022.access_restrictions import (
    AccessRestrictions,
)
from org.accellera.ipxact.v1685_2022.address_block_ref import AddressBlockRef
from org.accellera.ipxact.v1685_2022.alternate_register_ref import (
    AlternateRegisterRef,
)
from org.accellera.ipxact.v1685_2022.bank_ref import BankRef
from org.accellera.ipxact.v1685_2022.bit_stride import BitStride
from org.accellera.ipxact.v1685_2022.description import Description
from org.accellera.ipxact.v1685_2022.dim import Dim
from org.accellera.ipxact.v1685_2022.display_name import DisplayName
from org.accellera.ipxact.v1685_2022.enumerated_values import EnumeratedValues
from org.accellera.ipxact.v1685_2022.field_access_policy_definition_ref import (
    FieldAccessPolicyDefinitionRef,
)
from org.accellera.ipxact.v1685_2022.field_access_properties_type import (
    FieldAccessPropertiesType,
)
from org.accellera.ipxact.v1685_2022.field_ref import FieldRef
from org.accellera.ipxact.v1685_2022.memory_remap_ref import MemoryRemapRef
from org.accellera.ipxact.v1685_2022.mode_ref import ModeRef
from org.accellera.ipxact.v1685_2022.modified_write_value import (
    ModifiedWriteValue,
)
from org.accellera.ipxact.v1685_2022.parameters import Parameters
from org.accellera.ipxact.v1685_2022.read_action import ReadAction
from org.accellera.ipxact.v1685_2022.read_response import ReadResponse
from org.accellera.ipxact.v1685_2022.register_file_ref import RegisterFileRef
from org.accellera.ipxact.v1685_2022.register_ref import RegisterRef
from org.accellera.ipxact.v1685_2022.reset import Reset
from org.accellera.ipxact.v1685_2022.short_description import ShortDescription
from org.accellera.ipxact.v1685_2022.sliced_access_handle import (
    SlicedAccessHandle,
)
from org.accellera.ipxact.v1685_2022.testable_test_constraint import (
    TestableTestConstraint,
)
from org.accellera.ipxact.v1685_2022.unsigned_bit_expression import (
    UnsignedBitExpression,
)
from org.accellera.ipxact.v1685_2022.unsigned_int_expression import (
    UnsignedIntExpression,
)
from org.accellera.ipxact.v1685_2022.unsigned_positive_int_expression import (
    UnsignedPositiveIntExpression,
)
from org.accellera.ipxact.v1685_2022.vendor_extensions import VendorExtensions
from org.accellera.ipxact.v1685_2022.write_value_constraint import (
    WriteValueConstraint,
)

__NAMESPACE__ = "http://www.accellera.org/XMLSchema/IPXACT/1685-2022"


@dataclass(slots=True, kw_only=True)
class FieldType:
    """
    A field within a register.

    :ivar name: Unique name
    :ivar display_name:
    :ivar short_description:
    :ivar description:
    :ivar access_handles:
    :ivar array:
    :ivar bit_offset: Offset of this field's bit 0 from bit 0 of the
        register.
    :ivar choice:
    :ivar parameters:
    :ivar vendor_extensions:
    :ivar id:
    """

    class Meta:
        name = "fieldType"

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
    access_handles: None | FieldType.AccessHandles = field(
        default=None,
        metadata={
            "name": "accessHandles",
            "type": "Element",
            "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
        },
    )
    array: None | FieldType.Array = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
        },
    )
    bit_offset: UnsignedIntExpression = field(
        metadata={
            "name": "bitOffset",
            "type": "Element",
            "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
        }
    )
    choice: Sequence[
        FieldType.FieldDefinitionRef
        | str
        | UnsignedPositiveIntExpression
        | bool
        | FieldType.Resets
        | FieldType.AliasOf
        | FieldType.FieldAccessPolicies
        | EnumeratedValues
    ] = field(
        default_factory=list,
        metadata={
            "type": "Elements",
            "choices": (
                {
                    "name": "fieldDefinitionRef",
                    "type": ForwardRef("FieldType.FieldDefinitionRef"),
                    "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
                },
                {
                    "name": "typeIdentifier",
                    "type": str,
                    "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
                },
                {
                    "name": "bitWidth",
                    "type": UnsignedPositiveIntExpression,
                    "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
                },
                {
                    "name": "volatile",
                    "type": bool,
                    "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
                },
                {
                    "name": "resets",
                    "type": ForwardRef("FieldType.Resets"),
                    "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
                },
                {
                    "name": "aliasOf",
                    "type": ForwardRef("FieldType.AliasOf"),
                    "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
                },
                {
                    "name": "fieldAccessPolicies",
                    "type": ForwardRef("FieldType.FieldAccessPolicies"),
                    "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
                },
                {
                    "name": "enumeratedValues",
                    "type": EnumeratedValues,
                    "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
                },
            ),
            "max_occurs": 6,
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
    class Array:
        dim: Sequence[Dim] = field(
            default_factory=list,
            metadata={
                "type": "Element",
                "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
                "min_occurs": 1,
            },
        )
        bit_stride: None | BitStride = field(
            default=None,
            metadata={
                "name": "bitStride",
                "type": "Element",
                "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
            },
        )

    @dataclass(slots=True, kw_only=True)
    class FieldDefinitionRef:
        value: str = field(default="")
        type_definitions: str = field(
            metadata={
                "name": "typeDefinitions",
                "type": "Attribute",
            }
        )

    @dataclass(slots=True, kw_only=True)
    class Resets:
        """
        :ivar reset: BitField reset value
        """

        reset: Sequence[Reset] = field(
            default_factory=list,
            metadata={
                "type": "Element",
                "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
                "min_occurs": 1,
            },
        )

    @dataclass(slots=True, kw_only=True)
    class AliasOf:
        address_space_ref_or_memory_map_ref_or_memory_remap_ref: Sequence[
            FieldType.AliasOf.AddressSpaceRef
            | FieldType.AliasOf.MemoryMapRef
            | MemoryRemapRef
        ] = field(
            default_factory=list,
            metadata={
                "type": "Elements",
                "choices": (
                    {
                        "name": "addressSpaceRef",
                        "type": ForwardRef(
                            "FieldType.AliasOf.AddressSpaceRef"
                        ),
                        "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
                    },
                    {
                        "name": "memoryMapRef",
                        "type": ForwardRef("FieldType.AliasOf.MemoryMapRef"),
                        "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
                    },
                    {
                        "name": "memoryRemapRef",
                        "type": MemoryRemapRef,
                        "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
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
                "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
            },
        )
        address_block_ref: None | AddressBlockRef = field(
            default=None,
            metadata={
                "name": "addressBlockRef",
                "type": "Element",
                "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
            },
        )
        register_file_ref: Sequence[RegisterFileRef] = field(
            default_factory=list,
            metadata={
                "name": "registerFileRef",
                "type": "Element",
                "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
            },
        )
        register_ref: None | RegisterRef = field(
            default=None,
            metadata={
                "name": "registerRef",
                "type": "Element",
                "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
            },
        )
        alternate_register_ref: None | AlternateRegisterRef = field(
            default=None,
            metadata={
                "name": "alternateRegisterRef",
                "type": "Element",
                "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
            },
        )
        field_ref: FieldRef = field(
            metadata={
                "name": "fieldRef",
                "type": "Element",
                "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
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

    @dataclass(slots=True, kw_only=True)
    class FieldAccessPolicies(FieldAccessPropertiesType):
        field_access_policy: Sequence[
            FieldType.FieldAccessPolicies.FieldAccessPolicy
        ] = field(
            default_factory=list,
            metadata={
                "name": "fieldAccessPolicy",
                "type": "Element",
                "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
                "min_occurs": 1,
            },
        )

        @dataclass(slots=True, kw_only=True)
        class FieldAccessPolicy:
            """
            :ivar mode_ref:
            :ivar choice:
            :ivar broadcasts:
            :ivar access_restrictions: Access restrictions
            :ivar testable: Can the field be tested with an automated
                register test routine. The presumed value is true if not
                specified.
            :ivar reserved: Indicates that the field should be
                documented as reserved. The presumed value is '0' if not
                present.
            :ivar vendor_extensions:
            :ivar id:
            """

            mode_ref: Sequence[ModeRef] = field(
                default_factory=list,
                metadata={
                    "name": "modeRef",
                    "type": "Element",
                    "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
                },
            )
            choice: Sequence[
                FieldAccessPolicyDefinitionRef
                | Access
                | ModifiedWriteValue
                | WriteValueConstraint
                | ReadAction
                | ReadResponse
            ] = field(
                default_factory=list,
                metadata={
                    "type": "Elements",
                    "choices": (
                        {
                            "name": "fieldAccessPolicyDefinitionRef",
                            "type": FieldAccessPolicyDefinitionRef,
                            "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
                        },
                        {
                            "name": "access",
                            "type": Access,
                            "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
                        },
                        {
                            "name": "modifiedWriteValue",
                            "type": ModifiedWriteValue,
                            "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
                        },
                        {
                            "name": "writeValueConstraint",
                            "type": WriteValueConstraint,
                            "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
                        },
                        {
                            "name": "readAction",
                            "type": ReadAction,
                            "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
                        },
                        {
                            "name": "readResponse",
                            "type": ReadResponse,
                            "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
                        },
                    ),
                    "max_occurs": 5,
                },
            )
            broadcasts: (
                None
                | FieldType.FieldAccessPolicies.FieldAccessPolicy.Broadcasts
            ) = field(
                default=None,
                metadata={
                    "type": "Element",
                    "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
                },
            )
            access_restrictions: None | AccessRestrictions = field(
                default=None,
                metadata={
                    "name": "accessRestrictions",
                    "type": "Element",
                    "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
                },
            )
            testable: (
                None | FieldType.FieldAccessPolicies.FieldAccessPolicy.Testable
            ) = field(
                default=None,
                metadata={
                    "type": "Element",
                    "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
                },
            )
            reserved: None | UnsignedBitExpression = field(
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
            class Broadcasts:
                broadcast_to: Sequence[
                    FieldType.FieldAccessPolicies.FieldAccessPolicy.Broadcasts.BroadcastTo
                ] = field(
                    default_factory=list,
                    metadata={
                        "name": "broadcastTo",
                        "type": "Element",
                        "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
                        "min_occurs": 1,
                    },
                )

                @dataclass(slots=True, kw_only=True)
                class BroadcastTo:
                    address_space_ref_or_memory_map_ref_or_memory_remap_ref: Sequence[
                        FieldType.FieldAccessPolicies.FieldAccessPolicy.Broadcasts.BroadcastTo.AddressSpaceRef
                        | FieldType.FieldAccessPolicies.FieldAccessPolicy.Broadcasts.BroadcastTo.MemoryMapRef
                        | MemoryRemapRef
                    ] = field(
                        default_factory=list,
                        metadata={
                            "type": "Elements",
                            "choices": (
                                {
                                    "name": "addressSpaceRef",
                                    "type": ForwardRef(
                                        "FieldType.FieldAccessPolicies.FieldAccessPolicy.Broadcasts.BroadcastTo.AddressSpaceRef"
                                    ),
                                    "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
                                },
                                {
                                    "name": "memoryMapRef",
                                    "type": ForwardRef(
                                        "FieldType.FieldAccessPolicies.FieldAccessPolicy.Broadcasts.BroadcastTo.MemoryMapRef"
                                    ),
                                    "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
                                },
                                {
                                    "name": "memoryRemapRef",
                                    "type": MemoryRemapRef,
                                    "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
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
                            "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
                        },
                    )
                    address_block_ref: None | AddressBlockRef = field(
                        default=None,
                        metadata={
                            "name": "addressBlockRef",
                            "type": "Element",
                            "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
                        },
                    )
                    register_file_ref: Sequence[RegisterFileRef] = field(
                        default_factory=list,
                        metadata={
                            "name": "registerFileRef",
                            "type": "Element",
                            "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
                        },
                    )
                    register_ref: None | RegisterRef = field(
                        default=None,
                        metadata={
                            "name": "registerRef",
                            "type": "Element",
                            "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
                        },
                    )
                    alternate_register_ref: None | AlternateRegisterRef = (
                        field(
                            default=None,
                            metadata={
                                "name": "alternateRegisterRef",
                                "type": "Element",
                                "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
                            },
                        )
                    )
                    field_ref: FieldRef = field(
                        metadata={
                            "name": "fieldRef",
                            "type": "Element",
                            "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
                        }
                    )
                    id: None | str = field(
                        default=None,
                        metadata={
                            "type": "Attribute",
                            "namespace": "http://www.w3.org/XML/1998/namespace",
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
            class Testable:
                """
                :ivar value:
                :ivar test_constraint: Constraint for an automated
                    register test routine. 'unconstrained' (default)
                    means may read and write all legal values. 'restore'
                    means may read and write legal values but the value
                    must be restored to the initially read value before
                    accessing another register. 'writeAsRead' has
                    limitations on testability where only the value read
                    before a write may be written to the field.
                    'readOnly' has limitations on testability where
                    values may only be read from the field.
                """

                value: bool = field()
                test_constraint: TestableTestConstraint = field(
                    default=TestableTestConstraint.UNCONSTRAINED,
                    metadata={
                        "name": "testConstraint",
                        "type": "Attribute",
                    },
                )

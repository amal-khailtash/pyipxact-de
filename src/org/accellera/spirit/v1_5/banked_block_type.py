from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

from org.accellera.spirit.v1_5.access import Access
from org.accellera.spirit.v1_5.description import Description
from org.accellera.spirit.v1_5.display_name import DisplayName
from org.accellera.spirit.v1_5.field_type import FieldType
from org.accellera.spirit.v1_5.format_type import FormatType
from org.accellera.spirit.v1_5.parameters import Parameters
from org.accellera.spirit.v1_5.range_type_type import RangeTypeType
from org.accellera.spirit.v1_5.register_file import RegisterFile
from org.accellera.spirit.v1_5.resolve_type import ResolveType
from org.accellera.spirit.v1_5.usage_type import UsageType
from org.accellera.spirit.v1_5.vendor_extensions import VendorExtensions
from org.accellera.spirit.v1_5.volatile import Volatile

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5"


@dataclass(slots=True, kw_only=True)
class BankedBlockType:
    """
    Address blocks inside a bank do not specify address.

    :ivar name: Unique name
    :ivar display_name:
    :ivar description:
    :ivar range: The address range of an address block.  Expressed as
        the number of addressable units accessible to the block. The
        range and the width are related by the following formulas:
        number_of_bits_in_block = spirit:addressUnitBits * spirit:range
        number_of_rows_in_block = number_of_bits_in_block / spirit:width
    :ivar width: The bit width of a row in the address block. The range
        and the width are related by the following formulas:
        number_of_bits_in_block = spirit:addressUnitBits * spirit:range
        number_of_rows_in_block = number_of_bits_in_block / spirit:width
    :ivar usage: Indicates the usage of this block.  Possible values are
        'memory', 'register' and 'reserved'.
    :ivar volatile:
    :ivar access:
    :ivar parameters: Any additional parameters needed to describe this
        address block to the generators.
    :ivar register: A single register
    :ivar register_file: A structure of registers and register files
    :ivar vendor_extensions:
    :ivar id:
    """

    class Meta:
        name = "bankedBlockType"

    name: str = field(
        metadata={
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
        }
    )
    display_name: None | DisplayName = field(
        default=None,
        metadata={
            "name": "displayName",
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
        },
    )
    description: None | Description = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
        },
    )
    range: BankedBlockType.Range = field(
        metadata={
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
        }
    )
    width: BankedBlockType.Width = field(
        metadata={
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
        }
    )
    usage: None | UsageType = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
        },
    )
    volatile: None | Volatile = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
        },
    )
    access: None | Access = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
        },
    )
    parameters: None | Parameters = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
        },
    )
    register: Sequence[BankedBlockType.Register] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
        },
    )
    register_file: Sequence[RegisterFile] = field(
        default_factory=list,
        metadata={
            "name": "registerFile",
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
        },
    )
    vendor_extensions: None | VendorExtensions = field(
        default=None,
        metadata={
            "name": "vendorExtensions",
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
        },
    )
    id: None | str = field(
        default=None,
        metadata={
            "type": "Attribute",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
        },
    )

    @dataclass(slots=True, kw_only=True)
    class Range:
        value: str = field(
            default="",
            metadata={
                "pattern": r"[+]?(0x|0X|#)?[0]*[1-9a-fA-F][0-9a-fA-F]*[kmgtKMGT]?",
            },
        )
        format: FormatType = field(
            default=FormatType.LONG,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
            },
        )
        resolve: ResolveType = field(
            default=ResolveType.IMMEDIATE,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
            },
        )
        id: None | str = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
            },
        )
        dependency: None | str = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
            },
        )
        any_attributes: Mapping[str, str] = field(
            default_factory=dict,
            metadata={
                "type": "Attributes",
                "namespace": "##any",
            },
        )
        choice_ref: None | str = field(
            default=None,
            metadata={
                "name": "choiceRef",
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
            },
        )
        order: None | float = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
            },
        )
        config_groups: Sequence[str] = field(
            default_factory=list,
            metadata={
                "name": "configGroups",
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                "tokens": True,
            },
        )
        bit_string_length: None | int = field(
            default=None,
            metadata={
                "name": "bitStringLength",
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
            },
        )
        minimum: None | str = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
            },
        )
        maximum: None | str = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
            },
        )
        range_type: RangeTypeType = field(
            default=RangeTypeType.FLOAT,
            metadata={
                "name": "rangeType",
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
            },
        )
        prompt: None | str = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
            },
        )

    @dataclass(slots=True, kw_only=True)
    class Width:
        value: int = field()
        format: FormatType = field(
            default=FormatType.LONG,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
            },
        )
        resolve: ResolveType = field(
            default=ResolveType.IMMEDIATE,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
            },
        )
        id: None | str = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
            },
        )
        dependency: None | str = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
            },
        )
        any_attributes: Mapping[str, str] = field(
            default_factory=dict,
            metadata={
                "type": "Attributes",
                "namespace": "##any",
            },
        )
        choice_ref: None | str = field(
            default=None,
            metadata={
                "name": "choiceRef",
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
            },
        )
        order: None | float = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
            },
        )
        config_groups: Sequence[str] = field(
            default_factory=list,
            metadata={
                "name": "configGroups",
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                "tokens": True,
            },
        )
        bit_string_length: None | int = field(
            default=None,
            metadata={
                "name": "bitStringLength",
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
            },
        )
        minimum: None | str = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
            },
        )
        maximum: None | str = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
            },
        )
        range_type: RangeTypeType = field(
            default=RangeTypeType.FLOAT,
            metadata={
                "name": "rangeType",
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
            },
        )
        prompt: None | str = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
            },
        )

    @dataclass(slots=True, kw_only=True)
    class Register:
        """
        :ivar name: Unique name
        :ivar display_name:
        :ivar description:
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
        :ivar reset: Register value at reset.
        :ivar field_value: Describes individual bit fields within the
            register.
        :ivar alternate_registers: Alternate definitions for the current
            register
        :ivar parameters:
        :ivar vendor_extensions:
        :ivar id:
        """

        name: str = field(
            metadata={
                "type": "Element",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
            }
        )
        display_name: None | DisplayName = field(
            default=None,
            metadata={
                "name": "displayName",
                "type": "Element",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
            },
        )
        description: None | Description = field(
            default=None,
            metadata={
                "type": "Element",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
            },
        )
        dim: Sequence[int] = field(
            default_factory=list,
            metadata={
                "type": "Element",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
            },
        )
        address_offset: str = field(
            metadata={
                "name": "addressOffset",
                "type": "Element",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                "pattern": r"[+]?(0x|0X|#)?[0-9a-fA-F]+[kmgtKMGT]?",
            }
        )
        type_identifier: None | str = field(
            default=None,
            metadata={
                "name": "typeIdentifier",
                "type": "Element",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
            },
        )
        size: BankedBlockType.Register.Size = field(
            metadata={
                "type": "Element",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
            }
        )
        volatile: None | Volatile = field(
            default=None,
            metadata={
                "type": "Element",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
            },
        )
        access: None | Access = field(
            default=None,
            metadata={
                "type": "Element",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
            },
        )
        reset: None | BankedBlockType.Register.Reset = field(
            default=None,
            metadata={
                "type": "Element",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
            },
        )
        field_value: Sequence[FieldType] = field(
            default_factory=list,
            metadata={
                "name": "field",
                "type": "Element",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
            },
        )
        alternate_registers: (
            None | BankedBlockType.Register.AlternateRegisters
        ) = field(
            default=None,
            metadata={
                "name": "alternateRegisters",
                "type": "Element",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
            },
        )
        parameters: None | Parameters = field(
            default=None,
            metadata={
                "type": "Element",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
            },
        )
        vendor_extensions: None | VendorExtensions = field(
            default=None,
            metadata={
                "name": "vendorExtensions",
                "type": "Element",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
            },
        )
        id: None | str = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
            },
        )

        @dataclass(slots=True, kw_only=True)
        class AlternateRegisters:
            """
            :ivar alternate_register: Alternate definition for the
                current register
            """

            alternate_register: Sequence[
                BankedBlockType.Register.AlternateRegisters.AlternateRegister
            ] = field(
                default_factory=list,
                metadata={
                    "name": "alternateRegister",
                    "type": "Element",
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                    "min_occurs": 1,
                },
            )

            @dataclass(slots=True, kw_only=True)
            class AlternateRegister:
                """
                :ivar name: Unique name
                :ivar display_name:
                :ivar description:
                :ivar alternate_groups: Defines a list of grouping names
                    that this register description belongs.
                :ivar type_identifier: Identifier name used to indicate
                    that multiple register elements contain the exact
                    same information for the elements in the
                    alternateRegisterDefinitionGroup.
                :ivar volatile:
                :ivar access:
                :ivar reset: Register value at reset.
                :ivar field_value: Describes individual bit fields
                    within the register.
                :ivar parameters:
                :ivar vendor_extensions:
                :ivar id:
                """

                name: str = field(
                    metadata={
                        "type": "Element",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                    }
                )
                display_name: None | DisplayName = field(
                    default=None,
                    metadata={
                        "name": "displayName",
                        "type": "Element",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                    },
                )
                description: None | Description = field(
                    default=None,
                    metadata={
                        "type": "Element",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                    },
                )
                alternate_groups: BankedBlockType.Register.AlternateRegisters.AlternateRegister.AlternateGroups = field(
                    metadata={
                        "name": "alternateGroups",
                        "type": "Element",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                    }
                )
                type_identifier: None | str = field(
                    default=None,
                    metadata={
                        "name": "typeIdentifier",
                        "type": "Element",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                    },
                )
                volatile: None | Volatile = field(
                    default=None,
                    metadata={
                        "type": "Element",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                    },
                )
                access: None | Access = field(
                    default=None,
                    metadata={
                        "type": "Element",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                    },
                )
                reset: (
                    None
                    | BankedBlockType.Register.AlternateRegisters.AlternateRegister.Reset
                ) = field(
                    default=None,
                    metadata={
                        "type": "Element",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                    },
                )
                field_value: Sequence[FieldType] = field(
                    default_factory=list,
                    metadata={
                        "name": "field",
                        "type": "Element",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                    },
                )
                parameters: None | Parameters = field(
                    default=None,
                    metadata={
                        "type": "Element",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                    },
                )
                vendor_extensions: None | VendorExtensions = field(
                    default=None,
                    metadata={
                        "name": "vendorExtensions",
                        "type": "Element",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                    },
                )
                id: None | str = field(
                    default=None,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                    },
                )

                @dataclass(slots=True, kw_only=True)
                class AlternateGroups:
                    """
                    :ivar alternate_group: Defines a grouping name that
                        this register description belongs.
                    """

                    alternate_group: Sequence[str] = field(
                        default_factory=list,
                        metadata={
                            "name": "alternateGroup",
                            "type": "Element",
                            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                            "min_occurs": 1,
                        },
                    )

                @dataclass(slots=True, kw_only=True)
                class Reset:
                    """
                    :ivar value: The value itself.
                    :ivar mask: Mask to be anded with the value before
                        comparing to the reset value.
                    """

                    value: BankedBlockType.Register.AlternateRegisters.AlternateRegister.Reset.Value = field(
                        metadata={
                            "type": "Element",
                            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                        }
                    )
                    mask: (
                        None
                        | BankedBlockType.Register.AlternateRegisters.AlternateRegister.Reset.Mask
                    ) = field(
                        default=None,
                        metadata={
                            "type": "Element",
                            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                        },
                    )

                    @dataclass(slots=True, kw_only=True)
                    class Value:
                        value: str = field(
                            default="",
                            metadata={
                                "pattern": r"[+]?(0x|0X|#)?[0-9a-fA-F]+[kmgtKMGT]?",
                            },
                        )
                        format: FormatType = field(
                            default=FormatType.LONG,
                            metadata={
                                "type": "Attribute",
                                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                            },
                        )
                        resolve: ResolveType = field(
                            default=ResolveType.IMMEDIATE,
                            metadata={
                                "type": "Attribute",
                                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                            },
                        )
                        id: None | str = field(
                            default=None,
                            metadata={
                                "type": "Attribute",
                                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                            },
                        )
                        dependency: None | str = field(
                            default=None,
                            metadata={
                                "type": "Attribute",
                                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                            },
                        )
                        any_attributes: Mapping[str, str] = field(
                            default_factory=dict,
                            metadata={
                                "type": "Attributes",
                                "namespace": "##any",
                            },
                        )
                        choice_ref: None | str = field(
                            default=None,
                            metadata={
                                "name": "choiceRef",
                                "type": "Attribute",
                                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                            },
                        )
                        order: None | float = field(
                            default=None,
                            metadata={
                                "type": "Attribute",
                                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                            },
                        )
                        config_groups: Sequence[str] = field(
                            default_factory=list,
                            metadata={
                                "name": "configGroups",
                                "type": "Attribute",
                                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                                "tokens": True,
                            },
                        )
                        bit_string_length: None | int = field(
                            default=None,
                            metadata={
                                "name": "bitStringLength",
                                "type": "Attribute",
                                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                            },
                        )
                        minimum: None | str = field(
                            default=None,
                            metadata={
                                "type": "Attribute",
                                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                            },
                        )
                        maximum: None | str = field(
                            default=None,
                            metadata={
                                "type": "Attribute",
                                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                            },
                        )
                        range_type: RangeTypeType = field(
                            default=RangeTypeType.FLOAT,
                            metadata={
                                "name": "rangeType",
                                "type": "Attribute",
                                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                            },
                        )
                        prompt: None | str = field(
                            default=None,
                            metadata={
                                "type": "Attribute",
                                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                            },
                        )

                    @dataclass(slots=True, kw_only=True)
                    class Mask:
                        value: str = field(
                            default="",
                            metadata={
                                "pattern": r"[+]?(0x|0X|#)?[0-9a-fA-F]+[kmgtKMGT]?",
                            },
                        )
                        format: FormatType = field(
                            default=FormatType.LONG,
                            metadata={
                                "type": "Attribute",
                                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                            },
                        )
                        resolve: ResolveType = field(
                            default=ResolveType.IMMEDIATE,
                            metadata={
                                "type": "Attribute",
                                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                            },
                        )
                        id: None | str = field(
                            default=None,
                            metadata={
                                "type": "Attribute",
                                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                            },
                        )
                        dependency: None | str = field(
                            default=None,
                            metadata={
                                "type": "Attribute",
                                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                            },
                        )
                        any_attributes: Mapping[str, str] = field(
                            default_factory=dict,
                            metadata={
                                "type": "Attributes",
                                "namespace": "##any",
                            },
                        )
                        choice_ref: None | str = field(
                            default=None,
                            metadata={
                                "name": "choiceRef",
                                "type": "Attribute",
                                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                            },
                        )
                        order: None | float = field(
                            default=None,
                            metadata={
                                "type": "Attribute",
                                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                            },
                        )
                        config_groups: Sequence[str] = field(
                            default_factory=list,
                            metadata={
                                "name": "configGroups",
                                "type": "Attribute",
                                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                                "tokens": True,
                            },
                        )
                        bit_string_length: None | int = field(
                            default=None,
                            metadata={
                                "name": "bitStringLength",
                                "type": "Attribute",
                                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                            },
                        )
                        minimum: None | str = field(
                            default=None,
                            metadata={
                                "type": "Attribute",
                                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                            },
                        )
                        maximum: None | str = field(
                            default=None,
                            metadata={
                                "type": "Attribute",
                                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                            },
                        )
                        range_type: RangeTypeType = field(
                            default=RangeTypeType.FLOAT,
                            metadata={
                                "name": "rangeType",
                                "type": "Attribute",
                                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                            },
                        )
                        prompt: None | str = field(
                            default=None,
                            metadata={
                                "type": "Attribute",
                                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                            },
                        )

        @dataclass(slots=True, kw_only=True)
        class Size:
            value: int = field()
            format: FormatType = field(
                default=FormatType.LONG,
                metadata={
                    "type": "Attribute",
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                },
            )
            resolve: ResolveType = field(
                default=ResolveType.IMMEDIATE,
                metadata={
                    "type": "Attribute",
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                },
            )
            id: None | str = field(
                default=None,
                metadata={
                    "type": "Attribute",
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                },
            )
            dependency: None | str = field(
                default=None,
                metadata={
                    "type": "Attribute",
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                },
            )
            any_attributes: Mapping[str, str] = field(
                default_factory=dict,
                metadata={
                    "type": "Attributes",
                    "namespace": "##any",
                },
            )
            choice_ref: None | str = field(
                default=None,
                metadata={
                    "name": "choiceRef",
                    "type": "Attribute",
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                },
            )
            order: None | float = field(
                default=None,
                metadata={
                    "type": "Attribute",
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                },
            )
            config_groups: Sequence[str] = field(
                default_factory=list,
                metadata={
                    "name": "configGroups",
                    "type": "Attribute",
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                    "tokens": True,
                },
            )
            bit_string_length: None | int = field(
                default=None,
                metadata={
                    "name": "bitStringLength",
                    "type": "Attribute",
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                },
            )
            minimum: None | str = field(
                default=None,
                metadata={
                    "type": "Attribute",
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                },
            )
            maximum: None | str = field(
                default=None,
                metadata={
                    "type": "Attribute",
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                },
            )
            range_type: RangeTypeType = field(
                default=RangeTypeType.FLOAT,
                metadata={
                    "name": "rangeType",
                    "type": "Attribute",
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                },
            )
            prompt: None | str = field(
                default=None,
                metadata={
                    "type": "Attribute",
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                },
            )

        @dataclass(slots=True, kw_only=True)
        class Reset:
            """
            :ivar value: The value itself.
            :ivar mask: Mask to be anded with the value before comparing
                to the reset value.
            """

            value: BankedBlockType.Register.Reset.Value = field(
                metadata={
                    "type": "Element",
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                }
            )
            mask: None | BankedBlockType.Register.Reset.Mask = field(
                default=None,
                metadata={
                    "type": "Element",
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                },
            )

            @dataclass(slots=True, kw_only=True)
            class Value:
                value: str = field(
                    default="",
                    metadata={
                        "pattern": r"[+]?(0x|0X|#)?[0-9a-fA-F]+[kmgtKMGT]?",
                    },
                )
                format: FormatType = field(
                    default=FormatType.LONG,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                    },
                )
                resolve: ResolveType = field(
                    default=ResolveType.IMMEDIATE,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                    },
                )
                id: None | str = field(
                    default=None,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                    },
                )
                dependency: None | str = field(
                    default=None,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                    },
                )
                any_attributes: Mapping[str, str] = field(
                    default_factory=dict,
                    metadata={
                        "type": "Attributes",
                        "namespace": "##any",
                    },
                )
                choice_ref: None | str = field(
                    default=None,
                    metadata={
                        "name": "choiceRef",
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                    },
                )
                order: None | float = field(
                    default=None,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                    },
                )
                config_groups: Sequence[str] = field(
                    default_factory=list,
                    metadata={
                        "name": "configGroups",
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                        "tokens": True,
                    },
                )
                bit_string_length: None | int = field(
                    default=None,
                    metadata={
                        "name": "bitStringLength",
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                    },
                )
                minimum: None | str = field(
                    default=None,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                    },
                )
                maximum: None | str = field(
                    default=None,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                    },
                )
                range_type: RangeTypeType = field(
                    default=RangeTypeType.FLOAT,
                    metadata={
                        "name": "rangeType",
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                    },
                )
                prompt: None | str = field(
                    default=None,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                    },
                )

            @dataclass(slots=True, kw_only=True)
            class Mask:
                value: str = field(
                    default="",
                    metadata={
                        "pattern": r"[+]?(0x|0X|#)?[0-9a-fA-F]+[kmgtKMGT]?",
                    },
                )
                format: FormatType = field(
                    default=FormatType.LONG,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                    },
                )
                resolve: ResolveType = field(
                    default=ResolveType.IMMEDIATE,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                    },
                )
                id: None | str = field(
                    default=None,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                    },
                )
                dependency: None | str = field(
                    default=None,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                    },
                )
                any_attributes: Mapping[str, str] = field(
                    default_factory=dict,
                    metadata={
                        "type": "Attributes",
                        "namespace": "##any",
                    },
                )
                choice_ref: None | str = field(
                    default=None,
                    metadata={
                        "name": "choiceRef",
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                    },
                )
                order: None | float = field(
                    default=None,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                    },
                )
                config_groups: Sequence[str] = field(
                    default_factory=list,
                    metadata={
                        "name": "configGroups",
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                        "tokens": True,
                    },
                )
                bit_string_length: None | int = field(
                    default=None,
                    metadata={
                        "name": "bitStringLength",
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                    },
                )
                minimum: None | str = field(
                    default=None,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                    },
                )
                maximum: None | str = field(
                    default=None,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                    },
                )
                range_type: RangeTypeType = field(
                    default=RangeTypeType.FLOAT,
                    metadata={
                        "name": "rangeType",
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                    },
                )
                prompt: None | str = field(
                    default=None,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                    },
                )

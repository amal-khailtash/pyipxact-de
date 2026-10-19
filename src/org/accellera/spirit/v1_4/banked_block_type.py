from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

from org.accellera.spirit.v1_4.access import Access
from org.accellera.spirit.v1_4.field_type import FieldType
from org.accellera.spirit.v1_4.format_type import FormatType
from org.accellera.spirit.v1_4.parameters import Parameters
from org.accellera.spirit.v1_4.range_type_type import RangeTypeType
from org.accellera.spirit.v1_4.resolve_type import ResolveType
from org.accellera.spirit.v1_4.usage_type import UsageType
from org.accellera.spirit.v1_4.vendor_extensions import VendorExtensions
from org.accellera.spirit.v1_4.volatile import Volatile

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4"


@dataclass(slots=True, kw_only=True)
class BankedBlockType:
    """
    Address blocks inside a bank do not specify address.

    :ivar name: Unique name
    :ivar display_name: Element name for display purposes. Typically a
        few words providing a more detailed and/or user-friendly name
        than the spirit:name.
    :ivar description: Full description string, typically for
        documentation
    :ivar range: The address range of an address block.  Expressed as
        the number of addressable units accessible to the block. The
        range and the width are related by the following formulas:
        number_of_bits_in_block = spirit:bitsInLAU * spirit:range
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
    :ivar register:
    :ivar vendor_extensions:
    """

    class Meta:
        name = "bankedBlockType"

    name: str = field(
        metadata={
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
        }
    )
    display_name: None | str = field(
        default=None,
        metadata={
            "name": "displayName",
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
        },
    )
    description: None | str = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
        },
    )
    range: BankedBlockType.Range = field(
        metadata={
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
        }
    )
    width: BankedBlockType.Width = field(
        metadata={
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
        }
    )
    usage: None | UsageType = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
        },
    )
    volatile: None | Volatile = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
        },
    )
    access: None | Access = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
        },
    )
    parameters: None | Parameters = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
        },
    )
    register: Sequence[BankedBlockType.Register] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
        },
    )
    vendor_extensions: None | VendorExtensions = field(
        default=None,
        metadata={
            "name": "vendorExtensions",
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
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
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
            },
        )
        resolve: ResolveType = field(
            default=ResolveType.IMMEDIATE,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
            },
        )
        id: None | str = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
            },
        )
        dependency: None | str = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
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
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
            },
        )
        order: None | float = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
            },
        )
        config_groups: Sequence[str] = field(
            default_factory=list,
            metadata={
                "name": "configGroups",
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                "tokens": True,
            },
        )
        bit_string_length: None | int = field(
            default=None,
            metadata={
                "name": "bitStringLength",
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
            },
        )
        minimum: None | str = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
            },
        )
        maximum: None | str = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
            },
        )
        range_type: RangeTypeType = field(
            default=RangeTypeType.FLOAT,
            metadata={
                "name": "rangeType",
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
            },
        )
        prompt: None | str = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
            },
        )

    @dataclass(slots=True, kw_only=True)
    class Width:
        value: int = field()
        format: FormatType = field(
            default=FormatType.LONG,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
            },
        )
        resolve: ResolveType = field(
            default=ResolveType.IMMEDIATE,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
            },
        )
        id: None | str = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
            },
        )
        dependency: None | str = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
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
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
            },
        )
        order: None | float = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
            },
        )
        config_groups: Sequence[str] = field(
            default_factory=list,
            metadata={
                "name": "configGroups",
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                "tokens": True,
            },
        )
        bit_string_length: None | int = field(
            default=None,
            metadata={
                "name": "bitStringLength",
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
            },
        )
        minimum: None | str = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
            },
        )
        maximum: None | str = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
            },
        )
        range_type: RangeTypeType = field(
            default=RangeTypeType.FLOAT,
            metadata={
                "name": "rangeType",
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
            },
        )
        prompt: None | str = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
            },
        )

    @dataclass(slots=True, kw_only=True)
    class Register:
        """
        :ivar name: Unique name
        :ivar display_name: Element name for display purposes. Typically
            a few words providing a more detailed and/or user-friendly
            name than the spirit:name.
        :ivar description: Full description string, typically for
            documentation
        :ivar dim: Dimensions a register array, the semantics for dim
            elements are the same as the C language standard for the
            layout of memory in multidimensional arrays.
        :ivar address_offset: Offset from the address block's
            baseAddress.
        :ivar size: Size in bits.
        :ivar volatile:
        :ivar access:
        :ivar reset: Register value at reset.
        :ivar field_value: Describes individual bit fields within the
            register.
        :ivar parameters:
        :ivar vendor_extensions:
        """

        name: str = field(
            metadata={
                "type": "Element",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
            }
        )
        display_name: None | str = field(
            default=None,
            metadata={
                "name": "displayName",
                "type": "Element",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
            },
        )
        description: None | str = field(
            default=None,
            metadata={
                "type": "Element",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
            },
        )
        dim: Sequence[int] = field(
            default_factory=list,
            metadata={
                "type": "Element",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
            },
        )
        address_offset: str = field(
            metadata={
                "name": "addressOffset",
                "type": "Element",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                "pattern": r"[+]?(0x|0X|#)?[0-9a-fA-F]+[kmgtKMGT]?",
            }
        )
        size: BankedBlockType.Register.Size = field(
            metadata={
                "type": "Element",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
            }
        )
        volatile: None | Volatile = field(
            default=None,
            metadata={
                "type": "Element",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
            },
        )
        access: None | Access = field(
            default=None,
            metadata={
                "type": "Element",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
            },
        )
        reset: None | BankedBlockType.Register.Reset = field(
            default=None,
            metadata={
                "type": "Element",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
            },
        )
        field_value: Sequence[FieldType] = field(
            default_factory=list,
            metadata={
                "name": "field",
                "type": "Element",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
            },
        )
        parameters: None | Parameters = field(
            default=None,
            metadata={
                "type": "Element",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
            },
        )
        vendor_extensions: None | VendorExtensions = field(
            default=None,
            metadata={
                "name": "vendorExtensions",
                "type": "Element",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
            },
        )

        @dataclass(slots=True, kw_only=True)
        class Size:
            value: int = field()
            format: FormatType = field(
                default=FormatType.LONG,
                metadata={
                    "type": "Attribute",
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                },
            )
            resolve: ResolveType = field(
                default=ResolveType.IMMEDIATE,
                metadata={
                    "type": "Attribute",
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                },
            )
            id: None | str = field(
                default=None,
                metadata={
                    "type": "Attribute",
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                },
            )
            dependency: None | str = field(
                default=None,
                metadata={
                    "type": "Attribute",
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
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
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                },
            )
            order: None | float = field(
                default=None,
                metadata={
                    "type": "Attribute",
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                },
            )
            config_groups: Sequence[str] = field(
                default_factory=list,
                metadata={
                    "name": "configGroups",
                    "type": "Attribute",
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                    "tokens": True,
                },
            )
            bit_string_length: None | int = field(
                default=None,
                metadata={
                    "name": "bitStringLength",
                    "type": "Attribute",
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                },
            )
            minimum: None | str = field(
                default=None,
                metadata={
                    "type": "Attribute",
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                },
            )
            maximum: None | str = field(
                default=None,
                metadata={
                    "type": "Attribute",
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                },
            )
            range_type: RangeTypeType = field(
                default=RangeTypeType.FLOAT,
                metadata={
                    "name": "rangeType",
                    "type": "Attribute",
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                },
            )
            prompt: None | str = field(
                default=None,
                metadata={
                    "type": "Attribute",
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
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
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                }
            )
            mask: None | BankedBlockType.Register.Reset.Mask = field(
                default=None,
                metadata={
                    "type": "Element",
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
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
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                    },
                )
                resolve: ResolveType = field(
                    default=ResolveType.IMMEDIATE,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                    },
                )
                id: None | str = field(
                    default=None,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                    },
                )
                dependency: None | str = field(
                    default=None,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
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
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                    },
                )
                order: None | float = field(
                    default=None,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                    },
                )
                config_groups: Sequence[str] = field(
                    default_factory=list,
                    metadata={
                        "name": "configGroups",
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                        "tokens": True,
                    },
                )
                bit_string_length: None | int = field(
                    default=None,
                    metadata={
                        "name": "bitStringLength",
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                    },
                )
                minimum: None | str = field(
                    default=None,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                    },
                )
                maximum: None | str = field(
                    default=None,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                    },
                )
                range_type: RangeTypeType = field(
                    default=RangeTypeType.FLOAT,
                    metadata={
                        "name": "rangeType",
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                    },
                )
                prompt: None | str = field(
                    default=None,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
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
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                    },
                )
                resolve: ResolveType = field(
                    default=ResolveType.IMMEDIATE,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                    },
                )
                id: None | str = field(
                    default=None,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                    },
                )
                dependency: None | str = field(
                    default=None,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
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
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                    },
                )
                order: None | float = field(
                    default=None,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                    },
                )
                config_groups: Sequence[str] = field(
                    default_factory=list,
                    metadata={
                        "name": "configGroups",
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                        "tokens": True,
                    },
                )
                bit_string_length: None | int = field(
                    default=None,
                    metadata={
                        "name": "bitStringLength",
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                    },
                )
                minimum: None | str = field(
                    default=None,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                    },
                )
                maximum: None | str = field(
                    default=None,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                    },
                )
                range_type: RangeTypeType = field(
                    default=RangeTypeType.FLOAT,
                    metadata={
                        "name": "rangeType",
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                    },
                )
                prompt: None | str = field(
                    default=None,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                    },
                )

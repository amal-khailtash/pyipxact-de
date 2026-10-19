from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

from org.accellera.spirit.v1685_2009.ve.ams.address_unit_bits import (
    AddressUnitBits,
)
from org.accellera.spirit.v1685_2009.ve.ams.description import Description
from org.accellera.spirit.v1685_2009.ve.ams.display_name import DisplayName
from org.accellera.spirit.v1685_2009.ve.ams.executable_image import (
    ExecutableImage,
)
from org.accellera.spirit.v1685_2009.ve.ams.format_type import FormatType
from org.accellera.spirit.v1685_2009.ve.ams.local_memory_map_type import (
    LocalMemoryMapType,
)
from org.accellera.spirit.v1685_2009.ve.ams.parameters import Parameters
from org.accellera.spirit.v1685_2009.ve.ams.range_type_type import (
    RangeTypeType,
)
from org.accellera.spirit.v1685_2009.ve.ams.resolve_type import ResolveType
from org.accellera.spirit.v1685_2009.ve.ams.vendor_extensions import (
    VendorExtensions,
)

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009"


@dataclass(slots=True, kw_only=True)
class AddressSpaces:
    """
    If this component is a bus master, this lists all the address spaces
    defined by the component.

    :ivar address_space: This defines a logical space, referenced by a
        bus master.
    """

    class Meta:
        name = "addressSpaces"
        namespace = (
            "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009"
        )

    address_space: Sequence[AddressSpaces.AddressSpace] = field(
        default_factory=list,
        metadata={
            "name": "addressSpace",
            "type": "Element",
            "min_occurs": 1,
        },
    )

    @dataclass(slots=True, kw_only=True)
    class AddressSpace:
        """
        :ivar name: Unique name
        :ivar display_name:
        :ivar description:
        :ivar range: The address range of an address block.  Expressed
            as the number of addressable units accessible to the block.
            The range and the width are related by the following
            formulas: number_of_bits_in_block = spirit:addressUnitBits *
            spirit:range number_of_rows_in_block =
            number_of_bits_in_block / spirit:width
        :ivar width: The bit width of a row in the address block. The
            range and the width are related by the following formulas:
            number_of_bits_in_block = spirit:addressUnitBits *
            spirit:range number_of_rows_in_block =
            number_of_bits_in_block / spirit:width
        :ivar segments: Address segments withing an addressSpace
        :ivar address_unit_bits:
        :ivar executable_image:
        :ivar local_memory_map: Provides the local memory map of an
            address space.  Blocks in this memory map are accessable to
            master interfaces on this component that reference this
            address space.   They are not accessable to any external
            master interface.
        :ivar parameters: Data specific to this address space.
        :ivar vendor_extensions:
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
        range: AddressSpaces.AddressSpace.Range = field(
            metadata={
                "type": "Element",
            }
        )
        width: AddressSpaces.AddressSpace.Width = field(
            metadata={
                "type": "Element",
            }
        )
        segments: None | AddressSpaces.AddressSpace.Segments = field(
            default=None,
            metadata={
                "type": "Element",
            },
        )
        address_unit_bits: None | AddressUnitBits = field(
            default=None,
            metadata={
                "name": "addressUnitBits",
                "type": "Element",
            },
        )
        executable_image: Sequence[ExecutableImage] = field(
            default_factory=list,
            metadata={
                "name": "executableImage",
                "type": "Element",
            },
        )
        local_memory_map: None | LocalMemoryMapType = field(
            default=None,
            metadata={
                "name": "localMemoryMap",
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

        @dataclass(slots=True, kw_only=True)
        class Segments:
            """
            :ivar segment: Address segment withing an addressSpace
            """

            segment: Sequence[AddressSpaces.AddressSpace.Segments.Segment] = (
                field(
                    default_factory=list,
                    metadata={
                        "type": "Element",
                        "min_occurs": 1,
                    },
                )
            )

            @dataclass(slots=True, kw_only=True)
            class Segment:
                """
                :ivar name: Unique name
                :ivar display_name:
                :ivar description:
                :ivar address_offset: Address offset of the segment
                    within the containing address space.
                :ivar range: The address range of asegment.  Expressed
                    as the number of addressable units accessible to the
                    segment.
                :ivar vendor_extensions:
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
                address_offset: AddressSpaces.AddressSpace.Segments.Segment.AddressOffset = field(
                    metadata={
                        "name": "addressOffset",
                        "type": "Element",
                    }
                )
                range: AddressSpaces.AddressSpace.Segments.Segment.Range = (
                    field(
                        metadata={
                            "type": "Element",
                        }
                    )
                )
                vendor_extensions: None | VendorExtensions = field(
                    default=None,
                    metadata={
                        "name": "vendorExtensions",
                        "type": "Element",
                    },
                )

                @dataclass(slots=True, kw_only=True)
                class AddressOffset:
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
                            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
                        },
                    )
                    resolve: ResolveType = field(
                        default=ResolveType.IMMEDIATE,
                        metadata={
                            "type": "Attribute",
                            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
                        },
                    )
                    id: None | str = field(
                        default=None,
                        metadata={
                            "type": "Attribute",
                            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
                        },
                    )
                    dependency: None | str = field(
                        default=None,
                        metadata={
                            "type": "Attribute",
                            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
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
                            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
                        },
                    )
                    order: None | float = field(
                        default=None,
                        metadata={
                            "type": "Attribute",
                            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
                        },
                    )
                    config_groups: Sequence[str] = field(
                        default_factory=list,
                        metadata={
                            "name": "configGroups",
                            "type": "Attribute",
                            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
                            "tokens": True,
                        },
                    )
                    bit_string_length: None | int = field(
                        default=None,
                        metadata={
                            "name": "bitStringLength",
                            "type": "Attribute",
                            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
                        },
                    )
                    minimum: None | str = field(
                        default=None,
                        metadata={
                            "type": "Attribute",
                            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
                        },
                    )
                    maximum: None | str = field(
                        default=None,
                        metadata={
                            "type": "Attribute",
                            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
                        },
                    )
                    range_type: RangeTypeType = field(
                        default=RangeTypeType.FLOAT,
                        metadata={
                            "name": "rangeType",
                            "type": "Attribute",
                            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
                        },
                    )
                    prompt: None | str = field(
                        default=None,
                        metadata={
                            "type": "Attribute",
                            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
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
                            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
                        },
                    )
                    resolve: ResolveType = field(
                        default=ResolveType.IMMEDIATE,
                        metadata={
                            "type": "Attribute",
                            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
                        },
                    )
                    id: None | str = field(
                        default=None,
                        metadata={
                            "type": "Attribute",
                            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
                        },
                    )
                    dependency: None | str = field(
                        default=None,
                        metadata={
                            "type": "Attribute",
                            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
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
                            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
                        },
                    )
                    order: None | float = field(
                        default=None,
                        metadata={
                            "type": "Attribute",
                            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
                        },
                    )
                    config_groups: Sequence[str] = field(
                        default_factory=list,
                        metadata={
                            "name": "configGroups",
                            "type": "Attribute",
                            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
                            "tokens": True,
                        },
                    )
                    bit_string_length: None | int = field(
                        default=None,
                        metadata={
                            "name": "bitStringLength",
                            "type": "Attribute",
                            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
                        },
                    )
                    minimum: None | str = field(
                        default=None,
                        metadata={
                            "type": "Attribute",
                            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
                        },
                    )
                    maximum: None | str = field(
                        default=None,
                        metadata={
                            "type": "Attribute",
                            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
                        },
                    )
                    range_type: RangeTypeType = field(
                        default=RangeTypeType.FLOAT,
                        metadata={
                            "name": "rangeType",
                            "type": "Attribute",
                            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
                        },
                    )
                    prompt: None | str = field(
                        default=None,
                        metadata={
                            "type": "Attribute",
                            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
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
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
                },
            )
            resolve: ResolveType = field(
                default=ResolveType.IMMEDIATE,
                metadata={
                    "type": "Attribute",
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
                },
            )
            id: None | str = field(
                default=None,
                metadata={
                    "type": "Attribute",
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
                },
            )
            dependency: None | str = field(
                default=None,
                metadata={
                    "type": "Attribute",
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
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
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
                },
            )
            order: None | float = field(
                default=None,
                metadata={
                    "type": "Attribute",
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
                },
            )
            config_groups: Sequence[str] = field(
                default_factory=list,
                metadata={
                    "name": "configGroups",
                    "type": "Attribute",
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
                    "tokens": True,
                },
            )
            bit_string_length: None | int = field(
                default=None,
                metadata={
                    "name": "bitStringLength",
                    "type": "Attribute",
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
                },
            )
            minimum: None | str = field(
                default=None,
                metadata={
                    "type": "Attribute",
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
                },
            )
            maximum: None | str = field(
                default=None,
                metadata={
                    "type": "Attribute",
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
                },
            )
            range_type: RangeTypeType = field(
                default=RangeTypeType.FLOAT,
                metadata={
                    "name": "rangeType",
                    "type": "Attribute",
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
                },
            )
            prompt: None | str = field(
                default=None,
                metadata={
                    "type": "Attribute",
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
                },
            )

        @dataclass(slots=True, kw_only=True)
        class Width:
            value: int = field()
            format: FormatType = field(
                default=FormatType.LONG,
                metadata={
                    "type": "Attribute",
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
                },
            )
            resolve: ResolveType = field(
                default=ResolveType.IMMEDIATE,
                metadata={
                    "type": "Attribute",
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
                },
            )
            id: None | str = field(
                default=None,
                metadata={
                    "type": "Attribute",
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
                },
            )
            dependency: None | str = field(
                default=None,
                metadata={
                    "type": "Attribute",
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
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
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
                },
            )
            order: None | float = field(
                default=None,
                metadata={
                    "type": "Attribute",
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
                },
            )
            config_groups: Sequence[str] = field(
                default_factory=list,
                metadata={
                    "name": "configGroups",
                    "type": "Attribute",
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
                    "tokens": True,
                },
            )
            bit_string_length: None | int = field(
                default=None,
                metadata={
                    "name": "bitStringLength",
                    "type": "Attribute",
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
                },
            )
            minimum: None | str = field(
                default=None,
                metadata={
                    "type": "Attribute",
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
                },
            )
            maximum: None | str = field(
                default=None,
                metadata={
                    "type": "Attribute",
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
                },
            )
            range_type: RangeTypeType = field(
                default=RangeTypeType.FLOAT,
                metadata={
                    "name": "rangeType",
                    "type": "Attribute",
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
                },
            )
            prompt: None | str = field(
                default=None,
                metadata={
                    "type": "Attribute",
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
                },
            )

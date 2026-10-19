from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

from org.accellera.spirit.v1_0.access import Access
from org.accellera.spirit.v1_0.base_address import BaseAddress
from org.accellera.spirit.v1_0.bit_offset import BitOffset
from org.accellera.spirit.v1_0.choice_style_value import ChoiceStyleValue
from org.accellera.spirit.v1_0.direction_value import DirectionValue
from org.accellera.spirit.v1_0.field_type import FieldType
from org.accellera.spirit.v1_0.format_type import FormatType
from org.accellera.spirit.v1_0.name_value_pair_type import NameValuePairType
from org.accellera.spirit.v1_0.parameter import Parameter
from org.accellera.spirit.v1_0.range_type_type import RangeTypeType
from org.accellera.spirit.v1_0.resolve_type import ResolveType
from org.accellera.spirit.v1_0.usage_type import UsageType
from org.accellera.spirit.v1_0.vendor_extensions import VendorExtensions
from org.accellera.spirit.v1_0.volatile import Volatile

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0"


@dataclass(slots=True, kw_only=True)
class AddressBlockType:
    """
    :ivar base_address:
    :ivar bit_offset:
    :ivar range: The address range of an address block.  Expressed as
        the number of addressable units accessable to the block.
    :ivar width: Bit width of an address block.  If zero or absent and
        this is part of a slave memory map, the width is assumed to be
        the data width of the slave interface.  It this is part of a
        local memory map, a missing width is assumed to be the effective
        width of the address space.  If this is part of an address space
        definition, a missing width is assumed to be the widest data
        signal of all bus interfaces that reference this address space.
    :ivar usage: Indicates the usage of this block.  Possible values are
        'memory', 'register' and 'reserved'.
    :ivar volatile:
    :ivar access:
    :ivar parameter: Any additional parameters needed to describe this
        address block to the generators.
    :ivar register:
    :ivar vendor_extensions:
    :ivar name:
    """

    class Meta:
        name = "addressBlockType"

    base_address: BaseAddress = field(
        metadata={
            "name": "baseAddress",
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
        }
    )
    bit_offset: None | BitOffset = field(
        default=None,
        metadata={
            "name": "bitOffset",
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
        },
    )
    range: AddressBlockType.Range = field(
        metadata={
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
        }
    )
    width: None | AddressBlockType.Width = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
        },
    )
    usage: None | UsageType = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
        },
    )
    volatile: None | Volatile = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
        },
    )
    access: None | Access = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
        },
    )
    parameter: Sequence[NameValuePairType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
        },
    )
    register: Sequence[AddressBlockType.Register] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
        },
    )
    vendor_extensions: None | VendorExtensions = field(
        default=None,
        metadata={
            "name": "vendorExtensions",
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
        },
    )
    name: None | str = field(
        default=None,
        metadata={
            "type": "Attribute",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
        },
    )

    @dataclass(slots=True, kw_only=True)
    class Range:
        """
        :ivar value:
        :ivar format: This is a hint to the user interface about the
            data format to require for user resolved properties. The
            long.att attribute group sets the default format to "long".
        :ivar resolve:
        :ivar id:
        :ivar dependency:
        :ivar other_attributes:
        :ivar minimum: For user-resolved properties with numeric values,
            this indicates the minimum value allowed.
        :ivar maximum: For user-resolved properties with numeric values,
            this indicates the maximum value allowed.
        :ivar range_type:
        :ivar order: For components with auto-generated configuration
            forms, the user-resolved properties with order attibutes
            will be presented in ascending order.
        :ivar choice_ref: For user resolved properties with a "choice"
            format, this refers to a uiChoice element in the ui section
            of the component file.
        :ivar choice_style:
        :ivar direction:
        :ivar config_groups:
        :ivar prompt:
        """

        value: str = field(
            default="",
            metadata={
                "pattern": r"-?((0x)|(0X)|#)?[0-9a-fA-F]*[kmgtKMGT]?",
            },
        )
        format: FormatType = field(
            default=FormatType.LONG,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
            },
        )
        resolve: None | ResolveType = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
            },
        )
        id: None | str = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
            },
        )
        dependency: None | str = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
            },
        )
        other_attributes: Mapping[str, str] = field(
            default_factory=dict,
            metadata={
                "type": "Attributes",
                "namespace": "##other",
            },
        )
        minimum: None | str = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
            },
        )
        maximum: None | str = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
            },
        )
        range_type: None | RangeTypeType = field(
            default=None,
            metadata={
                "name": "rangeType",
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
            },
        )
        order: None | float = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
            },
        )
        choice_ref: None | str = field(
            default=None,
            metadata={
                "name": "choiceRef",
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
            },
        )
        choice_style: None | ChoiceStyleValue = field(
            default=None,
            metadata={
                "name": "choiceStyle",
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
            },
        )
        direction: None | DirectionValue = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
            },
        )
        config_groups: Sequence[str] = field(
            default_factory=list,
            metadata={
                "name": "configGroups",
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
                "tokens": True,
            },
        )
        prompt: None | str = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
            },
        )

    @dataclass(slots=True, kw_only=True)
    class Width:
        """
        :ivar value:
        :ivar format: This is a hint to the user interface about the
            data format to require for user resolved properties. The
            long.att attribute group sets the default format to "long".
        :ivar resolve:
        :ivar id:
        :ivar dependency:
        :ivar other_attributes:
        :ivar minimum: For user-resolved properties with numeric values,
            this indicates the minimum value allowed.
        :ivar maximum: For user-resolved properties with numeric values,
            this indicates the maximum value allowed.
        :ivar range_type:
        :ivar order: For components with auto-generated configuration
            forms, the user-resolved properties with order attibutes
            will be presented in ascending order.
        :ivar choice_ref: For user resolved properties with a "choice"
            format, this refers to a uiChoice element in the ui section
            of the component file.
        :ivar choice_style:
        :ivar direction:
        :ivar config_groups:
        :ivar prompt:
        """

        value: int = field()
        format: FormatType = field(
            default=FormatType.LONG,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
            },
        )
        resolve: None | ResolveType = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
            },
        )
        id: None | str = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
            },
        )
        dependency: None | str = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
            },
        )
        other_attributes: Mapping[str, str] = field(
            default_factory=dict,
            metadata={
                "type": "Attributes",
                "namespace": "##other",
            },
        )
        minimum: None | str = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
            },
        )
        maximum: None | str = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
            },
        )
        range_type: None | RangeTypeType = field(
            default=None,
            metadata={
                "name": "rangeType",
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
            },
        )
        order: None | float = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
            },
        )
        choice_ref: None | str = field(
            default=None,
            metadata={
                "name": "choiceRef",
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
            },
        )
        choice_style: None | ChoiceStyleValue = field(
            default=None,
            metadata={
                "name": "choiceStyle",
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
            },
        )
        direction: None | DirectionValue = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
            },
        )
        config_groups: Sequence[str] = field(
            default_factory=list,
            metadata={
                "name": "configGroups",
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
                "tokens": True,
            },
        )
        prompt: None | str = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
            },
        )

    @dataclass(slots=True, kw_only=True)
    class Register:
        """
        :ivar name: Register name.
        :ivar dim: Dimensions a register array.
        :ivar address_offset: Offset from baseAddress.
        :ivar size: Size in bits.
        :ivar volatile:
        :ivar access:
        :ivar dependency: Indicates that this register has a dependency
            on the setting of another register.
        :ivar reset_value: Register value at reset.
        :ivar field_value: Describes individual bit fields within the
            register.
        :ivar description: Register description
        :ivar parameter:
        :ivar vendor_extensions:
        """

        name: str = field(
            metadata={
                "type": "Element",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
            }
        )
        dim: Sequence[int] = field(
            default_factory=list,
            metadata={
                "type": "Element",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
            },
        )
        address_offset: str = field(
            metadata={
                "name": "addressOffset",
                "type": "Element",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
                "pattern": r"-?((0x)|(0X)|#)?[0-9a-fA-F]*[kmgtKMGT]?",
            }
        )
        size: int = field(
            metadata={
                "type": "Element",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
            }
        )
        volatile: None | Volatile = field(
            default=None,
            metadata={
                "type": "Element",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
            },
        )
        access: None | Access = field(
            default=None,
            metadata={
                "type": "Element",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
            },
        )
        dependency: Sequence[AddressBlockType.Register.Dependency] = field(
            default_factory=list,
            metadata={
                "type": "Element",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
            },
        )
        reset_value: None | str = field(
            default=None,
            metadata={
                "name": "resetValue",
                "type": "Element",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
                "pattern": r"-?((0x)|(0X)|#)?[0-9a-fA-F]*[kmgtKMGT]?",
            },
        )
        field_value: Sequence[FieldType] = field(
            default_factory=list,
            metadata={
                "name": "field",
                "type": "Element",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
            },
        )
        description: None | str = field(
            default=None,
            metadata={
                "type": "Element",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
            },
        )
        parameter: Sequence[Parameter] = field(
            default_factory=list,
            metadata={
                "type": "Element",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
            },
        )
        vendor_extensions: None | VendorExtensions = field(
            default=None,
            metadata={
                "name": "vendorExtensions",
                "type": "Element",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
            },
        )

        @dataclass(slots=True, kw_only=True)
        class Dependency:
            """
            :ivar register_ref: The name of the register that enables
                this register.
            :ivar field_ref: Name of the field within the register that
                enables this register.
            :ivar value: Value that the enabling field must be set to to
                enable this register.
            :ivar mask: Mask to be anded with the value of the enabling
                field or register before comparing to the dependency
                value.
            """

            register_ref: str = field(
                metadata={
                    "name": "registerRef",
                    "type": "Element",
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
                }
            )
            field_ref: None | str = field(
                default=None,
                metadata={
                    "name": "fieldRef",
                    "type": "Element",
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
                },
            )
            value: str = field(
                metadata={
                    "type": "Element",
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
                    "pattern": r"-?((0x)|(0X)|#)?[0-9a-fA-F]*[kmgtKMGT]?",
                }
            )
            mask: None | str = field(
                default=None,
                metadata={
                    "type": "Element",
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
                    "pattern": r"-?((0x)|(0X)|#)?[0-9a-fA-F]*[kmgtKMGT]?",
                },
            )

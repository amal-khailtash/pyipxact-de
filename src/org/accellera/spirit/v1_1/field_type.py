from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

from org.accellera.spirit.v1_1.access import Access
from org.accellera.spirit.v1_1.choice_style_value import ChoiceStyleValue
from org.accellera.spirit.v1_1.direction_value import DirectionValue
from org.accellera.spirit.v1_1.format_type import FormatType
from org.accellera.spirit.v1_1.parameter import Parameter
from org.accellera.spirit.v1_1.range_type_type import RangeTypeType
from org.accellera.spirit.v1_1.resolve_type import ResolveType
from org.accellera.spirit.v1_1.vendor_extensions import VendorExtensions

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.1"


@dataclass(slots=True, kw_only=True)
class FieldType:
    """
    :ivar name: Field name.
    :ivar bit_offset: Offset of this field's lsb from bit 0 of the
        register.
    :ivar bit_width: Width of the field in bits.
    :ivar access:
    :ivar description: Bit field description.
    :ivar values: Enumerates specific values that can be assigned to the
        bit field.
    :ivar parameter:
    :ivar vendor_extensions:
    """

    class Meta:
        name = "fieldType"

    name: str = field(
        metadata={
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.1",
        }
    )
    bit_offset: int = field(
        metadata={
            "name": "bitOffset",
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.1",
        }
    )
    bit_width: FieldType.BitWidth = field(
        metadata={
            "name": "bitWidth",
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.1",
        }
    )
    access: Access = field(
        metadata={
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.1",
        }
    )
    description: None | str = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.1",
        },
    )
    values: Sequence[FieldType.Values] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.1",
        },
    )
    parameter: Sequence[Parameter] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.1",
        },
    )
    vendor_extensions: None | VendorExtensions = field(
        default=None,
        metadata={
            "name": "vendorExtensions",
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.1",
        },
    )

    @dataclass(slots=True, kw_only=True)
    class BitWidth:
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
        """

        value: int = field()
        format: FormatType = field(
            default=FormatType.LONG,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.1",
            },
        )
        resolve: None | ResolveType = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.1",
            },
        )
        id: None | str = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.1",
            },
        )
        dependency: None | str = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.1",
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
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.1",
            },
        )
        maximum: None | str = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.1",
            },
        )
        range_type: None | RangeTypeType = field(
            default=None,
            metadata={
                "name": "rangeType",
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.1",
            },
        )
        order: None | float = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.1",
            },
        )
        choice_ref: None | str = field(
            default=None,
            metadata={
                "name": "choiceRef",
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.1",
            },
        )
        choice_style: None | ChoiceStyleValue = field(
            default=None,
            metadata={
                "name": "choiceStyle",
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.1",
            },
        )
        direction: None | DirectionValue = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.1",
            },
        )
        config_groups: Sequence[str] = field(
            default_factory=list,
            metadata={
                "name": "configGroups",
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.1",
                "tokens": True,
            },
        )

    @dataclass(slots=True, kw_only=True)
    class Values:
        """
        :ivar value: Enumerated bit field value.
        :ivar description: Description of a bit field value.
        :ivar name: The name of this enumerated value. This may be used
            as a token in generating code.
        """

        value: str = field(
            metadata={
                "type": "Element",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.1",
                "pattern": r"-?((0x)|(0X)|#)?[0-9a-fA-F]*[kmgtKMGT]?",
            }
        )
        description: str = field(
            metadata={
                "type": "Element",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.1",
            }
        )
        name: str = field(
            metadata={
                "type": "Element",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.1",
            }
        )

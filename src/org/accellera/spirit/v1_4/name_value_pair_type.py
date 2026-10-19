from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

from org.accellera.spirit.v1_4.format_type import FormatType
from org.accellera.spirit.v1_4.range_type_type import RangeTypeType
from org.accellera.spirit.v1_4.resolve_type import ResolveType
from org.accellera.spirit.v1_4.vendor_extensions import VendorExtensions

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4"


@dataclass(slots=True, kw_only=True)
class NameValuePairType:
    """
    Name and value type for use in resolvable elements.

    :ivar name: Unique name
    :ivar display_name: Short description string, typically for user
        interface
    :ivar description: Full description string, typically for
        documentation
    :ivar value: The value of the parameter.
    :ivar vendor_extensions:
    :ivar any_attributes:
    """

    class Meta:
        name = "nameValuePairType"

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
    value: NameValuePairType.Value = field(
        metadata={
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
        }
    )
    vendor_extensions: None | VendorExtensions = field(
        default=None,
        metadata={
            "name": "vendorExtensions",
            "type": "Element",
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

    @dataclass(slots=True, kw_only=True)
    class Value:
        value: str = field(default="")
        format: FormatType = field(
            default=FormatType.STRING,
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

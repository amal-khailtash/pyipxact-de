from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

from org.accellera.spirit.v1_1.choice_style_value import ChoiceStyleValue
from org.accellera.spirit.v1_1.direction_value import DirectionValue
from org.accellera.spirit.v1_1.format_type import FormatType
from org.accellera.spirit.v1_1.range_type_type import RangeTypeType
from org.accellera.spirit.v1_1.resolve_type import ResolveType

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.1"


@dataclass(slots=True, kw_only=True)
class AdHocConnection:
    """
    Represents an ad-hoc connection between component pins.

    :ivar export: Specifies whether this ad-hoc connection will be
        exported out of the design.
    :ivar pin_reference:
    :ivar name:
    """

    class Meta:
        name = "adHocConnection"
        namespace = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.1"

    export: None | AdHocConnection.Export = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    pin_reference: Sequence[AdHocConnection.PinReference] = field(
        default_factory=list,
        metadata={
            "name": "pinReference",
            "type": "Element",
            "min_occurs": 1,
        },
    )
    name: None | str = field(
        default=None,
        metadata={
            "type": "Attribute",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.1",
        },
    )

    @dataclass(slots=True, kw_only=True)
    class Export:
        """
        :ivar value:
        :ivar format: This is a hint to the user interface about the
            data format to require for user resolved properties. The
            bool.att attribute group sets the default format to "bool".
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

        value: bool = field()
        format: FormatType = field(
            default=FormatType.BOOL,
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
        prompt: None | str = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.1",
            },
        )

    @dataclass(slots=True, kw_only=True)
    class PinReference:
        component_ref: str = field(
            metadata={
                "name": "componentRef",
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.1",
            }
        )
        signal_ref: str = field(
            metadata={
                "name": "signalRef",
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.1",
            }
        )
        left: None | int = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.1",
            },
        )
        right: None | int = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.1",
            },
        )

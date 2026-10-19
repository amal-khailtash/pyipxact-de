from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import ForwardRef

from org.accellera.spirit.v1_2.path_element_type import PathElementType

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2"


@dataclass(slots=True, kw_only=True)
class PathSpecifier:
    """
    Defines one or more logical paths within a component.
    """

    class Meta:
        name = "pathSpecifier"
        namespace = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2"

    from_or_to_or_through: Sequence[
        PathSpecifier.From | PathSpecifier.To | PathSpecifier.Through
    ] = field(
        default_factory=list,
        metadata={
            "type": "Elements",
            "choices": (
                {
                    "name": "from",
                    "type": ForwardRef("PathSpecifier.From"),
                },
                {
                    "name": "to",
                    "type": ForwardRef("PathSpecifier.To"),
                },
                {
                    "name": "through",
                    "type": ForwardRef("PathSpecifier.Through"),
                },
            ),
        },
    )

    @dataclass(slots=True, kw_only=True)
    class From:
        value: str = field(default="")
        path_element: None | PathElementType = field(
            default=None,
            metadata={
                "name": "pathElement",
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2",
            },
        )

    @dataclass(slots=True, kw_only=True)
    class To:
        value: str = field(default="")
        path_element: None | PathElementType = field(
            default=None,
            metadata={
                "name": "pathElement",
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2",
            },
        )

    @dataclass(slots=True, kw_only=True)
    class Through:
        value: str = field(default="")
        path_element: None | PathElementType = field(
            default=None,
            metadata={
                "name": "pathElement",
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2",
            },
        )

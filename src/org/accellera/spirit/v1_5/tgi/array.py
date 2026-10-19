from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

__NAMESPACE__ = "http://schemas.xmlsoap.org/soap/encoding/"


@dataclass(slots=True, kw_only=True)
class Array:
    """
    'Array' is a complex type for accessors identified by position.
    """

    class Meta:
        namespace = "http://schemas.xmlsoap.org/soap/encoding/"

    any_element: Sequence[object] = field(
        default_factory=list,
        metadata={
            "type": "Wildcard",
            "namespace": "##any",
        },
    )
    array_type: None | str = field(
        default=None,
        metadata={
            "name": "arrayType",
            "type": "Attribute",
            "namespace": "http://schemas.xmlsoap.org/soap/encoding/",
        },
    )
    offset: None | str = field(
        default=None,
        metadata={
            "type": "Attribute",
            "namespace": "http://schemas.xmlsoap.org/soap/encoding/",
        },
    )
    id: None | str = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )
    href: None | str = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )
    other_attributes: Mapping[str, str] = field(
        default_factory=dict,
        metadata={
            "type": "Attributes",
            "namespace": "##other",
        },
    )

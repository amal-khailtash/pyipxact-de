from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

__NAMESPACE__ = "http://schemas.xmlsoap.org/soap/encoding/"


@dataclass(slots=True, kw_only=True)
class Idrefs:
    class Meta:
        name = "IDREFS"
        namespace = "http://schemas.xmlsoap.org/soap/encoding/"

    value: Sequence[str] = field(
        default_factory=list,
        metadata={
            "tokens": True,
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

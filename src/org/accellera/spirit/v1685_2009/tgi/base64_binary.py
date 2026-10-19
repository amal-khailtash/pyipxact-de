from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

__NAMESPACE__ = "http://schemas.xmlsoap.org/soap/encoding/"


@dataclass(slots=True, kw_only=True)
class Base64Binary:
    class Meta:
        name = "base64Binary"
        namespace = "http://schemas.xmlsoap.org/soap/encoding/"

    value: bytes = field(
        default=b"",
        metadata={
            "format": "base64",
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

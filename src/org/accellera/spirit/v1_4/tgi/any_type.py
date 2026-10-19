from __future__ import annotations

from dataclasses import dataclass, field

__NAMESPACE__ = "http://schemas.xmlsoap.org/soap/encoding/"


@dataclass(slots=True, kw_only=True)
class AnyType:
    class Meta:
        name = "anyType"
        namespace = "http://schemas.xmlsoap.org/soap/encoding/"

    any_element: None | object = field(
        default=None,
        metadata={
            "type": "Wildcard",
            "namespace": "##any",
        },
    )

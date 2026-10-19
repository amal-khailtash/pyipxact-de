from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from xsdata.models.datatype import XmlDateTime

__NAMESPACE__ = "http://schemas.xmlsoap.org/soap/encoding/"


@dataclass(slots=True, kw_only=True)
class DateTime:
    class Meta:
        name = "dateTime"
        namespace = "http://schemas.xmlsoap.org/soap/encoding/"

    value: XmlDateTime = field()
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

from __future__ import annotations

from dataclasses import dataclass, field

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.1"


@dataclass(slots=True, kw_only=True)
class ResolvedLibraryRefType:
    """
    Resolved SPIRIT document reference type.

    Contains vendor, library, name and optional version attributes and the
    URI of the referenced SPIRIT document.
    """

    class Meta:
        name = "resolvedLibraryRefType"

    value: str = field(default="")
    vendor: str = field(
        metadata={
            "type": "Attribute",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.1",
        }
    )
    library: str = field(
        metadata={
            "type": "Attribute",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.1",
        }
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.1",
        }
    )
    version: None | str = field(
        default=None,
        metadata={
            "type": "Attribute",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.1",
        },
    )

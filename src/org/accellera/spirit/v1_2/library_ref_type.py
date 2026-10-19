from __future__ import annotations

from dataclasses import dataclass, field

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2"


@dataclass(slots=True, kw_only=True)
class LibraryRefType:
    """
    Base SPIRIT document reference type.

    Contains vendor, library, name and version attributes.
    """

    class Meta:
        name = "libraryRefType"

    vendor: str = field(
        metadata={
            "type": "Attribute",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2",
        }
    )
    library: str = field(
        metadata={
            "type": "Attribute",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2",
        }
    )
    name: str = field(
        metadata={
            "type": "Attribute",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2",
        }
    )
    version: str = field(
        metadata={
            "type": "Attribute",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2",
        }
    )

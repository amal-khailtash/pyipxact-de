from __future__ import annotations

from dataclasses import dataclass, field

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0"


@dataclass(slots=True, kw_only=True)
class FileSetRef:
    """
    A reference to a fileSet.
    """

    class Meta:
        name = "fileSetRef"
        namespace = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0"

    value: str = field(default="")

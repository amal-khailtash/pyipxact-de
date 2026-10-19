from __future__ import annotations

from dataclasses import dataclass, field

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5"


@dataclass(slots=True, kw_only=True)
class Volatile:
    """
    Indicates whether the data is volatile.
    """

    class Meta:
        name = "volatile"
        namespace = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5"

    value: bool = field(default=False)

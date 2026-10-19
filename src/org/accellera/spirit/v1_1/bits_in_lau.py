from __future__ import annotations

from dataclasses import dataclass, field

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.1"


@dataclass(slots=True, kw_only=True)
class BitsInLau:
    """
    The number of bits in the least addressable unit.

    The default is byte addressable (8 bits).
    """

    class Meta:
        name = "bitsInLau"
        namespace = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.1"

    value: int = field()

from __future__ import annotations

from dataclasses import dataclass, field

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009"


@dataclass(slots=True, kw_only=True)
class AddressUnitBits:
    """
    The number of data bits in an addressable unit.

    The default is byte addressable (8 bits).
    """

    class Meta:
        name = "addressUnitBits"
        namespace = (
            "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009"
        )

    value: int = field()

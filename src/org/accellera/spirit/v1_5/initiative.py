from __future__ import annotations

from dataclasses import dataclass, field

from org.accellera.spirit.v1_5.initiative_value import InitiativeValue

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5"


@dataclass(slots=True, kw_only=True)
class Initiative:
    """
    If this element is present, the type of access is restricted to the
    specified value.
    """

    class Meta:
        name = "initiative"
        namespace = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5"

    value: InitiativeValue = field()

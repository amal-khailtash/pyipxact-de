from __future__ import annotations

from dataclasses import dataclass, field

from org.accellera.spirit.v1_0.add_rem_change_value import AddRemChangeValue

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0"


@dataclass(slots=True, kw_only=True)
class AddRemChange:
    """
    Indicates whether the alteration is an addition or a removal.
    """

    class Meta:
        name = "addRemChange"
        namespace = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0"

    value: AddRemChangeValue = field()

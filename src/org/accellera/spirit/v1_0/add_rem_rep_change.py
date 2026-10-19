from __future__ import annotations

from dataclasses import dataclass, field

from org.accellera.spirit.v1_0.add_rem_rep_change_value import (
    AddRemRepChangeValue,
)

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0"


@dataclass(slots=True, kw_only=True)
class AddRemRepChange:
    """
    Indicates whether the alteration is an addition, removal or a
    replacement.
    """

    class Meta:
        name = "addRemRepChange"
        namespace = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0"

    value: AddRemRepChangeValue = field()

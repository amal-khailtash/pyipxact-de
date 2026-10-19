from __future__ import annotations

from dataclasses import dataclass, field

from org.accellera.spirit.v1_2.strength import Strength
from org.accellera.spirit.v1_2.value import Value

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2"


@dataclass(slots=True, kw_only=True)
class SignalValueType:
    """
    Describes a signal value.

    The signal value can be just a value (number), a strength, or both. If
    the "value" is not given, it should be considered an X (unknown). A
    weak strength with no value given is considered Z (tristate).
    """

    class Meta:
        name = "signalValueType"

    strength_or_value: None | Strength | Value = field(
        default=None,
        metadata={
            "type": "Elements",
            "choices": (
                {
                    "name": "strength",
                    "type": Strength,
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2",
                },
                {
                    "name": "value",
                    "type": Value,
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2",
                },
            ),
        },
    )

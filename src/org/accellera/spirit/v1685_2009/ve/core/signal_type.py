from __future__ import annotations

from dataclasses import dataclass, field

from org.accellera.spirit.v1685_2009.ve.core.signal_type_1 import SignalType1

__NAMESPACE__ = (
    "http://www.accellera.org/XMLSchema/SPIRIT/1685-2009-VE/AMS-1.0"
)


@dataclass(slots=True, kw_only=True)
class SignalType:
    """
    The type of the signal.

    Possible values are continuous-conservative,
    continuous-non-conservative, and discrete.
    """

    class Meta:
        name = "signalType"
        namespace = (
            "http://www.accellera.org/XMLSchema/SPIRIT/1685-2009-VE/AMS-1.0"
        )

    value: SignalType1 = field()

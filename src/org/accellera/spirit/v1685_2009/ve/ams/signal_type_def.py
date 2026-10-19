from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from org.accellera.spirit.v1685_2009.ve.ams.signal_type import SignalType
from org.accellera.spirit.v1685_2009.ve.ams.view_name_ref import ViewNameRef

__NAMESPACE__ = (
    "http://www.accellera.org/XMLSchema/SPIRIT/1685-2009-VE/AMS-1.0"
)


@dataclass(slots=True, kw_only=True)
class SignalTypeDef:
    """
    Definition of a single signal type definition that can relate to
    multiple views.
    """

    class Meta:
        name = "signalTypeDef"
        namespace = (
            "http://www.accellera.org/XMLSchema/SPIRIT/1685-2009-VE/AMS-1.0"
        )

    signal_type: SignalType = field(
        metadata={
            "name": "signalType",
            "type": "Element",
        }
    )
    view_name_ref: Sequence[ViewNameRef] = field(
        default_factory=list,
        metadata={
            "name": "viewNameRef",
            "type": "Element",
            "namespace": "http://www.accellera.org/XMLSchema/SPIRIT/1685-2009-VE",
            "min_occurs": 1,
        },
    )

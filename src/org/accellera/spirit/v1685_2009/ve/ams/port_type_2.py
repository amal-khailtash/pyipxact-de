from __future__ import annotations

from dataclasses import dataclass

__NAMESPACE__ = "http://www.accellera.org/XMLSchema/SPIRIT/1685-2009-VE"


@dataclass(slots=True, kw_only=True)
class PortType2:
    """
    Port extension type definition.
    """

    class Meta:
        name = "portType"

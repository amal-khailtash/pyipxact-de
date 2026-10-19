from __future__ import annotations

from dataclasses import dataclass, field

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4"


@dataclass(slots=True, kw_only=True)
class PortAccessHandle:
    """
    If present, a netlister should use this string instead of the port name
    to access the port.
    """

    class Meta:
        name = "portAccessHandle"
        namespace = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4"

    value: str = field(default="")

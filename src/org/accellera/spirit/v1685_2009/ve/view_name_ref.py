from __future__ import annotations

from dataclasses import dataclass, field

__NAMESPACE__ = "http://www.accellera.org/XMLSchema/SPIRIT/1685-2009-VE"


@dataclass(slots=True, kw_only=True)
class ViewNameRef:
    """
    A reference to an existing spirit view name in the file.
    """

    class Meta:
        name = "viewNameRef"
        namespace = "http://www.accellera.org/XMLSchema/SPIRIT/1685-2009-VE"

    value: str = field(default="")

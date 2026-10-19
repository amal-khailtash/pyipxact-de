from __future__ import annotations

from dataclasses import dataclass, field

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009"


@dataclass(slots=True, kw_only=True)
class Dependency:
    """
    Specifies a location on which files or fileSets may be dependent.

    Typically, this would be a directory that would contain included files.
    """

    class Meta:
        name = "dependency"
        namespace = (
            "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009"
        )

    value: str = field(default="")

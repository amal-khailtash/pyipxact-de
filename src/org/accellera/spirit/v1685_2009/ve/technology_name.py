from __future__ import annotations

from dataclasses import dataclass, field

from org.accellera.spirit.v1685_2009.ve.type_value import TypeValue

__NAMESPACE__ = (
    "http://www.accellera.org/XMLSchema/SPIRIT/1685-2009-VE/PDP-1.0"
)


@dataclass(slots=True, kw_only=True)
class TechnologyName:
    """
    Technology name.
    """

    class Meta:
        name = "technologyName"
        namespace = (
            "http://www.accellera.org/XMLSchema/SPIRIT/1685-2009-VE/PDP-1.0"
        )

    value: str = field(default="")
    type_value: None | TypeValue = field(
        default=None,
        metadata={
            "name": "type",
            "type": "Attribute",
            "namespace": "http://www.accellera.org/XMLSchema/SPIRIT/1685-2009-VE/PDP-1.0",
        },
    )

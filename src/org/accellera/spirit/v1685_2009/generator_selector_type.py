from __future__ import annotations

from dataclasses import dataclass, field

from org.accellera.spirit.v1685_2009.group_selector import GroupSelector

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009"


@dataclass(slots=True, kw_only=True)
class GeneratorSelectorType:
    class Meta:
        name = "generatorSelectorType"

    group_selector: GroupSelector = field(
        metadata={
            "name": "groupSelector",
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
        }
    )

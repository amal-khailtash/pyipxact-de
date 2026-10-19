from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from org.accellera.spirit.v1_5.component_generator import ComponentGenerator

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5"


@dataclass(slots=True, kw_only=True)
class ComponentGenerators:
    """
    List of component generators.
    """

    class Meta:
        name = "componentGenerators"
        namespace = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5"

    component_generator: Sequence[ComponentGenerator] = field(
        default_factory=list,
        metadata={
            "name": "componentGenerator",
            "type": "Element",
            "min_occurs": 1,
        },
    )

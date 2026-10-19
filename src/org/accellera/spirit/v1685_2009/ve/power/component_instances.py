from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from org.accellera.spirit.v1685_2009.ve.power.component_instance_1 import (
    ComponentInstance1,
)

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009"


@dataclass(slots=True, kw_only=True)
class ComponentInstances:
    """
    Sub instances of internal components.
    """

    class Meta:
        name = "componentInstances"
        namespace = (
            "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009"
        )

    component_instance: Sequence[ComponentInstance1] = field(
        default_factory=list,
        metadata={
            "name": "componentInstance",
            "type": "Element",
            "min_occurs": 1,
        },
    )

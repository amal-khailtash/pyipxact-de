from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from org.accellera.spirit.v1_0.component_instance import ComponentInstance

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0"


@dataclass(slots=True, kw_only=True)
class ComponentInstances:
    """
    Sub instances of internal components.
    """

    class Meta:
        name = "componentInstances"
        namespace = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0"

    component_instance: Sequence[ComponentInstance] = field(
        default_factory=list,
        metadata={
            "name": "componentInstance",
            "type": "Element",
        },
    )

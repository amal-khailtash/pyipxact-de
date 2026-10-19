from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from org.accellera.spirit.v1_5.parameter import Parameter

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5"


@dataclass(slots=True, kw_only=True)
class Parameters:
    """
    A collection of parameters.
    """

    class Meta:
        name = "parameters"
        namespace = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5"

    parameter: Sequence[Parameter] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "min_occurs": 1,
        },
    )

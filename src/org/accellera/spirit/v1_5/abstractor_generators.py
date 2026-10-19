from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from org.accellera.spirit.v1_5.abstractor_generator import AbstractorGenerator

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5"


@dataclass(slots=True, kw_only=True)
class AbstractorGenerators:
    """
    List of abstractor generators.
    """

    class Meta:
        name = "abstractorGenerators"
        namespace = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5"

    abstractor_generator: Sequence[AbstractorGenerator] = field(
        default_factory=list,
        metadata={
            "name": "abstractorGenerator",
            "type": "Element",
            "min_occurs": 1,
        },
    )

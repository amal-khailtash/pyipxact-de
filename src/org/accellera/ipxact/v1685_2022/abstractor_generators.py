from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from org.accellera.ipxact.v1685_2022.abstractor_generator import (
    AbstractorGenerator,
)

__NAMESPACE__ = "http://www.accellera.org/XMLSchema/IPXACT/1685-2022"


@dataclass(slots=True, kw_only=True)
class AbstractorGenerators:
    """
    List of abstractor generators.
    """

    class Meta:
        name = "abstractorGenerators"
        namespace = "http://www.accellera.org/XMLSchema/IPXACT/1685-2022"

    abstractor_generator: Sequence[AbstractorGenerator] = field(
        default_factory=list,
        metadata={
            "name": "abstractorGenerator",
            "type": "Element",
            "min_occurs": 1,
        },
    )

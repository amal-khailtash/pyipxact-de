from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from org.accellera.spirit.v1_1.configurable_element import ConfigurableElement

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.1"


@dataclass(slots=True, kw_only=True)
class Configuration:
    """
    All configuration information for a contained component or channel
    instance.
    """

    class Meta:
        name = "configuration"
        namespace = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.1"

    configurable_element: Sequence[ConfigurableElement] = field(
        default_factory=list,
        metadata={
            "name": "configurableElement",
            "type": "Element",
        },
    )

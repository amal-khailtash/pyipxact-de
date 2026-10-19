from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from org.accellera.spirit.v1685_2009.ve.configurable_element_value import (
    ConfigurableElementValue,
)

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009"


@dataclass(slots=True, kw_only=True)
class ConfigurableElementValues:
    """
    All configuration information for a contained component, generator,
    generator chain or abstractor instance.

    :ivar configurable_element_value: Describes the content of a
        configurable element. The required referenceId attribute refers
        to the ID attribute of the configurable element.
    """

    class Meta:
        name = "configurableElementValues"
        namespace = (
            "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009"
        )

    configurable_element_value: Sequence[ConfigurableElementValue] = field(
        default_factory=list,
        metadata={
            "name": "configurableElementValue",
            "type": "Element",
            "min_occurs": 1,
        },
    )

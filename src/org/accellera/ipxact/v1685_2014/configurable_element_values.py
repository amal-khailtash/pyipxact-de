from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from org.accellera.ipxact.v1685_2014.configurable_element_value import (
    ConfigurableElementValue,
)

__NAMESPACE__ = "http://www.accellera.org/XMLSchema/IPXACT/1685-2014"


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
        namespace = "http://www.accellera.org/XMLSchema/IPXACT/1685-2014"

    configurable_element_value: Sequence[ConfigurableElementValue] = field(
        default_factory=list,
        metadata={
            "name": "configurableElementValue",
            "type": "Element",
            "min_occurs": 1,
        },
    )

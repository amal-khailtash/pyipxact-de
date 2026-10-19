from __future__ import annotations

from dataclasses import dataclass, field

from org.accellera.ipxact.v1685_2014.configurable_element_values import (
    ConfigurableElementValues,
)

__NAMESPACE__ = "http://www.accellera.org/XMLSchema/IPXACT/1685-2014"


@dataclass(slots=True, kw_only=True)
class ConfigurableLibraryRefType:
    """
    Base IP-XACT document reference type for configurable top-level
    objects.

    Contains vendor, library, name and version attributes along with
    configurable element values.
    """

    class Meta:
        name = "configurableLibraryRefType"

    configurable_element_values: None | ConfigurableElementValues = field(
        default=None,
        metadata={
            "name": "configurableElementValues",
            "type": "Element",
            "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2014",
        },
    )
    vendor: str = field(
        metadata={
            "type": "Attribute",
        }
    )
    library: str = field(
        metadata={
            "type": "Attribute",
        }
    )
    name: str = field(
        metadata={
            "type": "Attribute",
        }
    )
    version: str = field(
        metadata={
            "type": "Attribute",
        }
    )

from __future__ import annotations

from dataclasses import dataclass, field

from org.accellera.ipxact.v1685_2014.ad_hoc_connections import AdHocConnections
from org.accellera.ipxact.v1685_2014.assertions import Assertions
from org.accellera.ipxact.v1685_2014.component_instances import (
    ComponentInstances,
)
from org.accellera.ipxact.v1685_2014.description import Description
from org.accellera.ipxact.v1685_2014.interconnections import Interconnections
from org.accellera.ipxact.v1685_2014.parameters import Parameters
from org.accellera.ipxact.v1685_2014.vendor_extensions import VendorExtensions

__NAMESPACE__ = "http://www.accellera.org/XMLSchema/IPXACT/1685-2014"


@dataclass(slots=True, kw_only=True)
class Design:
    """
    Root element for a platform design.

    :ivar vendor: Name of the vendor who supplies this file.
    :ivar library: Name of the logical library this element belongs to.
    :ivar name: The name of the object.
    :ivar version: Indicates the version of the named element.
    :ivar component_instances:
    :ivar interconnections:
    :ivar ad_hoc_connections:
    :ivar description:
    :ivar parameters:
    :ivar assertions:
    :ivar vendor_extensions:
    :ivar id:
    """

    class Meta:
        name = "design"
        namespace = "http://www.accellera.org/XMLSchema/IPXACT/1685-2014"

    vendor: str = field(
        metadata={
            "type": "Element",
        }
    )
    library: str = field(
        metadata={
            "type": "Element",
        }
    )
    name: str = field(
        metadata={
            "type": "Element",
        }
    )
    version: str = field(
        metadata={
            "type": "Element",
        }
    )
    component_instances: None | ComponentInstances = field(
        default=None,
        metadata={
            "name": "componentInstances",
            "type": "Element",
        },
    )
    interconnections: None | Interconnections = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    ad_hoc_connections: None | AdHocConnections = field(
        default=None,
        metadata={
            "name": "adHocConnections",
            "type": "Element",
        },
    )
    description: None | Description = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    parameters: None | Parameters = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    assertions: None | Assertions = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    vendor_extensions: None | VendorExtensions = field(
        default=None,
        metadata={
            "name": "vendorExtensions",
            "type": "Element",
        },
    )
    id: None | str = field(
        default=None,
        metadata={
            "type": "Attribute",
            "namespace": "http://www.w3.org/XML/1998/namespace",
        },
    )

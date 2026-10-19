from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from org.accellera.spirit.v1_2.ad_hoc_connections import AdHocConnections
from org.accellera.spirit.v1_2.component_instances import ComponentInstances
from org.accellera.spirit.v1_2.interconnections import Interconnections
from org.accellera.spirit.v1_2.vendor_extensions import VendorExtensions

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2"


@dataclass(slots=True, kw_only=True)
class Design:
    """
    Root element for a platform design.

    :ivar vendor: Name of the vendor who supplies this file.
    :ivar library: Name of the logical library this element belongs to.
    :ivar name: The name of the object.
    :ivar version:
    :ivar component_instances:
    :ivar interconnections:
    :ivar ad_hoc_connections:
    :ivar hier_connections: A list of hierarchy connections between bus
        interfaces on component instances and the bus interfaces on the
        encompassing component.
    :ivar vendor_extensions:
    """

    class Meta:
        name = "design"
        namespace = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2"

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
    hier_connections: None | Design.HierConnections = field(
        default=None,
        metadata={
            "name": "hierConnections",
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

    @dataclass(slots=True, kw_only=True)
    class HierConnections:
        """
        :ivar hier_connection: Represents a hierarchy connection
        """

        hier_connection: Sequence[Design.HierConnections.HierConnection] = (
            field(
                default_factory=list,
                metadata={
                    "name": "hierConnection",
                    "type": "Element",
                },
            )
        )

        @dataclass(slots=True, kw_only=True)
        class HierConnection:
            """
            :ivar component_ref: This is the instance name of the
                component which owns the busInterface that is to be
                exported
            :ivar interface_ref: This is the name of the bus interface
                on the instance
            :ivar vendor_extensions:
            :ivar interface_name: This is the name of the bus interface
                on the upper level component.
            """

            component_ref: str = field(
                metadata={
                    "name": "componentRef",
                    "type": "Element",
                }
            )
            interface_ref: str = field(
                metadata={
                    "name": "interfaceRef",
                    "type": "Element",
                }
            )
            vendor_extensions: None | VendorExtensions = field(
                default=None,
                metadata={
                    "name": "vendorExtensions",
                    "type": "Element",
                },
            )
            interface_name: str = field(
                metadata={
                    "name": "interfaceName",
                    "type": "Attribute",
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2",
                }
            )

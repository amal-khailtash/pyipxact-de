from __future__ import annotations

from dataclasses import dataclass, field

from org.accellera.spirit.v1_5.port_declaration_type import PortDeclarationType
from org.accellera.spirit.v1_5.vendor_extensions import VendorExtensions

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5"


@dataclass(slots=True, kw_only=True)
class PortType(PortDeclarationType):
    """
    A port description, giving a name and an access type for high level
    ports.
    """

    class Meta:
        name = "portType"

    vendor_extensions: None | VendorExtensions = field(
        default=None,
        metadata={
            "name": "vendorExtensions",
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
        },
    )

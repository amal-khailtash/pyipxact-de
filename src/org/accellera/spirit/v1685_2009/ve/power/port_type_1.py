from __future__ import annotations

from dataclasses import dataclass, field

from org.accellera.spirit.v1685_2009.ve.power.port_declaration_type import (
    PortDeclarationType,
)
from org.accellera.spirit.v1685_2009.ve.power.vendor_extensions import (
    VendorExtensions,
)

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009"


@dataclass(slots=True, kw_only=True)
class PortType1(PortDeclarationType):
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
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
        },
    )

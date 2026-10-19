from __future__ import annotations

from dataclasses import dataclass, field

from org.accellera.ipxact.v1685_2022.power_domain_ref import PowerDomainRef
from org.accellera.ipxact.v1685_2022.range import Range
from org.accellera.ipxact.v1685_2022.vendor_extensions import VendorExtensions

__NAMESPACE__ = "http://www.accellera.org/XMLSchema/IPXACT/1685-2022"


@dataclass(slots=True, kw_only=True)
class WirePowerConstraintType:
    class Meta:
        name = "wirePowerConstraintType"

    power_domain_ref: PowerDomainRef = field(
        metadata={
            "name": "powerDomainRef",
            "type": "Element",
            "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
        }
    )
    range: None | Range = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
        },
    )
    vendor_extensions: None | VendorExtensions = field(
        default=None,
        metadata={
            "name": "vendorExtensions",
            "type": "Element",
            "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
        },
    )
    id: None | str = field(
        default=None,
        metadata={
            "type": "Attribute",
            "namespace": "http://www.w3.org/XML/1998/namespace",
        },
    )

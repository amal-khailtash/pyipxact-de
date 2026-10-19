from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from org.accellera.ipxact.v1685_2022.access_type import AccessType
from org.accellera.ipxact.v1685_2022.mode_ref import ModeRef
from org.accellera.ipxact.v1685_2022.vendor_extensions import VendorExtensions

__NAMESPACE__ = "http://www.accellera.org/XMLSchema/IPXACT/1685-2022"


@dataclass(slots=True, kw_only=True)
class AccessPolicies:
    class Meta:
        name = "accessPolicies"
        namespace = "http://www.accellera.org/XMLSchema/IPXACT/1685-2022"

    access_policy: Sequence[AccessPolicies.AccessPolicy] = field(
        default_factory=list,
        metadata={
            "name": "accessPolicy",
            "type": "Element",
            "min_occurs": 1,
        },
    )

    @dataclass(slots=True, kw_only=True)
    class AccessPolicy:
        mode_ref: Sequence[ModeRef] = field(
            default_factory=list,
            metadata={
                "name": "modeRef",
                "type": "Element",
            },
        )
        access: None | AccessType = field(
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

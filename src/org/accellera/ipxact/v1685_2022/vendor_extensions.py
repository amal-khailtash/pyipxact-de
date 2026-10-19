from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

__NAMESPACE__ = "http://www.accellera.org/XMLSchema/IPXACT/1685-2022"


@dataclass(slots=True, kw_only=True)
class VendorExtensions:
    """
    Container for vendor specific extensions.

    :ivar any_element: Accepts any element(s) the content provider wants
        to put here, including elements from the ipxact namespace.
    """

    class Meta:
        name = "vendorExtensions"
        namespace = "http://www.accellera.org/XMLSchema/IPXACT/1685-2022"

    any_element: Sequence[object] = field(
        default_factory=list,
        metadata={
            "type": "Wildcard",
            "namespace": "##any",
        },
    )

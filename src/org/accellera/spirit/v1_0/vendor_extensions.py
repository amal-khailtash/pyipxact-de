from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0"


@dataclass(slots=True, kw_only=True)
class VendorExtensions:
    """
    Container for vendor specific extensions.

    :ivar any_element: Accepts any element(s) the content provider wants
        to put here, including elements from the SPIRIT namespace.
    """

    class Meta:
        name = "vendorExtensions"
        namespace = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0"

    any_element: Sequence[object] = field(
        default_factory=list,
        metadata={
            "type": "Wildcard",
            "namespace": "##any",
        },
    )

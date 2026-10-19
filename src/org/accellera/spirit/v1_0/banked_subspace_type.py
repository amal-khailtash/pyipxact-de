from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from org.accellera.spirit.v1_0.name_value_pair_type import NameValuePairType
from org.accellera.spirit.v1_0.vendor_extensions import VendorExtensions

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0"


@dataclass(slots=True, kw_only=True)
class BankedSubspaceType:
    """
    Subspace references inside banks do not specify an address.

    :ivar parameter: Any parameters that may apply to the subspace
        reference.
    :ivar vendor_extensions:
    :ivar master_ref:
    """

    class Meta:
        name = "bankedSubspaceType"

    parameter: Sequence[NameValuePairType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
        },
    )
    vendor_extensions: None | VendorExtensions = field(
        default=None,
        metadata={
            "name": "vendorExtensions",
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
        },
    )
    master_ref: str = field(
        metadata={
            "name": "masterRef",
            "type": "Attribute",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
        }
    )

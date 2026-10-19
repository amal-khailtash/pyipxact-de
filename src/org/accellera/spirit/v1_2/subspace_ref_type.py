from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from org.accellera.spirit.v1_2.base_address import BaseAddress
from org.accellera.spirit.v1_2.bit_offset import BitOffset
from org.accellera.spirit.v1_2.name_value_pair_type import NameValuePairType
from org.accellera.spirit.v1_2.vendor_extensions import VendorExtensions

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2"


@dataclass(slots=True, kw_only=True)
class SubspaceRefType:
    """
    Address subspace type.

    Its subspaceReference attribute references the subspace from which the
    dimensions are taken.

    :ivar base_address:
    :ivar bit_offset:
    :ivar parameter: Any parameters that may apply to the subspace
        reference.
    :ivar vendor_extensions:
    :ivar master_ref:
    """

    class Meta:
        name = "subspaceRefType"

    base_address: BaseAddress = field(
        metadata={
            "name": "baseAddress",
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2",
        }
    )
    bit_offset: None | BitOffset = field(
        default=None,
        metadata={
            "name": "bitOffset",
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2",
        },
    )
    parameter: Sequence[NameValuePairType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2",
        },
    )
    vendor_extensions: None | VendorExtensions = field(
        default=None,
        metadata={
            "name": "vendorExtensions",
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2",
        },
    )
    master_ref: str = field(
        metadata={
            "name": "masterRef",
            "type": "Attribute",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2",
        }
    )

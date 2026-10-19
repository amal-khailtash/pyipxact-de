from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import ForwardRef

from org.accellera.spirit.v1_0.access import Access
from org.accellera.spirit.v1_0.bank_alignment_type import BankAlignmentType
from org.accellera.spirit.v1_0.banked_block_type import BankedBlockType
from org.accellera.spirit.v1_0.banked_subspace_type import BankedSubspaceType
from org.accellera.spirit.v1_0.name_value_pair_type import NameValuePairType
from org.accellera.spirit.v1_0.usage_type import UsageType
from org.accellera.spirit.v1_0.vendor_extensions import VendorExtensions
from org.accellera.spirit.v1_0.volatile import Volatile

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0"


@dataclass(slots=True, kw_only=True)
class BankedBankType:
    """
    Banks nested inside a bank do not specify address.

    :ivar address_block_or_bank_or_subspace_map:
    :ivar usage: Indicates the usage of this block.  Possible values are
        'memory', 'register' and 'reserved'.
    :ivar volatile:
    :ivar access:
    :ivar parameter: Any additional parameters needed to describe this
        address block to the generators.
    :ivar vendor_extensions:
    :ivar bank_alignment:
    """

    class Meta:
        name = "bankedBankType"

    address_block_or_bank_or_subspace_map: Sequence[
        BankedBlockType | BankedBankType | BankedSubspaceType
    ] = field(
        default_factory=list,
        metadata={
            "type": "Elements",
            "choices": (
                {
                    "name": "addressBlock",
                    "type": BankedBlockType,
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
                },
                {
                    "name": "bank",
                    "type": ForwardRef("BankedBankType"),
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
                },
                {
                    "name": "subspaceMap",
                    "type": BankedSubspaceType,
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
                },
            ),
        },
    )
    usage: None | UsageType = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
        },
    )
    volatile: None | Volatile = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
        },
    )
    access: None | Access = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
        },
    )
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
    bank_alignment: BankAlignmentType = field(
        metadata={
            "name": "bankAlignment",
            "type": "Attribute",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
        }
    )

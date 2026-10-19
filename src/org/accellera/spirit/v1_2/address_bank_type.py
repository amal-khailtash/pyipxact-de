from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from org.accellera.spirit.v1_2.access import Access
from org.accellera.spirit.v1_2.bank_alignment_type import BankAlignmentType
from org.accellera.spirit.v1_2.banked_bank_type import BankedBankType
from org.accellera.spirit.v1_2.banked_block_type import BankedBlockType
from org.accellera.spirit.v1_2.banked_subspace_type import BankedSubspaceType
from org.accellera.spirit.v1_2.base_address import BaseAddress
from org.accellera.spirit.v1_2.bit_offset import BitOffset
from org.accellera.spirit.v1_2.name_value_pair_type import NameValuePairType
from org.accellera.spirit.v1_2.usage_type import UsageType
from org.accellera.spirit.v1_2.vendor_extensions import VendorExtensions
from org.accellera.spirit.v1_2.volatile import Volatile

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2"


@dataclass(slots=True, kw_only=True)
class AddressBankType:
    """
    :ivar base_address:
    :ivar bit_offset:
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
        name = "addressBankType"

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
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2",
                },
                {
                    "name": "bank",
                    "type": BankedBankType,
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2",
                },
                {
                    "name": "subspaceMap",
                    "type": BankedSubspaceType,
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2",
                },
            ),
        },
    )
    usage: None | UsageType = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2",
        },
    )
    volatile: None | Volatile = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2",
        },
    )
    access: None | Access = field(
        default=None,
        metadata={
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
    bank_alignment: BankAlignmentType = field(
        metadata={
            "name": "bankAlignment",
            "type": "Attribute",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2",
        }
    )

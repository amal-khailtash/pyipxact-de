from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from org.accellera.spirit.v1685_2009.ve.pdp.access import Access
from org.accellera.spirit.v1685_2009.ve.pdp.bank_alignment_type import (
    BankAlignmentType,
)
from org.accellera.spirit.v1685_2009.ve.pdp.banked_bank_type import (
    BankedBankType,
)
from org.accellera.spirit.v1685_2009.ve.pdp.banked_block_type import (
    BankedBlockType,
)
from org.accellera.spirit.v1685_2009.ve.pdp.banked_subspace_type import (
    BankedSubspaceType,
)
from org.accellera.spirit.v1685_2009.ve.pdp.base_address import BaseAddress
from org.accellera.spirit.v1685_2009.ve.pdp.description import Description
from org.accellera.spirit.v1685_2009.ve.pdp.display_name import DisplayName
from org.accellera.spirit.v1685_2009.ve.pdp.parameters import Parameters
from org.accellera.spirit.v1685_2009.ve.pdp.usage_type import UsageType
from org.accellera.spirit.v1685_2009.ve.pdp.vendor_extensions import (
    VendorExtensions,
)
from org.accellera.spirit.v1685_2009.ve.pdp.volatile import Volatile

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009"


@dataclass(slots=True, kw_only=True)
class AddressBankType:
    """
    Top level bank the specify an address.

    :ivar name: Unique name
    :ivar display_name:
    :ivar description:
    :ivar base_address:
    :ivar address_block_or_bank_or_subspace_map:
    :ivar usage: Indicates the usage of this block.  Possible values are
        'memory', 'register' and 'reserved'.
    :ivar volatile:
    :ivar access:
    :ivar parameters: Any additional parameters needed to describe this
        address block to the generators.
    :ivar vendor_extensions:
    :ivar bank_alignment:
    """

    class Meta:
        name = "addressBankType"

    name: str = field(
        metadata={
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
        }
    )
    display_name: None | DisplayName = field(
        default=None,
        metadata={
            "name": "displayName",
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
        },
    )
    description: None | Description = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
        },
    )
    base_address: BaseAddress = field(
        metadata={
            "name": "baseAddress",
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
        }
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
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
                },
                {
                    "name": "bank",
                    "type": BankedBankType,
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
                },
                {
                    "name": "subspaceMap",
                    "type": BankedSubspaceType,
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
                },
            ),
        },
    )
    usage: None | UsageType = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
        },
    )
    volatile: None | Volatile = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
        },
    )
    access: None | Access = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
        },
    )
    parameters: None | Parameters = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
        },
    )
    vendor_extensions: None | VendorExtensions = field(
        default=None,
        metadata={
            "name": "vendorExtensions",
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
        },
    )
    bank_alignment: BankAlignmentType = field(
        metadata={
            "name": "bankAlignment",
            "type": "Attribute",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
        }
    )

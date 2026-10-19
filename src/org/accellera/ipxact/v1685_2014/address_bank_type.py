from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from org.accellera.ipxact.v1685_2014.access import Access
from org.accellera.ipxact.v1685_2014.bank_alignment_type import (
    BankAlignmentType,
)
from org.accellera.ipxact.v1685_2014.banked_bank_type import BankedBankType
from org.accellera.ipxact.v1685_2014.banked_block_type import BankedBlockType
from org.accellera.ipxact.v1685_2014.banked_subspace_type import (
    BankedSubspaceType,
)
from org.accellera.ipxact.v1685_2014.base_address import BaseAddress
from org.accellera.ipxact.v1685_2014.description import Description
from org.accellera.ipxact.v1685_2014.display_name import DisplayName
from org.accellera.ipxact.v1685_2014.is_present import IsPresent
from org.accellera.ipxact.v1685_2014.parameters import Parameters
from org.accellera.ipxact.v1685_2014.simple_access_handle import (
    SimpleAccessHandle,
)
from org.accellera.ipxact.v1685_2014.usage_type import UsageType
from org.accellera.ipxact.v1685_2014.vendor_extensions import VendorExtensions
from org.accellera.ipxact.v1685_2014.volatile import Volatile

__NAMESPACE__ = "http://www.accellera.org/XMLSchema/IPXACT/1685-2014"


@dataclass(slots=True, kw_only=True)
class AddressBankType:
    """
    Top level bank the specify an address.

    :ivar name: Unique name
    :ivar display_name:
    :ivar description:
    :ivar access_handles:
    :ivar base_address:
    :ivar is_present:
    :ivar address_block_or_bank_or_subspace_map:
    :ivar usage: Indicates the usage of this block.  Possible values are
        'memory', 'register' and 'reserved'.
    :ivar volatile:
    :ivar access:
    :ivar parameters: Any additional parameters needed to describe this
        address block to the generators.
    :ivar vendor_extensions:
    :ivar bank_alignment: Describes whether this bank's blocks are
        aligned in 'parallel' or 'serial'.
    :ivar id:
    """

    class Meta:
        name = "addressBankType"

    name: str = field(
        metadata={
            "type": "Element",
            "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2014",
        }
    )
    display_name: None | DisplayName = field(
        default=None,
        metadata={
            "name": "displayName",
            "type": "Element",
            "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2014",
        },
    )
    description: None | Description = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2014",
        },
    )
    access_handles: None | AddressBankType.AccessHandles = field(
        default=None,
        metadata={
            "name": "accessHandles",
            "type": "Element",
            "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2014",
        },
    )
    base_address: BaseAddress = field(
        metadata={
            "name": "baseAddress",
            "type": "Element",
            "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2014",
        }
    )
    is_present: None | IsPresent = field(
        default=None,
        metadata={
            "name": "isPresent",
            "type": "Element",
            "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2014",
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
                    "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2014",
                },
                {
                    "name": "bank",
                    "type": BankedBankType,
                    "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2014",
                },
                {
                    "name": "subspaceMap",
                    "type": BankedSubspaceType,
                    "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2014",
                },
            ),
        },
    )
    usage: None | UsageType = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2014",
        },
    )
    volatile: None | Volatile = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2014",
        },
    )
    access: None | Access = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2014",
        },
    )
    parameters: None | Parameters = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2014",
        },
    )
    vendor_extensions: None | VendorExtensions = field(
        default=None,
        metadata={
            "name": "vendorExtensions",
            "type": "Element",
            "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2014",
        },
    )
    bank_alignment: BankAlignmentType = field(
        metadata={
            "name": "bankAlignment",
            "type": "Attribute",
        }
    )
    id: None | str = field(
        default=None,
        metadata={
            "type": "Attribute",
            "namespace": "http://www.w3.org/XML/1998/namespace",
        },
    )

    @dataclass(slots=True, kw_only=True)
    class AccessHandles:
        access_handle: Sequence[SimpleAccessHandle] = field(
            default_factory=list,
            metadata={
                "name": "accessHandle",
                "type": "Element",
                "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2014",
                "min_occurs": 1,
            },
        )

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

from org.accellera.ipxact.v1685_2014.bits_in_lau import BitsInLau
from org.accellera.ipxact.v1685_2014.description import Description
from org.accellera.ipxact.v1685_2014.display_name import DisplayName
from org.accellera.ipxact.v1685_2014.endianess_type import EndianessType
from org.accellera.ipxact.v1685_2014.indirect_address_ref import (
    IndirectAddressRef,
)
from org.accellera.ipxact.v1685_2014.indirect_data_ref import IndirectDataRef
from org.accellera.ipxact.v1685_2014.parameters import Parameters
from org.accellera.ipxact.v1685_2014.transparent_bridge import (
    TransparentBridge,
)
from org.accellera.ipxact.v1685_2014.vendor_extensions import VendorExtensions

__NAMESPACE__ = "http://www.accellera.org/XMLSchema/IPXACT/1685-2014"


@dataclass(slots=True, kw_only=True)
class IndirectInterfaceType:
    """
    Type definition for a indirectInterface in a component.

    :ivar name: Unique name
    :ivar display_name:
    :ivar description:
    :ivar indirect_address_ref:
    :ivar indirect_data_ref:
    :ivar memory_map_ref_or_transparent_bridge:
    :ivar bits_in_lau:
    :ivar endianness: 'big': means the most significant element of any
        multi-element  data field is stored at the lowest memory
        address. 'little' means the least significant element of any
        multi-element data field is stored at the lowest memory address.
        If this element is not present the default is 'little' endian.
    :ivar parameters:
    :ivar vendor_extensions:
    :ivar any_attributes:
    """

    class Meta:
        name = "indirectInterfaceType"

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
    indirect_address_ref: IndirectAddressRef = field(
        metadata={
            "name": "indirectAddressRef",
            "type": "Element",
            "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2014",
        }
    )
    indirect_data_ref: IndirectDataRef = field(
        metadata={
            "name": "indirectDataRef",
            "type": "Element",
            "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2014",
        }
    )
    memory_map_ref_or_transparent_bridge: Sequence[str | TransparentBridge] = (
        field(
            default_factory=list,
            metadata={
                "type": "Elements",
                "choices": (
                    {
                        "name": "memoryMapRef",
                        "type": str,
                        "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2014",
                    },
                    {
                        "name": "transparentBridge",
                        "type": TransparentBridge,
                        "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2014",
                    },
                ),
            },
        )
    )
    bits_in_lau: None | BitsInLau = field(
        default=None,
        metadata={
            "name": "bitsInLau",
            "type": "Element",
            "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2014",
        },
    )
    endianness: None | EndianessType = field(
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
    any_attributes: Mapping[str, str] = field(
        default_factory=dict,
        metadata={
            "type": "Attributes",
            "namespace": "##any",
        },
    )

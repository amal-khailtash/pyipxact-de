from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import ForwardRef

from org.accellera.ipxact.v1685_2022.abstraction_types import AbstractionTypes
from org.accellera.ipxact.v1685_2022.addr_space_ref_type import (
    AddrSpaceRefType,
)
from org.accellera.ipxact.v1685_2022.bits_in_lau import BitsInLau
from org.accellera.ipxact.v1685_2022.configurable_library_ref_type import (
    ConfigurableLibraryRefType,
)
from org.accellera.ipxact.v1685_2022.description import Description
from org.accellera.ipxact.v1685_2022.display_name import DisplayName
from org.accellera.ipxact.v1685_2022.endianess_type import EndianessType
from org.accellera.ipxact.v1685_2022.file_set_ref import FileSetRef
from org.accellera.ipxact.v1685_2022.group import Group
from org.accellera.ipxact.v1685_2022.memory_map_ref import MemoryMapRef
from org.accellera.ipxact.v1685_2022.mode_ref import ModeRef
from org.accellera.ipxact.v1685_2022.monitor_interface_mode import (
    MonitorInterfaceMode,
)
from org.accellera.ipxact.v1685_2022.parameters import Parameters
from org.accellera.ipxact.v1685_2022.short_description import ShortDescription
from org.accellera.ipxact.v1685_2022.signed_longint_expression import (
    SignedLongintExpression,
)
from org.accellera.ipxact.v1685_2022.transparent_bridge import (
    TransparentBridge,
)
from org.accellera.ipxact.v1685_2022.unsigned_bit_expression import (
    UnsignedBitExpression,
)
from org.accellera.ipxact.v1685_2022.unsigned_longint_expression import (
    UnsignedLongintExpression,
)
from org.accellera.ipxact.v1685_2022.unsigned_positive_longint_expression import (
    UnsignedPositiveLongintExpression,
)
from org.accellera.ipxact.v1685_2022.vendor_extensions import VendorExtensions

__NAMESPACE__ = "http://www.accellera.org/XMLSchema/IPXACT/1685-2022"


@dataclass(slots=True, kw_only=True)
class BusInterfaceType:
    """
    Type definition for a busInterface in a component.

    :ivar name: Unique name
    :ivar display_name:
    :ivar short_description:
    :ivar description:
    :ivar bus_type: The bus type of this interface. Refers to bus
        definition using vendor, library, name, version attributes along
        with any configurable element values needed to configure this
        interface.
    :ivar abstraction_types:
    :ivar choice:
    :ivar connection_required: Indicates whether a connection to this
        interface is required for proper component functionality.
    :ivar bits_in_lau:
    :ivar bit_steering: Indicates whether bit steering should be used to
        map this interface onto a bus of different data width. Values
        are "0", "1" (defaults to "0").
    :ivar endianness: 'big': means the most significant element of any
        multi-element  data field is stored at the lowest memory
        address. 'little' means the least significant element of any
        multi-element data field is stored at the lowest memory address.
        If this element is not present the default is 'little' endian.
    :ivar parameters:
    :ivar vendor_extensions:
    :ivar id:
    :ivar other_attributes:
    """

    class Meta:
        name = "busInterfaceType"

    name: str = field(
        metadata={
            "type": "Element",
            "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
        }
    )
    display_name: None | DisplayName = field(
        default=None,
        metadata={
            "name": "displayName",
            "type": "Element",
            "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
        },
    )
    short_description: None | ShortDescription = field(
        default=None,
        metadata={
            "name": "shortDescription",
            "type": "Element",
            "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
        },
    )
    description: None | Description = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
        },
    )
    bus_type: ConfigurableLibraryRefType = field(
        metadata={
            "name": "busType",
            "type": "Element",
            "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
        }
    )
    abstraction_types: None | AbstractionTypes = field(
        default=None,
        metadata={
            "name": "abstractionTypes",
            "type": "Element",
            "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
        },
    )
    choice: (
        None
        | BusInterfaceType.Initiator
        | BusInterfaceType.Target
        | BusInterfaceType.System
        | BusInterfaceType.MirroredTarget
        | object
        | BusInterfaceType.MirroredSystem
        | BusInterfaceType.Monitor
    ) = field(
        default=None,
        metadata={
            "type": "Elements",
            "choices": (
                {
                    "name": "initiator",
                    "type": ForwardRef("BusInterfaceType.Initiator"),
                    "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
                },
                {
                    "name": "target",
                    "type": ForwardRef("BusInterfaceType.Target"),
                    "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
                },
                {
                    "name": "system",
                    "type": ForwardRef("BusInterfaceType.System"),
                    "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
                },
                {
                    "name": "mirroredTarget",
                    "type": ForwardRef("BusInterfaceType.MirroredTarget"),
                    "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
                },
                {
                    "name": "mirroredInitiator",
                    "type": object,
                    "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
                },
                {
                    "name": "mirroredSystem",
                    "type": ForwardRef("BusInterfaceType.MirroredSystem"),
                    "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
                },
                {
                    "name": "monitor",
                    "type": ForwardRef("BusInterfaceType.Monitor"),
                    "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
                },
            ),
        },
    )
    connection_required: None | bool = field(
        default=None,
        metadata={
            "name": "connectionRequired",
            "type": "Element",
            "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
        },
    )
    bits_in_lau: None | BitsInLau = field(
        default=None,
        metadata={
            "name": "bitsInLau",
            "type": "Element",
            "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
        },
    )
    bit_steering: None | UnsignedBitExpression = field(
        default=None,
        metadata={
            "name": "bitSteering",
            "type": "Element",
            "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
        },
    )
    endianness: None | EndianessType = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
        },
    )
    parameters: None | Parameters = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
        },
    )
    vendor_extensions: None | VendorExtensions = field(
        default=None,
        metadata={
            "name": "vendorExtensions",
            "type": "Element",
            "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
        },
    )
    id: None | str = field(
        default=None,
        metadata={
            "type": "Attribute",
            "namespace": "http://www.w3.org/XML/1998/namespace",
        },
    )
    other_attributes: Mapping[str, str] = field(
        default_factory=dict,
        metadata={
            "type": "Attributes",
            "namespace": "##other",
        },
    )

    @dataclass(slots=True, kw_only=True)
    class Initiator:
        """
        :ivar address_space_ref: If this initiator connects to an
            addressable bus, this element references the address space
            it maps to.
        """

        address_space_ref: (
            None | BusInterfaceType.Initiator.AddressSpaceRef
        ) = field(
            default=None,
            metadata={
                "name": "addressSpaceRef",
                "type": "Element",
                "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
            },
        )

        @dataclass(slots=True, kw_only=True)
        class AddressSpaceRef(AddrSpaceRefType):
            """
            :ivar base_address: Base of an address space.
            :ivar mode_ref:
            """

            base_address: None | SignedLongintExpression = field(
                default=None,
                metadata={
                    "name": "baseAddress",
                    "type": "Element",
                    "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
                },
            )
            mode_ref: Sequence[
                BusInterfaceType.Initiator.AddressSpaceRef.ModeRef
            ] = field(
                default_factory=list,
                metadata={
                    "name": "modeRef",
                    "type": "Element",
                    "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
                },
            )

            @dataclass(slots=True, kw_only=True)
            class ModeRef:
                """
                A reference to a mode.
                """

                value: str = field(default="")
                id: None | str = field(
                    default=None,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.w3.org/XML/1998/namespace",
                    },
                )

    @dataclass(slots=True, kw_only=True)
    class Target:
        """
        :ivar memory_map_ref_or_transparent_bridge:
        :ivar file_set_ref_group: This reference is used to point the
            filesets that are associated with this target port.
            Depending on the target port function, there may be
            completely different software drivers associated with the
            different ports.
        """

        memory_map_ref_or_transparent_bridge: Sequence[
            MemoryMapRef | TransparentBridge
        ] = field(
            default_factory=list,
            metadata={
                "type": "Elements",
                "choices": (
                    {
                        "name": "memoryMapRef",
                        "type": MemoryMapRef,
                        "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
                    },
                    {
                        "name": "transparentBridge",
                        "type": TransparentBridge,
                        "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
                    },
                ),
            },
        )
        file_set_ref_group: Sequence[
            BusInterfaceType.Target.FileSetRefGroup
        ] = field(
            default_factory=list,
            metadata={
                "name": "fileSetRefGroup",
                "type": "Element",
                "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
            },
        )

        @dataclass(slots=True, kw_only=True)
        class FileSetRefGroup:
            """
            :ivar group: Abritray name assigned to the collections of
                fileSets.
            :ivar file_set_ref:
            :ivar id:
            """

            group: None | str = field(
                default=None,
                metadata={
                    "type": "Element",
                    "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
                },
            )
            file_set_ref: Sequence[FileSetRef] = field(
                default_factory=list,
                metadata={
                    "name": "fileSetRef",
                    "type": "Element",
                    "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
                },
            )
            id: None | str = field(
                default=None,
                metadata={
                    "type": "Attribute",
                    "namespace": "http://www.w3.org/XML/1998/namespace",
                },
            )

    @dataclass(slots=True, kw_only=True)
    class System:
        group: Group = field(
            metadata={
                "type": "Element",
                "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
            }
        )

    @dataclass(slots=True, kw_only=True)
    class MirroredTarget:
        """
        :ivar base_addresses: Represents a set of remap base addresses.
        """

        base_addresses: (
            None | BusInterfaceType.MirroredTarget.BaseAddresses
        ) = field(
            default=None,
            metadata={
                "name": "baseAddresses",
                "type": "Element",
                "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
            },
        )

        @dataclass(slots=True, kw_only=True)
        class BaseAddresses:
            """
            :ivar remap_addresses:
            :ivar range: The address range of mirrored target, expressed
                as the number of bitsInLAU from the containing
                busInterface.
            """

            remap_addresses: Sequence[
                BusInterfaceType.MirroredTarget.BaseAddresses.RemapAddresses
            ] = field(
                default_factory=list,
                metadata={
                    "name": "remapAddresses",
                    "type": "Element",
                    "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
                    "min_occurs": 1,
                },
            )
            range: UnsignedPositiveLongintExpression = field(
                metadata={
                    "type": "Element",
                    "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
                }
            )

            @dataclass(slots=True, kw_only=True)
            class RemapAddresses:
                """
                :ivar remap_address: Base of an address block, expressed
                    as the number of bitsInLAU from the containing
                    busInterface. The modeRef element indicates the name
                    of the mode for which this address is valid.
                :ivar mode_ref:
                :ivar id:
                """

                remap_address: UnsignedLongintExpression = field(
                    metadata={
                        "name": "remapAddress",
                        "type": "Element",
                        "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
                    }
                )
                mode_ref: Sequence[ModeRef] = field(
                    default_factory=list,
                    metadata={
                        "name": "modeRef",
                        "type": "Element",
                        "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
                    },
                )
                id: None | str = field(
                    default=None,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.w3.org/XML/1998/namespace",
                    },
                )

    @dataclass(slots=True, kw_only=True)
    class MirroredSystem:
        group: Group = field(
            metadata={
                "type": "Element",
                "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
            }
        )

    @dataclass(slots=True, kw_only=True)
    class Monitor:
        """
        :ivar group: Indicates which system interface is being
            monitored. Name must match a group name present on one or
            more ports in the corresonding bus definition.
        :ivar interface_mode:
        """

        group: None | Group = field(
            default=None,
            metadata={
                "type": "Element",
                "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
            },
        )
        interface_mode: MonitorInterfaceMode = field(
            metadata={
                "name": "interfaceMode",
                "type": "Attribute",
            }
        )

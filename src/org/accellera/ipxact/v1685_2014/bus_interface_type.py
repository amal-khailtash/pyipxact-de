from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import ForwardRef

from org.accellera.ipxact.v1685_2014.abstraction_types import AbstractionTypes
from org.accellera.ipxact.v1685_2014.addr_space_ref_type import (
    AddrSpaceRefType,
)
from org.accellera.ipxact.v1685_2014.bits_in_lau import BitsInLau
from org.accellera.ipxact.v1685_2014.complex_bit_steering_expression import (
    ComplexBitSteeringExpression,
)
from org.accellera.ipxact.v1685_2014.configurable_library_ref_type import (
    ConfigurableLibraryRefType,
)
from org.accellera.ipxact.v1685_2014.description import Description
from org.accellera.ipxact.v1685_2014.display_name import DisplayName
from org.accellera.ipxact.v1685_2014.endianess_type import EndianessType
from org.accellera.ipxact.v1685_2014.file_set_ref import FileSetRef
from org.accellera.ipxact.v1685_2014.group import Group
from org.accellera.ipxact.v1685_2014.is_present import IsPresent
from org.accellera.ipxact.v1685_2014.memory_map_ref import MemoryMapRef
from org.accellera.ipxact.v1685_2014.monitor_interface_mode import (
    MonitorInterfaceMode,
)
from org.accellera.ipxact.v1685_2014.parameters import Parameters
from org.accellera.ipxact.v1685_2014.signed_longint_expression import (
    SignedLongintExpression,
)
from org.accellera.ipxact.v1685_2014.transparent_bridge import (
    TransparentBridge,
)
from org.accellera.ipxact.v1685_2014.unsigned_longint_expression import (
    UnsignedLongintExpression,
)
from org.accellera.ipxact.v1685_2014.unsigned_positive_longint_expression import (
    UnsignedPositiveLongintExpression,
)
from org.accellera.ipxact.v1685_2014.vendor_extensions import VendorExtensions

__NAMESPACE__ = "http://www.accellera.org/XMLSchema/IPXACT/1685-2014"


@dataclass(slots=True, kw_only=True)
class BusInterfaceType:
    """
    Type definition for a busInterface in a component.

    :ivar name: Unique name
    :ivar display_name:
    :ivar description:
    :ivar is_present:
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
        are "on", "off" (defaults to "off").
    :ivar endianness: 'big': means the most significant element of any
        multi-element  data field is stored at the lowest memory
        address. 'little' means the least significant element of any
        multi-element data field is stored at the lowest memory address.
        If this element is not present the default is 'little' endian.
    :ivar parameters:
    :ivar vendor_extensions:
    :ivar other_attributes:
    """

    class Meta:
        name = "busInterfaceType"

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
    is_present: None | IsPresent = field(
        default=None,
        metadata={
            "name": "isPresent",
            "type": "Element",
            "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2014",
        },
    )
    bus_type: ConfigurableLibraryRefType = field(
        metadata={
            "name": "busType",
            "type": "Element",
            "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2014",
        }
    )
    abstraction_types: None | AbstractionTypes = field(
        default=None,
        metadata={
            "name": "abstractionTypes",
            "type": "Element",
            "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2014",
        },
    )
    choice: (
        None
        | BusInterfaceType.Master
        | BusInterfaceType.Slave
        | BusInterfaceType.System
        | BusInterfaceType.MirroredSlave
        | object
        | BusInterfaceType.MirroredSystem
        | BusInterfaceType.Monitor
    ) = field(
        default=None,
        metadata={
            "type": "Elements",
            "choices": (
                {
                    "name": "master",
                    "type": ForwardRef("BusInterfaceType.Master"),
                    "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2014",
                },
                {
                    "name": "slave",
                    "type": ForwardRef("BusInterfaceType.Slave"),
                    "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2014",
                },
                {
                    "name": "system",
                    "type": ForwardRef("BusInterfaceType.System"),
                    "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2014",
                },
                {
                    "name": "mirroredSlave",
                    "type": ForwardRef("BusInterfaceType.MirroredSlave"),
                    "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2014",
                },
                {
                    "name": "mirroredMaster",
                    "type": object,
                    "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2014",
                },
                {
                    "name": "mirroredSystem",
                    "type": ForwardRef("BusInterfaceType.MirroredSystem"),
                    "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2014",
                },
                {
                    "name": "monitor",
                    "type": ForwardRef("BusInterfaceType.Monitor"),
                    "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2014",
                },
            ),
        },
    )
    connection_required: None | bool = field(
        default=None,
        metadata={
            "name": "connectionRequired",
            "type": "Element",
            "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2014",
        },
    )
    bits_in_lau: None | BitsInLau = field(
        default=None,
        metadata={
            "name": "bitsInLau",
            "type": "Element",
            "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2014",
        },
    )
    bit_steering: None | ComplexBitSteeringExpression = field(
        default=None,
        metadata={
            "name": "bitSteering",
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
    other_attributes: Mapping[str, str] = field(
        default_factory=dict,
        metadata={
            "type": "Attributes",
            "namespace": "##other",
        },
    )

    @dataclass(slots=True, kw_only=True)
    class Master:
        """
        :ivar address_space_ref: If this master connects to an
            addressable bus, this element references the address space
            it maps to.
        """

        address_space_ref: None | BusInterfaceType.Master.AddressSpaceRef = (
            field(
                default=None,
                metadata={
                    "name": "addressSpaceRef",
                    "type": "Element",
                    "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2014",
                },
            )
        )

        @dataclass(slots=True, kw_only=True)
        class AddressSpaceRef(AddrSpaceRefType):
            """
            :ivar base_address: Base of an address space.
            """

            base_address: None | SignedLongintExpression = field(
                default=None,
                metadata={
                    "name": "baseAddress",
                    "type": "Element",
                    "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2014",
                },
            )

    @dataclass(slots=True, kw_only=True)
    class Slave:
        """
        :ivar memory_map_ref_or_transparent_bridge:
        :ivar file_set_ref_group: This reference is used to point the
            filesets that are associated with this slave port. Depending
            on the slave port function, there may be completely
            different software drivers associated with the different
            ports.
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
        file_set_ref_group: Sequence[
            BusInterfaceType.Slave.FileSetRefGroup
        ] = field(
            default_factory=list,
            metadata={
                "name": "fileSetRefGroup",
                "type": "Element",
                "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2014",
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
                    "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2014",
                },
            )
            file_set_ref: Sequence[FileSetRef] = field(
                default_factory=list,
                metadata={
                    "name": "fileSetRef",
                    "type": "Element",
                    "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2014",
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
                "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2014",
            }
        )

    @dataclass(slots=True, kw_only=True)
    class MirroredSlave:
        """
        :ivar base_addresses: Represents a set of remap base addresses.
        """

        base_addresses: None | BusInterfaceType.MirroredSlave.BaseAddresses = (
            field(
                default=None,
                metadata={
                    "name": "baseAddresses",
                    "type": "Element",
                    "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2014",
                },
            )
        )

        @dataclass(slots=True, kw_only=True)
        class BaseAddresses:
            """
            :ivar remap_address: Base of an address block, expressed as
                the number of bitsInLAU from the containing
                busInterface. The state attribute indicates the name of
                the remap state for which this address is valid.
            :ivar range: The address range of mirrored slave, expressed
                as the number of bitsInLAU from the containing
                busInterface.
            """

            remap_address: Sequence[
                BusInterfaceType.MirroredSlave.BaseAddresses.RemapAddress
            ] = field(
                default_factory=list,
                metadata={
                    "name": "remapAddress",
                    "type": "Element",
                    "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2014",
                    "min_occurs": 1,
                },
            )
            range: UnsignedPositiveLongintExpression = field(
                metadata={
                    "type": "Element",
                    "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2014",
                }
            )

            @dataclass(slots=True, kw_only=True)
            class RemapAddress(UnsignedLongintExpression):
                """
                :ivar state: Name of the state in which this remapped
                    address range is valid
                :ivar id:
                """

                state: None | str = field(
                    default=None,
                    metadata={
                        "type": "Attribute",
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
                "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2014",
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
                "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2014",
            },
        )
        interface_mode: MonitorInterfaceMode = field(
            metadata={
                "name": "interfaceMode",
                "type": "Attribute",
            }
        )

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import ForwardRef

from org.accellera.spirit.v1_4.addr_space_ref_type import AddrSpaceRefType
from org.accellera.spirit.v1_4.bit_steering_type import BitSteeringType
from org.accellera.spirit.v1_4.bits_in_lau import BitsInLau
from org.accellera.spirit.v1_4.endianess_type import EndianessType
from org.accellera.spirit.v1_4.file_set_ref import FileSetRef
from org.accellera.spirit.v1_4.format_type import FormatType
from org.accellera.spirit.v1_4.group import Group
from org.accellera.spirit.v1_4.library_ref_type import LibraryRefType
from org.accellera.spirit.v1_4.memory_map_ref import MemoryMapRef
from org.accellera.spirit.v1_4.monitor_interface_mode import (
    MonitorInterfaceMode,
)
from org.accellera.spirit.v1_4.parameters import Parameters
from org.accellera.spirit.v1_4.range_type_type import RangeTypeType
from org.accellera.spirit.v1_4.resolve_type import ResolveType
from org.accellera.spirit.v1_4.vector import Vector
from org.accellera.spirit.v1_4.vendor_extensions import VendorExtensions

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4"


@dataclass(slots=True, kw_only=True)
class BusInterfaceType:
    """
    Type definition for a busInterface in a component.

    :ivar name: Unique name
    :ivar display_name: Element name for display purposes. Typically a
        few words providing a more detailed and/or user-friendly name
        than the spirit:name.
    :ivar description: Full description string, typically for
        documentation
    :ivar bus_type: The bus type of this interface. Refers to bus
        definition using vendor, library, name, version attributes.
    :ivar abstraction_type: The abstraction type/level of this
        interface. Refers to abstraction definition using vendor,
        library, name, version attributes. Bus definition can be found
        through a reference in this file.
    :ivar choice:
    :ivar connection_required: Indicates whether a connection to this
        interface is required for proper component functionality.
    :ivar port_maps: Listing of maps between component ports and bus
        ports.
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
    :ivar any_attributes:
    """

    class Meta:
        name = "busInterfaceType"

    name: str = field(
        metadata={
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
        }
    )
    display_name: None | str = field(
        default=None,
        metadata={
            "name": "displayName",
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
        },
    )
    description: None | str = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
        },
    )
    bus_type: LibraryRefType = field(
        metadata={
            "name": "busType",
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
        }
    )
    abstraction_type: None | LibraryRefType = field(
        default=None,
        metadata={
            "name": "abstractionType",
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
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
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                },
                {
                    "name": "slave",
                    "type": ForwardRef("BusInterfaceType.Slave"),
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                },
                {
                    "name": "system",
                    "type": ForwardRef("BusInterfaceType.System"),
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                },
                {
                    "name": "mirroredSlave",
                    "type": ForwardRef("BusInterfaceType.MirroredSlave"),
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                },
                {
                    "name": "mirroredMaster",
                    "type": object,
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                },
                {
                    "name": "mirroredSystem",
                    "type": ForwardRef("BusInterfaceType.MirroredSystem"),
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                },
                {
                    "name": "monitor",
                    "type": ForwardRef("BusInterfaceType.Monitor"),
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                },
            ),
        },
    )
    connection_required: None | bool = field(
        default=None,
        metadata={
            "name": "connectionRequired",
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
        },
    )
    port_maps: None | BusInterfaceType.PortMaps = field(
        default=None,
        metadata={
            "name": "portMaps",
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
        },
    )
    bits_in_lau: None | BitsInLau = field(
        default=None,
        metadata={
            "name": "bitsInLau",
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
        },
    )
    bit_steering: None | BusInterfaceType.BitSteering = field(
        default=None,
        metadata={
            "name": "bitSteering",
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
        },
    )
    endianness: None | EndianessType = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
        },
    )
    parameters: None | Parameters = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
        },
    )
    vendor_extensions: None | VendorExtensions = field(
        default=None,
        metadata={
            "name": "vendorExtensions",
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
        },
    )
    any_attributes: Mapping[str, str] = field(
        default_factory=dict,
        metadata={
            "type": "Attributes",
            "namespace": "##any",
        },
    )

    @dataclass(slots=True, kw_only=True)
    class PortMaps:
        """
        :ivar port_map: Maps a component's port to a port in a bus
            description. This is the logical to physical mapping. The
            logical pin comes from the bus interface and the physical
            pin from the component.
        """

        port_map: Sequence[BusInterfaceType.PortMaps.PortMap] = field(
            default_factory=list,
            metadata={
                "name": "portMap",
                "type": "Element",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                "min_occurs": 1,
            },
        )

        @dataclass(slots=True, kw_only=True)
        class PortMap:
            """
            :ivar logical_port: Logical port from abstraction definition
            :ivar physical_port: Physical port from this component
            """

            logical_port: BusInterfaceType.PortMaps.PortMap.LogicalPort = field(
                metadata={
                    "name": "logicalPort",
                    "type": "Element",
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                }
            )
            physical_port: BusInterfaceType.PortMaps.PortMap.PhysicalPort = field(
                metadata={
                    "name": "physicalPort",
                    "type": "Element",
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                }
            )

            @dataclass(slots=True, kw_only=True)
            class LogicalPort:
                """
                :ivar name: Bus port name as specified inside the
                    abstraction definition
                :ivar vector: Definition of the logical indecies for a
                    vectored port.
                """

                name: str = field(
                    metadata={
                        "type": "Element",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                    }
                )
                vector: (
                    None | BusInterfaceType.PortMaps.PortMap.LogicalPort.Vector
                ) = field(
                    default=None,
                    metadata={
                        "type": "Element",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                    },
                )

                @dataclass(slots=True, kw_only=True)
                class Vector:
                    """
                    :ivar left: Defines which logical bit maps to the
                        physical left bit below
                    :ivar right: Defines which logical bit maps to the
                        physical right bit below
                    """

                    left: BusInterfaceType.PortMaps.PortMap.LogicalPort.Vector.Left = field(
                        metadata={
                            "type": "Element",
                            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                        }
                    )
                    right: BusInterfaceType.PortMaps.PortMap.LogicalPort.Vector.Right = field(
                        metadata={
                            "type": "Element",
                            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                        }
                    )

                    @dataclass(slots=True, kw_only=True)
                    class Left:
                        value: int = field()
                        format: FormatType = field(
                            default=FormatType.LONG,
                            metadata={
                                "type": "Attribute",
                                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                            },
                        )
                        resolve: ResolveType = field(
                            default=ResolveType.IMMEDIATE,
                            metadata={
                                "type": "Attribute",
                                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                            },
                        )
                        id: None | str = field(
                            default=None,
                            metadata={
                                "type": "Attribute",
                                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                            },
                        )
                        dependency: None | str = field(
                            default=None,
                            metadata={
                                "type": "Attribute",
                                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                            },
                        )
                        any_attributes: Mapping[str, str] = field(
                            default_factory=dict,
                            metadata={
                                "type": "Attributes",
                                "namespace": "##any",
                            },
                        )
                        choice_ref: None | str = field(
                            default=None,
                            metadata={
                                "name": "choiceRef",
                                "type": "Attribute",
                                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                            },
                        )
                        order: None | float = field(
                            default=None,
                            metadata={
                                "type": "Attribute",
                                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                            },
                        )
                        config_groups: Sequence[str] = field(
                            default_factory=list,
                            metadata={
                                "name": "configGroups",
                                "type": "Attribute",
                                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                                "tokens": True,
                            },
                        )
                        bit_string_length: None | int = field(
                            default=None,
                            metadata={
                                "name": "bitStringLength",
                                "type": "Attribute",
                                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                            },
                        )
                        minimum: None | str = field(
                            default=None,
                            metadata={
                                "type": "Attribute",
                                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                            },
                        )
                        maximum: None | str = field(
                            default=None,
                            metadata={
                                "type": "Attribute",
                                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                            },
                        )
                        range_type: RangeTypeType = field(
                            default=RangeTypeType.FLOAT,
                            metadata={
                                "name": "rangeType",
                                "type": "Attribute",
                                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                            },
                        )
                        prompt: None | str = field(
                            default=None,
                            metadata={
                                "type": "Attribute",
                                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                            },
                        )

                    @dataclass(slots=True, kw_only=True)
                    class Right:
                        value: int = field()
                        format: FormatType = field(
                            default=FormatType.LONG,
                            metadata={
                                "type": "Attribute",
                                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                            },
                        )
                        resolve: ResolveType = field(
                            default=ResolveType.IMMEDIATE,
                            metadata={
                                "type": "Attribute",
                                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                            },
                        )
                        id: None | str = field(
                            default=None,
                            metadata={
                                "type": "Attribute",
                                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                            },
                        )
                        dependency: None | str = field(
                            default=None,
                            metadata={
                                "type": "Attribute",
                                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                            },
                        )
                        any_attributes: Mapping[str, str] = field(
                            default_factory=dict,
                            metadata={
                                "type": "Attributes",
                                "namespace": "##any",
                            },
                        )
                        choice_ref: None | str = field(
                            default=None,
                            metadata={
                                "name": "choiceRef",
                                "type": "Attribute",
                                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                            },
                        )
                        order: None | float = field(
                            default=None,
                            metadata={
                                "type": "Attribute",
                                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                            },
                        )
                        config_groups: Sequence[str] = field(
                            default_factory=list,
                            metadata={
                                "name": "configGroups",
                                "type": "Attribute",
                                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                                "tokens": True,
                            },
                        )
                        bit_string_length: None | int = field(
                            default=None,
                            metadata={
                                "name": "bitStringLength",
                                "type": "Attribute",
                                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                            },
                        )
                        minimum: None | str = field(
                            default=None,
                            metadata={
                                "type": "Attribute",
                                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                            },
                        )
                        maximum: None | str = field(
                            default=None,
                            metadata={
                                "type": "Attribute",
                                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                            },
                        )
                        range_type: RangeTypeType = field(
                            default=RangeTypeType.FLOAT,
                            metadata={
                                "name": "rangeType",
                                "type": "Attribute",
                                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                            },
                        )
                        prompt: None | str = field(
                            default=None,
                            metadata={
                                "type": "Attribute",
                                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                            },
                        )

            @dataclass(slots=True, kw_only=True)
            class PhysicalPort:
                """
                :ivar name: Component port name as specified inside the
                    model port section
                :ivar vector:
                """

                name: str = field(
                    metadata={
                        "type": "Element",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                    }
                )
                vector: None | Vector = field(
                    default=None,
                    metadata={
                        "type": "Element",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                    },
                )

    @dataclass(slots=True, kw_only=True)
    class BitSteering:
        value: BitSteeringType = field()
        format: FormatType = field(
            default=FormatType.STRING,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
            },
        )
        resolve: ResolveType = field(
            default=ResolveType.IMMEDIATE,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
            },
        )
        id: None | str = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
            },
        )
        dependency: None | str = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
            },
        )
        any_attributes: Mapping[str, str] = field(
            default_factory=dict,
            metadata={
                "type": "Attributes",
                "namespace": "##any",
            },
        )
        choice_ref: None | str = field(
            default=None,
            metadata={
                "name": "choiceRef",
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
            },
        )
        order: None | float = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
            },
        )
        config_groups: Sequence[str] = field(
            default_factory=list,
            metadata={
                "name": "configGroups",
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                "tokens": True,
            },
        )
        bit_string_length: None | int = field(
            default=None,
            metadata={
                "name": "bitStringLength",
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
            },
        )
        minimum: None | str = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
            },
        )
        maximum: None | str = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
            },
        )
        range_type: RangeTypeType = field(
            default=RangeTypeType.FLOAT,
            metadata={
                "name": "rangeType",
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
            },
        )
        prompt: None | str = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
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
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                },
            )
        )

        @dataclass(slots=True, kw_only=True)
        class AddressSpaceRef(AddrSpaceRefType):
            """
            :ivar base_address: Base of an address space.
            """

            base_address: (
                None | BusInterfaceType.Master.AddressSpaceRef.BaseAddress
            ) = field(
                default=None,
                metadata={
                    "name": "baseAddress",
                    "type": "Element",
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                },
            )

            @dataclass(slots=True, kw_only=True)
            class BaseAddress:
                value: str = field(
                    default="",
                    metadata={
                        "pattern": r"[+\-]?(0x|0X|#)?[0-9a-fA-F]+[kmgtKMGT]?",
                    },
                )
                format: FormatType = field(
                    default=FormatType.LONG,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                    },
                )
                resolve: ResolveType = field(
                    default=ResolveType.IMMEDIATE,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                    },
                )
                id: None | str = field(
                    default=None,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                    },
                )
                dependency: None | str = field(
                    default=None,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                    },
                )
                any_attributes: Mapping[str, str] = field(
                    default_factory=dict,
                    metadata={
                        "type": "Attributes",
                        "namespace": "##any",
                    },
                )
                choice_ref: None | str = field(
                    default=None,
                    metadata={
                        "name": "choiceRef",
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                    },
                )
                order: None | float = field(
                    default=None,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                    },
                )
                config_groups: Sequence[str] = field(
                    default_factory=list,
                    metadata={
                        "name": "configGroups",
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                        "tokens": True,
                    },
                )
                bit_string_length: None | int = field(
                    default=None,
                    metadata={
                        "name": "bitStringLength",
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                    },
                )
                minimum: None | str = field(
                    default=None,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                    },
                )
                maximum: None | str = field(
                    default=None,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                    },
                )
                range_type: RangeTypeType = field(
                    default=RangeTypeType.FLOAT,
                    metadata={
                        "name": "rangeType",
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                    },
                )
                prompt: str = field(
                    default="Base Address:",
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                    },
                )

    @dataclass(slots=True, kw_only=True)
    class Slave:
        """
        :ivar memory_map_ref:
        :ivar bridge: If this element is present, it indicates that the
            bus interface provides a bridge to another master bus
            interface on the same component.  It has a masterRef
            attribute which contains the name of the other bus
            interface.  It also has an opaque attribute to indicate that
            the bus bridge is opaque. Any slave interface can bridge to
            multiple master interfaces, and multiple slave interfaces
            can bridge to the same master interface.
        :ivar file_set_ref_group: This reference is used to point the
            filesets that are associated with this slave port. Depending
            on the slave port function, there may be completely
            different software drivers associated with the different
            ports.
        """

        memory_map_ref: None | MemoryMapRef = field(
            default=None,
            metadata={
                "name": "memoryMapRef",
                "type": "Element",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
            },
        )
        bridge: Sequence[BusInterfaceType.Slave.Bridge] = field(
            default_factory=list,
            metadata={
                "type": "Element",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
            },
        )
        file_set_ref_group: Sequence[
            BusInterfaceType.Slave.FileSetRefGroup
        ] = field(
            default_factory=list,
            metadata={
                "name": "fileSetRefGroup",
                "type": "Element",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
            },
        )

        @dataclass(slots=True, kw_only=True)
        class Bridge:
            """
            :ivar master_ref: The name of the master bus interface to
                which this interface bridges.
            :ivar opaque: If true, then this bridge is opaque; the whole
                of the address range is mappeed by the bridge and there
                are no gaps.
            """

            master_ref: str = field(
                metadata={
                    "name": "masterRef",
                    "type": "Attribute",
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                }
            )
            opaque: bool = field(
                metadata={
                    "type": "Attribute",
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                }
            )

        @dataclass(slots=True, kw_only=True)
        class FileSetRefGroup:
            """
            :ivar group: Abritray name assigned to the collections of
                fileSets.
            :ivar file_set_ref:
            """

            group: None | str = field(
                default=None,
                metadata={
                    "type": "Element",
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                },
            )
            file_set_ref: Sequence[FileSetRef] = field(
                default_factory=list,
                metadata={
                    "name": "fileSetRef",
                    "type": "Element",
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                },
            )

    @dataclass(slots=True, kw_only=True)
    class System:
        group: Group = field(
            metadata={
                "type": "Element",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
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
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                },
            )
        )

        @dataclass(slots=True, kw_only=True)
        class BaseAddresses:
            """
            :ivar remap_address: Base of an address block. The state
                attribute indicates the name of the remap state for
                which this address is valid.
            :ivar range: The address range of mirrored slave.
            """

            remap_address: Sequence[
                BusInterfaceType.MirroredSlave.BaseAddresses.RemapAddress
            ] = field(
                default_factory=list,
                metadata={
                    "name": "remapAddress",
                    "type": "Element",
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                    "min_occurs": 1,
                },
            )
            range: BusInterfaceType.MirroredSlave.BaseAddresses.Range = field(
                metadata={
                    "type": "Element",
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                }
            )

            @dataclass(slots=True, kw_only=True)
            class RemapAddress:
                """
                :ivar value:
                :ivar format:
                :ivar resolve:
                :ivar id:
                :ivar dependency:
                :ivar any_attributes:
                :ivar choice_ref:
                :ivar order:
                :ivar config_groups:
                :ivar bit_string_length:
                :ivar minimum:
                :ivar maximum:
                :ivar range_type:
                :ivar prompt:
                :ivar state: Name of the state in which this remapped
                    address range is valid
                """

                value: str = field(
                    default="",
                    metadata={
                        "pattern": r"[+]?(0x|0X|#)?[0-9a-fA-F]+[kmgtKMGT]?",
                    },
                )
                format: FormatType = field(
                    default=FormatType.LONG,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                    },
                )
                resolve: ResolveType = field(
                    default=ResolveType.IMMEDIATE,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                    },
                )
                id: None | str = field(
                    default=None,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                    },
                )
                dependency: None | str = field(
                    default=None,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                    },
                )
                any_attributes: Mapping[str, str] = field(
                    default_factory=dict,
                    metadata={
                        "type": "Attributes",
                        "namespace": "##any",
                    },
                )
                choice_ref: None | str = field(
                    default=None,
                    metadata={
                        "name": "choiceRef",
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                    },
                )
                order: None | float = field(
                    default=None,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                    },
                )
                config_groups: Sequence[str] = field(
                    default_factory=list,
                    metadata={
                        "name": "configGroups",
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                        "tokens": True,
                    },
                )
                bit_string_length: None | int = field(
                    default=None,
                    metadata={
                        "name": "bitStringLength",
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                    },
                )
                minimum: None | str = field(
                    default=None,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                    },
                )
                maximum: None | str = field(
                    default=None,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                    },
                )
                range_type: RangeTypeType = field(
                    default=RangeTypeType.FLOAT,
                    metadata={
                        "name": "rangeType",
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                    },
                )
                prompt: str = field(
                    default="Base Address:",
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                    },
                )
                state: None | str = field(
                    default=None,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                    },
                )

            @dataclass(slots=True, kw_only=True)
            class Range:
                value: str = field(
                    default="",
                    metadata={
                        "pattern": r"[+]?(0x|0X|#)?[0]*[1-9a-fA-F][0-9a-fA-F]*[kmgtKMGT]?",
                    },
                )
                format: FormatType = field(
                    default=FormatType.LONG,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                    },
                )
                resolve: ResolveType = field(
                    default=ResolveType.IMMEDIATE,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                    },
                )
                id: None | str = field(
                    default=None,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                    },
                )
                dependency: None | str = field(
                    default=None,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                    },
                )
                any_attributes: Mapping[str, str] = field(
                    default_factory=dict,
                    metadata={
                        "type": "Attributes",
                        "namespace": "##any",
                    },
                )
                choice_ref: None | str = field(
                    default=None,
                    metadata={
                        "name": "choiceRef",
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                    },
                )
                order: None | float = field(
                    default=None,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                    },
                )
                config_groups: Sequence[str] = field(
                    default_factory=list,
                    metadata={
                        "name": "configGroups",
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                        "tokens": True,
                    },
                )
                bit_string_length: None | int = field(
                    default=None,
                    metadata={
                        "name": "bitStringLength",
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                    },
                )
                minimum: None | str = field(
                    default=None,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                    },
                )
                maximum: None | str = field(
                    default=None,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                    },
                )
                range_type: RangeTypeType = field(
                    default=RangeTypeType.FLOAT,
                    metadata={
                        "name": "rangeType",
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                    },
                )
                prompt: None | str = field(
                    default=None,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                    },
                )

    @dataclass(slots=True, kw_only=True)
    class MirroredSystem:
        group: Group = field(
            metadata={
                "type": "Element",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
            }
        )

    @dataclass(slots=True, kw_only=True)
    class Monitor:
        group: None | Group = field(
            default=None,
            metadata={
                "type": "Element",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
            },
        )
        interface_mode: MonitorInterfaceMode = field(
            metadata={
                "name": "interfaceMode",
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
            }
        )

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import ForwardRef

from org.accellera.spirit.v1_5.addr_space_ref_type import AddrSpaceRefType
from org.accellera.spirit.v1_5.bit_steering_type import BitSteeringType
from org.accellera.spirit.v1_5.bits_in_lau import BitsInLau
from org.accellera.spirit.v1_5.description import Description
from org.accellera.spirit.v1_5.display_name import DisplayName
from org.accellera.spirit.v1_5.endianess_type import EndianessType
from org.accellera.spirit.v1_5.file_set_ref import FileSetRef
from org.accellera.spirit.v1_5.format_type import FormatType
from org.accellera.spirit.v1_5.group import Group
from org.accellera.spirit.v1_5.library_ref_type import LibraryRefType
from org.accellera.spirit.v1_5.memory_map_ref import MemoryMapRef
from org.accellera.spirit.v1_5.monitor_interface_mode import (
    MonitorInterfaceMode,
)
from org.accellera.spirit.v1_5.parameters import Parameters
from org.accellera.spirit.v1_5.range_type_type import RangeTypeType
from org.accellera.spirit.v1_5.resolve_type import ResolveType
from org.accellera.spirit.v1_5.vector import Vector
from org.accellera.spirit.v1_5.vendor_extensions import VendorExtensions

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5"


@dataclass(slots=True, kw_only=True)
class BusInterfaceType:
    """
    Type definition for a busInterface in a component.

    :ivar name: Unique name
    :ivar display_name:
    :ivar description:
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
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
        }
    )
    display_name: None | DisplayName = field(
        default=None,
        metadata={
            "name": "displayName",
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
        },
    )
    description: None | Description = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
        },
    )
    bus_type: LibraryRefType = field(
        metadata={
            "name": "busType",
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
        }
    )
    abstraction_type: None | LibraryRefType = field(
        default=None,
        metadata={
            "name": "abstractionType",
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
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
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                },
                {
                    "name": "slave",
                    "type": ForwardRef("BusInterfaceType.Slave"),
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                },
                {
                    "name": "system",
                    "type": ForwardRef("BusInterfaceType.System"),
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                },
                {
                    "name": "mirroredSlave",
                    "type": ForwardRef("BusInterfaceType.MirroredSlave"),
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                },
                {
                    "name": "mirroredMaster",
                    "type": object,
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                },
                {
                    "name": "mirroredSystem",
                    "type": ForwardRef("BusInterfaceType.MirroredSystem"),
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                },
                {
                    "name": "monitor",
                    "type": ForwardRef("BusInterfaceType.Monitor"),
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                },
            ),
        },
    )
    connection_required: None | bool = field(
        default=None,
        metadata={
            "name": "connectionRequired",
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
        },
    )
    port_maps: None | BusInterfaceType.PortMaps = field(
        default=None,
        metadata={
            "name": "portMaps",
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
        },
    )
    bits_in_lau: None | BitsInLau = field(
        default=None,
        metadata={
            "name": "bitsInLau",
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
        },
    )
    bit_steering: None | BusInterfaceType.BitSteering = field(
        default=None,
        metadata={
            "name": "bitSteering",
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
        },
    )
    endianness: None | EndianessType = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
        },
    )
    parameters: None | Parameters = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
        },
    )
    vendor_extensions: None | VendorExtensions = field(
        default=None,
        metadata={
            "name": "vendorExtensions",
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
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
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
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
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                }
            )
            physical_port: BusInterfaceType.PortMaps.PortMap.PhysicalPort = field(
                metadata={
                    "name": "physicalPort",
                    "type": "Element",
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
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
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                    }
                )
                vector: (
                    None | BusInterfaceType.PortMaps.PortMap.LogicalPort.Vector
                ) = field(
                    default=None,
                    metadata={
                        "type": "Element",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
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
                            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                        }
                    )
                    right: BusInterfaceType.PortMaps.PortMap.LogicalPort.Vector.Right = field(
                        metadata={
                            "type": "Element",
                            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                        }
                    )

                    @dataclass(slots=True, kw_only=True)
                    class Left:
                        value: int = field()
                        format: FormatType = field(
                            default=FormatType.LONG,
                            metadata={
                                "type": "Attribute",
                                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                            },
                        )
                        resolve: ResolveType = field(
                            default=ResolveType.IMMEDIATE,
                            metadata={
                                "type": "Attribute",
                                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                            },
                        )
                        id: None | str = field(
                            default=None,
                            metadata={
                                "type": "Attribute",
                                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                            },
                        )
                        dependency: None | str = field(
                            default=None,
                            metadata={
                                "type": "Attribute",
                                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
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
                                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                            },
                        )
                        order: None | float = field(
                            default=None,
                            metadata={
                                "type": "Attribute",
                                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                            },
                        )
                        config_groups: Sequence[str] = field(
                            default_factory=list,
                            metadata={
                                "name": "configGroups",
                                "type": "Attribute",
                                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                                "tokens": True,
                            },
                        )
                        bit_string_length: None | int = field(
                            default=None,
                            metadata={
                                "name": "bitStringLength",
                                "type": "Attribute",
                                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                            },
                        )
                        minimum: None | str = field(
                            default=None,
                            metadata={
                                "type": "Attribute",
                                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                            },
                        )
                        maximum: None | str = field(
                            default=None,
                            metadata={
                                "type": "Attribute",
                                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                            },
                        )
                        range_type: RangeTypeType = field(
                            default=RangeTypeType.FLOAT,
                            metadata={
                                "name": "rangeType",
                                "type": "Attribute",
                                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                            },
                        )
                        prompt: None | str = field(
                            default=None,
                            metadata={
                                "type": "Attribute",
                                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                            },
                        )

                    @dataclass(slots=True, kw_only=True)
                    class Right:
                        value: int = field()
                        format: FormatType = field(
                            default=FormatType.LONG,
                            metadata={
                                "type": "Attribute",
                                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                            },
                        )
                        resolve: ResolveType = field(
                            default=ResolveType.IMMEDIATE,
                            metadata={
                                "type": "Attribute",
                                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                            },
                        )
                        id: None | str = field(
                            default=None,
                            metadata={
                                "type": "Attribute",
                                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                            },
                        )
                        dependency: None | str = field(
                            default=None,
                            metadata={
                                "type": "Attribute",
                                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
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
                                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                            },
                        )
                        order: None | float = field(
                            default=None,
                            metadata={
                                "type": "Attribute",
                                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                            },
                        )
                        config_groups: Sequence[str] = field(
                            default_factory=list,
                            metadata={
                                "name": "configGroups",
                                "type": "Attribute",
                                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                                "tokens": True,
                            },
                        )
                        bit_string_length: None | int = field(
                            default=None,
                            metadata={
                                "name": "bitStringLength",
                                "type": "Attribute",
                                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                            },
                        )
                        minimum: None | str = field(
                            default=None,
                            metadata={
                                "type": "Attribute",
                                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                            },
                        )
                        maximum: None | str = field(
                            default=None,
                            metadata={
                                "type": "Attribute",
                                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                            },
                        )
                        range_type: RangeTypeType = field(
                            default=RangeTypeType.FLOAT,
                            metadata={
                                "name": "rangeType",
                                "type": "Attribute",
                                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                            },
                        )
                        prompt: None | str = field(
                            default=None,
                            metadata={
                                "type": "Attribute",
                                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
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
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                        "white_space": "collapse",
                        "pattern": r"\i[\p{L}\p{N}\.\-:_]*",
                    }
                )
                vector: None | Vector = field(
                    default=None,
                    metadata={
                        "type": "Element",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                    },
                )

    @dataclass(slots=True, kw_only=True)
    class BitSteering:
        value: BitSteeringType = field()
        format: FormatType = field(
            default=FormatType.STRING,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
            },
        )
        resolve: ResolveType = field(
            default=ResolveType.IMMEDIATE,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
            },
        )
        id: None | str = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
            },
        )
        dependency: None | str = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
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
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
            },
        )
        order: None | float = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
            },
        )
        config_groups: Sequence[str] = field(
            default_factory=list,
            metadata={
                "name": "configGroups",
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                "tokens": True,
            },
        )
        bit_string_length: None | int = field(
            default=None,
            metadata={
                "name": "bitStringLength",
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
            },
        )
        minimum: None | str = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
            },
        )
        maximum: None | str = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
            },
        )
        range_type: RangeTypeType = field(
            default=RangeTypeType.FLOAT,
            metadata={
                "name": "rangeType",
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
            },
        )
        prompt: None | str = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
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
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
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
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
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
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                    },
                )
                resolve: ResolveType = field(
                    default=ResolveType.IMMEDIATE,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                    },
                )
                id: None | str = field(
                    default=None,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                    },
                )
                dependency: None | str = field(
                    default=None,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
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
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                    },
                )
                order: None | float = field(
                    default=None,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                    },
                )
                config_groups: Sequence[str] = field(
                    default_factory=list,
                    metadata={
                        "name": "configGroups",
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                        "tokens": True,
                    },
                )
                bit_string_length: None | int = field(
                    default=None,
                    metadata={
                        "name": "bitStringLength",
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                    },
                )
                minimum: None | str = field(
                    default=None,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                    },
                )
                maximum: None | str = field(
                    default=None,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                    },
                )
                range_type: RangeTypeType = field(
                    default=RangeTypeType.FLOAT,
                    metadata={
                        "name": "rangeType",
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                    },
                )
                prompt: str = field(
                    default="Base Address:",
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
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
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
            },
        )
        bridge: Sequence[BusInterfaceType.Slave.Bridge] = field(
            default_factory=list,
            metadata={
                "type": "Element",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
            },
        )
        file_set_ref_group: Sequence[
            BusInterfaceType.Slave.FileSetRefGroup
        ] = field(
            default_factory=list,
            metadata={
                "name": "fileSetRefGroup",
                "type": "Element",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
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
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                }
            )
            opaque: bool = field(
                metadata={
                    "type": "Attribute",
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
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
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                },
            )
            file_set_ref: Sequence[FileSetRef] = field(
                default_factory=list,
                metadata={
                    "name": "fileSetRef",
                    "type": "Element",
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                },
            )

    @dataclass(slots=True, kw_only=True)
    class System:
        group: Group = field(
            metadata={
                "type": "Element",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
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
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
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
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                    "min_occurs": 1,
                },
            )
            range: BusInterfaceType.MirroredSlave.BaseAddresses.Range = field(
                metadata={
                    "type": "Element",
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
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
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                    },
                )
                resolve: ResolveType = field(
                    default=ResolveType.IMMEDIATE,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                    },
                )
                id: None | str = field(
                    default=None,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                    },
                )
                dependency: None | str = field(
                    default=None,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
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
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                    },
                )
                order: None | float = field(
                    default=None,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                    },
                )
                config_groups: Sequence[str] = field(
                    default_factory=list,
                    metadata={
                        "name": "configGroups",
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                        "tokens": True,
                    },
                )
                bit_string_length: None | int = field(
                    default=None,
                    metadata={
                        "name": "bitStringLength",
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                    },
                )
                minimum: None | str = field(
                    default=None,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                    },
                )
                maximum: None | str = field(
                    default=None,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                    },
                )
                range_type: RangeTypeType = field(
                    default=RangeTypeType.FLOAT,
                    metadata={
                        "name": "rangeType",
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                    },
                )
                prompt: str = field(
                    default="Base Address:",
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                    },
                )
                state: None | str = field(
                    default=None,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
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
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                    },
                )
                resolve: ResolveType = field(
                    default=ResolveType.IMMEDIATE,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                    },
                )
                id: None | str = field(
                    default=None,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                    },
                )
                dependency: None | str = field(
                    default=None,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
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
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                    },
                )
                order: None | float = field(
                    default=None,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                    },
                )
                config_groups: Sequence[str] = field(
                    default_factory=list,
                    metadata={
                        "name": "configGroups",
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                        "tokens": True,
                    },
                )
                bit_string_length: None | int = field(
                    default=None,
                    metadata={
                        "name": "bitStringLength",
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                    },
                )
                minimum: None | str = field(
                    default=None,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                    },
                )
                maximum: None | str = field(
                    default=None,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                    },
                )
                range_type: RangeTypeType = field(
                    default=RangeTypeType.FLOAT,
                    metadata={
                        "name": "rangeType",
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                    },
                )
                prompt: None | str = field(
                    default=None,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                    },
                )

    @dataclass(slots=True, kw_only=True)
    class MirroredSystem:
        group: Group = field(
            metadata={
                "type": "Element",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
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
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
            },
        )
        interface_mode: MonitorInterfaceMode = field(
            metadata={
                "name": "interfaceMode",
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
            }
        )

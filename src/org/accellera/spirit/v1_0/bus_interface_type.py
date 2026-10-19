from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import ForwardRef

from org.accellera.spirit.v1_0.addr_space_ref_type import AddrSpaceRefType
from org.accellera.spirit.v1_0.base_address import BaseAddress
from org.accellera.spirit.v1_0.bit_offset import BitOffset
from org.accellera.spirit.v1_0.bit_steering_type import BitSteeringType
from org.accellera.spirit.v1_0.bus_interface_type_connection import (
    BusInterfaceTypeConnection,
)
from org.accellera.spirit.v1_0.choice_style_value import ChoiceStyleValue
from org.accellera.spirit.v1_0.configurators import Configurators
from org.accellera.spirit.v1_0.direction_value import DirectionValue
from org.accellera.spirit.v1_0.file_set_ref import FileSetRef
from org.accellera.spirit.v1_0.format_type import FormatType
from org.accellera.spirit.v1_0.group import Group
from org.accellera.spirit.v1_0.library_ref_type import LibraryRefType
from org.accellera.spirit.v1_0.memory_map_ref import MemoryMapRef
from org.accellera.spirit.v1_0.range_type_type import RangeTypeType
from org.accellera.spirit.v1_0.resolve_type import ResolveType
from org.accellera.spirit.v1_0.vendor_extensions import VendorExtensions

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0"


@dataclass(slots=True, kw_only=True)
class BusInterfaceType:
    """
    :ivar name: Uniquely names this bus interface.
    :ivar bus_type: The bus type of this interface.  Refers to a bus
        description using vendor, library and name attributes.
    :ivar choice:
    :ivar connection: Directs how a bus interface is connected when the
        component is added to a design already containing a bus owner.
        Default behavior is "explicit".
    :ivar signal_map: Maps component signals to bus signals.
    :ivar index: Master or slave index of this bus interface's
        connection on a bus.  Only used on indexed buses.
    :ivar bit_steering: Indicates whether bit steering should be used to
        map this interface onto a bus of different data width. Values
        are "on", "off" or "default".
    :ivar configurators: Configuration generators for bus interfaces.
    :ivar vendor_extensions:
    :ivar other_attributes:
    """

    class Meta:
        name = "busInterfaceType"

    name: str = field(
        metadata={
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
        }
    )
    bus_type: LibraryRefType = field(
        metadata={
            "name": "busType",
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
        }
    )
    choice: (
        None
        | BusInterfaceType.Master
        | BusInterfaceType.Slave
        | BusInterfaceType.System
        | BusInterfaceType.MirroredSlave
        | object
        | BusInterfaceType.MirroredSystem
        | BusInterfaceType.ExportedInterface
    ) = field(
        default=None,
        metadata={
            "type": "Elements",
            "choices": (
                {
                    "name": "master",
                    "type": ForwardRef("BusInterfaceType.Master"),
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
                },
                {
                    "name": "slave",
                    "type": ForwardRef("BusInterfaceType.Slave"),
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
                },
                {
                    "name": "system",
                    "type": ForwardRef("BusInterfaceType.System"),
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
                },
                {
                    "name": "mirroredSlave",
                    "type": ForwardRef("BusInterfaceType.MirroredSlave"),
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
                },
                {
                    "name": "mirroredMaster",
                    "type": object,
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
                },
                {
                    "name": "mirroredSystem",
                    "type": ForwardRef("BusInterfaceType.MirroredSystem"),
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
                },
                {
                    "name": "exportedInterface",
                    "type": ForwardRef("BusInterfaceType.ExportedInterface"),
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
                },
            ),
        },
    )
    connection: None | BusInterfaceTypeConnection = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
        },
    )
    signal_map: None | BusInterfaceType.SignalMap = field(
        default=None,
        metadata={
            "name": "signalMap",
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
        },
    )
    index: None | BusInterfaceType.Index = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
        },
    )
    bit_steering: None | BusInterfaceType.BitSteering = field(
        default=None,
        metadata={
            "name": "bitSteering",
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
        },
    )
    configurators: None | Configurators = field(
        default=None,
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
    other_attributes: Mapping[str, str] = field(
        default_factory=dict,
        metadata={
            "type": "Attributes",
            "namespace": "##other",
        },
    )

    @dataclass(slots=True, kw_only=True)
    class SignalMap:
        """
        :ivar signal_name: Maps a component's signal to a signal in a
            bus description. The text content of this element identifies
            a signal on this component bu its signal name.  The
            busSignal attribute names the corresponding signal in the
            bus definition. The optional attributes left and right can
            be used to select a bit-slice of a signal vector to map to
            the bus interface.
        """

        signal_name: Sequence[BusInterfaceType.SignalMap.SignalName] = field(
            default_factory=list,
            metadata={
                "name": "signalName",
                "type": "Element",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
            },
        )

        @dataclass(slots=True, kw_only=True)
        class SignalName:
            value: str = field(default="")
            bus_signal: str = field(
                metadata={
                    "name": "busSignal",
                    "type": "Attribute",
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
                }
            )
            left: None | int = field(
                default=None,
                metadata={
                    "type": "Attribute",
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
                },
            )
            right: None | int = field(
                default=None,
                metadata={
                    "type": "Attribute",
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
                },
            )

    @dataclass(slots=True, kw_only=True)
    class Index:
        """
        :ivar value:
        :ivar format: This is a hint to the user interface about the
            data format to require for user resolved properties. The
            long.att attribute group sets the default format to "long".
        :ivar resolve:
        :ivar id:
        :ivar dependency:
        :ivar other_attributes:
        :ivar minimum: For user-resolved properties with numeric values,
            this indicates the minimum value allowed.
        :ivar maximum: For user-resolved properties with numeric values,
            this indicates the maximum value allowed.
        :ivar range_type:
        :ivar order: For components with auto-generated configuration
            forms, the user-resolved properties with order attibutes
            will be presented in ascending order.
        :ivar choice_ref: For user resolved properties with a "choice"
            format, this refers to a uiChoice element in the ui section
            of the component file.
        :ivar choice_style:
        :ivar direction:
        :ivar config_groups:
        :ivar prompt:
        """

        value: int = field()
        format: FormatType = field(
            default=FormatType.LONG,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
            },
        )
        resolve: None | ResolveType = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
            },
        )
        id: None | str = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
            },
        )
        dependency: None | str = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
            },
        )
        other_attributes: Mapping[str, str] = field(
            default_factory=dict,
            metadata={
                "type": "Attributes",
                "namespace": "##other",
            },
        )
        minimum: None | str = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
            },
        )
        maximum: None | str = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
            },
        )
        range_type: None | RangeTypeType = field(
            default=None,
            metadata={
                "name": "rangeType",
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
            },
        )
        order: None | float = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
            },
        )
        choice_ref: None | str = field(
            default=None,
            metadata={
                "name": "choiceRef",
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
            },
        )
        choice_style: None | ChoiceStyleValue = field(
            default=None,
            metadata={
                "name": "choiceStyle",
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
            },
        )
        direction: None | DirectionValue = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
            },
        )
        config_groups: Sequence[str] = field(
            default_factory=list,
            metadata={
                "name": "configGroups",
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
                "tokens": True,
            },
        )
        prompt: str = field(
            default="Connection Index:",
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
            },
        )

    @dataclass(slots=True, kw_only=True)
    class BitSteering:
        """
        :ivar value:
        :ivar resolve:
        :ivar id:
        :ivar dependency:
        :ivar other_attributes:
        :ivar minimum: For user-resolved properties with numeric values,
            this indicates the minimum value allowed.
        :ivar maximum: For user-resolved properties with numeric values,
            this indicates the maximum value allowed.
        :ivar range_type:
        :ivar order: For components with auto-generated configuration
            forms, the user-resolved properties with order attibutes
            will be presented in ascending order.
        :ivar choice_ref: For user resolved properties with a "choice"
            format, this refers to a uiChoice element in the ui section
            of the component file.
        :ivar choice_style:
        :ivar direction:
        :ivar config_groups:
        :ivar format:
        :ivar prompt:
        """

        value: BitSteeringType = field()
        resolve: None | ResolveType = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
            },
        )
        id: None | str = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
            },
        )
        dependency: None | str = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
            },
        )
        other_attributes: Mapping[str, str] = field(
            default_factory=dict,
            metadata={
                "type": "Attributes",
                "namespace": "##other",
            },
        )
        minimum: None | str = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
            },
        )
        maximum: None | str = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
            },
        )
        range_type: None | RangeTypeType = field(
            default=None,
            metadata={
                "name": "rangeType",
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
            },
        )
        order: None | float = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
            },
        )
        choice_ref: None | str = field(
            default=None,
            metadata={
                "name": "choiceRef",
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
            },
        )
        choice_style: None | ChoiceStyleValue = field(
            default=None,
            metadata={
                "name": "choiceStyle",
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
            },
        )
        direction: None | DirectionValue = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
            },
        )
        config_groups: Sequence[str] = field(
            default_factory=list,
            metadata={
                "name": "configGroups",
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
                "tokens": True,
            },
        )
        format: None | FormatType = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
            },
        )
        prompt: None | str = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
            },
        )

    @dataclass(slots=True, kw_only=True)
    class Master:
        """
        :ivar address_space_ref: If this master connects to an
            addressable bus, this element references the address space
            it maps to.  It has an addressSpaceRef attribute which is an
            addrSpaceID key ref.
        """

        address_space_ref: None | BusInterfaceType.Master.AddressSpaceRef = (
            field(
                default=None,
                metadata={
                    "name": "addressSpaceRef",
                    "type": "Element",
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
                },
            )
        )

        @dataclass(slots=True, kw_only=True)
        class AddressSpaceRef(AddrSpaceRefType):
            base_address: None | BaseAddress = field(
                default=None,
                metadata={
                    "name": "baseAddress",
                    "type": "Element",
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
                },
            )
            bit_offset: None | BitOffset = field(
                default=None,
                metadata={
                    "name": "bitOffset",
                    "type": "Element",
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
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
        :ivar file_set_ref_group:
        """

        memory_map_ref: None | MemoryMapRef = field(
            default=None,
            metadata={
                "name": "memoryMapRef",
                "type": "Element",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
            },
        )
        bridge: Sequence[BusInterfaceType.Slave.Bridge] = field(
            default_factory=list,
            metadata={
                "type": "Element",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
            },
        )
        file_set_ref_group: Sequence[
            BusInterfaceType.Slave.FileSetRefGroup
        ] = field(
            default_factory=list,
            metadata={
                "name": "fileSetRefGroup",
                "type": "Element",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
            },
        )

        @dataclass(slots=True, kw_only=True)
        class Bridge:
            """
            :ivar master_ref: The name of the master bus interface to
                which this interface bridges.
            :ivar opaque:
            """

            master_ref: str = field(
                metadata={
                    "name": "masterRef",
                    "type": "Attribute",
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
                }
            )
            opaque: None | bool = field(
                default=None,
                metadata={
                    "type": "Attribute",
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
                },
            )

        @dataclass(slots=True, kw_only=True)
        class FileSetRefGroup:
            group: None | str = field(
                default=None,
                metadata={
                    "type": "Element",
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
                },
            )
            file_set_ref: Sequence[FileSetRef] = field(
                default_factory=list,
                metadata={
                    "name": "fileSetRef",
                    "type": "Element",
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
                },
            )

    @dataclass(slots=True, kw_only=True)
    class System:
        group: Group = field(
            metadata={
                "type": "Element",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
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
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
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
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
                    "min_occurs": 1,
                },
            )
            range: BusInterfaceType.MirroredSlave.BaseAddresses.Range = field(
                metadata={
                    "type": "Element",
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
                }
            )

            @dataclass(slots=True, kw_only=True)
            class RemapAddress:
                """
                :ivar value:
                :ivar format: This is a hint to the user interface about
                    the data format to require for user resolved
                    properties. The long.att attribute group sets the
                    default format to "long".
                :ivar resolve:
                :ivar id:
                :ivar dependency:
                :ivar other_attributes:
                :ivar minimum: For user-resolved properties with numeric
                    values, this indicates the minimum value allowed.
                :ivar maximum: For user-resolved properties with numeric
                    values, this indicates the maximum value allowed.
                :ivar range_type:
                :ivar order: For components with auto-generated
                    configuration forms, the user-resolved properties
                    with order attibutes will be presented in ascending
                    order.
                :ivar choice_ref: For user resolved properties with a
                    "choice" format, this refers to a uiChoice element
                    in the ui section of the component file.
                :ivar choice_style:
                :ivar direction:
                :ivar config_groups:
                :ivar prompt:
                :ivar state:
                """

                value: str = field(
                    default="",
                    metadata={
                        "pattern": r"-?((0x)|(0X)|#)?[0-9a-fA-F]*[kmgtKMGT]?",
                    },
                )
                format: FormatType = field(
                    default=FormatType.LONG,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
                    },
                )
                resolve: None | ResolveType = field(
                    default=None,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
                    },
                )
                id: None | str = field(
                    default=None,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
                    },
                )
                dependency: None | str = field(
                    default=None,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
                    },
                )
                other_attributes: Mapping[str, str] = field(
                    default_factory=dict,
                    metadata={
                        "type": "Attributes",
                        "namespace": "##other",
                    },
                )
                minimum: None | str = field(
                    default=None,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
                    },
                )
                maximum: None | str = field(
                    default=None,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
                    },
                )
                range_type: None | RangeTypeType = field(
                    default=None,
                    metadata={
                        "name": "rangeType",
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
                    },
                )
                order: None | float = field(
                    default=None,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
                    },
                )
                choice_ref: None | str = field(
                    default=None,
                    metadata={
                        "name": "choiceRef",
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
                    },
                )
                choice_style: None | ChoiceStyleValue = field(
                    default=None,
                    metadata={
                        "name": "choiceStyle",
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
                    },
                )
                direction: None | DirectionValue = field(
                    default=None,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
                    },
                )
                config_groups: Sequence[str] = field(
                    default_factory=list,
                    metadata={
                        "name": "configGroups",
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
                        "tokens": True,
                    },
                )
                prompt: str = field(
                    default="Base Address:",
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
                    },
                )
                state: None | str = field(
                    default=None,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
                    },
                )

            @dataclass(slots=True, kw_only=True)
            class Range:
                """
                :ivar value:
                :ivar format: This is a hint to the user interface about
                    the data format to require for user resolved
                    properties. The long.att attribute group sets the
                    default format to "long".
                :ivar resolve:
                :ivar id:
                :ivar dependency:
                :ivar other_attributes:
                :ivar minimum: For user-resolved properties with numeric
                    values, this indicates the minimum value allowed.
                :ivar maximum: For user-resolved properties with numeric
                    values, this indicates the maximum value allowed.
                :ivar range_type:
                :ivar order: For components with auto-generated
                    configuration forms, the user-resolved properties
                    with order attibutes will be presented in ascending
                    order.
                :ivar choice_ref: For user resolved properties with a
                    "choice" format, this refers to a uiChoice element
                    in the ui section of the component file.
                :ivar choice_style:
                :ivar direction:
                :ivar config_groups:
                :ivar prompt:
                """

                value: str = field(
                    default="",
                    metadata={
                        "pattern": r"-?((0x)|(0X)|#)?[0-9a-fA-F]*[kmgtKMGT]?",
                    },
                )
                format: FormatType = field(
                    default=FormatType.LONG,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
                    },
                )
                resolve: None | ResolveType = field(
                    default=None,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
                    },
                )
                id: None | str = field(
                    default=None,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
                    },
                )
                dependency: None | str = field(
                    default=None,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
                    },
                )
                other_attributes: Mapping[str, str] = field(
                    default_factory=dict,
                    metadata={
                        "type": "Attributes",
                        "namespace": "##other",
                    },
                )
                minimum: None | str = field(
                    default=None,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
                    },
                )
                maximum: None | str = field(
                    default=None,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
                    },
                )
                range_type: None | RangeTypeType = field(
                    default=None,
                    metadata={
                        "name": "rangeType",
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
                    },
                )
                order: None | float = field(
                    default=None,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
                    },
                )
                choice_ref: None | str = field(
                    default=None,
                    metadata={
                        "name": "choiceRef",
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
                    },
                )
                choice_style: None | ChoiceStyleValue = field(
                    default=None,
                    metadata={
                        "name": "choiceStyle",
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
                    },
                )
                direction: None | DirectionValue = field(
                    default=None,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
                    },
                )
                config_groups: Sequence[str] = field(
                    default_factory=list,
                    metadata={
                        "name": "configGroups",
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
                        "tokens": True,
                    },
                )
                prompt: None | str = field(
                    default=None,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
                    },
                )

    @dataclass(slots=True, kw_only=True)
    class MirroredSystem:
        group: Group = field(
            metadata={
                "type": "Element",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
            }
        )

    @dataclass(slots=True, kw_only=True)
    class ExportedInterface:
        """
        :ivar component_ref: Indicates name of the sub-component
            containing the interface being exported.
        :ivar interface_ref: Indicates the name of the sub-component bus
            interface being exported.
        """

        component_ref: str = field(
            metadata={
                "name": "componentRef",
                "type": "Element",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
            }
        )
        interface_ref: str = field(
            metadata={
                "name": "interfaceRef",
                "type": "Element",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0",
            }
        )

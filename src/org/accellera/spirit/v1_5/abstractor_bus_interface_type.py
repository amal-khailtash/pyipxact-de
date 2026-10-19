from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

from org.accellera.spirit.v1_5.description import Description
from org.accellera.spirit.v1_5.display_name import DisplayName
from org.accellera.spirit.v1_5.format_type import FormatType
from org.accellera.spirit.v1_5.library_ref_type import LibraryRefType
from org.accellera.spirit.v1_5.parameters import Parameters
from org.accellera.spirit.v1_5.range_type_type import RangeTypeType
from org.accellera.spirit.v1_5.resolve_type import ResolveType
from org.accellera.spirit.v1_5.vector import Vector
from org.accellera.spirit.v1_5.vendor_extensions import VendorExtensions

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5"


@dataclass(slots=True, kw_only=True)
class AbstractorBusInterfaceType:
    """
    Type definition for a busInterface in a component.

    :ivar name: Unique name
    :ivar display_name:
    :ivar description:
    :ivar abstraction_type: The abstraction type/level of this
        interface. Refers to abstraction definition using vendor,
        library, name, version attributes. Bus definition can be found
        through a reference in this file.
    :ivar port_maps: Listing of maps between logical ports and physical
        ports.
    :ivar parameters:
    :ivar vendor_extensions:
    :ivar any_attributes:
    """

    class Meta:
        name = "abstractorBusInterfaceType"

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
    abstraction_type: LibraryRefType = field(
        metadata={
            "name": "abstractionType",
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
        }
    )
    port_maps: None | AbstractorBusInterfaceType.PortMaps = field(
        default=None,
        metadata={
            "name": "portMaps",
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

        port_map: Sequence[AbstractorBusInterfaceType.PortMaps.PortMap] = (
            field(
                default_factory=list,
                metadata={
                    "name": "portMap",
                    "type": "Element",
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                    "min_occurs": 1,
                },
            )
        )

        @dataclass(slots=True, kw_only=True)
        class PortMap:
            """
            :ivar logical_port: Logical port from abstraction definition
            :ivar physical_port: Physical port from this component
            """

            logical_port: AbstractorBusInterfaceType.PortMaps.PortMap.LogicalPort = field(
                metadata={
                    "name": "logicalPort",
                    "type": "Element",
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                }
            )
            physical_port: AbstractorBusInterfaceType.PortMaps.PortMap.PhysicalPort = field(
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
                    None
                    | AbstractorBusInterfaceType.PortMaps.PortMap.LogicalPort.Vector
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

                    left: AbstractorBusInterfaceType.PortMaps.PortMap.LogicalPort.Vector.Left = field(
                        metadata={
                            "type": "Element",
                            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
                        }
                    )
                    right: AbstractorBusInterfaceType.PortMaps.PortMap.LogicalPort.Vector.Right = field(
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

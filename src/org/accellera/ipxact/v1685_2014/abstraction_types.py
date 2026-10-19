from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import ForwardRef

from org.accellera.ipxact.v1685_2014.configurable_library_ref_type import (
    ConfigurableLibraryRefType,
)
from org.accellera.ipxact.v1685_2014.is_present import IsPresent
from org.accellera.ipxact.v1685_2014.part_select import PartSelect
from org.accellera.ipxact.v1685_2014.range import Range
from org.accellera.ipxact.v1685_2014.unsigned_positive_int_expression import (
    UnsignedPositiveIntExpression,
)
from org.accellera.ipxact.v1685_2014.view_ref import ViewRef

__NAMESPACE__ = "http://www.accellera.org/XMLSchema/IPXACT/1685-2014"


@dataclass(slots=True, kw_only=True)
class AbstractionTypes:
    """
    :ivar abstraction_type: The abstraction type/level of this
        interface. Refers to abstraction definition using vendor,
        library, name, version attributes along with any configurable
        element values needed to configure this abstraction. Bus
        definition can be found through a reference in this file.
    """

    class Meta:
        name = "abstractionTypes"
        namespace = "http://www.accellera.org/XMLSchema/IPXACT/1685-2014"

    abstraction_type: Sequence[AbstractionTypes.AbstractionType] = field(
        default_factory=list,
        metadata={
            "name": "abstractionType",
            "type": "Element",
            "min_occurs": 1,
        },
    )

    @dataclass(slots=True, kw_only=True)
    class AbstractionType:
        """
        :ivar view_ref: A reference to a view name in the file for which
            this type applies.
        :ivar abstraction_ref: Provides the VLNV of the abstraction
            type.
        :ivar port_maps: Listing of maps between component ports and bus
            ports.
        :ivar id:
        """

        view_ref: Sequence[ViewRef] = field(
            default_factory=list,
            metadata={
                "name": "viewRef",
                "type": "Element",
            },
        )
        abstraction_ref: ConfigurableLibraryRefType = field(
            metadata={
                "name": "abstractionRef",
                "type": "Element",
            }
        )
        port_maps: None | AbstractionTypes.AbstractionType.PortMaps = field(
            default=None,
            metadata={
                "name": "portMaps",
                "type": "Element",
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
        class PortMaps:
            """
            :ivar port_map: Maps a component's port to a port in a bus
                description. This is the logical to physical mapping.
                The logical pin comes from the bus interface and the
                physical pin from the component.
            """

            port_map: Sequence[
                AbstractionTypes.AbstractionType.PortMaps.PortMap
            ] = field(
                default_factory=list,
                metadata={
                    "name": "portMap",
                    "type": "Element",
                    "min_occurs": 1,
                },
            )

            @dataclass(slots=True, kw_only=True)
            class PortMap:
                """
                :ivar is_present:
                :ivar logical_port: Logical port from abstraction
                    definition
                :ivar physical_port_or_logical_tie_off:
                :ivar is_informative: When true, indicates that this
                    portMap element is for information purpose only.
                :ivar id:
                :ivar invert: Indicates that the connection between the
                    logical and physical ports should include an
                    inversion.
                """

                is_present: None | IsPresent = field(
                    default=None,
                    metadata={
                        "name": "isPresent",
                        "type": "Element",
                    },
                )
                logical_port: AbstractionTypes.AbstractionType.PortMaps.PortMap.LogicalPort = field(
                    metadata={
                        "name": "logicalPort",
                        "type": "Element",
                    }
                )
                physical_port_or_logical_tie_off: (
                    None
                    | AbstractionTypes.AbstractionType.PortMaps.PortMap.PhysicalPort
                    | UnsignedPositiveIntExpression
                ) = field(
                    default=None,
                    metadata={
                        "type": "Elements",
                        "choices": (
                            {
                                "name": "physicalPort",
                                "type": ForwardRef(
                                    "AbstractionTypes.AbstractionType.PortMaps.PortMap.PhysicalPort"
                                ),
                            },
                            {
                                "name": "logicalTieOff",
                                "type": UnsignedPositiveIntExpression,
                            },
                        ),
                    },
                )
                is_informative: None | bool = field(
                    default=None,
                    metadata={
                        "name": "isInformative",
                        "type": "Element",
                    },
                )
                id: None | str = field(
                    default=None,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.w3.org/XML/1998/namespace",
                    },
                )
                invert: object = field(
                    default="false",
                    metadata={
                        "type": "Attribute",
                    },
                )

                @dataclass(slots=True, kw_only=True)
                class LogicalPort:
                    """
                    :ivar name: Bus port name as specified inside the
                        abstraction definition
                    :ivar range:
                    """

                    name: str = field(
                        metadata={
                            "type": "Element",
                        }
                    )
                    range: None | Range = field(
                        default=None,
                        metadata={
                            "type": "Element",
                        },
                    )

                @dataclass(slots=True, kw_only=True)
                class PhysicalPort:
                    """
                    :ivar name: Component port name as specified inside
                        the model port section
                    :ivar part_select:
                    """

                    name: str = field(
                        metadata={
                            "type": "Element",
                            "white_space": "collapse",
                            "pattern": r"\i[\p{L}\p{N}\.\-:_]*",
                        }
                    )
                    part_select: None | PartSelect = field(
                        default=None,
                        metadata={
                            "name": "partSelect",
                            "type": "Element",
                        },
                    )

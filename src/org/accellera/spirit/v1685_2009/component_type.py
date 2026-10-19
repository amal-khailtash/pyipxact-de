from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from org.accellera.spirit.v1685_2009.address_space_ref import AddressSpaceRef
from org.accellera.spirit.v1685_2009.address_spaces import AddressSpaces
from org.accellera.spirit.v1685_2009.bus_interfaces import BusInterfaces
from org.accellera.spirit.v1685_2009.channels import Channels
from org.accellera.spirit.v1685_2009.choices import Choices
from org.accellera.spirit.v1685_2009.component_generators import (
    ComponentGenerators,
)
from org.accellera.spirit.v1685_2009.description import Description
from org.accellera.spirit.v1685_2009.display_name import DisplayName
from org.accellera.spirit.v1685_2009.file_sets import FileSets
from org.accellera.spirit.v1685_2009.memory_maps import MemoryMaps
from org.accellera.spirit.v1685_2009.model import Model
from org.accellera.spirit.v1685_2009.other_clocks import OtherClocks
from org.accellera.spirit.v1685_2009.parameters import Parameters
from org.accellera.spirit.v1685_2009.remap_states import RemapStates
from org.accellera.spirit.v1685_2009.vendor_extensions import VendorExtensions
from org.accellera.spirit.v1685_2009.whitebox_element_type import (
    WhiteboxElementType,
)

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009"


@dataclass(slots=True, kw_only=True)
class ComponentType:
    """
    Component-specific extension to componentType.

    :ivar vendor: Name of the vendor who supplies this file.
    :ivar library: Name of the logical library this element belongs to.
    :ivar name: The name of the object.
    :ivar version: Indicates the version of the named element.
    :ivar bus_interfaces:
    :ivar channels:
    :ivar remap_states:
    :ivar address_spaces:
    :ivar memory_maps:
    :ivar model:
    :ivar component_generators: Generator list is tools-specific.
    :ivar choices:
    :ivar file_sets:
    :ivar whitebox_elements: A list of whiteboxElements
    :ivar cpus: cpu's in the component
    :ivar other_clock_drivers: Defines a set of clock drivers that are
        not directly associated with an input port of the component.
    :ivar description:
    :ivar parameters:
    :ivar vendor_extensions:
    """

    class Meta:
        name = "componentType"

    vendor: str = field(
        metadata={
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
        }
    )
    library: str = field(
        metadata={
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
        }
    )
    name: str = field(
        metadata={
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
        }
    )
    version: str = field(
        metadata={
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
        }
    )
    bus_interfaces: None | BusInterfaces = field(
        default=None,
        metadata={
            "name": "busInterfaces",
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
        },
    )
    channels: None | Channels = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
        },
    )
    remap_states: None | RemapStates = field(
        default=None,
        metadata={
            "name": "remapStates",
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
        },
    )
    address_spaces: None | AddressSpaces = field(
        default=None,
        metadata={
            "name": "addressSpaces",
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
        },
    )
    memory_maps: None | MemoryMaps = field(
        default=None,
        metadata={
            "name": "memoryMaps",
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
        },
    )
    model: None | Model = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
        },
    )
    component_generators: None | ComponentGenerators = field(
        default=None,
        metadata={
            "name": "componentGenerators",
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
        },
    )
    choices: None | Choices = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
        },
    )
    file_sets: None | FileSets = field(
        default=None,
        metadata={
            "name": "fileSets",
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
        },
    )
    whitebox_elements: None | ComponentType.WhiteboxElements = field(
        default=None,
        metadata={
            "name": "whiteboxElements",
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
        },
    )
    cpus: None | ComponentType.Cpus = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
        },
    )
    other_clock_drivers: None | OtherClocks = field(
        default=None,
        metadata={
            "name": "otherClockDrivers",
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

    @dataclass(slots=True, kw_only=True)
    class WhiteboxElements:
        """
        :ivar whitebox_element: A whiteboxElement is a useful way to
            identify elements of a component that can not be identified
            through other means such as internal signals and non-
            software accessible registers.
        """

        whitebox_element: Sequence[WhiteboxElementType] = field(
            default_factory=list,
            metadata={
                "name": "whiteboxElement",
                "type": "Element",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
                "min_occurs": 1,
            },
        )

    @dataclass(slots=True, kw_only=True)
    class Cpus:
        """
        :ivar cpu: Describes a processor in this component.
        """

        cpu: Sequence[ComponentType.Cpus.Cpu] = field(
            default_factory=list,
            metadata={
                "type": "Element",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
                "min_occurs": 1,
            },
        )

        @dataclass(slots=True, kw_only=True)
        class Cpu:
            """
            :ivar name: Unique name
            :ivar display_name:
            :ivar description:
            :ivar address_space_ref: Indicates which address space maps
                into this cpu.
            :ivar parameters: Data specific to the cpu.
            :ivar vendor_extensions:
            """

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
            address_space_ref: Sequence[AddressSpaceRef] = field(
                default_factory=list,
                metadata={
                    "name": "addressSpaceRef",
                    "type": "Element",
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
                    "min_occurs": 1,
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

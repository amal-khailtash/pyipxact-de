from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from org.accellera.spirit.v1685_2009.ve.power.abstractor_bus_interface_type import (
    AbstractorBusInterfaceType,
)
from org.accellera.spirit.v1685_2009.ve.power.abstractor_generators import (
    AbstractorGenerators,
)
from org.accellera.spirit.v1685_2009.ve.power.abstractor_mode_type import (
    AbstractorModeType,
)
from org.accellera.spirit.v1685_2009.ve.power.abstractor_model_type import (
    AbstractorModelType,
)
from org.accellera.spirit.v1685_2009.ve.power.choices import Choices
from org.accellera.spirit.v1685_2009.ve.power.description import Description
from org.accellera.spirit.v1685_2009.ve.power.file_sets import FileSets
from org.accellera.spirit.v1685_2009.ve.power.library_ref_type import (
    LibraryRefType,
)
from org.accellera.spirit.v1685_2009.ve.power.parameters import Parameters
from org.accellera.spirit.v1685_2009.ve.power.vendor_extensions import (
    VendorExtensions,
)

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009"


@dataclass(slots=True, kw_only=True)
class AbstractorType:
    """
    Abstractor-specific extension to abstractorType.

    :ivar vendor: Name of the vendor who supplies this file.
    :ivar library: Name of the logical library this element belongs to.
    :ivar name: The name of the object.
    :ivar version: Indicates the version of the named element.
    :ivar abstractor_mode: Define the mode for the interfaces on this
        abstractor. For master the first interface connects to the
        master, the second connects to the mirroredMaster For slave the
        first interface connects to the mirroredSlave the second
        connects to the slave For direct the first interface connects to
        the master, the second connects to the slave For system the
        first interface connects to the system, the second connects to
        the mirroredSystem. For system the group attribute is required
    :ivar bus_type: The bus type of both interfaces. Refers to bus
        definition using vendor, library, name, version attributes.
    :ivar abstractor_interfaces: The interfaces supported by this
        abstractor
    :ivar model: Model information.
    :ivar abstractor_generators: Generator list is tools-specific.
    :ivar choices:
    :ivar file_sets:
    :ivar description:
    :ivar parameters:
    :ivar vendor_extensions:
    """

    class Meta:
        name = "abstractorType"

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
    abstractor_mode: AbstractorType.AbstractorMode = field(
        metadata={
            "name": "abstractorMode",
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
        }
    )
    bus_type: LibraryRefType = field(
        metadata={
            "name": "busType",
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
        }
    )
    abstractor_interfaces: AbstractorType.AbstractorInterfaces = field(
        metadata={
            "name": "abstractorInterfaces",
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
        }
    )
    model: None | AbstractorModelType = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
        },
    )
    abstractor_generators: None | AbstractorGenerators = field(
        default=None,
        metadata={
            "name": "abstractorGenerators",
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
    class AbstractorMode:
        """
        :ivar value:
        :ivar group: Define the system group if the mode is set to
            system
        """

        value: AbstractorModeType = field()
        group: None | str = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
            },
        )

    @dataclass(slots=True, kw_only=True)
    class AbstractorInterfaces:
        """
        :ivar abstractor_interface: An abstractor must have exactly 2
            Interfaces.
        """

        abstractor_interface: Sequence[AbstractorBusInterfaceType] = field(
            default_factory=list,
            metadata={
                "name": "abstractorInterface",
                "type": "Element",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
                "min_occurs": 2,
                "max_occurs": 2,
            },
        )

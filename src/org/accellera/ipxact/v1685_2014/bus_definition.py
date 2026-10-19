from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from org.accellera.ipxact.v1685_2014.assertions import Assertions
from org.accellera.ipxact.v1685_2014.description import Description
from org.accellera.ipxact.v1685_2014.library_ref_type import LibraryRefType
from org.accellera.ipxact.v1685_2014.parameters import Parameters
from org.accellera.ipxact.v1685_2014.unsigned_int_expression import (
    UnsignedIntExpression,
)
from org.accellera.ipxact.v1685_2014.vendor_extensions import VendorExtensions

__NAMESPACE__ = "http://www.accellera.org/XMLSchema/IPXACT/1685-2014"


@dataclass(slots=True, kw_only=True)
class BusDefinition:
    """
    Defines the structural information associated with a bus type,
    independent of the abstraction level.

    :ivar vendor: Name of the vendor who supplies this file.
    :ivar library: Name of the logical library this element belongs to.
    :ivar name: The name of the object.
    :ivar version: Indicates the version of the named element.
    :ivar direct_connection: This element indicates that a master
        interface may be directly connected to a slave interface (under
        certain conditions) for busses of this type.
    :ivar broadcast: This element indicates that this bus definition
        supports 'broadcast' mode. This means that it is legal to make
        one-to-many interface connections.
    :ivar is_addressable: If true, indicates that this is an addressable
        bus.
    :ivar extends: Optional name of bus type that this bus definition is
        compatible with. This bus definition may change the definitions
        in the existing bus definition
    :ivar max_masters: Indicates the maximum number of masters this bus
        supports.  If this element is not present, the number of masters
        allowed is unbounded.
    :ivar max_slaves: Indicates the maximum number of slaves this bus
        supports.  If the element is not present, the number of slaves
        allowed is unbounded.
    :ivar system_group_names: Indicates the list of system group names
        that are defined for this bus definition.
    :ivar description:
    :ivar parameters:
    :ivar assertions:
    :ivar vendor_extensions:
    :ivar id:
    """

    class Meta:
        name = "busDefinition"
        namespace = "http://www.accellera.org/XMLSchema/IPXACT/1685-2014"

    vendor: str = field(
        metadata={
            "type": "Element",
        }
    )
    library: str = field(
        metadata={
            "type": "Element",
        }
    )
    name: str = field(
        metadata={
            "type": "Element",
        }
    )
    version: str = field(
        metadata={
            "type": "Element",
        }
    )
    direct_connection: bool = field(
        metadata={
            "name": "directConnection",
            "type": "Element",
        }
    )
    broadcast: None | bool = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    is_addressable: bool = field(
        metadata={
            "name": "isAddressable",
            "type": "Element",
        }
    )
    extends: None | LibraryRefType = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    max_masters: None | UnsignedIntExpression = field(
        default=None,
        metadata={
            "name": "maxMasters",
            "type": "Element",
        },
    )
    max_slaves: None | UnsignedIntExpression = field(
        default=None,
        metadata={
            "name": "maxSlaves",
            "type": "Element",
        },
    )
    system_group_names: None | BusDefinition.SystemGroupNames = field(
        default=None,
        metadata={
            "name": "systemGroupNames",
            "type": "Element",
        },
    )
    description: None | Description = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    parameters: None | Parameters = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    assertions: None | Assertions = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    vendor_extensions: None | VendorExtensions = field(
        default=None,
        metadata={
            "name": "vendorExtensions",
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
    class SystemGroupNames:
        """
        :ivar system_group_name: Indicates the name of a system group
            defined for this bus definition.
        """

        system_group_name: Sequence[
            BusDefinition.SystemGroupNames.SystemGroupName
        ] = field(
            default_factory=list,
            metadata={
                "name": "systemGroupName",
                "type": "Element",
                "min_occurs": 1,
            },
        )

        @dataclass(slots=True, kw_only=True)
        class SystemGroupName:
            value: str = field(default="")
            id: None | str = field(
                default=None,
                metadata={
                    "type": "Attribute",
                    "namespace": "http://www.w3.org/XML/1998/namespace",
                },
            )

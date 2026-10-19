from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import ForwardRef

from org.accellera.ipxact.v1685_2022.abstractor_port_wire_type import (
    AbstractorPortWireType,
)
from org.accellera.ipxact.v1685_2022.arrays import Arrays
from org.accellera.ipxact.v1685_2022.component_port_direction_type import (
    ComponentPortDirectionType,
)
from org.accellera.ipxact.v1685_2022.description import Description
from org.accellera.ipxact.v1685_2022.display_name import DisplayName
from org.accellera.ipxact.v1685_2022.extended_vectors_type import (
    ExtendedVectorsType,
)
from org.accellera.ipxact.v1685_2022.port_access_type_1 import PortAccessType1
from org.accellera.ipxact.v1685_2022.short_description import ShortDescription
from org.accellera.ipxact.v1685_2022.struct_port_type_defs import (
    StructPortTypeDefs,
)
from org.accellera.ipxact.v1685_2022.vendor_extensions import VendorExtensions

__NAMESPACE__ = "http://www.accellera.org/XMLSchema/IPXACT/1685-2022"


@dataclass(slots=True, kw_only=True)
class AbstractorSubPortType:
    """
    A port description, giving a name and an access type for high level
    ports.

    :ivar name: Unique name
    :ivar display_name:
    :ivar short_description:
    :ivar description:
    :ivar wire_or_structured:
    :ivar arrays:
    :ivar access: Port access characteristics.
    :ivar vendor_extensions:
    :ivar id:
    :ivar is_io: When present and set to 'true' identifies this port as
        being an I/O to the containing structure port type.  Only valid
        for subPorts contained in a structured port with
        structType='interface'.
    """

    class Meta:
        name = "abstractorSubPortType"

    name: str = field(
        metadata={
            "type": "Element",
            "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
            "white_space": "collapse",
            "pattern": r"\i[\p{L}\p{N}\.\-:_]*",
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
    wire_or_structured: (
        None | AbstractorPortWireType | AbstractorPortStructuredType
    ) = field(
        default=None,
        metadata={
            "type": "Elements",
            "choices": (
                {
                    "name": "wire",
                    "type": AbstractorPortWireType,
                    "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
                },
                {
                    "name": "structured",
                    "type": ForwardRef("AbstractorPortStructuredType"),
                    "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
                },
            ),
        },
    )
    arrays: None | Arrays = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
        },
    )
    access: None | PortAccessType1 = field(
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
    is_io: None | bool = field(
        default=None,
        metadata={
            "name": "isIO",
            "type": "Attribute",
        },
    )


@dataclass(slots=True, kw_only=True)
class AbstractorPortStructuredType:
    """
    :ivar struct_or_union_or_interface:
    :ivar vectors: Vectored information.
    :ivar sub_ports:
    :ivar struct_port_type_defs:
    :ivar packed: When not present or set to 'true' indicates that this
        structured port is 'packed'.  If present and set to 'false',
        indicates that this structured port is 'unpacked'.
    """

    class Meta:
        name = "abstractorPortStructuredType"

    struct_or_union_or_interface: (
        None
        | AbstractorPortStructuredType.Struct
        | AbstractorPortStructuredType.UnionType
        | AbstractorPortStructuredType.Interface
    ) = field(
        default=None,
        metadata={
            "type": "Elements",
            "choices": (
                {
                    "name": "struct",
                    "type": ForwardRef("AbstractorPortStructuredType.Struct"),
                    "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
                },
                {
                    "name": "union",
                    "type": ForwardRef(
                        "AbstractorPortStructuredType.UnionType"
                    ),
                    "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
                },
                {
                    "name": "interface",
                    "type": ForwardRef(
                        "AbstractorPortStructuredType.Interface"
                    ),
                    "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
                },
            ),
        },
    )
    vectors: None | ExtendedVectorsType = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
        },
    )
    sub_ports: AbstractorPortStructuredType.SubPorts = field(
        metadata={
            "name": "subPorts",
            "type": "Element",
            "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
        }
    )
    struct_port_type_defs: StructPortTypeDefs = field(
        metadata={
            "name": "structPortTypeDefs",
            "type": "Element",
            "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
        }
    )
    packed: bool = field(
        default=True,
        metadata={
            "type": "Attribute",
        },
    )

    @dataclass(slots=True, kw_only=True)
    class SubPorts:
        sub_port: Sequence[AbstractorSubPortType] = field(
            default_factory=list,
            metadata={
                "name": "subPort",
                "type": "Element",
                "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
                "min_occurs": 1,
            },
        )

    @dataclass(slots=True, kw_only=True)
    class Struct:
        """
        :ivar direction: The direction of a wire style port. The basic
            directions for a port are 'in' for input ports, 'out' for
            output port and 'inout' for bidirectional and tristate
            ports. A value of 'phantom' is also allowed and define a
            port that exist on the IP-XACT component but not on the HDL
            model.
        """

        direction: None | ComponentPortDirectionType = field(
            default=None,
            metadata={
                "type": "Attribute",
            },
        )

    @dataclass(slots=True, kw_only=True)
    class UnionType:
        """
        :ivar direction: The direction of a wire style port. The basic
            directions for a port are 'in' for input ports, 'out' for
            output port and 'inout' for bidirectional and tristate
            ports. A value of 'phantom' is also allowed and define a
            port that exist on the IP-XACT component but not on the HDL
            model.
        """

        direction: None | ComponentPortDirectionType = field(
            default=None,
            metadata={
                "type": "Attribute",
            },
        )

    @dataclass(slots=True, kw_only=True)
    class Interface:
        phantom: None | bool = field(
            default=None,
            metadata={
                "type": "Attribute",
            },
        )

from __future__ import annotations

from dataclasses import dataclass, field

from org.accellera.ipxact.v1685_2014.api_type import ApiType
from org.accellera.ipxact.v1685_2014.description import Description
from org.accellera.ipxact.v1685_2014.display_name import DisplayName
from org.accellera.ipxact.v1685_2014.ipxact_uri import IpxactUri
from org.accellera.ipxact.v1685_2014.parameters import Parameters
from org.accellera.ipxact.v1685_2014.phase import Phase
from org.accellera.ipxact.v1685_2014.transport_method_type import (
    TransportMethodType,
)
from org.accellera.ipxact.v1685_2014.vendor_extensions import VendorExtensions

__NAMESPACE__ = "http://www.accellera.org/XMLSchema/IPXACT/1685-2014"


@dataclass(slots=True, kw_only=True)
class GeneratorType:
    """
    Types of generators.

    :ivar name: Unique name
    :ivar display_name:
    :ivar description:
    :ivar phase:
    :ivar parameters:
    :ivar api_type: Indicates the type of API used by the generator.
        Valid value are TGI_2009, TGI_2014_BASE, TGI_2014_EXTENDED, and
        none. If this element is not present, TGI_2014_BASE is assumed.
        The type TGI_2009 indicates a generator using the 1685-2009
        version of the TGI API. This is not part of the 1685-2014
        version of the standard and may not be supported by Design
        Environments.
    :ivar transport_methods:
    :ivar generator_exe: The pathname to the executable file that
        implements the generator
    :ivar vendor_extensions:
    :ivar hidden: If this attribute is true then the generator should
        not be presented to the user, it may be part of a chain and has
        no useful meaning when invoked standalone.
    :ivar id:
    """

    class Meta:
        name = "generatorType"

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
    phase: None | Phase = field(
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
    api_type: None | GeneratorType.ApiType = field(
        default=None,
        metadata={
            "name": "apiType",
            "type": "Element",
            "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2014",
        },
    )
    transport_methods: None | GeneratorType.TransportMethods = field(
        default=None,
        metadata={
            "name": "transportMethods",
            "type": "Element",
            "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2014",
        },
    )
    generator_exe: IpxactUri = field(
        metadata={
            "name": "generatorExe",
            "type": "Element",
            "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2014",
        }
    )
    vendor_extensions: None | VendorExtensions = field(
        default=None,
        metadata={
            "name": "vendorExtensions",
            "type": "Element",
            "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2014",
        },
    )
    hidden: bool = field(
        default=False,
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
    class ApiType:
        value: ApiType = field()
        id: None | str = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.w3.org/XML/1998/namespace",
            },
        )

    @dataclass(slots=True, kw_only=True)
    class TransportMethods:
        """
        :ivar transport_method: Defines a SOAP transport protocol other
            than HTTP which is supported by this generator. The only
            other currently supported protocol is 'file'.
        :ivar id:
        """

        transport_method: GeneratorType.TransportMethods.TransportMethod = field(
            metadata={
                "name": "transportMethod",
                "type": "Element",
                "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2014",
            }
        )
        id: None | str = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.w3.org/XML/1998/namespace",
            },
        )

        @dataclass(slots=True, kw_only=True)
        class TransportMethod:
            value: TransportMethodType = field()
            id: None | str = field(
                default=None,
                metadata={
                    "type": "Attribute",
                    "namespace": "http://www.w3.org/XML/1998/namespace",
                },
            )

from __future__ import annotations

from dataclasses import dataclass, field

from org.accellera.spirit.v1685_2009.ve.core.description import Description
from org.accellera.spirit.v1685_2009.ve.core.display_name import DisplayName
from org.accellera.spirit.v1685_2009.ve.core.generator_type_api_type import (
    GeneratorTypeApiType,
)
from org.accellera.spirit.v1685_2009.ve.core.parameters import Parameters
from org.accellera.spirit.v1685_2009.ve.core.phase import Phase
from org.accellera.spirit.v1685_2009.ve.core.transport_methods_transport_method import (
    TransportMethodsTransportMethod,
)
from org.accellera.spirit.v1685_2009.ve.core.vendor_extensions import (
    VendorExtensions,
)

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009"


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
        Valid value are TGI, and none. If this element is not present,
        TGI is assumed.
    :ivar transport_methods:
    :ivar generator_exe: The pathname to the executable file that
        implements the generator
    :ivar vendor_extensions:
    :ivar hidden: If this attribute is true then the generator should
        not be presented to the user, it may be part of a chain and has
        no useful meaning when invoked standalone.
    """

    class Meta:
        name = "generatorType"

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
    phase: None | Phase = field(
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
    api_type: None | GeneratorTypeApiType = field(
        default=None,
        metadata={
            "name": "apiType",
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
        },
    )
    transport_methods: None | GeneratorType.TransportMethods = field(
        default=None,
        metadata={
            "name": "transportMethods",
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
        },
    )
    generator_exe: str = field(
        metadata={
            "name": "generatorExe",
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
        }
    )
    vendor_extensions: None | VendorExtensions = field(
        default=None,
        metadata={
            "name": "vendorExtensions",
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
        },
    )
    hidden: bool = field(
        default=False,
        metadata={
            "type": "Attribute",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
        },
    )

    @dataclass(slots=True, kw_only=True)
    class TransportMethods:
        """
        :ivar transport_method: Defines a SOAP transport protocol other
            than HTTP which is supported by this generator. The only
            other currently supported protocol is 'file'.
        """

        transport_method: TransportMethodsTransportMethod = field(
            metadata={
                "name": "transportMethod",
                "type": "Element",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
            }
        )

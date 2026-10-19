from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from org.accellera.spirit.v1_2.generator_type_api_type import (
    GeneratorTypeApiType,
)
from org.accellera.spirit.v1_2.parameter import Parameter
from org.accellera.spirit.v1_2.phase import Phase
from org.accellera.spirit.v1_2.transport_methods_transport_method import (
    TransportMethodsTransportMethod,
)
from org.accellera.spirit.v1_2.vendor_extensions import VendorExtensions

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2"


@dataclass(slots=True, kw_only=True)
class GeneratorType:
    """
    Types of generators.

    :ivar name: The name of this generator.
    :ivar phase:
    :ivar parameter:
    :ivar api_type: Indicates the type of API used by the generator.
        Valid value are TGI, LGI, and none. If this element is not
        present, LGI is assumed.
    :ivar transport_methods:
    :ivar lgi_access_type: Identifies the special requirements that this
        loose generator may place up on the DE. Not valid for tight
        generators.
    :ivar generator_exe: The pathname to the executable file that
        implements the generator
    :ivar vendor_extensions:
    """

    class Meta:
        name = "generatorType"

    name: str = field(
        metadata={
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2",
        }
    )
    phase: None | Phase = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2",
        },
    )
    parameter: Sequence[Parameter] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2",
        },
    )
    api_type: None | GeneratorTypeApiType = field(
        default=None,
        metadata={
            "name": "apiType",
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2",
        },
    )
    transport_methods: None | GeneratorType.TransportMethods = field(
        default=None,
        metadata={
            "name": "transportMethods",
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2",
        },
    )
    lgi_access_type: None | GeneratorType.LgiAccessType = field(
        default=None,
        metadata={
            "name": "lgiAccessType",
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2",
        },
    )
    generator_exe: str = field(
        metadata={
            "name": "generatorExe",
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2",
        }
    )
    vendor_extensions: None | VendorExtensions = field(
        default=None,
        metadata={
            "name": "vendorExtensions",
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2",
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
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2",
            }
        )

    @dataclass(slots=True, kw_only=True)
    class LgiAccessType:
        """
        :ivar read_only: If true then this generator will not make
            changes to the  design.
        :ivar hierarchical: If true then this generator is capable of
            running in a hierarchical manner and so the DE must ensure
            that all lower levels of hierarchy are also made available
        :ivar instance_required: If true then the generator operates on
            designated instances, not the whole design. The DE must
            capture the instances to be operated on.
        :ivar subset_only: If present then this generator only needs a
            subset of the design information.
        """

        read_only: bool = field(
            default=False,
            metadata={
                "name": "readOnly",
                "type": "Element",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2",
            },
        )
        hierarchical: bool = field(
            default=True,
            metadata={
                "type": "Element",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2",
            },
        )
        instance_required: bool = field(
            default=False,
            metadata={
                "name": "instanceRequired",
                "type": "Element",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2",
            },
        )
        subset_only: None | GeneratorType.LgiAccessType.SubsetOnly = field(
            default=None,
            metadata={
                "name": "subsetOnly",
                "type": "Element",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2",
            },
        )

        @dataclass(slots=True, kw_only=True)
        class SubsetOnly:
            """
            :ivar design_file: If true then the generator only needs to
                look at design information.
            :ivar component_defs: If true then the generator only needs
                to look at component related information.
            :ivar bus_defs: If true then the generator only needs to
                look at bus definition information.
            """

            design_file: bool = field(
                default=True,
                metadata={
                    "name": "designFile",
                    "type": "Element",
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2",
                },
            )
            component_defs: bool = field(
                default=True,
                metadata={
                    "name": "componentDefs",
                    "type": "Element",
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2",
                },
            )
            bus_defs: bool = field(
                default=True,
                metadata={
                    "name": "busDefs",
                    "type": "Element",
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2",
                },
            )

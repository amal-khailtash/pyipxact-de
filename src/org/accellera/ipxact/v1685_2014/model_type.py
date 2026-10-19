from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from org.accellera.ipxact.v1685_2014.component_instantiation_type import (
    ComponentInstantiationType,
)
from org.accellera.ipxact.v1685_2014.description import Description
from org.accellera.ipxact.v1685_2014.design_configuration_instantiation_type import (
    DesignConfigurationInstantiationType,
)
from org.accellera.ipxact.v1685_2014.design_instantiation_type import (
    DesignInstantiationType,
)
from org.accellera.ipxact.v1685_2014.display_name import DisplayName
from org.accellera.ipxact.v1685_2014.is_present import IsPresent
from org.accellera.ipxact.v1685_2014.port import Port

__NAMESPACE__ = "http://www.accellera.org/XMLSchema/IPXACT/1685-2014"


@dataclass(slots=True, kw_only=True)
class ModelType:
    """
    Model information.

    :ivar views: Views container
    :ivar instantiations: Instantiations container
    :ivar ports: Port container
    """

    class Meta:
        name = "modelType"

    views: None | ModelType.Views = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2014",
        },
    )
    instantiations: None | ModelType.Instantiations = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2014",
        },
    )
    ports: None | ModelType.Ports = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2014",
        },
    )

    @dataclass(slots=True, kw_only=True)
    class Views:
        """
        :ivar view: Single view of a component
        """

        view: Sequence[ModelType.Views.View] = field(
            default_factory=list,
            metadata={
                "type": "Element",
                "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2014",
                "min_occurs": 1,
            },
        )

        @dataclass(slots=True, kw_only=True)
        class View:
            """
            :ivar name: Unique name
            :ivar display_name:
            :ivar description:
            :ivar is_present:
            :ivar env_identifier: Defines the hardware environment in
                which this view applies. The format of the string is
                language:tool:vendor_extension, with each piece being
                optional. The language must be one of the types from
                ipxact:fileType. The tool values are defined by the
                Accellera Systems Initiative, and include generic values
                "*Simulation" and "*Synthesis" to imply any tool of the
                indicated type. Having more than one envIdentifier
                indicates that the view applies to multiple
                environments.
            :ivar component_instantiation_ref:
            :ivar design_instantiation_ref:
            :ivar design_configuration_instantiation_ref:
            """

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
            is_present: None | IsPresent = field(
                default=None,
                metadata={
                    "name": "isPresent",
                    "type": "Element",
                    "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2014",
                },
            )
            env_identifier: Sequence[ModelType.Views.View.EnvIdentifier] = (
                field(
                    default_factory=list,
                    metadata={
                        "name": "envIdentifier",
                        "type": "Element",
                        "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2014",
                    },
                )
            )
            component_instantiation_ref: None | str = field(
                default=None,
                metadata={
                    "name": "componentInstantiationRef",
                    "type": "Element",
                    "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2014",
                },
            )
            design_instantiation_ref: None | str = field(
                default=None,
                metadata={
                    "name": "designInstantiationRef",
                    "type": "Element",
                    "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2014",
                },
            )
            design_configuration_instantiation_ref: None | str = field(
                default=None,
                metadata={
                    "name": "designConfigurationInstantiationRef",
                    "type": "Element",
                    "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2014",
                },
            )

            @dataclass(slots=True, kw_only=True)
            class EnvIdentifier:
                value: str = field(
                    default="",
                    metadata={
                        "pattern": r"[a-zA-Z0-9_+\*\.]*:[a-zA-Z0-9_+\*\.]*:[a-zA-Z0-9_+\*\.]*",
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
    class Instantiations:
        component_instantiation_or_design_instantiation_or_design_configuration_instantiation: Sequence[
            ComponentInstantiationType
            | DesignInstantiationType
            | DesignConfigurationInstantiationType
        ] = field(
            default_factory=list,
            metadata={
                "type": "Elements",
                "choices": (
                    {
                        "name": "componentInstantiation",
                        "type": ComponentInstantiationType,
                        "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2014",
                    },
                    {
                        "name": "designInstantiation",
                        "type": DesignInstantiationType,
                        "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2014",
                    },
                    {
                        "name": "designConfigurationInstantiation",
                        "type": DesignConfigurationInstantiationType,
                        "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2014",
                    },
                ),
            },
        )

    @dataclass(slots=True, kw_only=True)
    class Ports:
        port: Sequence[Port] = field(
            default_factory=list,
            metadata={
                "type": "Element",
                "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2014",
                "min_occurs": 1,
            },
        )

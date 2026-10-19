from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from org.accellera.spirit.v1685_2009.ve.core.configurable_element_values import (
    ConfigurableElementValues,
)
from org.accellera.spirit.v1685_2009.ve.core.description import Description
from org.accellera.spirit.v1685_2009.ve.core.display_name import DisplayName
from org.accellera.spirit.v1685_2009.ve.core.instance_name import InstanceName
from org.accellera.spirit.v1685_2009.ve.core.library_ref_type import (
    LibraryRefType,
)
from org.accellera.spirit.v1685_2009.ve.core.vendor_extensions import (
    VendorExtensions,
)

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009"


@dataclass(slots=True, kw_only=True)
class DesignConfiguration:
    """
    Top level element for describing the current configuration of a design.

    Does not describe instance parameterization.

    :ivar vendor: Name of the vendor who supplies this file.
    :ivar library: Name of the logical library this element belongs to.
    :ivar name: The name of the object.
    :ivar version: Indicates the version of the named element.
    :ivar design_ref: The design to which this configuration applies
    :ivar generator_chain_configuration: Contains the configurable
        information associated with a generatorChain and its generators.
        Note that configurable information for generators associated
        with components is stored in the design file.
    :ivar interconnection_configuration: Contains the information about
        the abstractors required to cross between two interfaces at with
        different abstractionDefs.
    :ivar view_configuration: Contains the active view for each instance
        in the design
    :ivar description:
    :ivar vendor_extensions:
    """

    class Meta:
        name = "designConfiguration"
        namespace = (
            "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009"
        )

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
    design_ref: LibraryRefType = field(
        metadata={
            "name": "designRef",
            "type": "Element",
        }
    )
    generator_chain_configuration: Sequence[
        DesignConfiguration.GeneratorChainConfiguration
    ] = field(
        default_factory=list,
        metadata={
            "name": "generatorChainConfiguration",
            "type": "Element",
        },
    )
    interconnection_configuration: Sequence[
        DesignConfiguration.InterconnectionConfiguration
    ] = field(
        default_factory=list,
        metadata={
            "name": "interconnectionConfiguration",
            "type": "Element",
        },
    )
    view_configuration: Sequence[DesignConfiguration.ViewConfiguration] = (
        field(
            default_factory=list,
            metadata={
                "name": "viewConfiguration",
                "type": "Element",
            },
        )
    )
    description: None | Description = field(
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

    @dataclass(slots=True, kw_only=True)
    class GeneratorChainConfiguration:
        """
        :ivar generator_chain_ref: References a generatorChain.
        :ivar configurable_element_values:
        """

        generator_chain_ref: LibraryRefType = field(
            metadata={
                "name": "generatorChainRef",
                "type": "Element",
            }
        )
        configurable_element_values: None | ConfigurableElementValues = field(
            default=None,
            metadata={
                "name": "configurableElementValues",
                "type": "Element",
            },
        )

    @dataclass(slots=True, kw_only=True)
    class InterconnectionConfiguration:
        """
        :ivar interconnection_ref: Reference to the interconnection
            name, monitor interconnection name or possibly a
            hierConnection interfaceName in a design file.
        :ivar abstractors: List of abstractors for this interconnection
        """

        interconnection_ref: str = field(
            metadata={
                "name": "interconnectionRef",
                "type": "Element",
            }
        )
        abstractors: DesignConfiguration.InterconnectionConfiguration.Abstractors = field(
            metadata={
                "type": "Element",
            }
        )

        @dataclass(slots=True, kw_only=True)
        class Abstractors:
            """
            :ivar abstractor: Element to hold a the abstractor
                reference, the configuration and viewName. If multiple
                elements are present then the order is the order in
                which the abstractors should be chained together.
            """

            abstractor: Sequence[
                DesignConfiguration.InterconnectionConfiguration.Abstractors.Abstractor
            ] = field(
                default_factory=list,
                metadata={
                    "type": "Element",
                    "min_occurs": 1,
                },
            )

            @dataclass(slots=True, kw_only=True)
            class Abstractor:
                """
                :ivar instance_name: Instance name for the abstractor
                :ivar display_name:
                :ivar description:
                :ivar abstractor_ref: Abstractor reference
                :ivar configurable_element_values:
                :ivar view_name: The name of the active view for this
                    abstractor instance.
                """

                instance_name: str = field(
                    metadata={
                        "name": "instanceName",
                        "type": "Element",
                    }
                )
                display_name: None | DisplayName = field(
                    default=None,
                    metadata={
                        "name": "displayName",
                        "type": "Element",
                    },
                )
                description: None | Description = field(
                    default=None,
                    metadata={
                        "type": "Element",
                    },
                )
                abstractor_ref: LibraryRefType = field(
                    metadata={
                        "name": "abstractorRef",
                        "type": "Element",
                    }
                )
                configurable_element_values: (
                    None | ConfigurableElementValues
                ) = field(
                    default=None,
                    metadata={
                        "name": "configurableElementValues",
                        "type": "Element",
                    },
                )
                view_name: str = field(
                    metadata={
                        "name": "viewName",
                        "type": "Element",
                    }
                )

    @dataclass(slots=True, kw_only=True)
    class ViewConfiguration:
        """
        :ivar instance_name:
        :ivar view_name: The name of the active view for this instance
        """

        instance_name: InstanceName = field(
            metadata={
                "name": "instanceName",
                "type": "Element",
            }
        )
        view_name: str = field(
            metadata={
                "name": "viewName",
                "type": "Element",
            }
        )

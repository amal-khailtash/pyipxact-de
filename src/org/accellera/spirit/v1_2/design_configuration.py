from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from org.accellera.spirit.v1_2.configurable_element import ConfigurableElement
from org.accellera.spirit.v1_2.instance_name import InstanceName
from org.accellera.spirit.v1_2.library_ref_type import LibraryRefType
from org.accellera.spirit.v1_2.vendor_extensions import VendorExtensions

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2"


@dataclass(slots=True, kw_only=True)
class DesignConfiguration:
    """
    Top level element for describing the current configuration of a design.

    Does not describe instance parameterization.

    :ivar vendor: Name of the vendor who supplies this file.
    :ivar library: Name of the logical library this element belongs to.
    :ivar name: The name of the object.
    :ivar version:
    :ivar design_ref: The design to which this configuration applies
    :ivar pmd_configuration: Contains the configurable information
        associated with a particular PMD
    :ivar generator_chain_configuration: Contains the configurable
        information associated with a generatorChain and its generators.
        Note that configurable information for generators associated
        with components is stored in the design file.
    :ivar view_configuration: Contains the active view for each instance
        in the design
    :ivar vendor_extensions:
    """

    class Meta:
        name = "designConfiguration"
        namespace = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2"

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
    pmd_configuration: Sequence[DesignConfiguration.PmdConfiguration] = field(
        default_factory=list,
        metadata={
            "name": "pmdConfiguration",
            "type": "Element",
        },
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
    view_configuration: Sequence[DesignConfiguration.ViewConfiguration] = (
        field(
            default_factory=list,
            metadata={
                "name": "viewConfiguration",
                "type": "Element",
            },
        )
    )
    vendor_extensions: None | VendorExtensions = field(
        default=None,
        metadata={
            "name": "vendorExtensions",
            "type": "Element",
        },
    )

    @dataclass(slots=True, kw_only=True)
    class PmdConfiguration:
        """
        :ivar pmd_ref: References a PMD.
        :ivar configurable_element:
        """

        pmd_ref: LibraryRefType = field(
            metadata={
                "name": "pmdRef",
                "type": "Element",
            }
        )
        configurable_element: Sequence[ConfigurableElement] = field(
            default_factory=list,
            metadata={
                "name": "configurableElement",
                "type": "Element",
                "min_occurs": 1,
            },
        )

    @dataclass(slots=True, kw_only=True)
    class GeneratorChainConfiguration:
        """
        :ivar generator_chain_ref: References a generatorChain.
        :ivar configurable_element:
        :ivar generators: Stores configurable information for generators
            referenced in the chain
        """

        generator_chain_ref: LibraryRefType = field(
            metadata={
                "name": "generatorChainRef",
                "type": "Element",
            }
        )
        configurable_element: Sequence[ConfigurableElement] = field(
            default_factory=list,
            metadata={
                "name": "configurableElement",
                "type": "Element",
            },
        )
        generators: Sequence[
            DesignConfiguration.GeneratorChainConfiguration.Generators
        ] = field(
            default_factory=list,
            metadata={
                "type": "Element",
            },
        )

        @dataclass(slots=True, kw_only=True)
        class Generators:
            """
            :ivar generator_name: This identifies the generator in the
                chain.
            :ivar configurable_element:
            """

            generator_name: str = field(
                metadata={
                    "name": "generatorName",
                    "type": "Element",
                }
            )
            configurable_element: Sequence[ConfigurableElement] = field(
                default_factory=list,
                metadata={
                    "name": "configurableElement",
                    "type": "Element",
                    "min_occurs": 1,
                },
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

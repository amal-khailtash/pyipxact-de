from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

from org.accellera.spirit.v1_2.add_rem_change import AddRemChange
from org.accellera.spirit.v1_2.add_rem_rep_change import AddRemRepChange
from org.accellera.spirit.v1_2.choice_style_value import ChoiceStyleValue
from org.accellera.spirit.v1_2.configurable_element import ConfigurableElement
from org.accellera.spirit.v1_2.configuration import Configuration
from org.accellera.spirit.v1_2.direction_value import DirectionValue
from org.accellera.spirit.v1_2.format_type import FormatType
from org.accellera.spirit.v1_2.instance_name import InstanceName
from org.accellera.spirit.v1_2.interconnection import Interconnection
from org.accellera.spirit.v1_2.library_ref_type import LibraryRefType
from org.accellera.spirit.v1_2.monitor_interconnection import (
    MonitorInterconnection,
)
from org.accellera.spirit.v1_2.range_type_type import RangeTypeType
from org.accellera.spirit.v1_2.resolve_type import ResolveType
from org.accellera.spirit.v1_2.vendor_extensions import VendorExtensions

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2"


@dataclass(slots=True, kw_only=True)
class GeneratorChangeList:
    """
    Defines the changes to be made to the design as directed by an external
    generator.

    :ivar component_changes: List of changes affecting components in the
        design.
    :ivar interconnection_changes: List of changes affecting
        interconnections in the design.
    :ivar ad_hoc_connection_changes: List of changes affecting ad-hoc
        connections in the design.
    :ivar design_configuration_changes: List of changes affecting the
        configuration of the design.
    :ivar vendor_extension_changes: List of changes affecting vendor
        defined extensions in the design.
    """

    class Meta:
        name = "generatorChangeList"
        namespace = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2"

    component_changes: None | GeneratorChangeList.ComponentChanges = field(
        default=None,
        metadata={
            "name": "componentChanges",
            "type": "Element",
        },
    )
    interconnection_changes: (
        None | GeneratorChangeList.InterconnectionChanges
    ) = field(
        default=None,
        metadata={
            "name": "interconnectionChanges",
            "type": "Element",
        },
    )
    ad_hoc_connection_changes: (
        None | GeneratorChangeList.AdHocConnectionChanges
    ) = field(
        default=None,
        metadata={
            "name": "adHocConnectionChanges",
            "type": "Element",
        },
    )
    design_configuration_changes: (
        None | GeneratorChangeList.DesignConfigurationChanges
    ) = field(
        default=None,
        metadata={
            "name": "designConfigurationChanges",
            "type": "Element",
        },
    )
    vendor_extension_changes: (
        None | GeneratorChangeList.VendorExtensionChanges
    ) = field(
        default=None,
        metadata={
            "name": "vendorExtensionChanges",
            "type": "Element",
        },
    )

    @dataclass(slots=True, kw_only=True)
    class ComponentChanges:
        component_change: Sequence[
            GeneratorChangeList.ComponentChanges.ComponentChange
        ] = field(
            default_factory=list,
            metadata={
                "name": "componentChange",
                "type": "Element",
            },
        )

        @dataclass(slots=True, kw_only=True)
        class ComponentChange:
            """
            :ivar add_rem_rep_change:
            :ivar instance_name:
            :ivar component_file_name: This is the file containing the
                component definition. Required only if the alteration is
                an addition or a replacement. Should be an absolute
                filename so that the DE may copy it.
            :ivar sub_components: Required only for hierarchical
                components. Holds the hierarchical component's sub-
                component definition files.
            :ivar configuration:
            """

            add_rem_rep_change: AddRemRepChange = field(
                metadata={
                    "name": "addRemRepChange",
                    "type": "Element",
                }
            )
            instance_name: InstanceName = field(
                metadata={
                    "name": "instanceName",
                    "type": "Element",
                }
            )
            component_file_name: None | str = field(
                default=None,
                metadata={
                    "name": "componentFileName",
                    "type": "Element",
                },
            )
            sub_components: (
                None
                | GeneratorChangeList.ComponentChanges.ComponentChange.SubComponents
            ) = field(
                default=None,
                metadata={
                    "name": "subComponents",
                    "type": "Element",
                },
            )
            configuration: None | Configuration = field(
                default=None,
                metadata={
                    "type": "Element",
                },
            )

            @dataclass(slots=True, kw_only=True)
            class SubComponents:
                """
                :ivar sub_component_file_name: Path to definitions of
                    components and channels instanced in hierarchical
                    component definition.
                """

                sub_component_file_name: Sequence[str] = field(
                    default_factory=list,
                    metadata={
                        "name": "subComponentFileName",
                        "type": "Element",
                        "min_occurs": 1,
                    },
                )

    @dataclass(slots=True, kw_only=True)
    class InterconnectionChanges:
        interconnection_change: Sequence[
            GeneratorChangeList.InterconnectionChanges.InterconnectionChange
        ] = field(
            default_factory=list,
            metadata={
                "name": "interconnectionChange",
                "type": "Element",
            },
        )

        @dataclass(slots=True, kw_only=True)
        class InterconnectionChange:
            add_rem_change: AddRemChange = field(
                metadata={
                    "name": "addRemChange",
                    "type": "Element",
                }
            )
            interconnection_or_monitor_interconnection: (
                None | Interconnection | MonitorInterconnection
            ) = field(
                default=None,
                metadata={
                    "type": "Elements",
                    "choices": (
                        {
                            "name": "interconnection",
                            "type": Interconnection,
                        },
                        {
                            "name": "monitorInterconnection",
                            "type": MonitorInterconnection,
                        },
                    ),
                },
            )

    @dataclass(slots=True, kw_only=True)
    class AdHocConnectionChanges:
        ad_hoc_connection_change: Sequence[
            GeneratorChangeList.AdHocConnectionChanges.AdHocConnectionChange
        ] = field(
            default_factory=list,
            metadata={
                "name": "adHocConnectionChange",
                "type": "Element",
            },
        )

        @dataclass(slots=True, kw_only=True)
        class AdHocConnectionChange:
            """
            :ivar add_rem_change:
            :ivar name: This is the name of the ad-hoc connection to
                modify
            :ivar export: Specifies whether this ad-hoc connection will
                be exported out of the design.
            :ivar pin_reference: Indicates the signal on the component
                which is being connected by this ad-hoc connection
            """

            add_rem_change: AddRemChange = field(
                metadata={
                    "name": "addRemChange",
                    "type": "Element",
                }
            )
            name: str = field(
                metadata={
                    "type": "Element",
                }
            )
            export: (
                None
                | GeneratorChangeList.AdHocConnectionChanges.AdHocConnectionChange.Export
            ) = field(
                default=None,
                metadata={
                    "type": "Element",
                },
            )
            pin_reference: Sequence[
                GeneratorChangeList.AdHocConnectionChanges.AdHocConnectionChange.PinReference
            ] = field(
                default_factory=list,
                metadata={
                    "name": "pinReference",
                    "type": "Element",
                },
            )

            @dataclass(slots=True, kw_only=True)
            class Export:
                """
                :ivar value:
                :ivar format: This is a hint to the user interface about
                    the data format to require for user resolved
                    properties. The bool.att attribute group sets the
                    default format to "bool".
                :ivar resolve:
                :ivar id:
                :ivar dependency:
                :ivar any_attributes:
                :ivar minimum: For user-resolved properties with numeric
                    values, this indicates the minimum value allowed.
                :ivar maximum: For user-resolved properties with numeric
                    values, this indicates the maximum value allowed.
                :ivar range_type:
                :ivar order: For components with auto-generated
                    configuration forms, the user-resolved properties
                    with order attibutes will be presented in ascending
                    order.
                :ivar choice_ref: For user resolved properties with a
                    "choice" format, this refers to a uiChoice element
                    in the ui section of the component file.
                :ivar choice_style:
                :ivar direction:
                :ivar config_groups:
                :ivar prompt:
                """

                value: bool = field()
                format: FormatType = field(
                    default=FormatType.BOOL,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2",
                    },
                )
                resolve: ResolveType = field(
                    default=ResolveType.IMMEDIATE,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2",
                    },
                )
                id: None | str = field(
                    default=None,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2",
                    },
                )
                dependency: None | str = field(
                    default=None,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2",
                    },
                )
                any_attributes: Mapping[str, str] = field(
                    default_factory=dict,
                    metadata={
                        "type": "Attributes",
                        "namespace": "##any",
                    },
                )
                minimum: None | str = field(
                    default=None,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2",
                    },
                )
                maximum: None | str = field(
                    default=None,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2",
                    },
                )
                range_type: RangeTypeType = field(
                    default=RangeTypeType.FLOAT,
                    metadata={
                        "name": "rangeType",
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2",
                    },
                )
                order: None | float = field(
                    default=None,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2",
                    },
                )
                choice_ref: None | str = field(
                    default=None,
                    metadata={
                        "name": "choiceRef",
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2",
                    },
                )
                choice_style: None | ChoiceStyleValue = field(
                    default=None,
                    metadata={
                        "name": "choiceStyle",
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2",
                    },
                )
                direction: None | DirectionValue = field(
                    default=None,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2",
                    },
                )
                config_groups: Sequence[str] = field(
                    default_factory=list,
                    metadata={
                        "name": "configGroups",
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2",
                        "tokens": True,
                    },
                )
                prompt: None | str = field(
                    default=None,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2",
                    },
                )

            @dataclass(slots=True, kw_only=True)
            class PinReference:
                """
                :ivar component_ref: This is the instance name of the
                    component
                :ivar signal_ref: The name of the signal on the
                    component
                :ivar left: If present, this is the left index of the
                    signal
                :ivar right: If present, this is the right index of the
                    signal
                """

                component_ref: str = field(
                    metadata={
                        "name": "componentRef",
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2",
                    }
                )
                signal_ref: str = field(
                    metadata={
                        "name": "signalRef",
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2",
                    }
                )
                left: int = field(
                    default=0,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2",
                    },
                )
                right: int = field(
                    default=0,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2",
                    },
                )

    @dataclass(slots=True, kw_only=True)
    class DesignConfigurationChanges:
        """
        :ivar pmd_configuration_change: Contains the configurable
            information associated with a particular PMD
        :ivar generator_chain_configuration_change: Contains the
            configurable information associated with a generatorChain
            and its generators. Note that configurable information for
            generators associated with components is stored in the
            design file.
        :ivar view_configuration_change: Contains the active view for
            each instance in the design
        :ivar vendor_extension_changes: List of changes affecting vendor
            defined extensions in the design.
        """

        pmd_configuration_change: Sequence[
            GeneratorChangeList.DesignConfigurationChanges.PmdConfigurationChange
        ] = field(
            default_factory=list,
            metadata={
                "name": "pmdConfigurationChange",
                "type": "Element",
            },
        )
        generator_chain_configuration_change: Sequence[
            GeneratorChangeList.DesignConfigurationChanges.GeneratorChainConfigurationChange
        ] = field(
            default_factory=list,
            metadata={
                "name": "generatorChainConfigurationChange",
                "type": "Element",
            },
        )
        view_configuration_change: Sequence[
            GeneratorChangeList.DesignConfigurationChanges.ViewConfigurationChange
        ] = field(
            default_factory=list,
            metadata={
                "name": "viewConfigurationChange",
                "type": "Element",
            },
        )
        vendor_extension_changes: (
            None
            | GeneratorChangeList.DesignConfigurationChanges.VendorExtensionChanges
        ) = field(
            default=None,
            metadata={
                "name": "vendorExtensionChanges",
                "type": "Element",
            },
        )

        @dataclass(slots=True, kw_only=True)
        class PmdConfigurationChange:
            """
            :ivar add_rem_rep_change:
            :ivar pmd_ref: References a PMD.
            :ivar configurable_element:
            """

            add_rem_rep_change: AddRemRepChange = field(
                metadata={
                    "name": "addRemRepChange",
                    "type": "Element",
                }
            )
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
        class GeneratorChainConfigurationChange:
            """
            :ivar generator_chain_ref: References a generatorChain.
            :ivar generator_chain_change:
            :ivar generator_change: Stores configurable information for
                generators referenced in the chain
            """

            generator_chain_ref: LibraryRefType = field(
                metadata={
                    "name": "generatorChainRef",
                    "type": "Element",
                }
            )
            generator_chain_change: Sequence[
                GeneratorChangeList.DesignConfigurationChanges.GeneratorChainConfigurationChange.GeneratorChainChange
            ] = field(
                default_factory=list,
                metadata={
                    "name": "generatorChainChange",
                    "type": "Element",
                },
            )
            generator_change: Sequence[
                GeneratorChangeList.DesignConfigurationChanges.GeneratorChainConfigurationChange.GeneratorChange
            ] = field(
                default_factory=list,
                metadata={
                    "name": "generatorChange",
                    "type": "Element",
                },
            )

            @dataclass(slots=True, kw_only=True)
            class GeneratorChainChange:
                add_rem_rep_change: AddRemRepChange = field(
                    metadata={
                        "name": "addRemRepChange",
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
            class GeneratorChange:
                """
                :ivar add_rem_rep_change:
                :ivar generator_name: This identifies the generator in
                    the chain.
                :ivar configurable_element:
                """

                add_rem_rep_change: AddRemRepChange = field(
                    metadata={
                        "name": "addRemRepChange",
                        "type": "Element",
                    }
                )
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
        class ViewConfigurationChange:
            """
            :ivar add_rem_rep_change:
            :ivar instance_name:
            :ivar view_name: The name of the active view for this
                instance
            """

            add_rem_rep_change: AddRemRepChange = field(
                metadata={
                    "name": "addRemRepChange",
                    "type": "Element",
                }
            )
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

        @dataclass(slots=True, kw_only=True)
        class VendorExtensionChanges:
            vendor_extension_change: Sequence[
                GeneratorChangeList.DesignConfigurationChanges.VendorExtensionChanges.VendorExtensionChange
            ] = field(
                default_factory=list,
                metadata={
                    "name": "vendorExtensionChange",
                    "type": "Element",
                    "min_occurs": 1,
                },
            )

            @dataclass(slots=True, kw_only=True)
            class VendorExtensionChange:
                add_rem_change: AddRemChange = field(
                    metadata={
                        "name": "addRemChange",
                        "type": "Element",
                    }
                )
                vendor_extensions: VendorExtensions = field(
                    metadata={
                        "name": "vendorExtensions",
                        "type": "Element",
                    }
                )

    @dataclass(slots=True, kw_only=True)
    class VendorExtensionChanges:
        vendor_extension_change: Sequence[
            GeneratorChangeList.VendorExtensionChanges.VendorExtensionChange
        ] = field(
            default_factory=list,
            metadata={
                "name": "vendorExtensionChange",
                "type": "Element",
            },
        )

        @dataclass(slots=True, kw_only=True)
        class VendorExtensionChange:
            add_rem_change: AddRemChange = field(
                metadata={
                    "name": "addRemChange",
                    "type": "Element",
                }
            )
            vendor_extensions: VendorExtensions = field(
                metadata={
                    "name": "vendorExtensions",
                    "type": "Element",
                }
            )

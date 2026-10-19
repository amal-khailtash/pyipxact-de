from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

from org.accellera.spirit.v1_1.add_rem_change import AddRemChange
from org.accellera.spirit.v1_1.add_rem_rep_change import AddRemRepChange
from org.accellera.spirit.v1_1.choice_style_value import ChoiceStyleValue
from org.accellera.spirit.v1_1.configuration import Configuration
from org.accellera.spirit.v1_1.direction_value import DirectionValue
from org.accellera.spirit.v1_1.format_type import FormatType
from org.accellera.spirit.v1_1.instance_name import InstanceName
from org.accellera.spirit.v1_1.interconnection import Interconnection
from org.accellera.spirit.v1_1.range_type_type import RangeTypeType
from org.accellera.spirit.v1_1.resolve_type import ResolveType
from org.accellera.spirit.v1_1.vendor_extensions import VendorExtensions

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.1"


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
    :ivar vendor_extension_changes: List of changes affecting vendor
        defined extensions in the design.
    """

    class Meta:
        name = "generatorChangeList"
        namespace = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.1"

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
            interconnection: Interconnection = field(
                metadata={
                    "type": "Element",
                }
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
                :ivar other_attributes:
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
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.1",
                    },
                )
                resolve: None | ResolveType = field(
                    default=None,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.1",
                    },
                )
                id: None | str = field(
                    default=None,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.1",
                    },
                )
                dependency: None | str = field(
                    default=None,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.1",
                    },
                )
                other_attributes: Mapping[str, str] = field(
                    default_factory=dict,
                    metadata={
                        "type": "Attributes",
                        "namespace": "##other",
                    },
                )
                minimum: None | str = field(
                    default=None,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.1",
                    },
                )
                maximum: None | str = field(
                    default=None,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.1",
                    },
                )
                range_type: None | RangeTypeType = field(
                    default=None,
                    metadata={
                        "name": "rangeType",
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.1",
                    },
                )
                order: None | float = field(
                    default=None,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.1",
                    },
                )
                choice_ref: None | str = field(
                    default=None,
                    metadata={
                        "name": "choiceRef",
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.1",
                    },
                )
                choice_style: None | ChoiceStyleValue = field(
                    default=None,
                    metadata={
                        "name": "choiceStyle",
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.1",
                    },
                )
                direction: None | DirectionValue = field(
                    default=None,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.1",
                    },
                )
                config_groups: Sequence[str] = field(
                    default_factory=list,
                    metadata={
                        "name": "configGroups",
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.1",
                        "tokens": True,
                    },
                )
                prompt: None | str = field(
                    default=None,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.1",
                    },
                )

            @dataclass(slots=True, kw_only=True)
            class PinReference:
                component_ref: str = field(
                    metadata={
                        "name": "componentRef",
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.1",
                    }
                )
                signal_ref: str = field(
                    metadata={
                        "name": "signalRef",
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.1",
                    }
                )
                left: None | int = field(
                    default=None,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.1",
                    },
                )
                right: None | int = field(
                    default=None,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.1",
                    },
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

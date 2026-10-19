from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

from org.accellera.spirit.v1_2.choice_style_value import ChoiceStyleValue
from org.accellera.spirit.v1_2.data_type_type import DataTypeType
from org.accellera.spirit.v1_2.dependency import Dependency
from org.accellera.spirit.v1_2.direction_value import DirectionValue
from org.accellera.spirit.v1_2.file import File
from org.accellera.spirit.v1_2.file_builder_type import FileBuilderType
from org.accellera.spirit.v1_2.format_type import FormatType
from org.accellera.spirit.v1_2.function_return_type import FunctionReturnType
from org.accellera.spirit.v1_2.library_ref_type import LibraryRefType
from org.accellera.spirit.v1_2.name_value_pair_type import NameValuePairType
from org.accellera.spirit.v1_2.range_type_type import RangeTypeType
from org.accellera.spirit.v1_2.resolve_type import ResolveType
from org.accellera.spirit.v1_2.source_file_file_type import SourceFileFileType
from org.accellera.spirit.v1_2.vendor_extensions import VendorExtensions

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2"


@dataclass(slots=True, kw_only=True)
class FileSetType:
    """
    :ivar owner: Specifies the original owner of the fileSet, used when
        importing fileSets from other components, as in Hierarchical
        components, to allow the parent component to correctly locate
        files imported from subcomponents
    :ivar group: Identifies this filleSet as belonging to a particular
        group or having a particular purpose. Examples might be
        "diagnostics", "boot", "application", "interrupt",
        "deviceDriver", etc.
    :ivar file:
    :ivar default_file_builder:
    :ivar dependency:
    :ivar function: Generator information if this file set describes a
        function. For example, this file set may describe diagnostics
        for which the DE can generate a diagnostics driver. The boolean
        attribute "replicate", if true (default is false), directs the
        generator to compile a separate object module for each instance
        of the component in the design. Otherwise the function will be
        called with different arguments for each instance (e.g.
        baseAddress).
    :ivar vendor_extensions:
    :ivar file_set_id:
    """

    class Meta:
        name = "fileSetType"

    owner: None | LibraryRefType = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2",
        },
    )
    group: Sequence[str] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2",
        },
    )
    file: Sequence[File] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2",
        },
    )
    default_file_builder: Sequence[FileBuilderType] = field(
        default_factory=list,
        metadata={
            "name": "defaultFileBuilder",
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2",
        },
    )
    dependency: Sequence[Dependency] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2",
        },
    )
    function: Sequence[FileSetType.Function] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2",
        },
    )
    vendor_extensions: None | VendorExtensions = field(
        default=None,
        metadata={
            "name": "vendorExtensions",
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2",
        },
    )
    file_set_id: str = field(
        metadata={
            "name": "fileSetId",
            "type": "Attribute",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2",
        }
    )

    @dataclass(slots=True, kw_only=True)
    class Function:
        """
        :ivar entry_point:
        :ivar file_ref: A reference to the file that contains the entry
            point function.
        :ivar return_type: Function return type. See the enumerations.
        :ivar argument: Arguments passed in when the function is called.
            Arguments are passed in order. This is an extension of the
            name-value pair which includes the data type in the
            spirit:dataType attribute.  The argument name is in the
            spirit:name attribute and its value is in the text content
            of the element.
        :ivar enabled: Specifies if the SW function is enabled. Default
            is true.
        :ivar source_file:
        :ivar replicate:
        """

        entry_point: None | str = field(
            default=None,
            metadata={
                "name": "entryPoint",
                "type": "Element",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2",
            },
        )
        file_ref: str = field(
            metadata={
                "name": "fileRef",
                "type": "Element",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2",
            }
        )
        return_type: None | FunctionReturnType = field(
            default=None,
            metadata={
                "name": "returnType",
                "type": "Element",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2",
            },
        )
        argument: Sequence[FileSetType.Function.Argument] = field(
            default_factory=list,
            metadata={
                "type": "Element",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2",
            },
        )
        enabled: None | FileSetType.Function.Enabled = field(
            default=None,
            metadata={
                "type": "Element",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2",
            },
        )
        source_file: Sequence[FileSetType.Function.SourceFile] = field(
            default_factory=list,
            metadata={
                "name": "sourceFile",
                "type": "Element",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2",
            },
        )
        replicate: None | bool = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2",
            },
        )

        @dataclass(slots=True, kw_only=True)
        class Argument(NameValuePairType):
            data_type: DataTypeType = field(
                metadata={
                    "name": "dataType",
                    "type": "Attribute",
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2",
                }
            )

        @dataclass(slots=True, kw_only=True)
        class Enabled:
            """
            :ivar value:
            :ivar format: This is a hint to the user interface about the
                data format to require for user resolved properties. The
                bool.att attribute group sets the default format to
                "bool".
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
                configuration forms, the user-resolved properties with
                order attibutes will be presented in ascending order.
            :ivar choice_ref: For user resolved properties with a
                "choice" format, this refers to a uiChoice element in
                the ui section of the component file.
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
        class SourceFile:
            """
            :ivar source_name: Source file for the boot load.  Relative
                names are searched for in the project directory and the
                source of the component directory.
            :ivar file_type_or_user_file_type:
            """

            source_name: FileSetType.Function.SourceFile.SourceName = field(
                metadata={
                    "name": "sourceName",
                    "type": "Element",
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2",
                }
            )
            file_type_or_user_file_type: None | SourceFileFileType | str = (
                field(
                    default=None,
                    metadata={
                        "type": "Elements",
                        "choices": (
                            {
                                "name": "fileType",
                                "type": SourceFileFileType,
                                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2",
                            },
                            {
                                "name": "userFileType",
                                "type": str,
                                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2",
                            },
                        ),
                    },
                )
            )

            @dataclass(slots=True, kw_only=True)
            class SourceName:
                """
                :ivar value:
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
                :ivar format:
                :ivar prompt:
                """

                value: str = field(default="")
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
                format: None | FormatType = field(
                    default=None,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2",
                    },
                )
                prompt: None | str = field(
                    default=None,
                    metadata={
                        "type": "Attribute",
                        "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2",
                    },
                )

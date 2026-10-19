from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

from org.accellera.spirit.v1_2.choice_style_value import ChoiceStyleValue
from org.accellera.spirit.v1_2.dependency import Dependency
from org.accellera.spirit.v1_2.direction_value import DirectionValue
from org.accellera.spirit.v1_2.file_file_type import FileFileType
from org.accellera.spirit.v1_2.format_type import FormatType
from org.accellera.spirit.v1_2.name_value_pair_type import NameValuePairType
from org.accellera.spirit.v1_2.range_type_type import RangeTypeType
from org.accellera.spirit.v1_2.resolve_type import ResolveType
from org.accellera.spirit.v1_2.vendor_extensions import VendorExtensions

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2"


@dataclass(slots=True, kw_only=True)
class File:
    """
    SPIRIT reference to a file or directory.

    :ivar name: Path to the file or directory.
    :ivar file_type_or_user_file_type:
    :ivar logical_name: Logical name for this file or directory e.g.
        VHDL library name.
    :ivar exported_name: Defines exported names that can be accessed
        externally, e.g. exported function names from a C source file.
    :ivar build_command: Command and flags used to build derived files
        from the sourceName files. If this element is present, the
        command and/or flags used to to build the file will override or
        augment any default builders at a higher level.
    :ivar dependency:
    :ivar define: Specifies define symbols that are used in the source
        file.  The spirit:name attribute gives the name to be defined
        and the text content of the element holds the value.  This
        element supports full configurability.
    :ivar image_type: Relates the current file to a certain executable
        image type in the design.
    :ivar vendor_extensions:
    :ivar file_id:
    :ivar any_attributes:
    """

    class Meta:
        name = "file"
        namespace = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2"

    name: File.Name = field(
        metadata={
            "type": "Element",
        }
    )
    file_type_or_user_file_type: Sequence[FileFileType | str] = field(
        default_factory=list,
        metadata={
            "type": "Elements",
            "choices": (
                {
                    "name": "fileType",
                    "type": FileFileType,
                },
                {
                    "name": "userFileType",
                    "type": str,
                },
            ),
        },
    )
    logical_name: None | File.LogicalName = field(
        default=None,
        metadata={
            "name": "logicalName",
            "type": "Element",
        },
    )
    exported_name: Sequence[str] = field(
        default_factory=list,
        metadata={
            "name": "exportedName",
            "type": "Element",
        },
    )
    build_command: None | File.BuildCommand = field(
        default=None,
        metadata={
            "name": "buildCommand",
            "type": "Element",
        },
    )
    dependency: Sequence[Dependency] = field(
        default_factory=list,
        metadata={
            "type": "Element",
        },
    )
    define: Sequence[NameValuePairType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
        },
    )
    image_type: Sequence[str] = field(
        default_factory=list,
        metadata={
            "name": "imageType",
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
    file_id: None | str = field(
        default=None,
        metadata={
            "name": "fileId",
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

    @dataclass(slots=True, kw_only=True)
    class Name:
        """
        :ivar value:
        :ivar resolve:
        :ivar id:
        :ivar dependency:
        :ivar any_attributes:
        :ivar minimum: For user-resolved properties with numeric values,
            this indicates the minimum value allowed.
        :ivar maximum: For user-resolved properties with numeric values,
            this indicates the maximum value allowed.
        :ivar range_type:
        :ivar order: For components with auto-generated configuration
            forms, the user-resolved properties with order attibutes
            will be presented in ascending order.
        :ivar choice_ref: For user resolved properties with a "choice"
            format, this refers to a uiChoice element in the ui section
            of the component file.
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

    @dataclass(slots=True, kw_only=True)
    class LogicalName:
        value: str = field(default="")
        default: None | str = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2",
            },
        )

    @dataclass(slots=True, kw_only=True)
    class BuildCommand:
        """
        :ivar command: Command used to build this file.
        :ivar flags: Flags given to the build command when building this
            file. If the optional attribute "append" is "true", this
            string will be appended to any existing flags, otherwise
            these flags will replace any existing default flags.
        :ivar replace_default_flags: If true, the value of the sibling
            element "flags" should replace any default flags specified
            at a more global level. If this is true and the sibling
            element "flags" is empty or missing, this has the effect of
            clearing any default flags.
        :ivar target_name: Pathname to the file that is derived (built)
            from the source file.
        """

        command: None | File.BuildCommand.Command = field(
            default=None,
            metadata={
                "type": "Element",
            },
        )
        flags: None | File.BuildCommand.Flags = field(
            default=None,
            metadata={
                "type": "Element",
            },
        )
        replace_default_flags: None | File.BuildCommand.ReplaceDefaultFlags = (
            field(
                default=None,
                metadata={
                    "name": "replaceDefaultFlags",
                    "type": "Element",
                },
            )
        )
        target_name: None | File.BuildCommand.TargetName = field(
            default=None,
            metadata={
                "name": "targetName",
                "type": "Element",
            },
        )

        @dataclass(slots=True, kw_only=True)
        class Command:
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
                configuration forms, the user-resolved properties with
                order attibutes will be presented in ascending order.
            :ivar choice_ref: For user resolved properties with a
                "choice" format, this refers to a uiChoice element in
                the ui section of the component file.
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

        @dataclass(slots=True, kw_only=True)
        class Flags:
            """
            :ivar value:
            :ivar append:
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
            :ivar format:
            :ivar prompt:
            """

            value: str = field(default="")
            append: None | bool = field(
                default=None,
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

        @dataclass(slots=True, kw_only=True)
        class ReplaceDefaultFlags:
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
                configuration forms, the user-resolved properties with
                order attibutes will be presented in ascending order.
            :ivar choice_ref: For user resolved properties with a
                "choice" format, this refers to a uiChoice element in
                the ui section of the component file.
            :ivar choice_style:
            :ivar direction:
            :ivar config_groups:
            :ivar format:
            :ivar prompt:
            """

            value: bool = field()
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

        @dataclass(slots=True, kw_only=True)
        class TargetName:
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
                configuration forms, the user-resolved properties with
                order attibutes will be presented in ascending order.
            :ivar choice_ref: For user resolved properties with a
                "choice" format, this refers to a uiChoice element in
                the ui section of the component file.
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

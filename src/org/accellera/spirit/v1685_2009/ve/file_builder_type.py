from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

from org.accellera.spirit.v1685_2009.ve.file_builder_type_file_type import (
    FileBuilderTypeFileType,
)
from org.accellera.spirit.v1685_2009.ve.format_type import FormatType
from org.accellera.spirit.v1685_2009.ve.range_type_type import RangeTypeType
from org.accellera.spirit.v1685_2009.ve.resolve_type import ResolveType

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009"


@dataclass(slots=True, kw_only=True)
class FileBuilderType:
    """
    :ivar file_type_or_user_file_type:
    :ivar command: Default command used to build files of the specified
        fileType.
    :ivar flags: Flags given to the build command when building files of
        this type.
    :ivar replace_default_flags: If true, replace any default flags
        value with the value in the sibling flags element. Otherwise,
        append the contents of the sibling flags element to any default
        flags value. If the value is true and the "flags" element is
        empty or missing, this will have the result of clearing any
        default flags value.
    """

    class Meta:
        name = "fileBuilderType"

    file_type_or_user_file_type: None | FileBuilderTypeFileType | str = field(
        default=None,
        metadata={
            "type": "Elements",
            "choices": (
                {
                    "name": "fileType",
                    "type": FileBuilderTypeFileType,
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
                },
                {
                    "name": "userFileType",
                    "type": str,
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
                },
            ),
        },
    )
    command: None | FileBuilderType.Command = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
        },
    )
    flags: None | FileBuilderType.Flags = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
        },
    )
    replace_default_flags: None | FileBuilderType.ReplaceDefaultFlags = field(
        default=None,
        metadata={
            "name": "replaceDefaultFlags",
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
        },
    )

    @dataclass(slots=True, kw_only=True)
    class Command:
        value: str = field(default="")
        format: FormatType = field(
            default=FormatType.STRING,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
            },
        )
        resolve: ResolveType = field(
            default=ResolveType.IMMEDIATE,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
            },
        )
        id: None | str = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
            },
        )
        dependency: None | str = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
            },
        )
        any_attributes: Mapping[str, str] = field(
            default_factory=dict,
            metadata={
                "type": "Attributes",
                "namespace": "##any",
            },
        )
        choice_ref: None | str = field(
            default=None,
            metadata={
                "name": "choiceRef",
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
            },
        )
        order: None | float = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
            },
        )
        config_groups: Sequence[str] = field(
            default_factory=list,
            metadata={
                "name": "configGroups",
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
                "tokens": True,
            },
        )
        bit_string_length: None | int = field(
            default=None,
            metadata={
                "name": "bitStringLength",
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
            },
        )
        minimum: None | str = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
            },
        )
        maximum: None | str = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
            },
        )
        range_type: RangeTypeType = field(
            default=RangeTypeType.FLOAT,
            metadata={
                "name": "rangeType",
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
            },
        )
        prompt: None | str = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
            },
        )

    @dataclass(slots=True, kw_only=True)
    class Flags:
        value: str = field(default="")
        format: FormatType = field(
            default=FormatType.STRING,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
            },
        )
        resolve: ResolveType = field(
            default=ResolveType.IMMEDIATE,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
            },
        )
        id: None | str = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
            },
        )
        dependency: None | str = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
            },
        )
        any_attributes: Mapping[str, str] = field(
            default_factory=dict,
            metadata={
                "type": "Attributes",
                "namespace": "##any",
            },
        )
        choice_ref: None | str = field(
            default=None,
            metadata={
                "name": "choiceRef",
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
            },
        )
        order: None | float = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
            },
        )
        config_groups: Sequence[str] = field(
            default_factory=list,
            metadata={
                "name": "configGroups",
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
                "tokens": True,
            },
        )
        bit_string_length: None | int = field(
            default=None,
            metadata={
                "name": "bitStringLength",
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
            },
        )
        minimum: None | str = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
            },
        )
        maximum: None | str = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
            },
        )
        range_type: RangeTypeType = field(
            default=RangeTypeType.FLOAT,
            metadata={
                "name": "rangeType",
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
            },
        )
        prompt: None | str = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
            },
        )

    @dataclass(slots=True, kw_only=True)
    class ReplaceDefaultFlags:
        value: bool = field()
        format: FormatType = field(
            default=FormatType.BOOL,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
            },
        )
        resolve: ResolveType = field(
            default=ResolveType.IMMEDIATE,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
            },
        )
        id: None | str = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
            },
        )
        dependency: None | str = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
            },
        )
        any_attributes: Mapping[str, str] = field(
            default_factory=dict,
            metadata={
                "type": "Attributes",
                "namespace": "##any",
            },
        )
        choice_ref: None | str = field(
            default=None,
            metadata={
                "name": "choiceRef",
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
            },
        )
        order: None | float = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
            },
        )
        config_groups: Sequence[str] = field(
            default_factory=list,
            metadata={
                "name": "configGroups",
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
                "tokens": True,
            },
        )
        bit_string_length: None | int = field(
            default=None,
            metadata={
                "name": "bitStringLength",
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
            },
        )
        minimum: None | str = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
            },
        )
        maximum: None | str = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
            },
        )
        range_type: RangeTypeType = field(
            default=RangeTypeType.INT,
            metadata={
                "name": "rangeType",
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
            },
        )
        prompt: None | str = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
            },
        )

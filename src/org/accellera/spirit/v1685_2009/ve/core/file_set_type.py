from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

from org.accellera.spirit.v1685_2009.ve.core.data_type_type import DataTypeType
from org.accellera.spirit.v1685_2009.ve.core.dependency import Dependency
from org.accellera.spirit.v1685_2009.ve.core.description import Description
from org.accellera.spirit.v1685_2009.ve.core.display_name import DisplayName
from org.accellera.spirit.v1685_2009.ve.core.file import File
from org.accellera.spirit.v1685_2009.ve.core.file_builder_type import (
    FileBuilderType,
)
from org.accellera.spirit.v1685_2009.ve.core.format_type import FormatType
from org.accellera.spirit.v1685_2009.ve.core.function_return_type import (
    FunctionReturnType,
)
from org.accellera.spirit.v1685_2009.ve.core.name_value_pair_type_1 import (
    NameValuePairType1,
)
from org.accellera.spirit.v1685_2009.ve.core.range_type_type import (
    RangeTypeType,
)
from org.accellera.spirit.v1685_2009.ve.core.resolve_type import ResolveType
from org.accellera.spirit.v1685_2009.ve.core.source_file_file_type import (
    SourceFileFileType,
)
from org.accellera.spirit.v1685_2009.ve.core.vendor_extensions import (
    VendorExtensions,
)

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009"


@dataclass(slots=True, kw_only=True)
class FileSetType:
    """
    :ivar name: Unique name
    :ivar display_name:
    :ivar description:
    :ivar group: Identifies this filleSet as belonging to a particular
        group or having a particular purpose. Examples might be
        "diagnostics", "boot", "application", "interrupt",
        "deviceDriver", etc.
    :ivar file:
    :ivar default_file_builder: Default command and flags used to build
        derived files from the sourceName files in this file set.
    :ivar dependency:
    :ivar function: Generator information if this file set describes a
        function. For example, this file set may describe diagnostics
        for which the DE can generate a diagnostics driver.
    :ivar vendor_extensions:
    """

    class Meta:
        name = "fileSetType"

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
    group: Sequence[str] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
        },
    )
    file: Sequence[File] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
        },
    )
    default_file_builder: Sequence[FileBuilderType] = field(
        default_factory=list,
        metadata={
            "name": "defaultFileBuilder",
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
        },
    )
    dependency: Sequence[Dependency] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
        },
    )
    function: Sequence[FileSetType.Function] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
        },
    )
    vendor_extensions: None | VendorExtensions = field(
        default=None,
        metadata={
            "name": "vendorExtensions",
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
        },
    )

    @dataclass(slots=True, kw_only=True)
    class Function:
        """
        :ivar entry_point: Optional name for the function.
        :ivar file_ref: A reference to the file that contains the entry
            point function.
        :ivar return_type: Function return type. Possible values are
            void and int.
        :ivar argument: Arguments passed in when the function is called.
            Arguments are passed in order. This is an extension of the
            name-value pair which includes the data type in the
            spirit:dataType attribute.  The argument name is in the
            spirit:name element and its value is in the spirit:value
            element.
        :ivar disabled: Specifies if the SW function is enabled. If not
            present the function is always enabled.
        :ivar source_file: Location information for the source file of
            this function.
        :ivar replicate: If true directs the generator to compile a
            separate object module for each instance of the component in
            the design. If false (default) the function will be called
            with different arguments for each instance.
        """

        entry_point: None | str = field(
            default=None,
            metadata={
                "name": "entryPoint",
                "type": "Element",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
            },
        )
        file_ref: str = field(
            metadata={
                "name": "fileRef",
                "type": "Element",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
            }
        )
        return_type: None | FunctionReturnType = field(
            default=None,
            metadata={
                "name": "returnType",
                "type": "Element",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
            },
        )
        argument: Sequence[FileSetType.Function.Argument] = field(
            default_factory=list,
            metadata={
                "type": "Element",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
            },
        )
        disabled: None | FileSetType.Function.Disabled = field(
            default=None,
            metadata={
                "type": "Element",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
            },
        )
        source_file: Sequence[FileSetType.Function.SourceFile] = field(
            default_factory=list,
            metadata={
                "name": "sourceFile",
                "type": "Element",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
            },
        )
        replicate: bool = field(
            default=False,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
            },
        )

        @dataclass(slots=True, kw_only=True)
        class Argument(NameValuePairType1):
            """
            :ivar data_type: The data type of the argument as pertains
                to the language. Example: "int", "double", "char *".
            """

            data_type: DataTypeType = field(
                metadata={
                    "name": "dataType",
                    "type": "Attribute",
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
                }
            )

        @dataclass(slots=True, kw_only=True)
        class Disabled:
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

        @dataclass(slots=True, kw_only=True)
        class SourceFile:
            """
            :ivar source_name: Source file for the boot load.  Relative
                names are searched for in the project directory and the
                source of the component directory.
            :ivar file_type_or_user_file_type:
            """

            source_name: str = field(
                metadata={
                    "name": "sourceName",
                    "type": "Element",
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009",
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
            )

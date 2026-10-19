from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from org.accellera.ipxact.v1685_2022.data_type_type import DataTypeType
from org.accellera.ipxact.v1685_2022.dependency import Dependency
from org.accellera.ipxact.v1685_2022.description import Description
from org.accellera.ipxact.v1685_2022.display_name import DisplayName
from org.accellera.ipxact.v1685_2022.file import File
from org.accellera.ipxact.v1685_2022.file_builder_type import FileBuilderType
from org.accellera.ipxact.v1685_2022.file_type import FileType
from org.accellera.ipxact.v1685_2022.ipxact_uri import IpxactUri
from org.accellera.ipxact.v1685_2022.name_value_pair_type import (
    NameValuePairType,
)
from org.accellera.ipxact.v1685_2022.return_type_type import ReturnTypeType
from org.accellera.ipxact.v1685_2022.short_description import ShortDescription
from org.accellera.ipxact.v1685_2022.unsigned_bit_expression import (
    UnsignedBitExpression,
)
from org.accellera.ipxact.v1685_2022.vendor_extensions import VendorExtensions

__NAMESPACE__ = "http://www.accellera.org/XMLSchema/IPXACT/1685-2022"


@dataclass(slots=True, kw_only=True)
class FileSetType:
    """
    :ivar name: Unique name
    :ivar display_name:
    :ivar short_description:
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
    :ivar id:
    """

    class Meta:
        name = "fileSetType"

    name: str = field(
        metadata={
            "type": "Element",
            "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
        }
    )
    display_name: None | DisplayName = field(
        default=None,
        metadata={
            "name": "displayName",
            "type": "Element",
            "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
        },
    )
    short_description: None | ShortDescription = field(
        default=None,
        metadata={
            "name": "shortDescription",
            "type": "Element",
            "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
        },
    )
    description: None | Description = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
        },
    )
    group: Sequence[FileSetType.Group] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
        },
    )
    file: Sequence[File] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
        },
    )
    default_file_builder: Sequence[FileBuilderType] = field(
        default_factory=list,
        metadata={
            "name": "defaultFileBuilder",
            "type": "Element",
            "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
        },
    )
    dependency: Sequence[Dependency] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
        },
    )
    function: Sequence[FileSetType.Function] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
        },
    )
    vendor_extensions: None | VendorExtensions = field(
        default=None,
        metadata={
            "name": "vendorExtensions",
            "type": "Element",
            "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
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
    class Group:
        value: str = field(default="")
        id: None | str = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.w3.org/XML/1998/namespace",
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
            ipxact:dataType attribute.  The argument name is in the
            ipxact:name element and its value is in the ipxact:value
            element.
        :ivar disabled: Specifies if the SW function is enabled. If not
            present the function is always enabled.
        :ivar source_file: Location information for the source file of
            this function.
        :ivar replicate: If true directs the generator to compile a
            separate object module for each instance of the component in
            the design. If false (default) the function will be called
            with different arguments for each instance.
        :ivar id:
        """

        entry_point: None | str = field(
            default=None,
            metadata={
                "name": "entryPoint",
                "type": "Element",
                "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
            },
        )
        file_ref: str = field(
            metadata={
                "name": "fileRef",
                "type": "Element",
                "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
            }
        )
        return_type: None | ReturnTypeType = field(
            default=None,
            metadata={
                "name": "returnType",
                "type": "Element",
                "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
            },
        )
        argument: Sequence[FileSetType.Function.Argument] = field(
            default_factory=list,
            metadata={
                "type": "Element",
                "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
            },
        )
        disabled: None | UnsignedBitExpression = field(
            default=None,
            metadata={
                "type": "Element",
                "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
            },
        )
        source_file: Sequence[FileSetType.Function.SourceFile] = field(
            default_factory=list,
            metadata={
                "name": "sourceFile",
                "type": "Element",
                "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
            },
        )
        replicate: bool = field(
            default=False,
            metadata={
                "type": "Attribute",
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
        class Argument(NameValuePairType):
            """
            :ivar data_type: The data type of the argument as pertains
                to the language. Example: "int", "double", "char *".
            """

            data_type: DataTypeType = field(
                metadata={
                    "name": "dataType",
                    "type": "Attribute",
                }
            )

        @dataclass(slots=True, kw_only=True)
        class SourceFile:
            """
            :ivar source_name: Source file for the boot load.  Relative
                names are searched for in the project directory and the
                source of the component directory.
            :ivar file_type:
            :ivar id:
            """

            source_name: IpxactUri = field(
                metadata={
                    "name": "sourceName",
                    "type": "Element",
                    "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
                }
            )
            file_type: FileType = field(
                metadata={
                    "name": "fileType",
                    "type": "Element",
                    "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
                }
            )
            id: None | str = field(
                default=None,
                metadata={
                    "type": "Attribute",
                    "namespace": "http://www.w3.org/XML/1998/namespace",
                },
            )

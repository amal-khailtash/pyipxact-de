from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from org.accellera.ipxact.v1685_2014.description import Description
from org.accellera.ipxact.v1685_2014.display_name import DisplayName
from org.accellera.ipxact.v1685_2014.file_set_ref import FileSetRef
from org.accellera.ipxact.v1685_2014.file_type import FileType
from org.accellera.ipxact.v1685_2014.linker_command_file import (
    LinkerCommandFile,
)
from org.accellera.ipxact.v1685_2014.parameters import Parameters
from org.accellera.ipxact.v1685_2014.string_expression import StringExpression
from org.accellera.ipxact.v1685_2014.unsigned_bit_expression import (
    UnsignedBitExpression,
)
from org.accellera.ipxact.v1685_2014.vendor_extensions import VendorExtensions

__NAMESPACE__ = "http://www.accellera.org/XMLSchema/IPXACT/1685-2014"


@dataclass(slots=True, kw_only=True)
class ExecutableImage:
    """
    Specifies an executable software image to be loaded into a processors
    address space.

    The format of the image is not specified. It could, for example, be an
    ELF loadfile, or it could be raw binary or ascii hex data for loading
    directly into a memory model instance.

    :ivar name: Unique name
    :ivar display_name:
    :ivar description:
    :ivar parameters: Additional information about the load module, e.g.
        stack base addresses, table addresses, etc.
    :ivar language_tools: Default commands and flags for software
        language tools needed to build the executable image.
    :ivar file_set_ref_group: Contains a group of file set references
        that indicates the set of file sets complying with the tool set
        of the current executable image.
    :ivar vendor_extensions:
    :ivar image_id: Unique ID for the executableImage, referenced in
        fileSet/function/fileRef
    :ivar image_type: Open element to describe the type of image. The
        contents is model and/or generator specific.
    :ivar id:
    """

    class Meta:
        name = "executableImage"
        namespace = "http://www.accellera.org/XMLSchema/IPXACT/1685-2014"

    name: str = field(
        metadata={
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
    parameters: None | Parameters = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    language_tools: None | ExecutableImage.LanguageTools = field(
        default=None,
        metadata={
            "name": "languageTools",
            "type": "Element",
        },
    )
    file_set_ref_group: None | ExecutableImage.FileSetRefGroup = field(
        default=None,
        metadata={
            "name": "fileSetRefGroup",
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
    image_id: str = field(
        metadata={
            "name": "imageId",
            "type": "Attribute",
        }
    )
    image_type: None | str = field(
        default=None,
        metadata={
            "name": "imageType",
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
    class LanguageTools:
        """
        :ivar file_builder: A generic placeholder for any file builder
            like compilers and assemblers.  It contains the file types
            to which the command should be applied, and the flags to be
            used with that command.
        :ivar linker:
        :ivar linker_flags_or_linker_command_file:
        """

        file_builder: Sequence[ExecutableImage.LanguageTools.FileBuilder] = (
            field(
                default_factory=list,
                metadata={
                    "name": "fileBuilder",
                    "type": "Element",
                },
            )
        )
        linker: None | StringExpression = field(
            default=None,
            metadata={
                "type": "Element",
            },
        )
        linker_flags_or_linker_command_file: Sequence[
            StringExpression | LinkerCommandFile
        ] = field(
            default_factory=list,
            metadata={
                "type": "Elements",
                "choices": (
                    {
                        "name": "linkerFlags",
                        "type": StringExpression,
                    },
                    {
                        "name": "linkerCommandFile",
                        "type": LinkerCommandFile,
                    },
                ),
                "max_occurs": 2,
            },
        )

        @dataclass(slots=True, kw_only=True)
        class FileBuilder:
            """
            :ivar file_type:
            :ivar command: Default command used to build files of the
                specified fileType.
            :ivar flags: Flags given to the build command when building
                files of this type.
            :ivar replace_default_flags: If true, replace any default
                flags value with the value in the sibling flags element.
                Otherwise, append the contents of the sibling flags
                element to any default flags value. If the value is true
                and the "flags" element is empty or missing, this will
                have the result of clearing any default flags value.
            :ivar vendor_extensions:
            :ivar id:
            """

            file_type: FileType = field(
                metadata={
                    "name": "fileType",
                    "type": "Element",
                }
            )
            command: StringExpression = field(
                metadata={
                    "type": "Element",
                }
            )
            flags: None | StringExpression = field(
                default=None,
                metadata={
                    "type": "Element",
                },
            )
            replace_default_flags: None | UnsignedBitExpression = field(
                default=None,
                metadata={
                    "name": "replaceDefaultFlags",
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
            id: None | str = field(
                default=None,
                metadata={
                    "type": "Attribute",
                    "namespace": "http://www.w3.org/XML/1998/namespace",
                },
            )

    @dataclass(slots=True, kw_only=True)
    class FileSetRefGroup:
        file_set_ref: Sequence[FileSetRef] = field(
            default_factory=list,
            metadata={
                "name": "fileSetRef",
                "type": "Element",
                "min_occurs": 1,
            },
        )

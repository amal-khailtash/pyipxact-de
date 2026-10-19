from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from org.accellera.ipxact.v1685_2022.address_block_definitions import (
    AddressBlockDefinitions,
)
from org.accellera.ipxact.v1685_2022.assertions import Assertions
from org.accellera.ipxact.v1685_2022.bank_definitions import BankDefinitions
from org.accellera.ipxact.v1685_2022.choices import Choices
from org.accellera.ipxact.v1685_2022.description import Description
from org.accellera.ipxact.v1685_2022.display_name import DisplayName
from org.accellera.ipxact.v1685_2022.enumeration_definitions import (
    EnumerationDefinitions,
)
from org.accellera.ipxact.v1685_2022.external_type_definitions import (
    ExternalTypeDefinitions,
)
from org.accellera.ipxact.v1685_2022.field_access_policy_definitions import (
    FieldAccessPolicyDefinitions,
)
from org.accellera.ipxact.v1685_2022.field_definitions import FieldDefinitions
from org.accellera.ipxact.v1685_2022.memory_map_definitions import (
    MemoryMapDefinitions,
)
from org.accellera.ipxact.v1685_2022.memory_remap_definitions import (
    MemoryRemapDefinitions,
)
from org.accellera.ipxact.v1685_2022.parameters import Parameters
from org.accellera.ipxact.v1685_2022.register_definitions import (
    RegisterDefinitions,
)
from org.accellera.ipxact.v1685_2022.register_file_definitions import (
    RegisterFileDefinitions,
)
from org.accellera.ipxact.v1685_2022.short_description import ShortDescription
from org.accellera.ipxact.v1685_2022.vendor_extensions import VendorExtensions

__NAMESPACE__ = "http://www.accellera.org/XMLSchema/IPXACT/1685-2022"


@dataclass(slots=True, kw_only=True)
class TypeDefinitions:
    """
    :ivar vendor: Name of the vendor who supplies this file.
    :ivar library: Name of the logical library this element belongs to.
    :ivar name: The name of the object.
    :ivar version: Indicates the version of the named element.
    :ivar display_name: Name for display purposes. Typically a few words
        providing a more detailed and/or user-friendly name than the
        vlnv.
    :ivar short_description:
    :ivar description:
    :ivar external_type_definitions:
    :ivar modes: A list of user defined component modes.
    :ivar views: A list of user defined views.
    :ivar field_access_policy_definitions:
    :ivar enumeration_definitions:
    :ivar field_definitions:
    :ivar register_definitions:
    :ivar register_file_definitions:
    :ivar address_block_definitions:
    :ivar bank_definitions:
    :ivar memory_map_definitions:
    :ivar memory_remap_definitions:
    :ivar reset_types: A list of user defined resetTypes applicable to
        this component.
    :ivar choices:
    :ivar parameters:
    :ivar assertions:
    :ivar vendor_extensions:
    :ivar id:
    """

    class Meta:
        name = "typeDefinitions"
        namespace = "http://www.accellera.org/XMLSchema/IPXACT/1685-2022"

    vendor: None | str = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    library: None | str = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    name: None | str = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    version: None | str = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    display_name: None | str = field(
        default=None,
        metadata={
            "name": "displayName",
            "type": "Element",
        },
    )
    short_description: None | ShortDescription = field(
        default=None,
        metadata={
            "name": "shortDescription",
            "type": "Element",
        },
    )
    description: None | Description = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    external_type_definitions: Sequence[ExternalTypeDefinitions] = field(
        default_factory=list,
        metadata={
            "name": "externalTypeDefinitions",
            "type": "Element",
        },
    )
    modes: None | TypeDefinitions.Modes = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    views: None | TypeDefinitions.Views = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    field_access_policy_definitions: None | FieldAccessPolicyDefinitions = (
        field(
            default=None,
            metadata={
                "name": "fieldAccessPolicyDefinitions",
                "type": "Element",
            },
        )
    )
    enumeration_definitions: None | EnumerationDefinitions = field(
        default=None,
        metadata={
            "name": "enumerationDefinitions",
            "type": "Element",
        },
    )
    field_definitions: None | FieldDefinitions = field(
        default=None,
        metadata={
            "name": "fieldDefinitions",
            "type": "Element",
        },
    )
    register_definitions: None | RegisterDefinitions = field(
        default=None,
        metadata={
            "name": "registerDefinitions",
            "type": "Element",
        },
    )
    register_file_definitions: None | RegisterFileDefinitions = field(
        default=None,
        metadata={
            "name": "registerFileDefinitions",
            "type": "Element",
        },
    )
    address_block_definitions: None | AddressBlockDefinitions = field(
        default=None,
        metadata={
            "name": "addressBlockDefinitions",
            "type": "Element",
        },
    )
    bank_definitions: None | BankDefinitions = field(
        default=None,
        metadata={
            "name": "bankDefinitions",
            "type": "Element",
        },
    )
    memory_map_definitions: None | MemoryMapDefinitions = field(
        default=None,
        metadata={
            "name": "memoryMapDefinitions",
            "type": "Element",
        },
    )
    memory_remap_definitions: None | MemoryRemapDefinitions = field(
        default=None,
        metadata={
            "name": "memoryRemapDefinitions",
            "type": "Element",
        },
    )
    reset_types: None | TypeDefinitions.ResetTypes = field(
        default=None,
        metadata={
            "name": "resetTypes",
            "type": "Element",
        },
    )
    choices: None | Choices = field(
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
    assertions: None | Assertions = field(
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
    id: None | str = field(
        default=None,
        metadata={
            "type": "Attribute",
            "namespace": "http://www.w3.org/XML/1998/namespace",
        },
    )

    @dataclass(slots=True, kw_only=True)
    class Modes:
        mode: Sequence[TypeDefinitions.Modes.Mode] = field(
            default_factory=list,
            metadata={
                "type": "Element",
                "min_occurs": 1,
            },
        )

        @dataclass(slots=True, kw_only=True)
        class Mode:
            """
            :ivar name: Unique name
            :ivar display_name:
            :ivar short_description:
            :ivar description:
            :ivar vendor_extensions:
            :ivar id:
            """

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
            short_description: None | ShortDescription = field(
                default=None,
                metadata={
                    "name": "shortDescription",
                    "type": "Element",
                },
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
            id: None | str = field(
                default=None,
                metadata={
                    "type": "Attribute",
                    "namespace": "http://www.w3.org/XML/1998/namespace",
                },
            )

    @dataclass(slots=True, kw_only=True)
    class Views:
        view: Sequence[TypeDefinitions.Views.View] = field(
            default_factory=list,
            metadata={
                "type": "Element",
                "min_occurs": 1,
            },
        )

        @dataclass(slots=True, kw_only=True)
        class View:
            """
            :ivar name: Unique name
            :ivar display_name:
            :ivar short_description:
            :ivar description:
            :ivar vendor_extensions:
            :ivar id:
            """

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
            short_description: None | ShortDescription = field(
                default=None,
                metadata={
                    "name": "shortDescription",
                    "type": "Element",
                },
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
            id: None | str = field(
                default=None,
                metadata={
                    "type": "Attribute",
                    "namespace": "http://www.w3.org/XML/1998/namespace",
                },
            )

    @dataclass(slots=True, kw_only=True)
    class ResetTypes:
        """
        :ivar reset_type: A user defined reset policy
        """

        reset_type: Sequence[TypeDefinitions.ResetTypes.ResetType] = field(
            default_factory=list,
            metadata={
                "name": "resetType",
                "type": "Element",
                "min_occurs": 1,
            },
        )

        @dataclass(slots=True, kw_only=True)
        class ResetType:
            """
            :ivar name: Unique name
            :ivar display_name:
            :ivar short_description:
            :ivar description:
            :ivar vendor_extensions:
            :ivar id:
            """

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
            short_description: None | ShortDescription = field(
                default=None,
                metadata={
                    "name": "shortDescription",
                    "type": "Element",
                },
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
            id: None | str = field(
                default=None,
                metadata={
                    "type": "Attribute",
                    "namespace": "http://www.w3.org/XML/1998/namespace",
                },
            )

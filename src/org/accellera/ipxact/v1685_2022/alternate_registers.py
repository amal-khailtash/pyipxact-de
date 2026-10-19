from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from org.accellera.ipxact.v1685_2022.access_policies import AccessPolicies
from org.accellera.ipxact.v1685_2022.description import Description
from org.accellera.ipxact.v1685_2022.display_name import DisplayName
from org.accellera.ipxact.v1685_2022.field_type import FieldType
from org.accellera.ipxact.v1685_2022.mode_ref import ModeRef
from org.accellera.ipxact.v1685_2022.parameters import Parameters
from org.accellera.ipxact.v1685_2022.short_description import ShortDescription
from org.accellera.ipxact.v1685_2022.simple_access_handle import (
    SimpleAccessHandle,
)
from org.accellera.ipxact.v1685_2022.vendor_extensions import VendorExtensions
from org.accellera.ipxact.v1685_2022.volatile import Volatile

__NAMESPACE__ = "http://www.accellera.org/XMLSchema/IPXACT/1685-2022"


@dataclass(slots=True, kw_only=True)
class AlternateRegisters:
    """
    Alternate definitions for the current register.

    :ivar alternate_register: Alternate definition for the current
        register
    """

    class Meta:
        name = "alternateRegisters"
        namespace = "http://www.accellera.org/XMLSchema/IPXACT/1685-2022"

    alternate_register: Sequence[AlternateRegisters.AlternateRegister] = field(
        default_factory=list,
        metadata={
            "name": "alternateRegister",
            "type": "Element",
            "min_occurs": 1,
        },
    )

    @dataclass(slots=True, kw_only=True)
    class AlternateRegister:
        """
        :ivar name: Unique name
        :ivar display_name:
        :ivar short_description:
        :ivar description:
        :ivar access_handles:
        :ivar mode_ref:
        :ivar type_identifier: Identifier name used to indicate that
            multiple register elements contain the exact same
            information for the elements in the
            alternateRegisterDefinitionGroup.
        :ivar volatile:
        :ivar access_policies:
        :ivar field_value: Describes individual bit fields within the
            register.
        :ivar parameters:
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
        access_handles: (
            None | AlternateRegisters.AlternateRegister.AccessHandles
        ) = field(
            default=None,
            metadata={
                "name": "accessHandles",
                "type": "Element",
            },
        )
        mode_ref: Sequence[ModeRef] = field(
            default_factory=list,
            metadata={
                "name": "modeRef",
                "type": "Element",
                "min_occurs": 1,
            },
        )
        type_identifier: None | str = field(
            default=None,
            metadata={
                "name": "typeIdentifier",
                "type": "Element",
            },
        )
        volatile: None | Volatile = field(
            default=None,
            metadata={
                "type": "Element",
            },
        )
        access_policies: None | AccessPolicies = field(
            default=None,
            metadata={
                "name": "accessPolicies",
                "type": "Element",
            },
        )
        field_value: Sequence[FieldType] = field(
            default_factory=list,
            metadata={
                "name": "field",
                "type": "Element",
                "min_occurs": 1,
            },
        )
        parameters: None | Parameters = field(
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
        class AccessHandles:
            access_handle: Sequence[SimpleAccessHandle] = field(
                default_factory=list,
                metadata={
                    "name": "accessHandle",
                    "type": "Element",
                    "min_occurs": 1,
                },
            )

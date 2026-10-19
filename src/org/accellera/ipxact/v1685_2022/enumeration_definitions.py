from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from org.accellera.ipxact.v1685_2022.description import Description
from org.accellera.ipxact.v1685_2022.display_name import DisplayName
from org.accellera.ipxact.v1685_2022.enumerated_value_type import (
    EnumeratedValueType,
)
from org.accellera.ipxact.v1685_2022.short_description import ShortDescription
from org.accellera.ipxact.v1685_2022.unsigned_positive_int_expression import (
    UnsignedPositiveIntExpression,
)
from org.accellera.ipxact.v1685_2022.vendor_extensions import VendorExtensions

__NAMESPACE__ = "http://www.accellera.org/XMLSchema/IPXACT/1685-2022"


@dataclass(slots=True, kw_only=True)
class EnumerationDefinitions:
    class Meta:
        name = "enumerationDefinitions"
        namespace = "http://www.accellera.org/XMLSchema/IPXACT/1685-2022"

    enumeration_definition: Sequence[
        EnumerationDefinitions.EnumerationDefinition
    ] = field(
        default_factory=list,
        metadata={
            "name": "enumerationDefinition",
            "type": "Element",
            "min_occurs": 1,
        },
    )

    @dataclass(slots=True, kw_only=True)
    class EnumerationDefinition:
        """
        :ivar name: Unique name
        :ivar display_name:
        :ivar short_description:
        :ivar description:
        :ivar width: Definition width used to resolve the value.
        :ivar enumerated_value: Enumerates specific values that can be
            assigned to the bit field. The name of this enumerated
            value. This may be used as a token in generating code.
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
        width: UnsignedPositiveIntExpression = field(
            metadata={
                "type": "Element",
            }
        )
        enumerated_value: Sequence[EnumeratedValueType] = field(
            default_factory=list,
            metadata={
                "name": "enumeratedValue",
                "type": "Element",
                "min_occurs": 1,
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

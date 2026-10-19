from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from org.accellera.ipxact.v1685_2014.description import Description
from org.accellera.ipxact.v1685_2014.display_name import DisplayName
from org.accellera.ipxact.v1685_2014.enumerated_value_usage import (
    EnumeratedValueUsage,
)
from org.accellera.ipxact.v1685_2014.unsigned_bit_vector_expression import (
    UnsignedBitVectorExpression,
)
from org.accellera.ipxact.v1685_2014.vendor_extensions import VendorExtensions

__NAMESPACE__ = "http://www.accellera.org/XMLSchema/IPXACT/1685-2014"


@dataclass(slots=True, kw_only=True)
class EnumeratedValues:
    """
    Enumerates specific values that can be assigned to the bit field.

    :ivar enumerated_value: Enumerates specific values that can be
        assigned to the bit field. The name of this enumerated value.
        This may be used as a token in generating code.
    """

    class Meta:
        name = "enumeratedValues"
        namespace = "http://www.accellera.org/XMLSchema/IPXACT/1685-2014"

    enumerated_value: Sequence[EnumeratedValues.EnumeratedValue] = field(
        default_factory=list,
        metadata={
            "name": "enumeratedValue",
            "type": "Element",
            "min_occurs": 1,
        },
    )

    @dataclass(slots=True, kw_only=True)
    class EnumeratedValue:
        """
        :ivar name: Unique name
        :ivar display_name:
        :ivar description:
        :ivar value: Enumerated bit field value.
        :ivar vendor_extensions:
        :ivar usage: Usage for the enumeration. 'read' for a software
            read access. 'write' for a software write access. 'read-
            write' for a software read or write access.
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
        description: None | Description = field(
            default=None,
            metadata={
                "type": "Element",
            },
        )
        value: UnsignedBitVectorExpression = field(
            metadata={
                "type": "Element",
            }
        )
        vendor_extensions: None | VendorExtensions = field(
            default=None,
            metadata={
                "name": "vendorExtensions",
                "type": "Element",
            },
        )
        usage: EnumeratedValueUsage = field(
            default=EnumeratedValueUsage.READ_WRITE,
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

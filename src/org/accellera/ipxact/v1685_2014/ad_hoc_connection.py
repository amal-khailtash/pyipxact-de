from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import ForwardRef

from org.accellera.ipxact.v1685_2014.complex_tied_value_type import (
    ComplexTiedValueType,
)
from org.accellera.ipxact.v1685_2014.description import Description
from org.accellera.ipxact.v1685_2014.display_name import DisplayName
from org.accellera.ipxact.v1685_2014.external_port_reference import (
    ExternalPortReference,
)
from org.accellera.ipxact.v1685_2014.is_present import IsPresent
from org.accellera.ipxact.v1685_2014.part_select import PartSelect
from org.accellera.ipxact.v1685_2014.vendor_extensions import VendorExtensions

__NAMESPACE__ = "http://www.accellera.org/XMLSchema/IPXACT/1685-2014"


@dataclass(slots=True, kw_only=True)
class AdHocConnection:
    """
    Represents an ad-hoc connection between component ports.

    :ivar name: Unique name
    :ivar display_name:
    :ivar description:
    :ivar is_present:
    :ivar tied_value: The logic value of this connection. The value can
        be an unsigned longint expression or open or default. Only valid
        for ports of style wire.
    :ivar port_references: Liist of internal and external port
        references involved in the adhocConnection
    :ivar vendor_extensions:
    :ivar id:
    """

    class Meta:
        name = "adHocConnection"
        namespace = "http://www.accellera.org/XMLSchema/IPXACT/1685-2014"

    name: str = field(
        metadata={
            "type": "Element",
            "white_space": "collapse",
            "pattern": r"\i[\p{L}\p{N}\.\-:_]*",
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
    is_present: None | IsPresent = field(
        default=None,
        metadata={
            "name": "isPresent",
            "type": "Element",
        },
    )
    tied_value: None | ComplexTiedValueType = field(
        default=None,
        metadata={
            "name": "tiedValue",
            "type": "Element",
        },
    )
    port_references: AdHocConnection.PortReferences = field(
        metadata={
            "name": "portReferences",
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
    id: None | str = field(
        default=None,
        metadata={
            "type": "Attribute",
            "namespace": "http://www.w3.org/XML/1998/namespace",
        },
    )

    @dataclass(slots=True, kw_only=True)
    class PortReferences:
        internal_port_reference_or_external_port_reference: Sequence[
            AdHocConnection.PortReferences.InternalPortReference
            | ExternalPortReference
        ] = field(
            default_factory=list,
            metadata={
                "type": "Elements",
                "choices": (
                    {
                        "name": "internalPortReference",
                        "type": ForwardRef(
                            "AdHocConnection.PortReferences.InternalPortReference"
                        ),
                    },
                    {
                        "name": "externalPortReference",
                        "type": ExternalPortReference,
                    },
                ),
            },
        )

        @dataclass(slots=True, kw_only=True)
        class InternalPortReference:
            """
            :ivar is_present:
            :ivar part_select:
            :ivar component_ref: A reference to the instanceName element
                of a component in this design.
            :ivar port_ref: A port on the on the referenced component
                from componentRef.
            :ivar id:
            """

            is_present: None | IsPresent = field(
                default=None,
                metadata={
                    "name": "isPresent",
                    "type": "Element",
                },
            )
            part_select: None | PartSelect = field(
                default=None,
                metadata={
                    "name": "partSelect",
                    "type": "Element",
                },
            )
            component_ref: str = field(
                metadata={
                    "name": "componentRef",
                    "type": "Attribute",
                }
            )
            port_ref: str = field(
                metadata={
                    "name": "portRef",
                    "type": "Attribute",
                    "white_space": "collapse",
                    "pattern": r"\i[\p{L}\p{N}\.\-:_]*",
                }
            )
            id: None | str = field(
                default=None,
                metadata={
                    "type": "Attribute",
                    "namespace": "http://www.w3.org/XML/1998/namespace",
                },
            )

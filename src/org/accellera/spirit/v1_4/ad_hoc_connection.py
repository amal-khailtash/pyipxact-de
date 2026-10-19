from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4"


@dataclass(slots=True, kw_only=True)
class AdHocConnection:
    """
    Represents an ad-hoc connection between component ports.

    :ivar name: Unique name
    :ivar display_name: Element name for display purposes. Typically a
        few words providing a more detailed and/or user-friendly name
        than the spirit:name.
    :ivar description: Full description string, typically for
        documentation
    :ivar internal_port_reference: Defines a reference to a port on a
        component contained within the design.
    :ivar external_port_reference: Defines a reference to a port on the
        component containing this design. The portRef attribute
        indicates the name of the port in the containing component.
    :ivar tied_value: The logic value of this connection. Only valid for
        ports of style wire.
    """

    class Meta:
        name = "adHocConnection"
        namespace = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4"

    name: str = field(
        metadata={
            "type": "Element",
        }
    )
    display_name: None | str = field(
        default=None,
        metadata={
            "name": "displayName",
            "type": "Element",
        },
    )
    description: None | str = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    internal_port_reference: Sequence[
        AdHocConnection.InternalPortReference
    ] = field(
        default_factory=list,
        metadata={
            "name": "internalPortReference",
            "type": "Element",
            "min_occurs": 1,
        },
    )
    external_port_reference: Sequence[
        AdHocConnection.ExternalPortReference
    ] = field(
        default_factory=list,
        metadata={
            "name": "externalPortReference",
            "type": "Element",
        },
    )
    tied_value: None | str = field(
        default=None,
        metadata={
            "name": "tiedValue",
            "type": "Attribute",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
            "pattern": r"[+]?(0x|0X|#)?[0-9a-fA-F]+[kmgtKMGT]?",
        },
    )

    @dataclass(slots=True, kw_only=True)
    class InternalPortReference:
        """
        :ivar component_ref: A reference to the instanceName element of
            a component in this design.
        :ivar port_ref: A port on the on the referenced component from
            componentRef.
        :ivar left: Left index of a vector.
        :ivar right: Right index of a vector.
        """

        component_ref: str = field(
            metadata={
                "name": "componentRef",
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
            }
        )
        port_ref: str = field(
            metadata={
                "name": "portRef",
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
            }
        )
        left: None | int = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
            },
        )
        right: None | int = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
            },
        )

    @dataclass(slots=True, kw_only=True)
    class ExternalPortReference:
        """
        :ivar port_ref: A port on the top level component.
        :ivar left: Left index of a vector.
        :ivar right: Right index of a vector.
        """

        port_ref: str = field(
            metadata={
                "name": "portRef",
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
            }
        )
        left: None | int = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
            },
        )
        right: None | int = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
            },
        )

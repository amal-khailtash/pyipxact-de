from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4"


@dataclass(slots=True, kw_only=True)
class RemapStates:
    """
    Contains a list of remap state names and associated port values.

    :ivar remap_state: Contains a list of ports and values which tell
        the decoder to enter this remap state. The name attribute
        identifies the name of the state
    """

    class Meta:
        name = "remapStates"
        namespace = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4"

    remap_state: Sequence[RemapStates.RemapState] = field(
        default_factory=list,
        metadata={
            "name": "remapState",
            "type": "Element",
            "min_occurs": 1,
        },
    )

    @dataclass(slots=True, kw_only=True)
    class RemapState:
        """
        :ivar name: Unique name
        :ivar display_name: Element name for display purposes. Typically
            a few words providing a more detailed and/or user-friendly
            name than the spirit:name.
        :ivar description: Full description string, typically for
            documentation
        :ivar remap_port: Contains the name and value of a port on the
            component, the value indicates the logic value which this
            port must take to effect the remapping. The portMapRef
            attribute stores the name of the port which takes that
            value.
        """

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
        remap_port: Sequence[RemapStates.RemapState.RemapPort] = field(
            default_factory=list,
            metadata={
                "name": "remapPort",
                "type": "Element",
                "min_occurs": 1,
            },
        )

        @dataclass(slots=True, kw_only=True)
        class RemapPort:
            """
            :ivar value:
            :ivar port_name_ref: This attribute identifies a signal on
                the component which affects the component's memory
                layout
            :ivar port_index: Index for a vectored type port. Must be a
                number between left and right for the port.
            """

            value: str = field(
                default="",
                metadata={
                    "pattern": r"[+]?(0x|0X|#)?[0-9a-fA-F]+[kmgtKMGT]?",
                },
            )
            port_name_ref: str = field(
                metadata={
                    "name": "portNameRef",
                    "type": "Attribute",
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                }
            )
            port_index: None | int = field(
                default=None,
                metadata={
                    "name": "portIndex",
                    "type": "Attribute",
                    "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4",
                },
            )

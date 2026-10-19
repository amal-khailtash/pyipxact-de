from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import ForwardRef

from org.accellera.spirit.v1_0.choices import Choices
from org.accellera.spirit.v1_0.default_value_strength import (
    DefaultValueStrength,
)
from org.accellera.spirit.v1_0.library_ref_type import LibraryRefType
from org.accellera.spirit.v1_0.on_master_value import OnMasterValue
from org.accellera.spirit.v1_0.on_slave_value import OnSlaveValue
from org.accellera.spirit.v1_0.on_system_value import OnSystemValue
from org.accellera.spirit.v1_0.requires_driver import RequiresDriver
from org.accellera.spirit.v1_0.vendor_extensions import VendorExtensions

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0"


@dataclass(slots=True, kw_only=True)
class BusDefinition:
    """
    Defines the signals and high-level function of a bus.

    :ivar vendor: Name of the vendor who supplies this file.
    :ivar library: Name of the logical library this component belongs
        to.  Note that a physical library may contain components from
        multiple logical libraries.  Logical libraries are displayes in
        component browser.
    :ivar name: The name of the object.  Must match the root name of the
        XML file and the directory name it or its version directory
        belongs to.
    :ivar version:
    :ivar direct_connection: When present this element indicates that a
        master interface may be directly connected to a slave interface
        (under certain conditions) for busses of this type.
    :ivar extends: Optional name of bus type that this bus definition is
        compatible with. This bus definition may change the definitions
        of signals in the existing bus definition and add new signals,
        the signals in the original bus are not deleted but may be
        marked illegal to disallow their use.
    :ivar max_masters: Indicates the maximum number of masters this bus
        supports.  Default value of zero means unbounded.
    :ivar max_slaves: Indicates the maximum number of slaves this bus
        supports.  Default value of zero means unbounded.
    :ivar signals: This is a list of logical signals defined by the bus.
    :ivar choices:
    :ivar vendor_extensions:
    """

    class Meta:
        name = "busDefinition"
        namespace = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.0"

    vendor: str = field(
        metadata={
            "type": "Element",
        }
    )
    library: str = field(
        metadata={
            "type": "Element",
        }
    )
    name: str = field(
        metadata={
            "type": "Element",
        }
    )
    version: str = field(
        metadata={
            "type": "Element",
        }
    )
    direct_connection: None | bool = field(
        default=None,
        metadata={
            "name": "directConnection",
            "type": "Element",
        },
    )
    extends: None | LibraryRefType = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    max_masters: None | int = field(
        default=None,
        metadata={
            "name": "maxMasters",
            "type": "Element",
        },
    )
    max_slaves: None | int = field(
        default=None,
        metadata={
            "name": "maxSlaves",
            "type": "Element",
        },
    )
    signals: BusDefinition.Signals = field(
        metadata={
            "type": "Element",
        }
    )
    choices: None | Choices = field(
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

    @dataclass(slots=True, kw_only=True)
    class Signals:
        signal: Sequence[BusDefinition.Signals.Signal] = field(
            default_factory=list,
            metadata={
                "type": "Element",
                "min_occurs": 1,
            },
        )

        @dataclass(slots=True, kw_only=True)
        class Signal:
            """
            :ivar logical_name: The assigned name of this signal in bus
                specifications.
            :ivar choice:
            :ivar requires_driver:
            :ivar on_system: Defines constraints for this signal when
                present in a system bus interface with a matching group
                name.
            :ivar on_master: Defines constraints for this signal when
                present in a master bus interface.
            :ivar on_slave: Defines constraints for this signal when
                present in a slave bus interface.
            :ivar default_value: Default value for the signal when used
                as an input and it ends up  being unconnected. Ignored
                for signals that require a singleShot or clock type
                driver. This value may be overridden by a defaultValue
                on a component pin.
            :ivar vendor_extensions:
            """

            logical_name: str = field(
                metadata={
                    "name": "logicalName",
                    "type": "Element",
                }
            )
            choice: (
                None
                | BusDefinition.Signals.Signal.IsAddress
                | BusDefinition.Signals.Signal.IsData
                | BusDefinition.Signals.Signal.IsClock
                | BusDefinition.Signals.Signal.IsReset
            ) = field(
                default=None,
                metadata={
                    "type": "Elements",
                    "choices": (
                        {
                            "name": "isAddress",
                            "type": ForwardRef(
                                "BusDefinition.Signals.Signal.IsAddress"
                            ),
                        },
                        {
                            "name": "isData",
                            "type": ForwardRef(
                                "BusDefinition.Signals.Signal.IsData"
                            ),
                        },
                        {
                            "name": "isClock",
                            "type": ForwardRef(
                                "BusDefinition.Signals.Signal.IsClock"
                            ),
                        },
                        {
                            "name": "isReset",
                            "type": ForwardRef(
                                "BusDefinition.Signals.Signal.IsReset"
                            ),
                        },
                    ),
                },
            )
            requires_driver: None | RequiresDriver = field(
                default=None,
                metadata={
                    "name": "requiresDriver",
                    "type": "Element",
                },
            )
            on_system: Sequence[BusDefinition.Signals.Signal.OnSystem] = field(
                default_factory=list,
                metadata={
                    "name": "onSystem",
                    "type": "Element",
                },
            )
            on_master: None | BusDefinition.Signals.Signal.OnMaster = field(
                default=None,
                metadata={
                    "name": "onMaster",
                    "type": "Element",
                },
            )
            on_slave: None | BusDefinition.Signals.Signal.OnSlave = field(
                default=None,
                metadata={
                    "name": "onSlave",
                    "type": "Element",
                },
            )
            default_value: None | BusDefinition.Signals.Signal.DefaultValue = (
                field(
                    default=None,
                    metadata={
                        "name": "defaultValue",
                        "type": "Element",
                    },
                )
            )
            vendor_extensions: None | VendorExtensions = field(
                default=None,
                metadata={
                    "name": "vendorExtensions",
                    "type": "Element",
                },
            )

            @dataclass(slots=True, kw_only=True)
            class OnSystem:
                """
                :ivar group: Used to group system signals into different
                    groups within a common bus.
                :ivar bit_width: Number of bits required to represent
                    this signal. Absence of this element indicates
                    unconstrained number of bits, i.e. the component
                    will define th enumber of bits in this signal.
                :ivar direction: If this element is present, the
                    direction of this signal is restricted to the
                    specified value. The direction is relative to the
                    non-mirrored interface.
                """

                group: str = field(
                    metadata={
                        "type": "Element",
                    }
                )
                bit_width: None | int = field(
                    default=None,
                    metadata={
                        "name": "bitWidth",
                        "type": "Element",
                    },
                )
                direction: None | OnSystemValue = field(
                    default=None,
                    metadata={
                        "type": "Element",
                    },
                )

            @dataclass(slots=True, kw_only=True)
            class OnMaster:
                """
                :ivar bit_width: Number of bits required to represent
                    this signal. Absence of this element indicates
                    unconstrained number of bits, i.e. the component
                    will define th enumber of bits in this signal.
                :ivar direction: If this element is present, the
                    direction of this signal is restricted to the
                    specified value. The direction is relative to the
                    non-mirrored interface.
                """

                bit_width: None | int = field(
                    default=None,
                    metadata={
                        "name": "bitWidth",
                        "type": "Element",
                    },
                )
                direction: None | OnMasterValue = field(
                    default=None,
                    metadata={
                        "type": "Element",
                    },
                )

            @dataclass(slots=True, kw_only=True)
            class OnSlave:
                """
                :ivar bit_width: Number of bits required to represent
                    this signal. Absence of this element indicates
                    unconstrained number of bits, i.e. the component
                    will define th enumber of bits in this signal.
                :ivar direction: If this element is present, the
                    direction of this signal is restricted to the
                    specified value. The direction is relative to the
                    non-mirrored interface.
                """

                bit_width: None | int = field(
                    default=None,
                    metadata={
                        "name": "bitWidth",
                        "type": "Element",
                    },
                )
                direction: None | OnSlaveValue = field(
                    default=None,
                    metadata={
                        "type": "Element",
                    },
                )

            @dataclass(slots=True, kw_only=True)
            class DefaultValue:
                strength_or_value: Sequence[DefaultValueStrength | object] = (
                    field(
                        default_factory=list,
                        metadata={
                            "type": "Elements",
                            "choices": (
                                {
                                    "name": "strength",
                                    "type": DefaultValueStrength,
                                    "max_occurs": 2,
                                },
                                {
                                    "name": "value",
                                    "type": object,
                                },
                            ),
                            "max_occurs": 2,
                        },
                    )
                )

            @dataclass(slots=True, kw_only=True)
            class IsAddress:
                value: bool = field()

            @dataclass(slots=True, kw_only=True)
            class IsData:
                value: bool = field()

            @dataclass(slots=True, kw_only=True)
            class IsClock:
                value: bool = field()

            @dataclass(slots=True, kw_only=True)
            class IsReset:
                value: bool = field()

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import ForwardRef

from org.accellera.spirit.v1_4.abstraction_def_port_constraints_type import (
    AbstractionDefPortConstraintsType,
)
from org.accellera.spirit.v1_4.library_ref_type import LibraryRefType
from org.accellera.spirit.v1_4.on_master_direction import OnMasterDirection
from org.accellera.spirit.v1_4.on_slave_direction import OnSlaveDirection
from org.accellera.spirit.v1_4.on_system_direction import OnSystemDirection
from org.accellera.spirit.v1_4.presence import Presence
from org.accellera.spirit.v1_4.requires_driver import RequiresDriver
from org.accellera.spirit.v1_4.service_type import ServiceType
from org.accellera.spirit.v1_4.vendor_extensions import VendorExtensions

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4"


@dataclass(slots=True, kw_only=True)
class AbstractionDefinition:
    """
    Define the ports and other information of a particular abstraction of
    the bus.

    :ivar vendor: Name of the vendor who supplies this file.
    :ivar library: Name of the logical library this element belongs to.
    :ivar name: The name of the object.
    :ivar version: Indicates the version of the named element.
    :ivar bus_type: Reference to the busDefinition that this
        abstractionDefinition implements.
    :ivar extends: Optional name of abstraction type that this
        abstraction definition is compatible with. This abstraction
        definition may change the definitions of ports in the existing
        abstraction definition and add new ports, the ports in the
        original abstraction are not deleted but may be marked illegal
        to disallow their use. This abstraction definition may only
        extend another abstraction definition if the bus type of this
        abstraction definition extends the bus type of the extended
        abstraction definition
    :ivar ports: This is a list of logical ports defined by the bus.
    :ivar description: String for describing the abstraction definition
        to users; no semantic impact
    :ivar vendor_extensions:
    """

    class Meta:
        name = "abstractionDefinition"
        namespace = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.4"

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
    bus_type: LibraryRefType = field(
        metadata={
            "name": "busType",
            "type": "Element",
        }
    )
    extends: None | LibraryRefType = field(
        default=None,
        metadata={
            "type": "Element",
        },
    )
    ports: AbstractionDefinition.Ports = field(
        metadata={
            "type": "Element",
        }
    )
    description: None | str = field(
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
    class Ports:
        port: Sequence[AbstractionDefinition.Ports.Port] = field(
            default_factory=list,
            metadata={
                "type": "Element",
                "min_occurs": 1,
            },
        )

        @dataclass(slots=True, kw_only=True)
        class Port:
            """
            :ivar logical_name: The assigned name of this port in bus
                specifications.
            :ivar display_name: Short description string, typically for
                user interface
            :ivar description: Full description string, typically for
                documentation
            :ivar wire_or_transactional:
            :ivar vendor_extensions:
            """

            logical_name: str = field(
                metadata={
                    "name": "logicalName",
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
            wire_or_transactional: (
                None
                | AbstractionDefinition.Ports.Port.Wire
                | AbstractionDefinition.Ports.Port.Transactional
            ) = field(
                default=None,
                metadata={
                    "type": "Elements",
                    "choices": (
                        {
                            "name": "wire",
                            "type": ForwardRef(
                                "AbstractionDefinition.Ports.Port.Wire"
                            ),
                        },
                        {
                            "name": "transactional",
                            "type": ForwardRef(
                                "AbstractionDefinition.Ports.Port.Transactional"
                            ),
                        },
                    ),
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
            class Wire:
                """
                :ivar qualifier: The type of information this port
                    carries A wire port can carry both address and data,
                    but may not mix this with a clock or reset
                :ivar on_system: Defines constraints for this port when
                    present in a system bus interface with a matching
                    group name.
                :ivar on_master: Defines constraints for this port when
                    present in a master bus interface.
                :ivar on_slave: Defines constraints for this port when
                    present in a slave bus interface.
                :ivar default_value_or_requires_driver:
                """

                qualifier: (
                    None | AbstractionDefinition.Ports.Port.Wire.Qualifier
                ) = field(
                    default=None,
                    metadata={
                        "type": "Element",
                    },
                )
                on_system: Sequence[
                    AbstractionDefinition.Ports.Port.Wire.OnSystem
                ] = field(
                    default_factory=list,
                    metadata={
                        "name": "onSystem",
                        "type": "Element",
                    },
                )
                on_master: (
                    None | AbstractionDefinition.Ports.Port.Wire.OnMaster
                ) = field(
                    default=None,
                    metadata={
                        "name": "onMaster",
                        "type": "Element",
                    },
                )
                on_slave: (
                    None | AbstractionDefinition.Ports.Port.Wire.OnSlave
                ) = field(
                    default=None,
                    metadata={
                        "name": "onSlave",
                        "type": "Element",
                    },
                )
                default_value_or_requires_driver: (
                    None | str | RequiresDriver
                ) = field(
                    default=None,
                    metadata={
                        "type": "Elements",
                        "choices": (
                            {
                                "name": "defaultValue",
                                "type": str,
                                "pattern": r"[+]?(0x|0X|#)?[0-9a-fA-F]+[kmgtKMGT]?",
                            },
                            {
                                "name": "requiresDriver",
                                "type": RequiresDriver,
                            },
                        ),
                    },
                )

                @dataclass(slots=True, kw_only=True)
                class Qualifier:
                    choice: Sequence[
                        AbstractionDefinition.Ports.Port.Wire.Qualifier.IsAddress
                        | AbstractionDefinition.Ports.Port.Wire.Qualifier.IsData
                        | AbstractionDefinition.Ports.Port.Wire.Qualifier.IsClock
                        | AbstractionDefinition.Ports.Port.Wire.Qualifier.IsReset
                    ] = field(
                        default_factory=list,
                        metadata={
                            "type": "Elements",
                            "choices": (
                                {
                                    "name": "isAddress",
                                    "type": ForwardRef(
                                        "AbstractionDefinition.Ports.Port.Wire.Qualifier.IsAddress"
                                    ),
                                },
                                {
                                    "name": "isData",
                                    "type": ForwardRef(
                                        "AbstractionDefinition.Ports.Port.Wire.Qualifier.IsData"
                                    ),
                                },
                                {
                                    "name": "isClock",
                                    "type": ForwardRef(
                                        "AbstractionDefinition.Ports.Port.Wire.Qualifier.IsClock"
                                    ),
                                },
                                {
                                    "name": "isReset",
                                    "type": ForwardRef(
                                        "AbstractionDefinition.Ports.Port.Wire.Qualifier.IsReset"
                                    ),
                                },
                            ),
                            "max_occurs": 2,
                        },
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

                @dataclass(slots=True, kw_only=True)
                class OnSystem:
                    """
                    :ivar group: Used to group system ports into
                        different groups within a common bus.
                    :ivar presence:
                    :ivar width: Number of bits required to represent
                        this port. Absence of this element indicates
                        unconstrained number of bits, i.e. the component
                        will define the number of bits in this port. The
                        logical numbering of the port starts at 0 to
                        width-1.
                    :ivar direction: If this element is present, the
                        direction of this port is restricted to the
                        specified value. The direction is relative to
                        the non-mirrored interface.
                    :ivar mode_constraints: Specifies default
                        constraints for the enclosing wire type port. If
                        the mirroredModeConstraints element is not
                        defined, then these constraints applied to this
                        port when it appears in a 'mode' bus interface
                        or a mirrored-'mode' bus interface. Otherwise
                        they only apply when the port appears in a
                        'mode' bus interface.
                    :ivar mirrored_mode_constraints: Specifies default
                        constraints for the enclosing wire type port
                        when it appears in a mirrored-'mode' bus
                        interface.
                    """

                    group: str = field(
                        metadata={
                            "type": "Element",
                        }
                    )
                    presence: None | Presence = field(
                        default=None,
                        metadata={
                            "type": "Element",
                        },
                    )
                    width: None | int = field(
                        default=None,
                        metadata={
                            "type": "Element",
                        },
                    )
                    direction: None | OnSystemDirection = field(
                        default=None,
                        metadata={
                            "type": "Element",
                        },
                    )
                    mode_constraints: (
                        None | AbstractionDefPortConstraintsType
                    ) = field(
                        default=None,
                        metadata={
                            "name": "modeConstraints",
                            "type": "Element",
                        },
                    )
                    mirrored_mode_constraints: (
                        None | AbstractionDefPortConstraintsType
                    ) = field(
                        default=None,
                        metadata={
                            "name": "mirroredModeConstraints",
                            "type": "Element",
                        },
                    )

                @dataclass(slots=True, kw_only=True)
                class OnMaster:
                    """
                    :ivar presence:
                    :ivar width: Number of bits required to represent
                        this port. Absence of this element indicates
                        unconstrained number of bits, i.e. the component
                        will define the number of bits in this port. The
                        logical numbering of the port starts at 0 to
                        width-1.
                    :ivar direction: If this element is present, the
                        direction of this port is restricted to the
                        specified value. The direction is relative to
                        the non-mirrored interface.
                    :ivar mode_constraints: Specifies default
                        constraints for the enclosing wire type port. If
                        the mirroredModeConstraints element is not
                        defined, then these constraints applied to this
                        port when it appears in a 'mode' bus interface
                        or a mirrored-'mode' bus interface. Otherwise
                        they only apply when the port appears in a
                        'mode' bus interface.
                    :ivar mirrored_mode_constraints: Specifies default
                        constraints for the enclosing wire type port
                        when it appears in a mirrored-'mode' bus
                        interface.
                    """

                    presence: None | Presence = field(
                        default=None,
                        metadata={
                            "type": "Element",
                        },
                    )
                    width: None | int = field(
                        default=None,
                        metadata={
                            "type": "Element",
                        },
                    )
                    direction: None | OnMasterDirection = field(
                        default=None,
                        metadata={
                            "type": "Element",
                        },
                    )
                    mode_constraints: (
                        None | AbstractionDefPortConstraintsType
                    ) = field(
                        default=None,
                        metadata={
                            "name": "modeConstraints",
                            "type": "Element",
                        },
                    )
                    mirrored_mode_constraints: (
                        None | AbstractionDefPortConstraintsType
                    ) = field(
                        default=None,
                        metadata={
                            "name": "mirroredModeConstraints",
                            "type": "Element",
                        },
                    )

                @dataclass(slots=True, kw_only=True)
                class OnSlave:
                    """
                    :ivar presence:
                    :ivar width: Number of bits required to represent
                        this port. Absence of this element indicates
                        unconstrained number of bits, i.e. the component
                        will define the number of bits in this port. The
                        logical numbering of the port starts at 0 to
                        width-1.
                    :ivar direction: If this element is present, the
                        direction of this port is restricted to the
                        specified value. The direction is relative to
                        the non-mirrored interface.
                    :ivar mode_constraints: Specifies default
                        constraints for the enclosing wire type port. If
                        the mirroredModeConstraints element is not
                        defined, then these constraints applied to this
                        port when it appears in a 'mode' bus interface
                        or a mirrored-'mode' bus interface. Otherwise
                        they only apply when the port appears in a
                        'mode' bus interface.
                    :ivar mirrored_mode_constraints: Specifies default
                        constraints for the enclosing wire type port
                        when it appears in a mirrored-'mode' bus
                        interface.
                    """

                    presence: None | Presence = field(
                        default=None,
                        metadata={
                            "type": "Element",
                        },
                    )
                    width: None | int = field(
                        default=None,
                        metadata={
                            "type": "Element",
                        },
                    )
                    direction: None | OnSlaveDirection = field(
                        default=None,
                        metadata={
                            "type": "Element",
                        },
                    )
                    mode_constraints: (
                        None | AbstractionDefPortConstraintsType
                    ) = field(
                        default=None,
                        metadata={
                            "name": "modeConstraints",
                            "type": "Element",
                        },
                    )
                    mirrored_mode_constraints: (
                        None | AbstractionDefPortConstraintsType
                    ) = field(
                        default=None,
                        metadata={
                            "name": "mirroredModeConstraints",
                            "type": "Element",
                        },
                    )

            @dataclass(slots=True, kw_only=True)
            class Transactional:
                """
                :ivar qualifier: The type of information this port
                    carries A transactional port can carry both address
                    and data information.
                :ivar on_system: Defines constraints for this port when
                    present in a system bus interface with a matching
                    group name.
                :ivar on_master: Defines constraints for this port when
                    present in a master bus interface.
                :ivar on_slave: Defines constraints for this port when
                    present in a slave bus interface.
                """

                qualifier: (
                    None
                    | AbstractionDefinition.Ports.Port.Transactional.Qualifier
                ) = field(
                    default=None,
                    metadata={
                        "type": "Element",
                    },
                )
                on_system: Sequence[
                    AbstractionDefinition.Ports.Port.Transactional.OnSystem
                ] = field(
                    default_factory=list,
                    metadata={
                        "name": "onSystem",
                        "type": "Element",
                    },
                )
                on_master: (
                    None
                    | AbstractionDefinition.Ports.Port.Transactional.OnMaster
                ) = field(
                    default=None,
                    metadata={
                        "name": "onMaster",
                        "type": "Element",
                    },
                )
                on_slave: (
                    None
                    | AbstractionDefinition.Ports.Port.Transactional.OnSlave
                ) = field(
                    default=None,
                    metadata={
                        "name": "onSlave",
                        "type": "Element",
                    },
                )

                @dataclass(slots=True, kw_only=True)
                class Qualifier:
                    """
                    :ivar is_address: If this element is present, the
                        port contains address information.
                    :ivar is_data: If this element is present, the port
                        contains data information.
                    """

                    is_address: None | bool = field(
                        default=None,
                        metadata={
                            "name": "isAddress",
                            "type": "Element",
                        },
                    )
                    is_data: None | bool = field(
                        default=None,
                        metadata={
                            "name": "isData",
                            "type": "Element",
                        },
                    )

                @dataclass(slots=True, kw_only=True)
                class OnSystem:
                    """
                    :ivar group: Used to group system ports into
                        different groups within a common bus.
                    :ivar presence:
                    :ivar service: The service that this transactional
                        port can provide or requires.
                    """

                    group: str = field(
                        metadata={
                            "type": "Element",
                        }
                    )
                    presence: None | Presence = field(
                        default=None,
                        metadata={
                            "type": "Element",
                        },
                    )
                    service: ServiceType = field(
                        metadata={
                            "type": "Element",
                        }
                    )

                @dataclass(slots=True, kw_only=True)
                class OnMaster:
                    """
                    :ivar presence:
                    :ivar service: The service that this transactional
                        port can provide or requires.
                    """

                    presence: None | Presence = field(
                        default=None,
                        metadata={
                            "type": "Element",
                        },
                    )
                    service: ServiceType = field(
                        metadata={
                            "type": "Element",
                        }
                    )

                @dataclass(slots=True, kw_only=True)
                class OnSlave:
                    """
                    :ivar presence:
                    :ivar service: The service that this transactional
                        port can provide or requires.
                    """

                    presence: None | Presence = field(
                        default=None,
                        metadata={
                            "type": "Element",
                        },
                    )
                    service: ServiceType = field(
                        metadata={
                            "type": "Element",
                        }
                    )

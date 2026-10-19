from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from org.accellera.spirit.v1_5.service_type_initiative import (
    ServiceTypeInitiative,
)
from org.accellera.spirit.v1_5.vendor_extensions import VendorExtensions

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5"


@dataclass(slots=True, kw_only=True)
class ServiceType:
    """
    The service that this transactional port can provide or requires.

    :ivar initiative: If this element is present, the type of access is
        restricted to the specified value.
    :ivar type_name: Defines the name of the transactional interface
        type.
    :ivar vendor_extensions:
    """

    class Meta:
        name = "serviceType"

    initiative: ServiceTypeInitiative = field(
        default=ServiceTypeInitiative.REQUIRES,
        metadata={
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
        },
    )
    type_name: Sequence[ServiceType.TypeName] = field(
        default_factory=list,
        metadata={
            "name": "typeName",
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
            "min_occurs": 1,
        },
    )
    vendor_extensions: None | VendorExtensions = field(
        default=None,
        metadata={
            "name": "vendorExtensions",
            "type": "Element",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
        },
    )

    @dataclass(slots=True, kw_only=True)
    class TypeName:
        """
        :ivar value:
        :ivar implicit: Defines that the typeName supplied for this
            service is implicit and a netlister should not declare this
            service in a language specific top-level netlist
        """

        value: str = field(default="")
        implicit: bool = field(
            default=False,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5",
            },
        )

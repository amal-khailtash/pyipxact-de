from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from org.accellera.spirit.v1685_2009.ve.ams.view_name_ref import ViewNameRef

__NAMESPACE__ = (
    "http://www.accellera.org/XMLSchema/SPIRIT/1685-2009-VE/AMS-1.0"
)


@dataclass(slots=True, kw_only=True)
class DomainTypeDef:
    """
    Definition of a single wire type definition that can relate to multiple
    views.

    :ivar type_name: The name of the domain type. Examples could be
        ddiscrete, electrical, ...
    :ivar type_definition: Where the definition of the type is
        contained. For Verilog-AMS, it is the include file required.
    :ivar view_name_ref:
    """

    class Meta:
        name = "domainTypeDef"
        namespace = (
            "http://www.accellera.org/XMLSchema/SPIRIT/1685-2009-VE/AMS-1.0"
        )

    type_name: str = field(
        metadata={
            "name": "typeName",
            "type": "Element",
        }
    )
    type_definition: Sequence[str] = field(
        default_factory=list,
        metadata={
            "name": "typeDefinition",
            "type": "Element",
        },
    )
    view_name_ref: Sequence[ViewNameRef] = field(
        default_factory=list,
        metadata={
            "name": "viewNameRef",
            "type": "Element",
            "namespace": "http://www.accellera.org/XMLSchema/SPIRIT/1685-2009-VE",
            "min_occurs": 1,
        },
    )

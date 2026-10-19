from __future__ import annotations

from dataclasses import dataclass, field

from org.accellera.ipxact.v1685_2022.initiative_type import InitiativeType

__NAMESPACE__ = "http://www.accellera.org/XMLSchema/IPXACT/1685-2022"


@dataclass(slots=True, kw_only=True)
class Initiative:
    """
    If this element is present, the type of access is restricted to the
    specified value.
    """

    class Meta:
        name = "initiative"
        namespace = "http://www.accellera.org/XMLSchema/IPXACT/1685-2022"

    value: InitiativeType = field()

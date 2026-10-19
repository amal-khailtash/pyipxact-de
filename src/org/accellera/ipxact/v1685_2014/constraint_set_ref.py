from __future__ import annotations

from dataclasses import dataclass, field

from org.accellera.ipxact.v1685_2014.is_present import IsPresent

__NAMESPACE__ = "http://www.accellera.org/XMLSchema/IPXACT/1685-2014"


@dataclass(slots=True, kw_only=True)
class ConstraintSetRef:
    """
    A reference to a set of port constraints.
    """

    class Meta:
        name = "constraintSetRef"
        namespace = "http://www.accellera.org/XMLSchema/IPXACT/1685-2014"

    local_name: str = field(
        metadata={
            "name": "localName",
            "type": "Element",
        }
    )
    is_present: None | IsPresent = field(
        default=None,
        metadata={
            "name": "isPresent",
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

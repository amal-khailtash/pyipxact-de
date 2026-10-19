from __future__ import annotations

from dataclasses import dataclass, field

from org.accellera.ipxact.v1685_2022.string_expression import StringExpression

__NAMESPACE__ = "http://www.accellera.org/XMLSchema/IPXACT/1685-2022"


@dataclass(slots=True, kw_only=True)
class PortPathSegmentType(StringExpression):
    """
    Identifies one level of hierarchy in the view specifed by viewNameRef.

    This is a simple name and optionally some indices into a multi
    dimensional element.
    """

    class Meta:
        name = "portPathSegmentType"

    id: None | str = field(
        default=None,
        metadata={
            "type": "Attribute",
            "namespace": "http://www.w3.org/XML/1998/namespace",
        },
    )

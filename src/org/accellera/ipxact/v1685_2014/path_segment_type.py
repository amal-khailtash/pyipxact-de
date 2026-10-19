from __future__ import annotations

from dataclasses import dataclass, field

from org.accellera.ipxact.v1685_2014.indices_type import IndicesType

__NAMESPACE__ = "http://www.accellera.org/XMLSchema/IPXACT/1685-2014"


@dataclass(slots=True, kw_only=True)
class PathSegmentType:
    """
    Identifies one level of hierarchy in the view specifed by viewNameRef.

    This is a simple name and optionally some indices into a multi
    dimensional element.

    :ivar path_segment_name: One section of a HDL path
    :ivar indices: Specifies a multi-dimensional index into
        pathSegementName
    :ivar id:
    """

    class Meta:
        name = "pathSegmentType"

    path_segment_name: str = field(
        metadata={
            "name": "pathSegmentName",
            "type": "Element",
            "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2014",
        }
    )
    indices: None | IndicesType = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2014",
        },
    )
    id: None | str = field(
        default=None,
        metadata={
            "type": "Attribute",
            "namespace": "http://www.w3.org/XML/1998/namespace",
        },
    )

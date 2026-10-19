from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from org.accellera.ipxact.v1685_2022.path_segment_type import PathSegmentType
from org.accellera.ipxact.v1685_2022.vendor_extensions import VendorExtensions

__NAMESPACE__ = "http://www.accellera.org/XMLSchema/IPXACT/1685-2022"


@dataclass(slots=True, kw_only=True)
class SimpleAccessHandle:
    """
    :ivar view_ref: A list of views this accessHandle is applicable to.
        Note this element is optional, if it is not present the
        accessHandle applies to all views.
    :ivar path_segments: An ordered list of pathSegment elements. When
        concatenated with a desired separator the elements in this form
        a HDL path for the parent slice into the referenced view.
    :ivar vendor_extensions:
    :ivar id:
    """

    class Meta:
        name = "simpleAccessHandle"

    view_ref: Sequence[SimpleAccessHandle.ViewRef] = field(
        default_factory=list,
        metadata={
            "name": "viewRef",
            "type": "Element",
            "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
        },
    )
    path_segments: SimpleAccessHandle.PathSegments = field(
        metadata={
            "name": "pathSegments",
            "type": "Element",
            "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
        }
    )
    vendor_extensions: None | VendorExtensions = field(
        default=None,
        metadata={
            "name": "vendorExtensions",
            "type": "Element",
            "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
        },
    )
    id: None | str = field(
        default=None,
        metadata={
            "type": "Attribute",
            "namespace": "http://www.w3.org/XML/1998/namespace",
        },
    )

    @dataclass(slots=True, kw_only=True)
    class ViewRef:
        value: str = field(default="")
        id: None | str = field(
            default=None,
            metadata={
                "type": "Attribute",
                "namespace": "http://www.w3.org/XML/1998/namespace",
            },
        )

    @dataclass(slots=True, kw_only=True)
    class PathSegments:
        path_segment: Sequence[PathSegmentType] = field(
            default_factory=list,
            metadata={
                "name": "pathSegment",
                "type": "Element",
                "namespace": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022",
                "min_occurs": 1,
            },
        )

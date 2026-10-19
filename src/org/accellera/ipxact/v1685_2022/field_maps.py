from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from org.accellera.ipxact.v1685_2022.field_map import FieldMap

__NAMESPACE__ = "http://www.accellera.org/XMLSchema/IPXACT/1685-2022"


@dataclass(slots=True, kw_only=True)
class FieldMaps:
    """
    Listing of maps between component port slices and field slices.
    """

    class Meta:
        name = "fieldMaps"
        namespace = "http://www.accellera.org/XMLSchema/IPXACT/1685-2022"

    field_map: Sequence[FieldMap] = field(
        default_factory=list,
        metadata={
            "name": "fieldMap",
            "type": "Element",
            "min_occurs": 1,
        },
    )

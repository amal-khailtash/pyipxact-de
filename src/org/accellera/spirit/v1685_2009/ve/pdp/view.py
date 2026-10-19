from __future__ import annotations

from dataclasses import dataclass, field

from org.accellera.spirit.v1685_2009.ve.pdp.area_estimation import (
    AreaEstimation,
)
from org.accellera.spirit.v1685_2009.ve.pdp.technology_name import (
    TechnologyName,
)

__NAMESPACE__ = "http://www.accellera.org/XMLSchema/SPIRIT/1685-2009-VE"


@dataclass(slots=True, kw_only=True)
class View:
    """
    View extension.
    """

    class Meta:
        name = "view"
        namespace = "http://www.accellera.org/XMLSchema/SPIRIT/1685-2009-VE"

    technology_name: None | TechnologyName = field(
        default=None,
        metadata={
            "name": "technologyName",
            "type": "Element",
            "namespace": "http://www.accellera.org/XMLSchema/SPIRIT/1685-2009-VE/PDP-1.0",
        },
    )
    area_estimation: None | AreaEstimation = field(
        default=None,
        metadata={
            "name": "areaEstimation",
            "type": "Element",
            "namespace": "http://www.accellera.org/XMLSchema/SPIRIT/1685-2009-VE/PDP-1.0",
        },
    )

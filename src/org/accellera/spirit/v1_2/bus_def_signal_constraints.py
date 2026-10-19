from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from org.accellera.spirit.v1_2.design_rule_constraints import (
    DesignRuleConstraints,
)
from org.accellera.spirit.v1_2.drive_constraint import DriveConstraint
from org.accellera.spirit.v1_2.load_constraint import LoadConstraint
from org.accellera.spirit.v1_2.timing_constraint import TimingConstraint

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2"


@dataclass(slots=True, kw_only=True)
class BusDefSignalConstraints:
    """
    Defines constraints that apply to a signal in a bus definition.

    If multiple busDefSignalConstraints are used, each must have a unique
    value of the constraintSet attribute. These constraints are carried
    over to the associated component signal as default values.
    """

    class Meta:
        name = "busDefSignalConstraints"
        namespace = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2"

    timing_constraint: Sequence[TimingConstraint] = field(
        default_factory=list,
        metadata={
            "name": "timingConstraint",
            "type": "Element",
        },
    )
    design_rule_constraints: None | DesignRuleConstraints = field(
        default=None,
        metadata={
            "name": "designRuleConstraints",
            "type": "Element",
        },
    )
    drive_constraint: None | DriveConstraint = field(
        default=None,
        metadata={
            "name": "driveConstraint",
            "type": "Element",
        },
    )
    load_constraint: None | LoadConstraint = field(
        default=None,
        metadata={
            "name": "loadConstraint",
            "type": "Element",
        },
    )
    constraint_set_id: str = field(
        default="default",
        metadata={
            "name": "constraintSetId",
            "type": "Attribute",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.2",
        },
    )

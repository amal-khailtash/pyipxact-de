from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from org.accellera.spirit.v1_1.design_rule_constraints import (
    DesignRuleConstraints,
)
from org.accellera.spirit.v1_1.drive_constraint import DriveConstraint
from org.accellera.spirit.v1_1.load_constraint import LoadConstraint
from org.accellera.spirit.v1_1.timing_constraint import TimingConstraint

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.1"


@dataclass(slots=True, kw_only=True)
class SignalConstraints:
    """
    Defines constraints that apply to a component signal.

    If multiple signalConstraints elements are used, each must have a
    unique value for the constraintSet attribute.
    """

    class Meta:
        name = "signalConstraints"
        namespace = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.1"

    drive_constraint_or_load_constraint: (
        None | DriveConstraint | LoadConstraint
    ) = field(
        default=None,
        metadata={
            "type": "Elements",
            "choices": (
                {
                    "name": "driveConstraint",
                    "type": DriveConstraint,
                },
                {
                    "name": "loadConstraint",
                    "type": LoadConstraint,
                },
            ),
        },
    )
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
    constraint_set_id: str = field(
        default="default",
        metadata={
            "name": "constraintSetId",
            "type": "Attribute",
            "namespace": "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.1",
        },
    )

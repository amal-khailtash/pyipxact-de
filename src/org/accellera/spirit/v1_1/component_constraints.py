from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from org.accellera.spirit.v1_1.design_rule_constraints import (
    DesignRuleConstraints,
)
from org.accellera.spirit.v1_1.false_path import FalsePath
from org.accellera.spirit.v1_1.multi_cycle_path import MultiCyclePath
from org.accellera.spirit.v1_1.timed_path import TimedPath

__NAMESPACE__ = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.1"


@dataclass(slots=True, kw_only=True)
class ComponentConstraints:
    """
    Defines the set of implementation constraints associated with a
    component.

    If multiple componentConstraints elements are used, each must have a
    unique value for the constraintSet attribute.
    """

    class Meta:
        name = "componentConstraints"
        namespace = "http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.1"

    design_rule_constraints: None | DesignRuleConstraints = field(
        default=None,
        metadata={
            "name": "designRuleConstraints",
            "type": "Element",
        },
    )
    false_path: Sequence[FalsePath] = field(
        default_factory=list,
        metadata={
            "name": "falsePath",
            "type": "Element",
        },
    )
    multi_cycle_path: Sequence[MultiCyclePath] = field(
        default_factory=list,
        metadata={
            "name": "multiCyclePath",
            "type": "Element",
        },
    )
    timed_path: Sequence[TimedPath] = field(
        default_factory=list,
        metadata={
            "name": "timedPath",
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

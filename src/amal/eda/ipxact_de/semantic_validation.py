"""Scoped IEEE 1685-2022 semantic checks, independent of XSD validation and TGI handles."""

from dataclasses import dataclass

from org.accellera.ipxact.v1685_2022 import AbstractionDefinition, Component
from org.accellera.ipxact.v1685_2022.clock_driver import ClockDriver
from org.accellera.ipxact.v1685_2022.component_port_direction_type import ComponentPortDirectionType
from org.accellera.ipxact.v1685_2022.direction import Direction
from org.accellera.ipxact.v1685_2022.drive_constraint import DriveConstraint
from org.accellera.ipxact.v1685_2022.load_constraint import LoadConstraint
from org.accellera.ipxact.v1685_2022.port_wire_type import PortWireType
from org.accellera.ipxact.v1685_2022.wire import Wire


@dataclass(frozen=True, slots=True)
class SemanticIssue:
    """A standard rule violation and an XPath using the ``ipxact`` namespace prefix."""

    rule_id: str
    path: str
    message: str


@dataclass(frozen=True, slots=True)
class SemanticValidationResult:
    """Result for explicitly listed rules; success does not imply complete semantic conformance."""

    checked_rules: tuple[str, ...]
    issues: tuple[SemanticIssue, ...]

    @property
    def ok(self) -> bool:
        return not self.issues


_ABSTRACTION_CONSTRAINT_RULES = ("SCR 12.3", "SCR 12.4", "SCR 12.5", "SCR 12.6", "SCR 12.8")


def validate_abstraction_constraints(document: AbstractionDefinition) -> SemanticValidationResult:
    """Check direction constraints and local clock references (IEEE Annex B.2.12).

    Check normal/mirrored wire modes and timing clock references to another logical
    port containing an isClock qualifier. This function reads the supplied 2022
    model without mutating it. It does not resolve inheritance or configurations,
    evaluate expressions, or replace XSD validation.
    """
    if not isinstance(document, AbstractionDefinition):
        raise TypeError("Expected an IEEE 1685-2022 AbstractionDefinition")
    ports = document.ports.port if document.ports is not None else []
    issues: list[SemanticIssue] = []
    for port_index, port in enumerate(ports, 1):
        wire = port.wire_or_transactional
        if not isinstance(wire, Wire):
            continue
        port_path = f"/ipxact:abstractionDefinition/ipxact:ports/ipxact:port[{port_index}]/ipxact:wire"
        modes = [("onInitiator", wire.on_initiator), ("onTarget", wire.on_target)]
        modes.extend((f"onSystem[{index}]", mode) for index, mode in enumerate(wire.on_system, 1))
        for mode_name, mode in modes:
            if mode is None:
                continue
            for attr, xml_name, forbidden in (
                ("mode_constraints", "modeConstraints", {
                    Direction.OUT: (DriveConstraint, "driveConstraint", "SCR 12.3"),
                    Direction.IN: (LoadConstraint, "loadConstraint", "SCR 12.4"),
                }),
                ("mirrored_mode_constraints", "mirroredModeConstraints", {
                    Direction.OUT: (LoadConstraint, "loadConstraint", "SCR 12.5"),
                    Direction.IN: (DriveConstraint, "driveConstraint", "SCR 12.6"),
                }),
            ):
                constraints = getattr(mode, attr)
                if constraints is None:
                    continue
                path = f"{port_path}/ipxact:{mode_name}/ipxact:{xml_name}"
                restriction = forbidden.get(mode.direction)
                if restriction is not None:
                    constraint_type, child_name, rule_id = restriction
                    child_index = 0
                    for child in constraints.drive_constraint_or_load_constraint:
                        if isinstance(child, constraint_type):
                            child_index += 1
                            issues.append(SemanticIssue(
                                rule_id, f"{path}/ipxact:{child_name}[{child_index}]",
                                f"Logical port {port.logical_name!r} with direction {mode.direction.value!r} "
                                f"shall not contain {child_name} in {xml_name}.",
                            ))
                for index, timing in enumerate(constraints.timing_constraint, 1):
                    targets = [candidate for candidate in ports
                               if candidate is not port and candidate.logical_name == timing.clock_name]
                    if not any(candidate.wire_or_transactional is not None
                               and candidate.wire_or_transactional.qualifier is not None
                               and candidate.wire_or_transactional.qualifier.is_clock is not None
                               for candidate in targets):
                        issues.append(SemanticIssue(
                            "SCR 12.8", f"{path}/ipxact:timingConstraint[{index}]/@clockName",
                            f"Clock {timing.clock_name!r} shall reference another logical port "
                            "containing an isClock qualifier.",
                        ))
    return SemanticValidationResult(_ABSTRACTION_CONSTRAINT_RULES, tuple(issues))


def validate_component_constraints(document: Component) -> SemanticValidationResult:
    """Check local component direction and clock rules SCR 12.1, 12.2 and 12.7.

    Clock drivers without clockName use their containing port name. If any clock
    driver exists, timing references must match a driver clock name; otherwise
    they must reference another component port. Expressions, configured views,
    driver bit widths and inheritance remain outside this scoped validation.
    """
    if not isinstance(document, Component):
        raise TypeError("Expected an IEEE 1685-2022 Component")
    ports = document.model.ports.port if document.model is not None and document.model.ports is not None else []
    clock_names: set[str] = set()
    for port in ports:
        wire = port.wire_or_transactional_or_structured
        if isinstance(wire, PortWireType) and wire.drivers is not None:
            for driver in wire.drivers.driver:
                clock = driver.default_value_or_clock_driver_or_single_shot_driver
                if isinstance(clock, ClockDriver):
                    clock_names.add(clock.clock_name if clock.clock_name is not None else port.name)
    if document.other_clock_drivers is not None:
        clock_names.update(clock.clock_name for clock in document.other_clock_drivers.other_clock_driver)
    issues: list[SemanticIssue] = []
    for port_index, port in enumerate(ports, 1):
        wire = port.wire_or_transactional_or_structured
        if not isinstance(wire, PortWireType) or wire.constraint_sets is None:
            continue
        port_path = f"/ipxact:component/ipxact:model/ipxact:ports/ipxact:port[{port_index}]/ipxact:wire"
        for index, constraints in enumerate(wire.constraint_sets.constraint_set, 1):
            path = f"{port_path}/ipxact:constraintSets/ipxact:constraintSet[{index}]"
            for direction, attr, child, rule in (
                (ComponentPortDirectionType.OUT, "drive_constraint", "driveConstraint", "SCR 12.1"),
                (ComponentPortDirectionType.IN, "load_constraint", "loadConstraint", "SCR 12.2"),
            ):
                if wire.direction == direction and getattr(constraints, attr) is not None:
                    issues.append(SemanticIssue(
                        rule, f"{path}/ipxact:{child}",
                        f"Component port {port.name!r} with direction {direction.value!r} "
                        f"shall not contain {child}.",
                    ))
            for timing_index, timing in enumerate(constraints.timing_constraint, 1):
                valid = timing.clock_name in clock_names if clock_names else any(
                    candidate is not port and candidate.name == timing.clock_name for candidate in ports
                )
                if not valid:
                    requirement = "a component clock driver" if clock_names else "another component port"
                    issues.append(SemanticIssue(
                        "SCR 12.7", f"{path}/ipxact:timingConstraint[{timing_index}]/@clockName",
                        f"Clock {timing.clock_name!r} shall reference {requirement}.",
                    ))
    return SemanticValidationResult(("SCR 12.1", "SCR 12.2", "SCR 12.7"), tuple(issues))

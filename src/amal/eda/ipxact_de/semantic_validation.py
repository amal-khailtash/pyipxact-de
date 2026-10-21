"""Scoped IEEE 1685-2022 semantic checks, independent of XSD validation and TGI handles."""

from dataclasses import dataclass

from org.accellera.ipxact.v1685_2022 import AbstractionDefinition
from org.accellera.ipxact.v1685_2022.direction import Direction
from org.accellera.ipxact.v1685_2022.drive_constraint import DriveConstraint
from org.accellera.ipxact.v1685_2022.load_constraint import LoadConstraint
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

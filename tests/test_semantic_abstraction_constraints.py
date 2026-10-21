"""IEEE constraint diagnostics cover all wire loci and normal/mirrored alternatives."""

import pytest
from lxml import etree

from amal.eda.ipxact_de.semantic_validation import validate_abstraction_constraints
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import AbstractionDefinition, LibraryRefType, QualifierType
from org.accellera.ipxact.v1685_2022.abstraction_def_port_constraints_type import AbstractionDefPortConstraintsType
from org.accellera.ipxact.v1685_2022.cell_function_value_type import CellFunctionValueType
from org.accellera.ipxact.v1685_2022.cell_specification import CellSpecification
from org.accellera.ipxact.v1685_2022.direction import Direction
from org.accellera.ipxact.v1685_2022.drive_constraint import DriveConstraint
from org.accellera.ipxact.v1685_2022.load_constraint import LoadConstraint
from org.accellera.ipxact.v1685_2022.timing_constraint import TimingConstraint
from org.accellera.ipxact.v1685_2022.unsigned_positive_int_expression import UnsignedPositiveIntExpression
from org.accellera.ipxact.v1685_2022.wire import Wire

NS = {"ipxact": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022"}


def make_document(mode):
    return AbstractionDefinition(
        vendor="v", library="l", name="a", version="1",
        bus_type=LibraryRefType(vendor="v", library="l", name="b", version="1"),
        ports=AbstractionDefinition.Ports(port=[AbstractionDefinition.Ports.Port(
            logical_name="data", wire_or_transactional=Wire(on_initiator=mode),
        )]),
    )


def make_constraints():
    cell = CellSpecification(cell_function_or_cell_class=CellSpecification.CellFunction(
        value=CellFunctionValueType.BUF,
    ))
    return AbstractionDefPortConstraintsType(drive_constraint_or_load_constraint=[
        DriveConstraint(cell_specification=cell),
        LoadConstraint(cell_specification=cell, count=UnsignedPositiveIntExpression(value="1")),
    ])


@pytest.mark.parametrize("locus", ["on_initiator", "on_target", "on_system"])
@pytest.mark.parametrize("attr,direction,rule,child", [
    ("mode_constraints", Direction.OUT, "SCR 12.3", "driveConstraint"),
    ("mode_constraints", Direction.IN, "SCR 12.4", "loadConstraint"),
    ("mirrored_mode_constraints", Direction.OUT, "SCR 12.5", "loadConstraint"),
    ("mirrored_mode_constraints", Direction.IN, "SCR 12.6", "driveConstraint"),
])
def test_direction_rules_after_schema_valid_reload(locus, attr, direction, rule, child):
    mode_type = {"on_initiator": Wire.OnInitiator, "on_target": Wire.OnTarget, "on_system": Wire.OnSystem}[locus]
    mode = mode_type(direction=direction, **({"group": "system"} if locus == "on_system" else {}))
    if attr == "mirrored_mode_constraints":
        mode.mode_constraints = AbstractionDefPortConstraintsType(
            timing_constraint=[TimingConstraint(value=0.0, clock_name="clk")],
        )
    setattr(mode, attr, make_constraints())
    document = make_document(None)
    document.ports.port.append(AbstractionDefinition.Ports.Port(
        logical_name="clk", wire_or_transactional=Wire(qualifier=QualifierType(is_clock=True)),
    ))
    wire = document.ports.port[0].wire_or_transactional
    setattr(wire, locus, [mode] if locus == "on_system" else mode)
    xml = XmlDocument.serializer().render(document)
    schema = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))
    tree = etree.fromstring(xml.encode())
    assert schema.validate(tree), schema.error_log
    loaded = XmlDocument.parser().from_string(xml, AbstractionDefinition)
    result = validate_abstraction_constraints(loaded)
    assert not result.ok
    assert len(result.issues) == 1
    issue = result.issues[0]
    assert issue.rule_id == rule
    assert child in issue.path
    assert len(tree.xpath(issue.path, namespaces=NS)) == 1
    assert XmlDocument.serializer().render(loaded) == xml


@pytest.mark.parametrize("direction", [Direction.INOUT, None])
def test_unspecified_and_bidirectional_modes_have_no_direction_restriction(direction):
    mode = Wire.OnInitiator(direction=direction, mode_constraints=make_constraints(),
                            mirrored_mode_constraints=make_constraints())
    assert validate_abstraction_constraints(make_document(mode)).ok


@pytest.mark.parametrize("qualifier", [None, QualifierType(), QualifierType(is_clock=True),
                                       QualifierType(is_clock=False)])
@pytest.mark.parametrize("reference", ["clk", "missing", "data"])
def test_clock_reference_requires_another_port_with_clock_element(qualifier, reference):
    mode = Wire.OnInitiator(mode_constraints=AbstractionDefPortConstraintsType(
        timing_constraint=[TimingConstraint(value=0.0, clock_name=reference)],
    ))
    document = make_document(mode)
    document.ports.port.append(AbstractionDefinition.Ports.Port(
        logical_name="clk", wire_or_transactional=Wire(qualifier=qualifier),
    ))
    document.ports.port[0].wire_or_transactional.qualifier = QualifierType(is_clock=True)
    result = validate_abstraction_constraints(document)
    valid = reference == "clk" and qualifier is not None and qualifier.is_clock is not None
    assert result.ok is valid
    if not valid:
        assert [issue.rule_id for issue in result.issues] == ["SCR 12.8"]
        assert result.issues[0].path.endswith("timingConstraint[1]/@clockName")


def test_mirrored_system_timing_can_reference_clock_qualified_transactional_port():
    mode = Wire.OnSystem(group="g", mirrored_mode_constraints=AbstractionDefPortConstraintsType(
        timing_constraint=[TimingConstraint(value=1.0, clock_name="clk")],
    ))
    document = make_document(None)
    document.ports.port[0].wire_or_transactional.on_system.append(mode)
    document.ports.port.append(AbstractionDefinition.Ports.Port(
        logical_name="clk", wire_or_transactional=AbstractionDefinition.Ports.Port.Transactional(
            qualifier=QualifierType(is_clock=True),
        ),
    ))
    result = validate_abstraction_constraints(document)
    assert result.ok
    document.ports.port[1].wire_or_transactional.qualifier = None
    result = validate_abstraction_constraints(document)
    assert not result.ok
    assert "onSystem[1]/ipxact:mirroredModeConstraints" in result.issues[0].path


def test_result_lists_scoped_rules_and_rejects_other_models():
    result = validate_abstraction_constraints(make_document(None))
    assert result.ok
    assert result.checked_rules == ("SCR 12.3", "SCR 12.4", "SCR 12.5", "SCR 12.6", "SCR 12.8")
    with pytest.raises(TypeError):
        validate_abstraction_constraints(Wire())


@pytest.mark.parametrize("direction", [Direction.IN, Direction.OUT])
def test_compatible_direction_constraints_pass(direction):
    normal = make_constraints()
    mirrored = make_constraints()
    normal.drive_constraint_or_load_constraint = [normal.drive_constraint_or_load_constraint[
        0 if direction == Direction.IN else 1
    ]]
    mirrored.drive_constraint_or_load_constraint = [mirrored.drive_constraint_or_load_constraint[
        1 if direction == Direction.IN else 0
    ]]
    mode = Wire.OnInitiator(direction=direction, mode_constraints=normal, mirrored_mode_constraints=mirrored)
    assert validate_abstraction_constraints(make_document(mode)).ok


def test_all_violations_are_reported_in_document_order_without_mutation():
    mode = Wire.OnInitiator(direction=Direction.OUT, mode_constraints=make_constraints(),
                            mirrored_mode_constraints=make_constraints())
    mode.mode_constraints.timing_constraint = [TimingConstraint(value=0.0, clock_name="missing")]
    document = make_document(mode)
    before = XmlDocument.serializer().render(document)
    result = validate_abstraction_constraints(document)
    assert [issue.rule_id for issue in result.issues] == ["SCR 12.3", "SCR 12.8", "SCR 12.5"]
    assert XmlDocument.serializer().render(document) == before

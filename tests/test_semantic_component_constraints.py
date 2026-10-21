"""Component constraint rules use local driver names and the port fallback."""

import pytest
from lxml import etree

from amal.eda.ipxact_de.semantic_validation import validate_component_constraints
from amal.eda.ipxact_de.xml_document import XmlDocument
from amal.eda.ipxact_de.xml_validation import validate_ipxact_xml
from org.accellera.ipxact.v1685_2022 import Component

NS = {"ipxact": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022"}
CLOCK = '''<clockPeriod>10</clockPeriod><clockPulseOffset>0</clockPulseOffset>
<clockPulseValue>1</clockPulseValue><clockPulseDuration>5</clockPulseDuration>'''
CELL = '<cellSpecification><cellFunction>buf</cellFunction></cellSpecification>'


def xml_component(direction="in", constraint='', driver='', other='', clock="clk"):
    return f'''<component xmlns="{NS['ipxact']}">
<vendor>v</vendor><library>l</library><name>c</name><version>1</version>
<model><ports><port><name>data</name><wire><direction>{direction}</direction>
<constraintSets><constraintSet>{constraint}<timingConstraint clockName="{clock}">0</timingConstraint>
</constraintSet></constraintSets></wire></port>
<port><name>clk</name><wire><direction>in</direction>{driver}</wire></port>
</ports></model>{other}</component>'''


def parse(xml):
    return XmlDocument.parser().from_string(xml, Component)


@pytest.mark.parametrize("direction,child,rule", [
    ("out", f'<driveConstraint>{CELL}</driveConstraint>', "SCR 12.1"),
    ("in", f'<loadConstraint>{CELL}<count>1</count></loadConstraint>', "SCR 12.2"),
])
def test_direction_semantics_are_not_schema_rules(direction, child, rule):
    xml = xml_component(direction, child)
    tree = etree.fromstring(xml.encode())
    schema = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))
    assert schema.validate(tree), schema.error_log
    document = parse(xml)
    before = XmlDocument.serializer().render(document)
    result = validate_component_constraints(document)
    assert not result.ok
    assert [issue.rule_id for issue in result.issues] == [rule]
    assert len(tree.xpath(result.issues[0].path, namespaces=NS)) == 1
    assert XmlDocument.serializer().render(document) == before


@pytest.mark.parametrize("direction", ["inout", "phantom"])
def test_other_directions_have_no_drive_load_restrictions(direction):
    both = f'<driveConstraint>{CELL}</driveConstraint><loadConstraint>{CELL}<count>1</count></loadConstraint>'
    assert validate_component_constraints(parse(xml_component(direction, both))).ok


@pytest.mark.parametrize("driver_name", [None, "driven"])
@pytest.mark.parametrize("reference", ["clk", "driven", "data", "missing"])
def test_driver_names_override_port_fallback(driver_name, reference):
    attr = '' if driver_name is None else f' clockName="{driver_name}"'
    driver = f'<drivers><driver><clockDriver{attr}>{CLOCK}</clockDriver></driver></drivers>'
    result = validate_component_constraints(parse(xml_component(driver=driver, clock=reference)))
    assert result.ok is (reference == (driver_name or "clk"))
    if not result.ok:
        assert result.issues[0].rule_id == "SCR 12.7"


@pytest.mark.parametrize("reference,valid", [("external", True), ("clk", False)])
def test_other_clock_driver_blocks_port_fallback(reference, valid):
    other = f'<otherClockDrivers><otherClockDriver clockName="external">{CLOCK}</otherClockDriver></otherClockDrivers>'
    result = validate_component_constraints(parse(xml_component(other=other, clock=reference)))
    assert result.ok is valid


@pytest.mark.parametrize("reference,valid", [("clk", True), ("data", False), ("missing", False)])
def test_no_drivers_uses_another_port(reference, valid):
    result = validate_component_constraints(parse(xml_component(clock=reference)))
    assert result.ok is valid
    assert result.checked_rules == ("SCR 12.1", "SCR 12.2", "SCR 12.7")


@pytest.mark.parametrize("clock,valid", [("clk", True), ("data", False)])
def test_component_file_workflow(tmp_path, clock, valid):
    path = tmp_path / "c.xml"
    path.write_text(xml_component(clock=clock))
    assert validate_ipxact_xml(path, schema_root="submodules/accellera-schemas").ok
    result = validate_ipxact_xml(path, schema_root="submodules/accellera-schemas", semantic=True)
    assert result.ok is valid
    assert len(result.checked_semantic_rules) == 3
    if not valid:
        assert result.issues[0].line == 4
        assert result.issues[0].rule_id == "SCR 12.7"


def test_wrong_model_is_rejected():
    with pytest.raises(TypeError):
        validate_component_constraints(object())

"""Constraint Set timing percentages follow Annex F and the 2022 schema."""

import inspect

import pytest
from lxml import etree

from amal.eda.accellera.ipxact.v1685_2022 import tgi
from amal.eda.accellera.ipxact.v1685_2022.tgi import constraint_set as api
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import TgiError, get_handle, get_parent_info, resolve_handle
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import ConstraintSet, TimingConstraint

_SCHEMA = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))


def _valid(root):
    xml = XmlDocument.serializer().render(root)
    _SCHEMA.assertValid(etree.fromstring(xml.encode()))
    return xml


def test_public_contracts_and_boundary_values_roundtrip_with_ownership():
    root = ConstraintSet(constraint_set_id="timing")
    handle = get_handle(root)
    assert api.getConstraintSetTimingConstraints(handle) == []
    first = api.addConstraintSetTimingConstraint(constraintSetID=handle, value=0, clockName="clk")
    second = api.addConstraintSetTimingConstraint(handle, 100.0, "  clk:phase\t")
    assert api.getConstraintSetTimingConstraints(handle) == [0.0, 100.0]
    assert resolve_handle(second).clock_name == "clk:phase"
    assert get_parent_info(first).parent_handle == handle
    xml = _valid(root)
    parsed = XmlDocument.parser().from_string(xml, ConstraintSet)
    parsed_id = get_handle(parsed)
    assert api.getConstraintSetTimingConstraints(parsed_id) == [0.0, 100.0]
    assert get_parent_info(get_handle(parsed.timing_constraint[0])).parent_handle == parsed_id
    assert parsed == root
    values = api.getConstraintSetTimingConstraints(handle)
    values.clear()
    assert len(root.timing_constraint) == 2
    for operation in api.__all__:
        function = getattr(api, operation)
        assert getattr(tgi, operation) is function
        assert all(part in inspect.getdoc(function) for part in ["Args:", "Returns:", "Section:"])
    assert list(inspect.signature(api.addConstraintSetTimingConstraint).parameters) == [
        "constraintSetID",
        "value",
        "clockName",
    ]


@pytest.mark.parametrize("value", [-0.1, 100.1, float("nan"), float("inf"), -float("inf"), True, "25", None, 10**1000])
def test_invalid_values_are_atomic(value):
    root = ConstraintSet(timing_constraint=[TimingConstraint(value=25.0, clock_name="clk")])
    handle = get_handle(root)
    before = _valid(root)
    with pytest.raises(TgiError):
        api.addConstraintSetTimingConstraint(handle, value, "clk")
    assert _valid(root) == before


@pytest.mark.parametrize("clock", ["", " ", "3clock", "clock name", "clock/name", None, "clock[0]"])
def test_invalid_clock_names_are_atomic(clock):
    root = ConstraintSet()
    before = _valid(root)
    with pytest.raises(TgiError):
        api.addConstraintSetTimingConstraint(get_handle(root), 25.0, clock)
    assert _valid(root) == before


@pytest.mark.parametrize("clock", ["clk", "_clock", "clock.name-1", "δοκιμή", "时", ":clock"])
def test_schema_port_names_preserve_unicode_and_punctuation(clock):
    root = ConstraintSet()
    api.addConstraintSetTimingConstraint(get_handle(root), 12.5, clock)
    _valid(root)
    assert root.timing_constraint[0].clock_name == clock


@pytest.mark.parametrize("handle", ["missing", None, 3])
def test_invalid_handles_raise_tgi_faults(handle):
    for operation in [
        lambda: api.getConstraintSetTimingConstraints(handle),
        lambda: api.addConstraintSetTimingConstraint(handle, 25.0, "clk"),
    ]:
        with pytest.raises(TgiError):
            operation()


def test_source_metadata_is_preserved_and_invalid_model_values_are_not_silently_skipped():
    from org.accellera.ipxact.v1685_2022 import DelayValueType, EdgeValueType

    source = TimingConstraint(
        value=50.0, clock_name="clk", clock_edge=EdgeValueType.FALL, delay_type=DelayValueType.MIN
    )
    source.id = "constraint"
    root = ConstraintSet(timing_constraint=(source,))
    handle = get_handle(root)
    source_id = get_handle(source)
    api.addConstraintSetTimingConstraint(handle, 25.0, "other")
    assert root.timing_constraint[0] is source
    assert get_handle(source) == source_id
    assert source.id == "constraint"
    _valid(root)
    source.value = float("nan")
    with pytest.raises(TgiError):
        api.getConstraintSetTimingConstraints(handle)

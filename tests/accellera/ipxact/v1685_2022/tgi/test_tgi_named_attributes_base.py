"""BASE string/enum XML attribute getters preserve values across reloads."""

import pytest

from amal.eda.accellera.ipxact.v1685_2022 import tgi
from amal.eda.accellera.ipxact.v1685_2022.tgi import element_attribute as api
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import TgiError, get_handle
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import (
    BankAlignmentType,
    BaseAddress,
    CellSpecification,
    CellStrengthValueType,
    ClockDriverType,
    EdgeValueType,
    Left,
    LocalAddressBankType,
    ModuleParameterArrays,
    OtherClockDriver,
    Right,
    TimingConstraint,
    UnsignedBitExpression,
)


def _clock(source: str | None) -> OtherClockDriver:
    return OtherClockDriver(
        clock_name="clk",
        clock_source=source,
        clock_period=ClockDriverType.ClockPeriod(value="10"),
        clock_pulse_offset=ClockDriverType.ClockPulseOffset(value="0"),
        clock_pulse_value=UnsignedBitExpression(value="1"),
        clock_pulse_duration=ClockDriverType.ClockPulseDuration(value="5"),
    )


@pytest.mark.parametrize(
    "name,obj,expected",
    [
        (
            "getArrayIdAttribute",
            ModuleParameterArrays.Array(left=Left(value="7"), right=Right(value="0"), array_id="A"),
            "A",
        ),
        (
            "getBankAlignmentAttribute",
            LocalAddressBankType(
                name="bank", base_address=BaseAddress(value="0"), bank_alignment=BankAlignmentType.PARALLEL
            ),
            "parallel",
        ),
        ("getCellStrengthAttribute", CellSpecification(cell_strength=CellStrengthValueType.HIGH), "high"),
        (
            "getClockEdgeAttribute",
            TimingConstraint(value=50.0, clock_name="clk", clock_edge=EdgeValueType.FALL),
            "fall",
        ),
        ("getClockNameAttribute", _clock("src"), "clk"),
        ("getClockSourceAttribute", _clock("src"), "src"),
    ],
)
def test_named_attribute(name, obj, expected):
    getter = getattr(api, name)
    before = XmlDocument.serializer().render(obj)
    assert getter(get_handle(obj)) == expected
    parsed = XmlDocument.parser().from_string(before, type(obj))
    assert getter(get_handle(parsed)) == expected
    assert XmlDocument.serializer().render(obj) == before
    assert getattr(tgi, name) is getter
    assert getter(get_handle(object())) is None
    with pytest.raises(TgiError):
        getter("missing")


def test_optional_and_empty_attributes():
    assert api.getCellStrengthAttribute(get_handle(CellSpecification())) is None
    driver = _clock("")
    assert api.getClockSourceAttribute(get_handle(driver)) == ""
    driver.clock_source = None
    assert api.getClockSourceAttribute(get_handle(driver)) is None

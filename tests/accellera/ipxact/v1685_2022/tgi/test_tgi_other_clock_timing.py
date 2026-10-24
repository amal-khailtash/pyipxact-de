"""Other clock driver period and pulse timing getters evaluate expressions safely."""

from collections.abc import Callable, Iterator
from inspect import signature
from typing import get_type_hints

import pytest
from lxml import etree
from xsdata.formats.dataclass.parsers import XmlParser
from xsdata.formats.dataclass.serializers import XmlSerializer

from amal.eda.accellera.ipxact.v1685_2022 import tgi as package_api
from amal.eda.accellera.ipxact.v1685_2022.tgi import driver as api
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import (
    TgiError,
    TgiFaultCode,
    get_handle,
    get_parent_info,
    registry,
)
from org.accellera.ipxact.v1685_2022 import (
    ClockDriver,
    ClockDriverType,
    Component,
    DelayValueUnitType,
    Model,
    OtherClockDriver,
    Port,
    RealExpression,
    UnsignedBitExpression,
)
from org.accellera.ipxact.v1685_2022.other_clocks import OtherClocks

_SCHEMA = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))
_TIMING_FIELDS: tuple[
    tuple[
        str,
        type[RealExpression],
        Callable[[str], float | None],
        Callable[[str], str | None],
        Callable[[str], str | None],
    ],
    ...,
] = (
    (
        "clock_period",
        ClockDriverType.ClockPeriod,
        api.getOtherClockDriverClockPeriod,
        api.getOtherClockDriverClockPeriodExpression,
        api.getOtherClockDriverClockPeriodID,
    ),
    (
        "clock_pulse_duration",
        ClockDriverType.ClockPulseDuration,
        api.getOtherClockDriverClockPulseDuration,
        api.getOtherClockDriverClockPulseDurationExpression,
        api.getOtherClockDriverClockPulseDurationID,
    ),
    (
        "clock_pulse_offset",
        ClockDriverType.ClockPulseOffset,
        api.getOtherClockDriverClockPulseOffset,
        api.getOtherClockDriverClockPulseOffsetExpression,
        api.getOtherClockDriverClockPulseOffsetID,
    ),
)
_INVALID_SOURCES = (
    "1 +",
    "UNRESOLVED_CLOCK_PERIOD",
    "4'bx001",
    'string\'("not a number")',
    "nan",
    "inf",
    "1.0 / 0.0",
    "1e9999",
)


@pytest.fixture(autouse=True)
def clean_registry() -> Iterator[None]:
    registry.clear()
    yield
    registry.clear()


def _other_clock_driver() -> OtherClockDriver:
    return OtherClockDriver(
        clock_period=ClockDriverType.ClockPeriod(value="10"),
        clock_pulse_offset=ClockDriverType.ClockPulseOffset(value="0"),
        clock_pulse_value=UnsignedBitExpression(value="1"),
        clock_pulse_duration=ClockDriverType.ClockPulseDuration(value="5"),
        clock_name="external-clock",
    )


@pytest.mark.parametrize(
    ("field_name", "wrapper_type", "numeric_getter", "expression_getter", "id_getter"), _TIMING_FIELDS
)
@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("21", 21.0),
        ("2.75", 2.75),
        ("16'd21", 21.0),
        ("8'hA", 10.0),
        ('"A"', 65.0),
        ("real'(3)", 3.0),
        ("3 * (2 + 1)", 9.0),
    ],
)
def test_other_clock_timing_getters_evaluate_and_return_exact_source(
    field_name: str,
    wrapper_type: type[RealExpression],
    numeric_getter: Callable[[str], float | None],
    expression_getter: Callable[[str], str | None],
    id_getter: Callable[[str], str | None],
    source: str,
    expected: float,
) -> None:
    clock = _other_clock_driver()
    wrapper = wrapper_type(value=source)
    setattr(clock, field_name, wrapper)
    clock_id = get_handle(clock)

    assert numeric_getter(clock_id) == expected
    assert expression_getter(clock_id) == source
    wrapper_id = id_getter(clock_id)
    assert wrapper_id == get_handle(wrapper)
    owner = get_parent_info(wrapper_id)
    assert owner is not None
    assert owner.parent_handle == clock_id
    assert owner.path == (field_name,)
    assert owner.container == "single"


@pytest.mark.parametrize(
    ("field_name", "wrapper_type", "numeric_getter", "expression_getter", "id_getter"), _TIMING_FIELDS
)
@pytest.mark.parametrize("source", _INVALID_SOURCES)
def test_other_clock_timing_numeric_getters_reject_invalid_or_nonfinite_expressions(
    field_name: str,
    wrapper_type: type[RealExpression],
    numeric_getter: Callable[[str], float | None],
    expression_getter: Callable[[str], str | None],
    id_getter: Callable[[str], str | None],
    source: str,
) -> None:
    clock = _other_clock_driver()
    setattr(clock, field_name, wrapper_type(value=source))

    with pytest.raises(TgiError) as error:
        numeric_getter(get_handle(clock))
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT


@pytest.mark.parametrize(
    ("field_name", "wrapper_type", "numeric_getter", "expression_getter", "id_getter"), _TIMING_FIELDS
)
@pytest.mark.parametrize(("source", "expected"), [("1", 1.0), ("5", 5.0)])
def test_other_clock_timing_bounds_are_inclusive(
    field_name: str,
    wrapper_type: type[RealExpression],
    numeric_getter: Callable[[str], float | None],
    expression_getter: Callable[[str], str | None],
    id_getter: Callable[[str], str | None],
    source: str,
    expected: float,
) -> None:
    clock = _other_clock_driver()
    setattr(clock, field_name, wrapper_type(value=source, minimum=1.0, maximum=5.0))

    assert numeric_getter(get_handle(clock)) == expected


@pytest.mark.parametrize(
    ("field_name", "wrapper_type", "numeric_getter", "expression_getter", "id_getter"), _TIMING_FIELDS
)
def test_other_clock_timing_accepts_schema_infinite_bounds(
    field_name: str,
    wrapper_type: type[RealExpression],
    numeric_getter: Callable[[str], float | None],
    expression_getter: Callable[[str], str | None],
    id_getter: Callable[[str], str | None],
) -> None:
    clock = _other_clock_driver()
    setattr(clock, field_name, wrapper_type(value="2", minimum=float("-inf"), maximum=float("inf")))

    assert numeric_getter(get_handle(clock)) == 2.0


@pytest.mark.parametrize(
    ("field_name", "wrapper_type", "numeric_getter", "expression_getter", "id_getter"), _TIMING_FIELDS
)
@pytest.mark.parametrize("source", ["0", "6"])
def test_other_clock_timing_rejects_values_outside_bounds(
    field_name: str,
    wrapper_type: type[RealExpression],
    numeric_getter: Callable[[str], float | None],
    expression_getter: Callable[[str], str | None],
    id_getter: Callable[[str], str | None],
    source: str,
) -> None:
    clock = _other_clock_driver()
    setattr(clock, field_name, wrapper_type(value=source, minimum=1.0, maximum=5.0))

    with pytest.raises(TgiError) as error:
        numeric_getter(get_handle(clock))
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT


@pytest.mark.parametrize(
    ("field_name", "wrapper_type", "numeric_getter", "expression_getter", "id_getter"), _TIMING_FIELDS
)
@pytest.mark.parametrize(("minimum", "maximum"), [(float("nan"), 5.0), (5.0, 4.0)])
def test_other_clock_timing_rejects_invalid_bounds(
    field_name: str,
    wrapper_type: type[RealExpression],
    numeric_getter: Callable[[str], float | None],
    expression_getter: Callable[[str], str | None],
    id_getter: Callable[[str], str | None],
    minimum: float,
    maximum: float,
) -> None:
    clock = _other_clock_driver()
    setattr(clock, field_name, wrapper_type(value="3", minimum=minimum, maximum=maximum))

    with pytest.raises(TgiError) as error:
        numeric_getter(get_handle(clock))
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT


@pytest.mark.parametrize(
    ("field_name", "wrapper_type", "numeric_getter", "expression_getter", "id_getter"), _TIMING_FIELDS
)
def test_optional_other_clock_timing_fields_return_none_when_absent(
    field_name: str,
    wrapper_type: type[RealExpression],
    numeric_getter: Callable[[str], float | None],
    expression_getter: Callable[[str], str | None],
    id_getter: Callable[[str], str | None],
) -> None:
    clock = _other_clock_driver()
    setattr(clock, field_name, None)
    clock_id = get_handle(clock)

    assert numeric_getter(clock_id) is None
    assert expression_getter(clock_id) is None
    assert id_getter(clock_id) is None


@pytest.mark.parametrize(
    ("field_name", "wrapper_type", "numeric_getter", "expression_getter", "id_getter"), _TIMING_FIELDS
)
def test_other_clock_timing_getters_reject_wrong_wrapper_type(
    field_name: str,
    wrapper_type: type[RealExpression],
    numeric_getter: Callable[[str], float | None],
    expression_getter: Callable[[str], str | None],
    id_getter: Callable[[str], str | None],
) -> None:
    clock = _other_clock_driver()
    setattr(clock, field_name, UnsignedBitExpression(value="1"))

    for getter in (numeric_getter, expression_getter, id_getter):
        with pytest.raises(TgiError) as error:
            getter(get_handle(clock))
        assert error.value.fault_code == TgiFaultCode.INVALID_ID


def test_other_and_port_clock_timing_getters_reject_each_others_driver_handles() -> None:
    port_clock = ClockDriver(
        clock_period=ClockDriverType.ClockPeriod(value="10"),
        clock_pulse_offset=ClockDriverType.ClockPulseOffset(value="0"),
        clock_pulse_value=UnsignedBitExpression(value="1"),
        clock_pulse_duration=ClockDriverType.ClockPulseDuration(value="5"),
    )
    other_clock = _other_clock_driver()
    invalid_ids = (
        "missing-clock-driver",
        get_handle(Port(name="clk")),
        get_handle(port_clock),
        get_handle(other_clock),
    )

    for _, _, numeric_getter, expression_getter, id_getter in _TIMING_FIELDS:
        for getter in (numeric_getter, expression_getter, id_getter):
            with pytest.raises(TgiError) as error:
                getter(invalid_ids[2])
            assert error.value.fault_code == TgiFaultCode.INVALID_ID

    original_getters = (
        (api.getClockDriverClockPeriod, api.getClockDriverClockPeriodExpression, api.getClockDriverClockPeriodID),
        (
            api.getClockDriverClockPulseDuration,
            api.getClockDriverClockPulseDurationExpression,
            api.getClockDriverClockPulseDurationID,
        ),
        (
            api.getClockDriverClockPulseOffset,
            api.getClockDriverClockPulseOffsetExpression,
            api.getClockDriverClockPulseOffsetID,
        ),
    )
    for group in original_getters:
        for getter in group:
            with pytest.raises(TgiError) as error:
                getter(invalid_ids[3])
            assert error.value.fault_code == TgiFaultCode.INVALID_ID

    for invalid_id in invalid_ids[:2]:
        for _, _, numeric_getter, expression_getter, id_getter in _TIMING_FIELDS:
            for getter in (numeric_getter, expression_getter, id_getter):
                with pytest.raises(TgiError) as error:
                    getter(invalid_id)
                assert error.value.fault_code == TgiFaultCode.INVALID_ID


def test_other_clock_timing_exports_have_annex_signatures_and_native_types() -> None:
    for _, _, numeric_getter, expression_getter, id_getter in _TIMING_FIELDS:
        for getter, return_type in (
            (numeric_getter, float | None),
            (expression_getter, str | None),
            (id_getter, str | None),
        ):
            assert getter.__name__ in api.__all__
            assert getter.__name__ in package_api.__all__
            assert getattr(package_api, getter.__name__) is getter
            parameters = signature(getter).parameters
            assert list(parameters) == ["otherClockDriverID"]
            assert parameters["otherClockDriverID"].annotation is str
            assert signature(getter).return_annotation == return_type
            assert get_type_hints(getter) == {"otherClockDriverID": str, "return": return_type}


def test_other_clock_timing_units_sources_and_ids_survive_schema_valid_round_trip() -> None:
    clock = OtherClockDriver(
        clock_period=ClockDriverType.ClockPeriod(
            value=" 8 / 2 ", units=DelayValueUnitType.PS, minimum=4.0, maximum=4.0
        ),
        clock_pulse_offset=ClockDriverType.ClockPulseOffset(
            value=" 1 + 2 ", units=DelayValueUnitType.NS, minimum=0.0, maximum=3.0
        ),
        clock_pulse_value=UnsignedBitExpression(value="1"),
        clock_pulse_duration=ClockDriverType.ClockPulseDuration(
            value="2.50", units=DelayValueUnitType.PS, minimum=2.0, maximum=3.0
        ),
        clock_name="external-clock",
        clock_source="pll.out",
        id="external-clock-driver-1",
    )
    root = Component(
        vendor="acme",
        library="test",
        name="other-clock-timing",
        version="1.0",
        model=Model(),
        other_clock_drivers=OtherClocks(other_clock_driver=[clock]),
    )
    clock_id = get_handle(clock)
    expected_sources = (" 8 / 2 ", "2.50", " 1 + 2 ")
    expected_numbers = (4.0, 2.5, 3.0)
    getters = tuple(entry[2:4] for entry in _TIMING_FIELDS)
    id_getters = tuple(entry[4] for entry in _TIMING_FIELDS)
    wrappers = (clock.clock_period, clock.clock_pulse_duration, clock.clock_pulse_offset)
    for (numeric_getter, expression_getter), source, number, wrapper, id_getter in zip(
        getters, expected_sources, expected_numbers, wrappers, id_getters, strict=True
    ):
        assert numeric_getter(clock_id) == number
        assert expression_getter(clock_id) == source
        assert id_getter(clock_id) == get_handle(wrapper)

    xml = XmlSerializer().render(root)
    _SCHEMA.assertValid(etree.fromstring(xml.encode()))
    parsed = XmlParser().from_string(xml, Component)
    parsed_clock = parsed.other_clock_drivers.other_clock_driver[0]
    parsed_clock_id = get_handle(parsed_clock)
    parsed_wrappers = (parsed_clock.clock_period, parsed_clock.clock_pulse_duration, parsed_clock.clock_pulse_offset)
    units = (DelayValueUnitType.PS, DelayValueUnitType.PS, DelayValueUnitType.NS)
    bounds = ((4.0, 4.0), (2.0, 3.0), (0.0, 3.0))
    for (numeric_getter, expression_getter), source, number, wrapper, unit, bound, id_getter in zip(
        getters, expected_sources, expected_numbers, parsed_wrappers, units, bounds, id_getters, strict=True
    ):
        assert numeric_getter(parsed_clock_id) == number
        assert expression_getter(parsed_clock_id) == source
        assert id_getter(parsed_clock_id) == get_handle(wrapper)
        assert wrapper.value == source
        assert wrapper.units is unit
        assert (wrapper.minimum, wrapper.maximum) == bound
    assert parsed_clock.clock_name == "external-clock"
    assert parsed_clock.clock_source == "pll.out"
    assert parsed_clock.id == "external-clock-driver-1"

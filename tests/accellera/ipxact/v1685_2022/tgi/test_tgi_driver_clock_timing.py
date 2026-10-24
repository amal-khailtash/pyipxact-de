"""Clock driver period and pulse timing getters evaluate expressions safely."""

from collections.abc import Callable, Iterator

import pytest
from lxml import etree
from xsdata.formats.dataclass.parsers import XmlParser
from xsdata.formats.dataclass.serializers import XmlSerializer

from amal.eda.accellera.ipxact.v1685_2022.tgi import driver as api
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import (
    TgiError,
    TgiFaultCode,
    detach_child_by_handle,
    get_handle,
    get_parent_info,
    register_parent,
    registry,
    resolve_handle,
)
from org.accellera.ipxact.v1685_2022 import (
    ClockDriver,
    ClockDriverType,
    Component,
    ComponentPortDirectionType,
    DelayValueUnitType,
    Driver,
    Drivers,
    Model,
    OtherClockDriver,
    Port,
    PortWireType,
    RealExpression,
    UnsignedBitExpression,
)

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
        api.getClockDriverClockPeriod,
        api.getClockDriverClockPeriodExpression,
        api.getClockDriverClockPeriodID,
    ),
    (
        "clock_pulse_duration",
        ClockDriverType.ClockPulseDuration,
        api.getClockDriverClockPulseDuration,
        api.getClockDriverClockPulseDurationExpression,
        api.getClockDriverClockPulseDurationID,
    ),
    (
        "clock_pulse_offset",
        ClockDriverType.ClockPulseOffset,
        api.getClockDriverClockPulseOffset,
        api.getClockDriverClockPulseOffsetExpression,
        api.getClockDriverClockPulseOffsetID,
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


def _clock_driver() -> ClockDriver:
    return ClockDriver(
        clock_period=ClockDriverType.ClockPeriod(value="10"),
        clock_pulse_offset=ClockDriverType.ClockPulseOffset(value="0"),
        clock_pulse_value=UnsignedBitExpression(value="1"),
        clock_pulse_duration=ClockDriverType.ClockPulseDuration(value="5"),
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
def test_clock_timing_getters_evaluate_and_return_exact_source(
    field_name: str,
    wrapper_type: type[RealExpression],
    numeric_getter: Callable[[str], float | None],
    expression_getter: Callable[[str], str | None],
    id_getter: Callable[[str], str | None],
    source: str,
    expected: float,
) -> None:
    clock = _clock_driver()
    wrapper = wrapper_type(value=source)
    setattr(clock, field_name, wrapper)
    clock_id = get_handle(clock)

    assert numeric_getter(clock_id) == expected
    assert expression_getter(clock_id) == source
    wrapper_id = id_getter(clock_id)
    assert wrapper_id == get_handle(wrapper)
    owner = get_parent_info(wrapper_id)
    assert owner.parent_handle == clock_id
    assert owner.path == (field_name,)
    assert owner.container == "single"


@pytest.mark.parametrize(
    ("field_name", "wrapper_type", "numeric_getter", "expression_getter", "id_getter"), _TIMING_FIELDS
)
@pytest.mark.parametrize("source", _INVALID_SOURCES)
def test_clock_timing_numeric_getters_reject_invalid_or_nonfinite_expressions(
    field_name: str,
    wrapper_type: type[RealExpression],
    numeric_getter: Callable[[str], float | None],
    expression_getter: Callable[[str], str | None],
    id_getter: Callable[[str], str | None],
    source: str,
) -> None:
    clock = _clock_driver()
    setattr(clock, field_name, wrapper_type(value=source))

    with pytest.raises(TgiError) as error:
        numeric_getter(get_handle(clock))
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT


@pytest.mark.parametrize(
    ("field_name", "wrapper_type", "numeric_getter", "expression_getter", "id_getter"), _TIMING_FIELDS
)
@pytest.mark.parametrize(("source", "expected"), [("1", 1.0), ("5", 5.0)])
def test_clock_timing_minimum_and_maximum_bounds_are_inclusive(
    field_name: str,
    wrapper_type: type[RealExpression],
    numeric_getter: Callable[[str], float | None],
    expression_getter: Callable[[str], str | None],
    id_getter: Callable[[str], str | None],
    source: str,
    expected: float,
) -> None:
    clock = _clock_driver()
    setattr(clock, field_name, wrapper_type(value=source, minimum=1.0, maximum=5.0))

    assert numeric_getter(get_handle(clock)) == expected


@pytest.mark.parametrize(
    ("field_name", "wrapper_type", "numeric_getter", "expression_getter", "id_getter"), _TIMING_FIELDS
)
def test_clock_timing_numeric_getters_allow_schema_infinite_bounds(
    field_name: str,
    wrapper_type: type[RealExpression],
    numeric_getter: Callable[[str], float | None],
    expression_getter: Callable[[str], str | None],
    id_getter: Callable[[str], str | None],
) -> None:
    clock = _clock_driver()
    setattr(clock, field_name, wrapper_type(value="2", minimum=float("-inf"), maximum=float("inf")))

    assert numeric_getter(get_handle(clock)) == 2.0


@pytest.mark.parametrize(
    ("field_name", "wrapper_type", "numeric_getter", "expression_getter", "id_getter"), _TIMING_FIELDS
)
@pytest.mark.parametrize("source", ["0", "6"])
def test_clock_timing_numeric_getters_reject_values_outside_bounds(
    field_name: str,
    wrapper_type: type[RealExpression],
    numeric_getter: Callable[[str], float | None],
    expression_getter: Callable[[str], str | None],
    id_getter: Callable[[str], str | None],
    source: str,
) -> None:
    clock = _clock_driver()
    setattr(clock, field_name, wrapper_type(value=source, minimum=1.0, maximum=5.0))

    with pytest.raises(TgiError) as error:
        numeric_getter(get_handle(clock))
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT


@pytest.mark.parametrize(
    ("field_name", "wrapper_type", "numeric_getter", "expression_getter", "id_getter"), _TIMING_FIELDS
)
@pytest.mark.parametrize(("minimum", "maximum"), [(float("nan"), 5.0), (5.0, 4.0)])
def test_clock_timing_numeric_getters_reject_invalid_bounds(
    field_name: str,
    wrapper_type: type[RealExpression],
    numeric_getter: Callable[[str], float | None],
    expression_getter: Callable[[str], str | None],
    id_getter: Callable[[str], str | None],
    minimum: float,
    maximum: float,
) -> None:
    clock = _clock_driver()
    setattr(clock, field_name, wrapper_type(value="3", minimum=minimum, maximum=maximum))

    with pytest.raises(TgiError) as error:
        numeric_getter(get_handle(clock))
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT


@pytest.mark.parametrize(
    ("field_name", "wrapper_type", "numeric_getter", "expression_getter", "id_getter"), _TIMING_FIELDS
)
def test_optional_clock_timing_fields_return_none_when_absent(
    field_name: str,
    wrapper_type: type[RealExpression],
    numeric_getter: Callable[[str], float | None],
    expression_getter: Callable[[str], str | None],
    id_getter: Callable[[str], str | None],
) -> None:
    clock = _clock_driver()
    setattr(clock, field_name, None)
    clock_id = get_handle(clock)

    assert numeric_getter(clock_id) is None
    assert expression_getter(clock_id) is None
    assert id_getter(clock_id) is None


@pytest.mark.parametrize(
    ("field_name", "wrapper_type", "numeric_getter", "expression_getter", "id_getter"), _TIMING_FIELDS
)
def test_clock_timing_getters_reject_wrong_wrapper_types(
    field_name: str,
    wrapper_type: type[RealExpression],
    numeric_getter: Callable[[str], float | None],
    expression_getter: Callable[[str], str | None],
    id_getter: Callable[[str], str | None],
) -> None:
    clock = _clock_driver()
    setattr(clock, field_name, UnsignedBitExpression(value="1"))
    clock_id = get_handle(clock)

    for getter in (numeric_getter, expression_getter, id_getter):
        with pytest.raises(TgiError) as error:
            getter(clock_id)
        assert error.value.fault_code == TgiFaultCode.INVALID_ID


def test_clock_timing_getters_reject_invalid_and_stale_clock_driver_ids() -> None:
    for invalid_id in (
        "missing-clock-driver",
        get_handle(object()),
        get_handle(
            OtherClockDriver(
                clock_period=ClockDriverType.ClockPeriod(value="10"),
                clock_pulse_offset=ClockDriverType.ClockPulseOffset(value="0"),
                clock_pulse_value=UnsignedBitExpression(value="1"),
                clock_pulse_duration=ClockDriverType.ClockPulseDuration(value="5"),
                clock_name="external",
            )
        ),
    ):
        for _, _, numeric_getter, expression_getter, id_getter in _TIMING_FIELDS:
            with pytest.raises(TgiError) as error:
                numeric_getter(invalid_id)
            assert error.value.fault_code == TgiFaultCode.INVALID_ID
            with pytest.raises(TgiError) as error:
                expression_getter(invalid_id)
            assert error.value.fault_code == TgiFaultCode.INVALID_ID
            with pytest.raises(TgiError) as error:
                id_getter(invalid_id)
            assert error.value.fault_code == TgiFaultCode.INVALID_ID

    stale_clock = _clock_driver()
    stale_id = get_handle(stale_clock)
    parent = Driver(default_value_or_clock_driver_or_single_shot_driver=stale_clock)
    register_parent(stale_clock, parent, ("default_value_or_clock_driver_or_single_shot_driver",), "single")
    assert detach_child_by_handle(stale_id)
    assert resolve_handle(stale_id) is None
    for _, _, numeric_getter, expression_getter, id_getter in _TIMING_FIELDS:
        for getter in (numeric_getter, expression_getter, id_getter):
            with pytest.raises(TgiError) as error:
                getter(stale_id)
            assert error.value.fault_code == TgiFaultCode.INVALID_ID


def test_clock_timing_sources_units_and_metadata_survive_schema_valid_round_trip() -> None:
    clock = ClockDriver(
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
        id="clock-driver-1",
    )
    root = Component(
        vendor="acme",
        library="test",
        name="clock-timing",
        version="1.0",
        model=Model(
            ports=Model.Ports(
                port=[
                    Port(
                        name="clk",
                        wire_or_transactional_or_structured=PortWireType(
                            direction=ComponentPortDirectionType.IN,
                            drivers=Drivers(driver=[Driver(default_value_or_clock_driver_or_single_shot_driver=clock)]),
                        ),
                    )
                ]
            )
        ),
    )
    clock_id = get_handle(clock)
    expected_sources = (" 8 / 2 ", "2.50", " 1 + 2 ")
    expected_numbers = (4.0, 2.5, 3.0)
    expected_ids = (
        api.getClockDriverClockPeriodID,
        api.getClockDriverClockPulseDurationID,
        api.getClockDriverClockPulseOffsetID,
    )
    wrappers = (clock.clock_period, clock.clock_pulse_duration, clock.clock_pulse_offset)
    getters = tuple(entry[2:4] for entry in _TIMING_FIELDS)
    for (numeric_getter, expression_getter), source, number, wrapper, id_getter in zip(
        getters, expected_sources, expected_numbers, wrappers, expected_ids, strict=True
    ):
        assert numeric_getter(clock_id) == number
        assert expression_getter(clock_id) == source
        assert id_getter(clock_id) == get_handle(wrapper)

    xml = XmlSerializer().render(root)
    _SCHEMA.assertValid(etree.fromstring(xml.encode()))
    parsed = XmlParser().from_string(xml, Component)
    parsed_clock = (
        parsed.model.ports.port[0]
        .wire_or_transactional_or_structured.drivers.driver[0]
        .default_value_or_clock_driver_or_single_shot_driver
    )
    parsed_clock_id = get_handle(parsed_clock)
    parsed_wrappers = (parsed_clock.clock_period, parsed_clock.clock_pulse_duration, parsed_clock.clock_pulse_offset)
    units = (DelayValueUnitType.PS, DelayValueUnitType.PS, DelayValueUnitType.NS)
    bounds = ((4.0, 4.0), (2.0, 3.0), (0.0, 3.0))
    for (numeric_getter, expression_getter), source, number, wrapper, unit, bound, id_getter in zip(
        getters, expected_sources, expected_numbers, parsed_wrappers, units, bounds, expected_ids, strict=True
    ):
        assert numeric_getter(parsed_clock_id) == number
        assert expression_getter(parsed_clock_id) == source
        assert id_getter(parsed_clock_id) == get_handle(wrapper)
        assert wrapper.value == source
        assert wrapper.units is unit
        assert (wrapper.minimum, wrapper.maximum) == bound
    assert parsed_clock.id == "clock-driver-1"

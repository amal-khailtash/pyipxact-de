"""Driver value getters preserve source text and follow the generated choice model."""

import inspect
from collections.abc import Callable, Iterator
from typing import get_type_hints

import pytest
from lxml import etree
from xsdata.formats.dataclass.parsers import XmlParser
from xsdata.formats.dataclass.serializers import XmlSerializer

from amal.eda.accellera.ipxact.v1685_2022 import tgi
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
    DefaultValue,
    DelayValueUnitType,
    Driver,
    Drivers,
    Model,
    Port,
    PortWireType,
    RealExpression,
    SingleShotDriver,
    UnsignedBitExpression,
    UnsignedBitVectorExpression,
)

_SCHEMA = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))


@pytest.fixture(autouse=True)
def clean_registry() -> Iterator[None]:
    registry.clear()
    yield
    registry.clear()


def _clock_driver(value: str | None = "1") -> ClockDriver:
    return ClockDriver(
        clock_period=ClockDriverType.ClockPeriod(value="10"),
        clock_pulse_offset=ClockDriverType.ClockPulseOffset(value="0"),
        clock_pulse_value=None if value is None else UnsignedBitExpression(value=value),
        clock_pulse_duration=ClockDriverType.ClockPulseDuration(value="5"),
    )


def _single_shot_driver() -> SingleShotDriver:
    return SingleShotDriver(
        single_shot_offset=SingleShotDriver.SingleShotOffset(value="1", units=DelayValueUnitType.NS),
        single_shot_value=UnsignedBitVectorExpression(value="1"),
        single_shot_duration=SingleShotDriver.SingleShotDuration(value="2", units=DelayValueUnitType.PS),
    )


def _component(*drivers: Driver) -> Component:
    ports = [
        Port(
            name=f"port{index}",
            wire_or_transactional_or_structured=PortWireType(
                direction=ComponentPortDirectionType.IN,
                drivers=Drivers(driver=[driver]),
            ),
        )
        for index, driver in enumerate(drivers)
    ]
    return Component(
        vendor="acme",
        library="test",
        name="driver-values",
        version="1.0",
        model=Model(ports=Model.Ports(port=ports)),
    )


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("0", False),
        ("1", True),
        ("2", False),
        ("3", True),
        ("2.5", True),
        ("1'bx", False),
        ("1'bz", False),
        ("1'bx + 2", False),
    ],
)
def test_clock_pulse_value_casts_to_systemverilog_bit_and_keeps_exact_source(source: str, expected: bool) -> None:
    clock = _clock_driver(source)
    clock_id = get_handle(clock)
    value_id = api.getClockDriverClockPulseValueID(clock_id)

    assert api.getClockDriverClockPulseValue(clock_id) is expected
    assert api.getClockDriverClockPulseValueExpression(clock_id) == source
    assert value_id == get_handle(clock.clock_pulse_value)
    owner = get_parent_info(value_id)
    assert owner is not None
    assert (owner.parent_handle, owner.path, owner.container) == (clock_id, ("clock_pulse_value",), "single")


@pytest.mark.parametrize("source", ["UNKNOWN_VALUE", "1 +", "(3 *"])
def test_clock_pulse_value_rejects_unresolved_or_malformed_expressions(source: str) -> None:
    clock = _clock_driver(source)
    clock_id = get_handle(clock)

    with pytest.raises(TgiError) as error:
        api.getClockDriverClockPulseValue(clock_id)
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert api.getClockDriverClockPulseValueExpression(clock_id) == source


def test_clock_pulse_value_optional_field_and_wrong_wrapper_are_handled() -> None:
    clock = _clock_driver(None)
    clock_id = get_handle(clock)
    assert api.getClockDriverClockPulseValue(clock_id) is None
    assert api.getClockDriverClockPulseValueExpression(clock_id) is None
    assert api.getClockDriverClockPulseValueID(clock_id) is None

    clock.clock_pulse_value = RealExpression(value="1")
    for getter in (
        api.getClockDriverClockPulseValue,
        api.getClockDriverClockPulseValueExpression,
        api.getClockDriverClockPulseValueID,
    ):
        with pytest.raises(TgiError) as error:
            getter(clock_id)
        assert error.value.fault_code == TgiFaultCode.INVALID_ID


@pytest.mark.parametrize(
    ("branch", "clock_getter", "single_shot_getter", "default_getter"),
    [
        (ClockDriver, api.getDriverClockDriverID, api.getDriverSingleShotDriverID, api.getDriverDefaultValueID),
        (SingleShotDriver, api.getDriverClockDriverID, api.getDriverSingleShotDriverID, api.getDriverDefaultValueID),
        (DefaultValue, api.getDriverClockDriverID, api.getDriverSingleShotDriverID, api.getDriverDefaultValueID),
    ],
)
def test_driver_choice_getters_return_only_the_selected_child(
    branch: type[ClockDriver] | type[SingleShotDriver] | type[DefaultValue],
    clock_getter: Callable[[str], str | None],
    single_shot_getter: Callable[[str], str | None],
    default_getter: Callable[[str], str | None],
) -> None:
    child = {
        ClockDriver: _clock_driver(),
        SingleShotDriver: _single_shot_driver(),
        DefaultValue: DefaultValue(value="8'hf"),
    }[branch]
    driver = Driver(default_value_or_clock_driver_or_single_shot_driver=child)
    driver_id = get_handle(driver)

    expected_clock = get_handle(child) if branch is ClockDriver else None
    expected_single_shot = get_handle(child) if branch is SingleShotDriver else None
    expected_default = get_handle(child) if branch is DefaultValue else None
    assert clock_getter(driver_id) == expected_clock
    assert single_shot_getter(driver_id) == expected_single_shot
    assert default_getter(driver_id) == expected_default

    selected_id = expected_clock or expected_single_shot or expected_default
    if selected_id is not None:
        owner = get_parent_info(selected_id)
        assert owner is not None
        assert (owner.parent_handle, owner.path, owner.container) == (
            driver_id,
            ("default_value_or_clock_driver_or_single_shot_driver",),
            "single",
        )


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("42", "42"),
        ("8'h2a", "42"),
        ("3 * (2 + 1)", "9"),
        ("2.75", "2.75"),
        ('string\'("READY")', '"READY"'),
        ("4'bx001", "4'bx001"),
    ],
)
def test_default_value_evaluates_constants_and_returns_exact_expression(source: str, expected: str) -> None:
    wrapper = DefaultValue(value=source)
    driver = Driver(default_value_or_clock_driver_or_single_shot_driver=wrapper)
    driver_id = get_handle(driver)

    assert api.getDriverDefaultValue(driver_id) == expected
    assert api.getDriverDefaultValueExpression(driver_id) == source
    value_id = api.getDriverDefaultValueID(driver_id)
    assert value_id == get_handle(wrapper)
    owner = get_parent_info(value_id)
    assert owner is not None
    assert (owner.parent_handle, owner.path, owner.container) == (
        driver_id,
        ("default_value_or_clock_driver_or_single_shot_driver",),
        "single",
    )


@pytest.mark.parametrize("source", ["UNRESOLVED_DEFAULT", "1 +"])
def test_default_value_rejects_unresolved_and_malformed_values(source: str) -> None:
    driver = Driver(default_value_or_clock_driver_or_single_shot_driver=DefaultValue(value=source))
    with pytest.raises(TgiError) as error:
        api.getDriverDefaultValue(get_handle(driver))
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT


def test_value_getters_return_none_for_absent_branches_and_reject_bad_choices() -> None:
    empty = get_handle(Driver())
    assert api.getDriverClockDriverID(empty) is None
    assert api.getDriverSingleShotDriverID(empty) is None
    assert api.getDriverDefaultValue(empty) is None
    assert api.getDriverDefaultValueExpression(empty) is None
    assert api.getDriverDefaultValueID(empty) is None

    malformed = get_handle(Driver(default_value_or_clock_driver_or_single_shot_driver=object()))
    for getter in (
        api.getDriverClockDriverID,
        api.getDriverSingleShotDriverID,
        api.getDriverDefaultValue,
        api.getDriverDefaultValueExpression,
        api.getDriverDefaultValueID,
    ):
        with pytest.raises(TgiError) as error:
            getter(malformed)
        assert error.value.fault_code == TgiFaultCode.INVALID_ID


def test_value_getters_reject_wrong_and_stale_handles() -> None:
    wrong_type_id = get_handle(DefaultValue(value="1"))
    for getter in (
        api.getClockDriverClockPulseValue,
        api.getClockDriverClockPulseValueExpression,
        api.getClockDriverClockPulseValueID,
        api.getDriverClockDriverID,
        api.getDriverSingleShotDriverID,
        api.getDriverDefaultValue,
        api.getDriverDefaultValueExpression,
        api.getDriverDefaultValueID,
    ):
        with pytest.raises(TgiError) as error:
            getter("missing-id")
        assert error.value.fault_code == TgiFaultCode.INVALID_ID
        with pytest.raises(TgiError) as error:
            getter(wrong_type_id)
        assert error.value.fault_code == TgiFaultCode.INVALID_ID

    clock = _clock_driver()
    stale_clock_id = get_handle(clock)
    driver = Driver(default_value_or_clock_driver_or_single_shot_driver=clock)
    register_parent(clock, driver, ("default_value_or_clock_driver_or_single_shot_driver",), "single")
    assert detach_child_by_handle(stale_clock_id)
    assert resolve_handle(stale_clock_id) is None
    for getter in (
        api.getClockDriverClockPulseValue,
        api.getClockDriverClockPulseValueExpression,
        api.getClockDriverClockPulseValueID,
        api.getDriverClockDriverID,
    ):
        with pytest.raises(TgiError) as error:
            getter(stale_clock_id)
        assert error.value.fault_code == TgiFaultCode.INVALID_ID


def test_value_getter_signatures_exports_and_native_annotations() -> None:
    expected = {
        "getClockDriverClockPulseValue": ([str], bool | None),
        "getClockDriverClockPulseValueExpression": ([str], str | None),
        "getClockDriverClockPulseValueID": ([str], str | None),
        "getDriverClockDriverID": ([str], str | None),
        "getDriverSingleShotDriverID": ([str], str | None),
        "getDriverDefaultValue": ([str], str | None),
        "getDriverDefaultValueExpression": ([str], str | None),
        "getDriverDefaultValueID": ([str], str | None),
    }

    for name, (parameters, return_type) in expected.items():
        function = getattr(api, name)
        assert getattr(tgi, name) is function
        assert name in api.__all__
        assert name in tgi.__all__
        signature = inspect.signature(function)
        assert list(signature.parameters) == ["clockDriverID" if name.startswith("getClockDriver") else "driverID"]
        assert len(parameters) == len(signature.parameters)
        hints = get_type_hints(function)
        assert [hints[parameter] for parameter in signature.parameters] == parameters
        assert hints["return"] == return_type
        assert signature.return_annotation == return_type
        assert not isinstance(signature.return_annotation, str)


def test_value_sources_and_clock_metadata_survive_schema_valid_xml_round_trip() -> None:
    pulse_source = " 2.5 "
    clock = ClockDriver(
        clock_period=ClockDriverType.ClockPeriod(value="4", units=DelayValueUnitType.NS, minimum=4.0, maximum=4.0),
        clock_pulse_offset=ClockDriverType.ClockPulseOffset(value="1", units=DelayValueUnitType.NS),
        clock_pulse_value=UnsignedBitExpression(value=pulse_source, other_attributes={"{urn:test}tag": "pulse"}),
        clock_pulse_duration=ClockDriverType.ClockPulseDuration(value="3", units=DelayValueUnitType.PS),
        clock_name="clk_internal",
        id="clock-1",
    )
    single_shot = _single_shot_driver()
    single_shot.single_shot_value = UnsignedBitVectorExpression(value="8'hA")
    default = DefaultValue(value="8'h2a", other_attributes={"{urn:test}tag": "default"})
    drivers = (
        Driver(default_value_or_clock_driver_or_single_shot_driver=clock, id="driver-clock"),
        Driver(default_value_or_clock_driver_or_single_shot_driver=single_shot, id="driver-single-shot"),
        Driver(default_value_or_clock_driver_or_single_shot_driver=default, id="driver-default"),
    )
    root = _component(*drivers)

    for driver in drivers:
        selected = driver.default_value_or_clock_driver_or_single_shot_driver
        driver_id = get_handle(driver)
        if isinstance(selected, ClockDriver):
            clock_id = api.getDriverClockDriverID(driver_id)
            assert clock_id == get_handle(selected)
            assert api.getClockDriverClockPulseValue(clock_id) is True
            assert api.getClockDriverClockPulseValueExpression(clock_id) == pulse_source
            assert selected.clock_pulse_value is not None
            assert api.getClockDriverClockPulseValueID(clock_id) == get_handle(selected.clock_pulse_value)
        elif isinstance(selected, SingleShotDriver):
            assert api.getDriverSingleShotDriverID(driver_id) == get_handle(selected)
        else:
            assert api.getDriverDefaultValue(driver_id) == "42"
            assert api.getDriverDefaultValueExpression(driver_id) == "8'h2a"
            assert api.getDriverDefaultValueID(driver_id) == get_handle(selected)

    xml = XmlSerializer().render(root)
    _SCHEMA.assertValid(etree.fromstring(xml.encode()))
    parsed = XmlParser().from_string(xml, Component)
    assert parsed == root
    parsed_drivers = parsed.model.ports.port
    round_trip_values = [
        port.wire_or_transactional_or_structured.drivers.driver[0].default_value_or_clock_driver_or_single_shot_driver
        for port in parsed_drivers
    ]
    parsed_clock, parsed_single_shot, parsed_default = round_trip_values
    assert isinstance(parsed_clock, ClockDriver)
    assert parsed_clock.id == "clock-1"
    assert parsed_clock.clock_name == "clk_internal"
    assert parsed_clock.clock_period.units is DelayValueUnitType.NS
    assert parsed_clock.clock_pulse_offset.units is DelayValueUnitType.NS
    assert parsed_clock.clock_pulse_duration.units is DelayValueUnitType.PS
    assert parsed_clock.clock_pulse_value is not None
    assert parsed_clock.clock_pulse_value.value == pulse_source
    assert parsed_clock.clock_pulse_value.other_attributes == {"{urn:test}tag": "pulse"}
    assert isinstance(parsed_single_shot, SingleShotDriver)
    assert parsed_single_shot.single_shot_offset.units is DelayValueUnitType.NS
    assert parsed_single_shot.single_shot_duration.units is DelayValueUnitType.PS
    assert isinstance(parsed_default, DefaultValue)
    assert parsed_default.value == "8'h2a"
    assert parsed_default.other_attributes == {"{urn:test}tag": "default"}
    assert [driver.id for driver in parsed.model.ports.port[0].wire_or_transactional_or_structured.drivers.driver] == [
        "driver-clock"
    ]

    parsed_driver = parsed.model.ports.port[0].wire_or_transactional_or_structured.drivers.driver[0]
    parsed_clock_id = api.getDriverClockDriverID(get_handle(parsed_driver))
    assert parsed_clock_id is not None
    assert api.getClockDriverClockPulseValue(parsed_clock_id) is True
    assert api.getClockDriverClockPulseValueExpression(parsed_clock_id) == pulse_source
    assert parsed_clock.clock_pulse_value is not None
    assert api.getClockDriverClockPulseValueID(parsed_clock_id) == get_handle(parsed_clock.clock_pulse_value)
    assert api.getDriverSingleShotDriverID(
        get_handle(parsed.model.ports.port[1].wire_or_transactional_or_structured.drivers.driver[0])
    ) == get_handle(parsed_single_shot)
    parsed_default_driver = parsed.model.ports.port[2].wire_or_transactional_or_structured.drivers.driver[0]
    assert api.getDriverDefaultValue(get_handle(parsed_default_driver)) == "42"
    assert api.getDriverDefaultValueExpression(get_handle(parsed_default_driver)) == "8'h2a"
    assert api.getDriverDefaultValueID(get_handle(parsed_default_driver)) == get_handle(parsed_default)

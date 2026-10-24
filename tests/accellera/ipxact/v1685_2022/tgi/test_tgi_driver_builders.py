"""Driver builders compose validated setters and preserve generated model ownership."""

from collections.abc import Callable, Iterator
from copy import deepcopy
from inspect import signature
from typing import get_type_hints

import pytest
from lxml import etree

from amal.eda.accellera.ipxact.v1685_2022 import tgi as package_api
from amal.eda.accellera.ipxact.v1685_2022.tgi import driver as api
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import (
    TgiError,
    TgiFaultCode,
    get_handle,
    get_parent_info,
    registry,
    resolve_handle,
)
from amal.eda.ipxact_de.xml_document import XmlDocument
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
    SingleShotDriver,
    UnsignedBitExpression,
    UnsignedBitVectorExpression,
)
from org.accellera.ipxact.v1685_2022.driver_type import DriverType

_SCHEMA = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))


@pytest.fixture(autouse=True)
def clean_registry() -> Iterator[None]:
    registry.clear()
    yield
    registry.clear()


def _component(driver: Driver, view_names: tuple[str, ...] = ("rtl",)) -> Component:
    return Component(
        vendor="acme",
        library="driver-builders",
        name="builders",
        version="1.0",
        model=Model(
            views=Model.Views(view=[Model.Views.View(name=name) for name in view_names]),
            ports=Model.Ports(
                port=[
                    Port(
                        name="data",
                        wire_or_transactional_or_structured=PortWireType(
                            direction=ComponentPortDirectionType.IN,
                            drivers=Drivers(driver=[driver]),
                        ),
                    )
                ]
            ),
        ),
    )


def _round_trip(driver: Driver, view_names: tuple[str, ...] = ("rtl",)) -> Driver:
    component = _component(driver, view_names)
    serialized = XmlDocument.serializer().render(component)
    root = etree.fromstring(serialized.encode())
    assert _SCHEMA.validate(root), str(_SCHEMA.error_log)
    loaded = XmlDocument.parser().from_string(serialized, Component)
    assert loaded == component
    return loaded.model.ports.port[0].wire_or_transactional_or_structured.drivers.driver[0]


def _choice(driver: Driver) -> object | None:
    return driver.default_value_or_clock_driver_or_single_shot_driver


def test_driver_builder_exports_have_exact_annex_signatures() -> None:
    expected = {
        "addDriverSingleShotDriver": (["driverID", "offset", "value", "duration"], str, "F.7.42.1"),
        "addDriverViewRef": (["driverID", "viewRef"], str, "F.7.42.2"),
        "setDriverClockDriver": (
            ["driverID", "clockPeriod", "clockPulseOffset", "clockPulseValue", "clockPulseDuration"],
            bool,
            "F.7.42.11",
        ),
        "setDriverSingleShotDriver": (
            ["driverID", "singleShotOffset", "singleShotValue", "singleShotDuration"],
            bool,
            "F.7.42.12",
        ),
    }

    for name, (parameters, return_type, section) in expected.items():
        function = getattr(api, name)
        assert getattr(package_api, name) is function
        assert name in api.__all__
        assert name in package_api.__all__
        function_signature = signature(function)
        assert list(function_signature.parameters) == parameters
        assert [parameter.annotation for parameter in function_signature.parameters.values()] == [str] * len(parameters)
        assert function_signature.return_annotation is return_type
        assert get_type_hints(function) == dict.fromkeys(parameters, str) | {"return": return_type}
        assert f"Section: {section}." in (function.__doc__ or "")


def test_add_single_shot_driver_builds_complete_choice_and_returns_choice_handle() -> None:
    driver = Driver()
    driver_id = get_handle(driver)

    shot_id = api.addDriverSingleShotDriver(driver_id, "2 + 1", "1", "4 * 2")

    shot = _choice(driver)
    assert isinstance(shot, SingleShotDriver)
    assert shot_id == api.getDriverSingleShotDriverID(driver_id) == get_handle(shot)
    assert api.getSingleShotDriverSingleShotOffsetExpression(shot_id) == "2 + 1"
    assert api.getSingleShotDriverSingleShotValueExpression(shot_id) == "1"
    assert api.getSingleShotDriverSingleShotDurationExpression(shot_id) == "4 * 2"
    assert api.getSingleShotDriverSingleShotOffsetID(shot_id) == get_handle(shot.single_shot_offset)
    assert api.getSingleShotDriverSingleShotValueID(shot_id) == get_handle(shot.single_shot_value)
    assert api.getSingleShotDriverSingleShotDurationID(shot_id) == get_handle(shot.single_shot_duration)
    assert _round_trip(driver) == driver


@pytest.mark.parametrize(
    "existing",
    [
        DefaultValue(value="1"),
        ClockDriver(
            clock_period=ClockDriverType.ClockPeriod(value="10"),
            clock_pulse_offset=ClockDriverType.ClockPulseOffset(value="0"),
            clock_pulse_value=UnsignedBitExpression(value="1"),
            clock_pulse_duration=ClockDriverType.ClockPulseDuration(value="5"),
        ),
        SingleShotDriver(
            single_shot_offset=SingleShotDriver.SingleShotOffset(value="1"),
            single_shot_value=UnsignedBitVectorExpression(value="1"),
            single_shot_duration=SingleShotDriver.SingleShotDuration(value="2"),
        ),
    ],
    ids=["default-value", "clock-driver", "single-shot-driver"],
)
def test_add_single_shot_driver_rejects_any_existing_choice_without_mutation(
    existing: DefaultValue | ClockDriver | SingleShotDriver,
) -> None:
    driver = Driver(default_value_or_clock_driver_or_single_shot_driver=existing)
    before = deepcopy(driver)

    with pytest.raises(TgiError) as error:
        api.addDriverSingleShotDriver(get_handle(driver), "1", "1", "2")

    assert error.value.fault_code == TgiFaultCode.ALREADY_EXISTS
    assert driver == before
    assert _choice(driver) is existing


@pytest.mark.parametrize(
    ("offset", "value", "duration"),
    [
        ("1 +", "1", "2"),
        ("1", "2", "2"),
        ("1", "1'bx", "2"),
        ("1", "1", "1.0 / 0.0"),
        ("1", "1", "1e9999"),
        ("1", "1", "bad\x00xml"),
    ],
)
def test_add_single_shot_driver_validates_every_source_before_creating_choice(
    offset: str, value: str, duration: str
) -> None:
    driver = Driver()
    before = deepcopy(driver)

    with pytest.raises(TgiError) as error:
        api.addDriverSingleShotDriver(get_handle(driver), offset, value, duration)

    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert driver == before
    assert _choice(driver) is None


@pytest.mark.parametrize("source", [None, 3, float("nan"), float("inf")])
def test_add_single_shot_driver_rejects_native_sources_atomically(source: object) -> None:
    driver = Driver()
    before = deepcopy(driver)

    with pytest.raises(TgiError) as error:
        api.addDriverSingleShotDriver(get_handle(driver), "1", "1", source)  # type: ignore[arg-type]

    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert driver == before


@pytest.mark.parametrize("source", ["0", "1", "1 + 0", "CONFIGURED_VALUE"])
def test_set_single_shot_driver_keeps_valid_zero_one_and_symbolic_value_sources(source: str) -> None:
    driver = Driver()
    driver_id = get_handle(driver)

    assert api.setDriverSingleShotDriver(driver_id, "CONFIGURED_OFFSET", source, "CONFIGURED_DURATION")

    shot = _choice(driver)
    assert isinstance(shot, SingleShotDriver)
    shot_id = api.getDriverSingleShotDriverID(driver_id)
    assert shot_id == get_handle(shot)
    assert api.getSingleShotDriverSingleShotOffsetExpression(shot_id) == "CONFIGURED_OFFSET"
    assert api.getSingleShotDriverSingleShotValueExpression(shot_id) == source
    assert api.getSingleShotDriverSingleShotDurationExpression(shot_id) == "CONFIGURED_DURATION"
    if source == "CONFIGURED_VALUE":
        with pytest.raises(TgiError) as error:
            api.getSingleShotDriverSingleShotValue(shot_id)
        assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    else:
        expected = 0 if source == "0" else 1
        assert api.getSingleShotDriverSingleShotValue(shot_id) == expected


@pytest.mark.parametrize(
    ("operation", "arguments"),
    [
        (api.addDriverSingleShotDriver, ("1", "1", "2")),
        (api.setDriverClockDriver, ("1", "0", "1", "2")),
        (api.setDriverSingleShotDriver, ("1", "1", "2")),
    ],
    ids=["add-single-shot", "set-clock", "set-single-shot"],
)
def test_choice_builders_reject_invalid_driver_handles(
    operation: Callable[..., str | bool], arguments: tuple[str, ...]
) -> None:
    with pytest.raises(TgiError) as error:
        operation("missing-driver", *arguments)
    assert error.value.fault_code == TgiFaultCode.INVALID_ID

    wrong_handle = get_handle(DriverType.ViewRef(value="rtl"))
    with pytest.raises(TgiError) as error:
        operation(wrong_handle, *arguments)
    assert error.value.fault_code == TgiFaultCode.INVALID_ID


def test_add_driver_view_ref_rejects_invalid_driver_handles() -> None:
    with pytest.raises(TgiError) as error:
        api.addDriverViewRef("missing-driver", "rtl")
    assert error.value.fault_code == TgiFaultCode.INVALID_ID

    wrong_handle = get_handle(DriverType.ViewRef(value="rtl"))
    with pytest.raises(TgiError) as error:
        api.addDriverViewRef(wrong_handle, "rtl")
    assert error.value.fault_code == TgiFaultCode.INVALID_ID


def test_set_clock_driver_bitcasts_pulse_value_and_preserves_source() -> None:
    driver = Driver()
    driver_id = get_handle(driver)

    assert api.setDriverClockDriver(driver_id, "10", "0", "3", "5")

    clock = _choice(driver)
    assert isinstance(clock, ClockDriver)
    clock_id = api.getDriverClockDriverID(driver_id)
    assert clock_id == get_handle(clock)
    assert api.getClockDriverClockPeriodExpression(clock_id) == "10"
    assert api.getClockDriverClockPulseOffsetExpression(clock_id) == "0"
    assert api.getClockDriverClockPulseValueExpression(clock_id) == "3"
    assert api.getClockDriverClockPulseValue(clock_id) is True
    assert api.getClockDriverClockPulseDurationExpression(clock_id) == "5"
    assert _round_trip(driver) == driver


def test_set_single_shot_driver_preserves_same_choice_wrapper_metadata_units_and_bounds() -> None:
    offset = SingleShotDriver.SingleShotOffset(
        value="1", units=DelayValueUnitType.NS, minimum=1.0, maximum=5.0, other_attributes={"{urn:test}tag": "offset"}
    )
    value = UnsignedBitVectorExpression(value="0", other_attributes={"{urn:test}tag": "value"})
    duration = SingleShotDriver.SingleShotDuration(
        value="2", units=DelayValueUnitType.PS, minimum=1.0, maximum=8.0, other_attributes={"{urn:test}tag": "duration"}
    )
    shot = SingleShotDriver(single_shot_offset=offset, single_shot_value=value, single_shot_duration=duration)
    driver = Driver(default_value_or_clock_driver_or_single_shot_driver=shot)
    driver_id = get_handle(driver)
    shot_id = get_handle(shot)
    old_field_ids = (get_handle(offset), get_handle(value), get_handle(duration))

    assert api.setDriverSingleShotDriver(driver_id, "3", "1", "4")

    assert api.getDriverSingleShotDriverID(driver_id) == shot_id
    assert _choice(driver) is shot
    assert (shot.single_shot_offset, shot.single_shot_value, shot.single_shot_duration) == (offset, value, duration)
    assert (offset.value, value.value, duration.value) == ("3", "1", "4")
    assert (offset.units, offset.minimum, offset.maximum, offset.other_attributes) == (
        DelayValueUnitType.NS,
        1.0,
        5.0,
        {"{urn:test}tag": "offset"},
    )
    assert (duration.units, duration.minimum, duration.maximum, duration.other_attributes) == (
        DelayValueUnitType.PS,
        1.0,
        8.0,
        {"{urn:test}tag": "duration"},
    )
    assert value.other_attributes == {"{urn:test}tag": "value"}
    assert api.getSingleShotDriverSingleShotOffsetID(shot_id) == old_field_ids[0]
    assert api.getSingleShotDriverSingleShotValueID(shot_id) == old_field_ids[1]
    assert api.getSingleShotDriverSingleShotDurationID(shot_id) == old_field_ids[2]


@pytest.mark.parametrize("invalid_value", ["2", "1'bx", "1 +"])
def test_set_single_shot_driver_rejects_invalid_resolved_value_before_creating_choice(invalid_value: str) -> None:
    driver = Driver()
    before = deepcopy(driver)

    with pytest.raises(TgiError) as error:
        api.setDriverSingleShotDriver(get_handle(driver), "3", invalid_value, "4")

    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert driver == before
    assert _choice(driver) is None


def test_set_clock_driver_preserves_same_choice_wrappers_units_bounds_and_handles() -> None:
    period = ClockDriverType.ClockPeriod(value="10", units=DelayValueUnitType.NS, minimum=1.0, maximum=20.0)
    offset = ClockDriverType.ClockPulseOffset(value="0", units=DelayValueUnitType.PS, minimum=0.0, maximum=5.0)
    pulse = UnsignedBitExpression(value="1")
    duration = ClockDriverType.ClockPulseDuration(value="5", units=DelayValueUnitType.NS, minimum=1.0, maximum=10.0)
    clock = ClockDriver(
        clock_period=period, clock_pulse_offset=offset, clock_pulse_value=pulse, clock_pulse_duration=duration
    )
    driver = Driver(default_value_or_clock_driver_or_single_shot_driver=clock)
    driver_id = get_handle(driver)
    clock_id = get_handle(clock)
    field_ids = (get_handle(period), get_handle(offset), get_handle(pulse), get_handle(duration))

    assert api.setDriverClockDriver(driver_id, "12", "2", "3", "7")

    assert api.getDriverClockDriverID(driver_id) == clock_id
    assert _choice(driver) is clock
    assert (clock.clock_period, clock.clock_pulse_offset, clock.clock_pulse_value, clock.clock_pulse_duration) == (
        period,
        offset,
        pulse,
        duration,
    )
    assert (period.value, offset.value, pulse.value, duration.value) == ("12", "2", "3", "7")
    assert api.getClockDriverClockPeriodID(clock_id) == field_ids[0]
    assert api.getClockDriverClockPulseOffsetID(clock_id) == field_ids[1]
    assert api.getClockDriverClockPulseValueID(clock_id) == field_ids[2]
    assert api.getClockDriverClockPulseDurationID(clock_id) == field_ids[3]
    assert (period.units, period.minimum, period.maximum) == (DelayValueUnitType.NS, 1.0, 20.0)
    assert (offset.units, offset.minimum, offset.maximum) == (DelayValueUnitType.PS, 0.0, 5.0)
    assert (duration.units, duration.minimum, duration.maximum) == (DelayValueUnitType.NS, 1.0, 10.0)


@pytest.mark.parametrize(
    ("operation", "valid_prefix", "invalid_last"),
    [
        (api.setDriverClockDriver, ("12", "2", "3"), "1 +"),
        (api.setDriverSingleShotDriver, ("3", "1"), "1e9999"),
    ],
    ids=["clock", "single-shot"],
)
def test_choice_builders_validate_later_fields_before_mutating_existing_choice(
    operation: Callable[..., str | bool], valid_prefix: tuple[str, ...], invalid_last: str
) -> None:
    existing = DefaultValue(value="1")
    driver = Driver(default_value_or_clock_driver_or_single_shot_driver=existing)
    before = deepcopy(driver)

    with pytest.raises(TgiError) as error:
        operation(get_handle(driver), *valid_prefix, invalid_last)

    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert driver == before
    assert _choice(driver) is existing
    assert resolve_handle(get_handle(existing)) is existing


@pytest.mark.parametrize(
    ("operation", "arguments"),
    [
        (api.setDriverClockDriver, ("20", "2", "3", "7")),
        (api.setDriverSingleShotDriver, ("3", "1", "4")),
    ],
    ids=["clock", "single-shot"],
)
@pytest.mark.parametrize("bad_source", [None, 3, float("nan"), float("inf"), "1e9999", "1.0 / 0.0"])
def test_choice_builders_reject_native_and_nonfinite_sources_atomically(
    operation: Callable[..., str | bool], arguments: tuple[str, ...], bad_source: object
) -> None:
    driver = Driver()
    before = deepcopy(driver)
    values = (*arguments[:-1], bad_source)

    with pytest.raises(TgiError) as error:
        operation(get_handle(driver), *values)

    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert driver == before
    assert _choice(driver) is None


def test_set_driver_builders_replace_alternate_choice_and_invalidate_old_subtree() -> None:
    previous = SingleShotDriver(
        single_shot_offset=SingleShotDriver.SingleShotOffset(value="1"),
        single_shot_value=UnsignedBitVectorExpression(value="1"),
        single_shot_duration=SingleShotDriver.SingleShotDuration(value="2"),
    )
    driver = Driver(default_value_or_clock_driver_or_single_shot_driver=previous)
    driver_id = get_handle(driver)
    previous_id = get_handle(previous)
    old_child_ids = (
        get_handle(previous.single_shot_offset),
        get_handle(previous.single_shot_value),
        get_handle(previous.single_shot_duration),
    )

    assert api.setDriverClockDriver(driver_id, "10", "0", "3", "5")

    clock = _choice(driver)
    assert isinstance(clock, ClockDriver)
    clock_id = api.getDriverClockDriverID(driver_id)
    assert clock_id == get_handle(clock)
    assert all(resolve_handle(handle) is None for handle in (previous_id, *old_child_ids))
    assert api.getDriverSingleShotDriverID(driver_id) is None
    assert (
        clock.clock_period.value,
        clock.clock_pulse_offset.value,
        clock.clock_pulse_value.value,
        clock.clock_pulse_duration.value,
    ) == (
        "10",
        "0",
        "3",
        "5",
    )

    clock_child_ids = (
        get_handle(clock.clock_period),
        get_handle(clock.clock_pulse_offset),
        get_handle(clock.clock_pulse_value),
        get_handle(clock.clock_pulse_duration),
    )
    assert api.setDriverSingleShotDriver(driver_id, "2", "0", "4")
    shot = _choice(driver)
    assert isinstance(shot, SingleShotDriver)
    shot_id = api.getDriverSingleShotDriverID(driver_id)
    assert shot_id == get_handle(shot)
    assert all(resolve_handle(handle) is None for handle in (clock_id, *clock_child_ids))
    assert api.getDriverClockDriverID(driver_id) is None
    assert (shot.single_shot_offset.value, shot.single_shot_value.value, shot.single_shot_duration.value) == (
        "2",
        "0",
        "4",
    )
    assert _round_trip(driver) == driver


@pytest.mark.parametrize(
    ("view_ref", "expected"),
    [("\t9rtl\n", "9rtl"), (" qualified:rtl ", "qualified:rtl"), (" λ-view ", "λ-view")],
)
def test_add_driver_view_ref_normalizes_nmtoken_and_allows_forward_references(view_ref: str, expected: str) -> None:
    driver = Driver()
    driver_id = get_handle(driver)

    reference_id = api.addDriverViewRef(driver_id, view_ref)

    assert driver.view_ref == [DriverType.ViewRef(value=expected)]
    assert api.getDriverViewRefIDs(driver_id) == [reference_id]
    reference = resolve_handle(reference_id)
    assert isinstance(reference, DriverType.ViewRef)
    assert reference.value == expected
    assert api.getDriverViewRefIDs(driver_id) == [reference_id]
    with pytest.raises(TgiError) as error:
        api.getDriverViewRefByID(driver_id, reference_id)
    assert error.value.fault_code == TgiFaultCode.NOT_FOUND
    owner = get_parent_info(reference_id)
    assert owner is not None
    assert (owner.parent_handle, owner.path, owner.container) == (driver_id, ("view_ref",), "list")
    driver.default_value_or_clock_driver_or_single_shot_driver = DefaultValue(value="0")
    assert _round_trip(driver, (expected,)) == driver


@pytest.mark.parametrize("invalid", ["", " \t ", "bad token", "bad/name", "bad\x00name", None, 7])
def test_add_driver_view_ref_rejects_invalid_tokens_without_mutation(invalid: object) -> None:
    driver = Driver(view_ref=[DriverType.ViewRef(value="rtl")])
    before = deepcopy(driver)

    with pytest.raises(TgiError) as error:
        api.addDriverViewRef(get_handle(driver), invalid)  # type: ignore[arg-type]

    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert driver == before


def test_add_driver_view_ref_rejects_duplicate_after_normalization() -> None:
    existing = DriverType.ViewRef(value="rtl")
    driver = Driver(view_ref=[existing])
    driver_id = get_handle(driver)
    existing_id = get_handle(existing)

    with pytest.raises(TgiError) as error:
        api.addDriverViewRef(driver_id, "\t rtl \n")

    assert error.value.fault_code == TgiFaultCode.ALREADY_EXISTS
    assert driver.view_ref == [existing]
    assert driver.view_ref[0] is existing
    assert get_handle(existing) == existing_id
    assert api.getDriverViewRefIDs(driver_id) == [existing_id]


def test_add_driver_view_ref_normalizes_tuple_collection_to_owned_list() -> None:
    first = DriverType.ViewRef(value="9rtl")
    second = DriverType.ViewRef(value="gate")
    driver = Driver()
    driver.view_ref = (first, second)  # type: ignore[assignment]
    driver_id = get_handle(driver)

    added_id = api.addDriverViewRef(driver_id, "future-view")

    assert isinstance(driver.view_ref, list)
    assert driver.view_ref[:2] == [first, second]
    assert driver.view_ref[0] is first
    assert driver.view_ref[1] is second
    assert [entry.value for entry in driver.view_ref] == ["9rtl", "gate", "future-view"]
    assert api.getDriverViewRefIDs(driver_id)[-1] == added_id
    assert get_parent_info(added_id).container == "list"

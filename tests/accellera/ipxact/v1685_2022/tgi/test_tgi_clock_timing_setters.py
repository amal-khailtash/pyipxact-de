"""Clock timing setters retain expression source, metadata, and element identity."""

from collections.abc import Callable, Iterator
from inspect import getdoc, signature
from typing import NamedTuple, get_type_hints

import pytest
from lxml import etree
from xsdata.formats.dataclass.parsers import XmlParser
from xsdata.formats.dataclass.serializers import XmlSerializer

from amal.eda.accellera.ipxact.v1685_2022 import tgi as package_api
from amal.eda.accellera.ipxact.v1685_2022.tgi import driver as api
from amal.eda.accellera.ipxact.v1685_2022.tgi import miscellaneous as misc_api
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import (
    TgiError,
    TgiFaultCode,
    get_handle,
    get_parent_info,
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
from org.accellera.ipxact.v1685_2022.other_clocks import OtherClocks

_SCHEMA = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))


class _TimingOperation(NamedTuple):
    owner_type: type[ClockDriver] | type[OtherClockDriver]
    field_name: str
    wrapper_type: type[RealExpression]
    setter: Callable[[str, str], bool]
    numeric_getter: Callable[[str], float | None]
    expression_getter: Callable[[str], str | None]
    id_getter: Callable[[str], str | None]
    id_parameter: str
    value_parameter: str
    section: str


_TIMING_OPERATIONS = (
    _TimingOperation(
        ClockDriver,
        "clock_period",
        ClockDriverType.ClockPeriod,
        api.setClockDriverClockPeriod,
        api.getClockDriverClockPeriod,
        api.getClockDriverClockPeriodExpression,
        api.getClockDriverClockPeriodID,
        "clockDriverID",
        "clockPeriod",
        "F.7.42.7",
    ),
    _TimingOperation(
        ClockDriver,
        "clock_pulse_duration",
        ClockDriverType.ClockPulseDuration,
        api.setClockDriverClockPulseDuration,
        api.getClockDriverClockPulseDuration,
        api.getClockDriverClockPulseDurationExpression,
        api.getClockDriverClockPulseDurationID,
        "clockDriverID",
        "clockPulseDuration",
        "F.7.42.8",
    ),
    _TimingOperation(
        ClockDriver,
        "clock_pulse_offset",
        ClockDriverType.ClockPulseOffset,
        api.setClockDriverClockPulseOffset,
        api.getClockDriverClockPulseOffset,
        api.getClockDriverClockPulseOffsetExpression,
        api.getClockDriverClockPulseOffsetID,
        "clockDriverID",
        "pulseOffset",
        "F.7.42.9",
    ),
    _TimingOperation(
        OtherClockDriver,
        "clock_period",
        ClockDriverType.ClockPeriod,
        api.setOtherClockDriverClockPeriod,
        api.getOtherClockDriverClockPeriod,
        api.getOtherClockDriverClockPeriodExpression,
        api.getOtherClockDriverClockPeriodID,
        "otherClockDriverID",
        "clockPeriod",
        "F.7.42.15",
    ),
    _TimingOperation(
        OtherClockDriver,
        "clock_pulse_duration",
        ClockDriverType.ClockPulseDuration,
        api.setOtherClockDriverClockPulseDuration,
        api.getOtherClockDriverClockPulseDuration,
        api.getOtherClockDriverClockPulseDurationExpression,
        api.getOtherClockDriverClockPulseDurationID,
        "otherClockDriverID",
        "clockPulseDuration",
        "F.7.42.16",
    ),
    _TimingOperation(
        OtherClockDriver,
        "clock_pulse_offset",
        ClockDriverType.ClockPulseOffset,
        api.setOtherClockDriverClockPulseOffset,
        api.getOtherClockDriverClockPulseOffset,
        api.getOtherClockDriverClockPulseOffsetExpression,
        api.getOtherClockDriverClockPulseOffsetID,
        "otherClockDriverID",
        "clockPulseOffset",
        "F.7.42.17",
    ),
)
_TIMING_OPERATION_IDS = [operation.setter.__name__ for operation in _TIMING_OPERATIONS]
_FIELD_TO_SOURCE = {
    "clock_period": "8 / 2",
    "clock_pulse_duration": "2.5",
    "clock_pulse_offset": "1 + 2",
}


@pytest.fixture(autouse=True)
def clean_registry() -> Iterator[None]:
    registry.clear()
    yield
    registry.clear()


def _clock(owner_type: type[ClockDriver] | type[OtherClockDriver]) -> ClockDriver | OtherClockDriver:
    values = {
        "clock_period": ClockDriverType.ClockPeriod(value="4", units=DelayValueUnitType.PS),
        "clock_pulse_offset": ClockDriverType.ClockPulseOffset(value="3", units=DelayValueUnitType.NS),
        "clock_pulse_value": UnsignedBitExpression(value="1"),
        "clock_pulse_duration": ClockDriverType.ClockPulseDuration(value="2", units=DelayValueUnitType.PS),
    }
    if owner_type is ClockDriver:
        return ClockDriver(**values, clock_name="internal-clock", id="clock-driver-id")
    return OtherClockDriver(**values, clock_name="external-clock", clock_source="pll.clk", id="other-clock-id")


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
def test_other_clock_pulse_value_uses_standard_bit_cast_and_preserves_source(source: str, expected: bool) -> None:
    clock = _clock(OtherClockDriver)
    assert isinstance(clock, OtherClockDriver)
    clock.clock_pulse_value = UnsignedBitExpression(value=source)
    clock_id = get_handle(clock)

    assert api.getOtherClockDriverClockPulseValue(clock_id) is expected
    assert api.getOtherClockDriverClockPulseValueExpression(clock_id) == source
    value_id = api.getOtherClockDriverClockPulseValueID(clock_id)
    assert value_id == get_handle(clock.clock_pulse_value)
    owner = get_parent_info(value_id)
    assert owner is not None
    assert (owner.parent_handle, owner.path, owner.container) == (clock_id, ("clock_pulse_value",), "single")


def test_other_clock_pulse_value_getters_cover_absent_invalid_and_wrong_driver_handles() -> None:
    clock = _clock(OtherClockDriver)
    assert isinstance(clock, OtherClockDriver)
    clock_id = get_handle(clock)
    getters = (
        api.getOtherClockDriverClockPulseValue,
        api.getOtherClockDriverClockPulseValueExpression,
        api.getOtherClockDriverClockPulseValueID,
    )

    clock.clock_pulse_value = None  # type: ignore[assignment]
    assert [getter(clock_id) for getter in getters] == [None, None, None]

    clock.clock_pulse_value = RealExpression(value="1")  # type: ignore[assignment]
    for getter in getters:
        with pytest.raises(TgiError) as error:
            getter(clock_id)
        assert error.value.fault_code == TgiFaultCode.INVALID_ID

    other_id = get_handle(_clock(ClockDriver))
    for invalid_id in ("missing-other-clock", other_id):
        for getter in getters:
            with pytest.raises(TgiError) as error:
                getter(invalid_id)
            assert error.value.fault_code == TgiFaultCode.INVALID_ID


@pytest.mark.parametrize("source", ["UNRESOLVED_PULSE", "1 +"])
def test_other_clock_pulse_value_rejects_unresolved_or_malformed_expression(source: str) -> None:
    clock = _clock(OtherClockDriver)
    assert isinstance(clock, OtherClockDriver)
    clock.clock_pulse_value = UnsignedBitExpression(value=source)
    clock_id = get_handle(clock)

    with pytest.raises(TgiError) as error:
        api.getOtherClockDriverClockPulseValue(clock_id)
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert api.getOtherClockDriverClockPulseValueExpression(clock_id) == source


def test_other_clock_pulse_value_exports_have_annex_signatures_and_native_types() -> None:
    expected = (
        (api.getOtherClockDriverClockPulseValue, bool | None, "F.7.41.33"),
        (api.getOtherClockDriverClockPulseValueExpression, str | None, "F.7.41.34"),
        (api.getOtherClockDriverClockPulseValueID, str | None, "F.7.41.35"),
    )
    for function, return_type, section in expected:
        assert function.__name__ in api.__all__
        assert function.__name__ in package_api.__all__
        assert getattr(package_api, function.__name__) is function
        function_signature = signature(function)
        assert list(function_signature.parameters) == ["otherClockDriverID"]
        assert function_signature.parameters["otherClockDriverID"].annotation is str
        assert function_signature.return_annotation == return_type
        assert get_type_hints(function) == {"otherClockDriverID": str, "return": return_type}
        assert f"Section: {section}." in getdoc(function)


@pytest.mark.parametrize("operation", _TIMING_OPERATIONS, ids=_TIMING_OPERATION_IDS)
def test_clock_timing_setters_have_exact_annex_contracts(operation: _TimingOperation) -> None:
    function = operation.setter
    assert function.__name__ in api.__all__
    assert function.__name__ in package_api.__all__
    assert getattr(package_api, function.__name__) is function
    function_signature = signature(function)
    assert list(function_signature.parameters) == [operation.id_parameter, operation.value_parameter]
    assert [parameter.annotation for parameter in function_signature.parameters.values()] == [str, str]
    assert function_signature.return_annotation is bool
    assert get_type_hints(function) == {
        operation.id_parameter: str,
        operation.value_parameter: str,
        "return": bool,
    }
    doc = getdoc(function)
    assert f"Section: {operation.section}." in doc


@pytest.mark.parametrize("operation", _TIMING_OPERATIONS, ids=_TIMING_OPERATION_IDS)
def test_clock_timing_setters_preserve_wrapper_identity_metadata_and_ownership(operation: _TimingOperation) -> None:
    owner = _clock(operation.owner_type)
    owner_id = get_handle(owner)
    wrapper = getattr(owner, operation.field_name)
    wrapper.units = DelayValueUnitType.PS
    wrapper.minimum = 1.0
    wrapper.maximum = 10.0
    wrapper.other_attributes = {"{urn:test}tag": "keep"}
    wrapper_id = get_handle(wrapper)
    sibling_values = {
        field: getattr(owner, field)
        for field in ("clock_period", "clock_pulse_duration", "clock_pulse_offset")
        if field != operation.field_name
    }
    source = _FIELD_TO_SOURCE[operation.field_name]

    assert operation.setter(owner_id, source)

    assert getattr(owner, operation.field_name) is wrapper
    assert wrapper.value == source
    assert (wrapper.units, wrapper.minimum, wrapper.maximum, wrapper.other_attributes) == (
        DelayValueUnitType.PS,
        1.0,
        10.0,
        {"{urn:test}tag": "keep"},
    )
    assert operation.id_getter(owner_id) == wrapper_id
    assert operation.expression_getter(owner_id) == source
    assert operation.numeric_getter(owner_id) == {"8 / 2": 4.0, "2.5": 2.5, "1 + 2": 3.0}[source]
    assert all(getattr(owner, field) is value for field, value in sibling_values.items())
    ownership = get_parent_info(wrapper_id)
    assert ownership is not None
    assert (ownership.parent_handle, ownership.path, ownership.container) == (
        owner_id,
        (operation.field_name,),
        "single",
    )


@pytest.mark.parametrize("operation", _TIMING_OPERATIONS, ids=_TIMING_OPERATION_IDS)
def test_clock_timing_setters_create_missing_wrapper_with_ownership(operation: _TimingOperation) -> None:
    owner = _clock(operation.owner_type)
    setattr(owner, operation.field_name, None)
    owner_id = get_handle(owner)
    source = _FIELD_TO_SOURCE[operation.field_name]

    assert operation.setter(owner_id, source)

    wrapper = getattr(owner, operation.field_name)
    assert isinstance(wrapper, operation.wrapper_type)
    assert wrapper.value == source
    assert operation.id_getter(owner_id) == get_handle(wrapper)
    ownership = get_parent_info(get_handle(wrapper))
    assert ownership is not None
    assert (ownership.parent_handle, ownership.path, ownership.container) == (
        owner_id,
        (operation.field_name,),
        "single",
    )


@pytest.mark.parametrize("operation", _TIMING_OPERATIONS, ids=_TIMING_OPERATION_IDS)
def test_clock_timing_setters_reject_wrong_driver_and_wrapper_handles(operation: _TimingOperation) -> None:
    with pytest.raises(TgiError) as error:
        operation.setter("missing-clock-id", "3")
    assert error.value.fault_code == TgiFaultCode.INVALID_ID

    wrong_owner_type = OtherClockDriver if operation.owner_type is ClockDriver else ClockDriver
    wrong_owner = _clock(wrong_owner_type)
    with pytest.raises(TgiError) as error:
        operation.setter(get_handle(wrong_owner), "3")
    assert error.value.fault_code == TgiFaultCode.INVALID_ID

    owner = _clock(operation.owner_type)
    wrong_wrapper = UnsignedBitExpression(value="3")
    setattr(owner, operation.field_name, wrong_wrapper)
    owner_id = get_handle(owner)
    with pytest.raises(TgiError) as error:
        operation.setter(owner_id, "4")
    assert error.value.fault_code == TgiFaultCode.INVALID_ID
    assert getattr(owner, operation.field_name) is wrong_wrapper
    assert wrong_wrapper.value == "3"


@pytest.mark.parametrize("operation", _TIMING_OPERATIONS, ids=_TIMING_OPERATION_IDS)
@pytest.mark.parametrize(
    "source",
    [
        None,
        4,
        float("nan"),
        float("inf"),
        "",
        "1 +",
        "1'bx",
        'string\'("not numeric")',
        "1.0 / 0.0",
        "1e9999",
        "bad\x00xml",
    ],
)
def test_clock_timing_setters_reject_invalid_sources_atomically(operation: _TimingOperation, source: object) -> None:
    owner = _clock(operation.owner_type)
    wrapper = getattr(owner, operation.field_name)
    wrapper.value = "3"
    wrapper.minimum = 1.0
    wrapper.maximum = 5.0
    owner_id = get_handle(owner)

    with pytest.raises(TgiError) as error:
        operation.setter(owner_id, source)  # type: ignore[arg-type]
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert getattr(owner, operation.field_name) is wrapper
    assert wrapper.value == "3"
    assert (wrapper.minimum, wrapper.maximum) == (1.0, 5.0)


@pytest.mark.parametrize("operation", _TIMING_OPERATIONS, ids=_TIMING_OPERATION_IDS)
@pytest.mark.parametrize(
    ("minimum", "maximum", "source"),
    [(1.0, 5.0, "0"), (1.0, 5.0, "6"), (float("nan"), 5.0, "3"), (5.0, 4.0, "3")],
)
def test_clock_timing_setters_reject_bound_violations_atomically(
    operation: _TimingOperation, minimum: float, maximum: float, source: str
) -> None:
    owner = _clock(operation.owner_type)
    wrapper = getattr(owner, operation.field_name)
    wrapper.value = "3"
    wrapper.minimum = minimum
    wrapper.maximum = maximum
    owner_id = get_handle(owner)

    with pytest.raises(TgiError) as error:
        operation.setter(owner_id, source)
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert wrapper.value == "3"
    assert getattr(owner, operation.field_name) is wrapper


@pytest.mark.parametrize("operation", _TIMING_OPERATIONS, ids=_TIMING_OPERATION_IDS)
@pytest.mark.parametrize(("source", "expected"), [("1", 1.0), ("5", 5.0)])
def test_clock_timing_setters_accept_inclusive_bounds(
    operation: _TimingOperation, source: str, expected: float
) -> None:
    owner = _clock(operation.owner_type)
    wrapper = getattr(owner, operation.field_name)
    wrapper.minimum = 1.0
    wrapper.maximum = 5.0

    assert operation.setter(get_handle(owner), source)
    assert wrapper.value == source
    assert operation.numeric_getter(get_handle(owner)) == expected


@pytest.mark.parametrize("operation", _TIMING_OPERATIONS, ids=_TIMING_OPERATION_IDS)
def test_clock_timing_setters_accept_schema_infinite_bounds(operation: _TimingOperation) -> None:
    owner = _clock(operation.owner_type)
    wrapper = getattr(owner, operation.field_name)
    wrapper.minimum = float("-inf")
    wrapper.maximum = float("inf")

    assert operation.setter(get_handle(owner), "2")
    assert wrapper.value == "2"
    assert operation.numeric_getter(get_handle(owner)) == 2.0


@pytest.mark.parametrize("operation", _TIMING_OPERATIONS, ids=_TIMING_OPERATION_IDS)
@pytest.mark.parametrize(("minimum", "maximum"), [(float("nan"), 5.0), (5.0, 4.0)])
def test_clock_timing_setters_reject_invalid_bounds_for_unresolved_sources(
    operation: _TimingOperation, minimum: float, maximum: float
) -> None:
    owner = _clock(operation.owner_type)
    wrapper = getattr(owner, operation.field_name)
    wrapper.value = "3"
    wrapper.minimum = minimum
    wrapper.maximum = maximum

    with pytest.raises(TgiError) as error:
        operation.setter(get_handle(owner), "CONFIGURED_CLOCK_PERIOD")
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert wrapper.value == "3"


@pytest.mark.parametrize("operation", _TIMING_OPERATIONS, ids=_TIMING_OPERATION_IDS)
def test_clock_timing_setters_defer_unresolved_identifiers(operation: _TimingOperation) -> None:
    owner = _clock(operation.owner_type)
    owner_id = get_handle(owner)

    for source in ("CONFIGURED_CLOCK_PERIOD", "nan", "inf"):
        assert operation.setter(owner_id, source)
        assert operation.expression_getter(owner_id) == source
        with pytest.raises(TgiError) as error:
            operation.numeric_getter(owner_id)
        assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT


@pytest.mark.parametrize("operation", _TIMING_OPERATIONS, ids=_TIMING_OPERATION_IDS)
def test_clock_timing_setters_do_not_create_missing_wrapper_for_invalid_source(operation: _TimingOperation) -> None:
    owner = _clock(operation.owner_type)
    setattr(owner, operation.field_name, None)
    owner_id = get_handle(owner)

    with pytest.raises(TgiError) as error:
        operation.setter(owner_id, "1 +")
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert getattr(owner, operation.field_name) is None


def test_set_expression_value_validates_real_expressions_and_defers_identifiers() -> None:
    expression = ClockDriverType.ClockPeriod(
        value="2", units=DelayValueUnitType.PS, minimum=1.0, maximum=5.0, other_attributes={"{urn:test}tag": "keep"}
    )
    expression_id = get_handle(expression)

    assert misc_api.setExpressionValue(expression_id, "2 + 2")
    assert expression.value == "2 + 2"
    assert (expression.units, expression.minimum, expression.maximum, expression.other_attributes) == (
        DelayValueUnitType.PS,
        1.0,
        5.0,
        {"{urn:test}tag": "keep"},
    )

    for source in ("1 +", "0", "6", "1'bx", 'string\'("not numeric")', "1.0 / 0.0", "1e9999"):
        with pytest.raises(TgiError) as error:
            misc_api.setExpressionValue(expression_id, source)
        assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
        assert expression.value == "2 + 2"

    for source in ("CONFIGURED_PERIOD", "nan", "inf"):
        assert misc_api.setExpressionValue(expression_id, source)
        assert expression.value == source
        with pytest.raises(TgiError) as error:
            api.getClockDriverClockPeriod(get_handle(_clock_with_period(expression)))
        assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT


@pytest.mark.parametrize("source", ["3", "CONFIGURED_PERIOD"])
@pytest.mark.parametrize(("minimum", "maximum"), [(float("nan"), 5.0), (5.0, 4.0)])
def test_set_expression_value_rejects_invalid_real_bounds_atomically(
    source: str, minimum: float, maximum: float
) -> None:
    expression = ClockDriverType.ClockPeriod(value="2", minimum=minimum, maximum=maximum)

    with pytest.raises(TgiError) as error:
        misc_api.setExpressionValue(get_handle(expression), source)
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert expression.value == "2"


def _clock_with_period(period: ClockDriverType.ClockPeriod) -> ClockDriver:
    clock = _clock(ClockDriver)
    assert isinstance(clock, ClockDriver)
    clock.clock_period = period
    return clock


@pytest.mark.parametrize("owner_type", [ClockDriver, OtherClockDriver])
def test_clock_timing_setters_round_trip_source_units_bounds_and_identity(
    owner_type: type[ClockDriver] | type[OtherClockDriver],
) -> None:
    clock = _clock(owner_type)
    for operation in (entry for entry in _TIMING_OPERATIONS if entry.owner_type is owner_type):
        wrapper = getattr(clock, operation.field_name)
        wrapper.minimum = 0.0
        wrapper.maximum = 10.0
        wrapper.units = DelayValueUnitType.PS
        assert operation.setter(get_handle(clock), _FIELD_TO_SOURCE[operation.field_name])

    if owner_type is ClockDriver:
        component = Component(
            vendor="acme",
            library="test",
            name="clock-setters",
            version="1.0",
            model=Model(
                ports=Model.Ports(
                    port=[
                        Port(
                            name="clk",
                            wire_or_transactional_or_structured=PortWireType(
                                direction=ComponentPortDirectionType.IN,
                                drivers=Drivers(
                                    driver=[
                                        Driver(
                                            default_value_or_clock_driver_or_single_shot_driver=clock,
                                        )
                                    ]
                                ),
                            ),
                        )
                    ]
                )
            ),
        )
    else:
        component = Component(
            vendor="acme",
            library="test",
            name="other-clock-setters",
            version="1.0",
            model=Model(),
            other_clock_drivers=OtherClocks(other_clock_driver=[clock]),
        )

    xml = XmlSerializer().render(component)
    _SCHEMA.assertValid(etree.fromstring(xml.encode()))
    parsed = XmlParser().from_string(xml, Component)
    if owner_type is ClockDriver:
        parsed_clock = (
            parsed.model.ports.port[0]
            .wire_or_transactional_or_structured.drivers.driver[0]
            .default_value_or_clock_driver_or_single_shot_driver
        )
    else:
        parsed_clock = parsed.other_clock_drivers.other_clock_driver[0]

    for operation in (entry for entry in _TIMING_OPERATIONS if entry.owner_type is owner_type):
        wrapper = getattr(parsed_clock, operation.field_name)
        source = _FIELD_TO_SOURCE[operation.field_name]
        assert wrapper.value == source
        assert wrapper.units is DelayValueUnitType.PS
        assert (wrapper.minimum, wrapper.maximum) == (0.0, 10.0)
        assert operation.expression_getter(get_handle(parsed_clock)) == source
        assert operation.numeric_getter(get_handle(parsed_clock)) == {"8 / 2": 4.0, "2.5": 2.5, "1 + 2": 3.0}[source]
    assert resolve_handle(get_handle(clock)) is clock

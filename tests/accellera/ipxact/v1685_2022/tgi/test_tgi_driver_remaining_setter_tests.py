"""Source-preserving setters for clock pulse and single-shot driver values."""

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
    SingleShotDriver,
    UnsignedBitExpression,
    UnsignedBitVectorExpression,
)
from org.accellera.ipxact.v1685_2022.other_clocks import OtherClocks

_SCHEMA = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))


class _SetterOperation(NamedTuple):
    name: str
    owner_type: type[ClockDriver] | type[OtherClockDriver] | type[SingleShotDriver]
    field_name: str
    wrapper_type: type[RealExpression] | type[UnsignedBitExpression] | type[UnsignedBitVectorExpression]
    setter: Callable[[str, str], bool]
    value_getter: Callable[[str], bool | int | float | None]
    expression_getter: Callable[[str], str | None]
    id_getter: Callable[[str], str | None]
    id_parameter: str
    value_parameter: str
    section: str
    source: str
    expected: bool | int | float


_OPERATIONS = (
    _SetterOperation(
        "clock-driver",
        ClockDriver,
        "clock_pulse_value",
        UnsignedBitExpression,
        api.setClockDriverClockPulseValue,
        api.getClockDriverClockPulseValue,
        api.getClockDriverClockPulseValueExpression,
        api.getClockDriverClockPulseValueID,
        "clockDriverID",
        "clockPulseValue",
        "F.7.42.10",
        "3",
        True,
    ),
    _SetterOperation(
        "other-clock-driver",
        OtherClockDriver,
        "clock_pulse_value",
        UnsignedBitExpression,
        api.setOtherClockDriverClockPulseValue,
        api.getOtherClockDriverClockPulseValue,
        api.getOtherClockDriverClockPulseValueExpression,
        api.getOtherClockDriverClockPulseValueID,
        "otherClockDriverID",
        "clockPulseValue",
        "F.7.42.18",
        "2",
        False,
    ),
    _SetterOperation(
        "single-shot-duration",
        SingleShotDriver,
        "single_shot_duration",
        SingleShotDriver.SingleShotDuration,
        api.setSingleShotDriverSingleShotDuration,
        api.getSingleShotDriverSingleShotDuration,
        api.getSingleShotDriverSingleShotDurationExpression,
        api.getSingleShotDriverSingleShotDurationID,
        "singleShotDriverID",
        "singleShotDuration",
        "F.7.42.19",
        "2 + 2",
        4.0,
    ),
    _SetterOperation(
        "single-shot-offset",
        SingleShotDriver,
        "single_shot_offset",
        SingleShotDriver.SingleShotOffset,
        api.setSingleShotDriverSingleShotOffset,
        api.getSingleShotDriverSingleShotOffset,
        api.getSingleShotDriverSingleShotOffsetExpression,
        api.getSingleShotDriverSingleShotOffsetID,
        "singleShotDriverID",
        "singleShotOffset",
        "F.7.42.20",
        "1 + 2",
        3.0,
    ),
    _SetterOperation(
        "single-shot-value",
        SingleShotDriver,
        "single_shot_value",
        UnsignedBitVectorExpression,
        api.setSingleShotDriverSingleShotValue,
        api.getSingleShotDriverSingleShotValue,
        api.getSingleShotDriverSingleShotValueExpression,
        api.getSingleShotDriverSingleShotValueID,
        "singleShotDriverID",
        "singleShotValue",
        "F.7.42.21",
        "1'b1",
        1,
    ),
)
_OPERATION_IDS = [operation.name for operation in _OPERATIONS]
_TIMING_OPERATIONS = tuple(operation for operation in _OPERATIONS if operation.name.startswith("single-shot-"))[:2]
_CLOCK_VALUE_OPERATIONS = _OPERATIONS[:2]


@pytest.fixture(autouse=True)
def clean_registry() -> Iterator[None]:
    registry.clear()
    yield
    registry.clear()


def _owner(operation: _SetterOperation) -> ClockDriver | OtherClockDriver | SingleShotDriver:
    if operation.owner_type is ClockDriver:
        return ClockDriver(
            clock_period=ClockDriverType.ClockPeriod(value="4", units=DelayValueUnitType.PS),
            clock_pulse_offset=ClockDriverType.ClockPulseOffset(value="1", units=DelayValueUnitType.NS),
            clock_pulse_value=UnsignedBitExpression(value="1"),
            clock_pulse_duration=ClockDriverType.ClockPulseDuration(value="2", units=DelayValueUnitType.PS),
        )
    if operation.owner_type is OtherClockDriver:
        return OtherClockDriver(
            clock_period=ClockDriverType.ClockPeriod(value="4", units=DelayValueUnitType.PS),
            clock_pulse_offset=ClockDriverType.ClockPulseOffset(value="1", units=DelayValueUnitType.NS),
            clock_pulse_value=UnsignedBitExpression(value="1"),
            clock_pulse_duration=ClockDriverType.ClockPulseDuration(value="2", units=DelayValueUnitType.PS),
            clock_name="external-clock",
            clock_source="pll.clk",
        )
    return SingleShotDriver(
        single_shot_offset=SingleShotDriver.SingleShotOffset(value="1", units=DelayValueUnitType.NS),
        single_shot_value=UnsignedBitVectorExpression(value="1"),
        single_shot_duration=SingleShotDriver.SingleShotDuration(value="2", units=DelayValueUnitType.PS),
    )


def _set_source(operation: _SetterOperation, owner_id: str, source: object) -> bool:
    return operation.setter(owner_id, source)  # type: ignore[arg-type]


@pytest.mark.parametrize("operation", _OPERATIONS, ids=_OPERATION_IDS)
def test_setters_have_exact_annex_signatures_exports_and_native_types(operation: _SetterOperation) -> None:
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
    assert f"Section: {operation.section}." in getdoc(function)


@pytest.mark.parametrize("operation", _OPERATIONS, ids=_OPERATION_IDS)
def test_setters_preserve_valid_expression_source_wrapper_identity_metadata_and_ownership(
    operation: _SetterOperation,
) -> None:
    owner = _owner(operation)
    owner_id = get_handle(owner)
    wrapper = getattr(owner, operation.field_name)
    wrapper.other_attributes = {"{urn:test}tag": "keep"}
    if operation in _TIMING_OPERATIONS:
        wrapper.units = DelayValueUnitType.PS
        wrapper.minimum = 1.0
        wrapper.maximum = 5.0
    wrapper_id = get_handle(wrapper)

    assert operation.setter(owner_id, operation.source)

    assert getattr(owner, operation.field_name) is wrapper
    assert wrapper.value == operation.source
    assert wrapper.other_attributes == {"{urn:test}tag": "keep"}
    assert operation.id_getter(owner_id) == wrapper_id
    assert operation.expression_getter(owner_id) == operation.source
    assert operation.value_getter(owner_id) == operation.expected
    if operation in _TIMING_OPERATIONS:
        assert (wrapper.units, wrapper.minimum, wrapper.maximum) == (DelayValueUnitType.PS, 1.0, 5.0)
    owner_info = get_parent_info(wrapper_id)
    assert owner_info is not None
    assert (owner_info.parent_handle, owner_info.path, owner_info.container) == (
        owner_id,
        (operation.field_name,),
        "single",
    )


@pytest.mark.parametrize("operation", _OPERATIONS, ids=_OPERATION_IDS)
def test_setters_create_missing_wrapper_with_owned_expression(operation: _SetterOperation) -> None:
    owner = _owner(operation)
    setattr(owner, operation.field_name, None)
    owner_id = get_handle(owner)

    assert operation.setter(owner_id, operation.source)

    wrapper = getattr(owner, operation.field_name)
    assert isinstance(wrapper, operation.wrapper_type)
    assert wrapper.value == operation.source
    assert operation.expression_getter(owner_id) == operation.source
    wrapper_id = operation.id_getter(owner_id)
    assert wrapper_id == get_handle(wrapper)
    owner_info = get_parent_info(wrapper_id)
    assert owner_info is not None
    assert (owner_info.parent_handle, owner_info.path, owner_info.container) == (
        owner_id,
        (operation.field_name,),
        "single",
    )


@pytest.mark.parametrize("operation", _OPERATIONS, ids=_OPERATION_IDS)
def test_setters_reuse_generic_expression_value_setter(
    operation: _SetterOperation, monkeypatch: pytest.MonkeyPatch
) -> None:
    owner = _owner(operation)
    owner_id = get_handle(owner)
    wrapper = getattr(owner, operation.field_name)
    expected_wrapper_id = get_handle(wrapper)
    original_setter = api.setExpressionValue
    calls: list[tuple[str, str]] = []

    def record_expression_setter(expression_id: str, value: str) -> bool:
        calls.append((expression_id, value))
        return original_setter(expression_id, value)

    monkeypatch.setattr(api, "setExpressionValue", record_expression_setter)
    assert operation.setter(owner_id, operation.source)
    assert calls == [(expected_wrapper_id, operation.source)]
    assert wrapper.value == operation.source


@pytest.mark.parametrize("operation", _OPERATIONS, ids=_OPERATION_IDS)
def test_setters_reject_malformed_or_native_sources_atomically(operation: _SetterOperation) -> None:
    invalid_sources: tuple[object, ...] = (None, 4, 1.5, float("nan"), "", "1 +", "bad\x00xml")
    owner = _owner(operation)
    owner_id = get_handle(owner)
    wrapper = getattr(owner, operation.field_name)
    wrapper.value = "1"
    if operation in _TIMING_OPERATIONS:
        wrapper.minimum = 1.0
        wrapper.maximum = 5.0

    for invalid_source in invalid_sources:
        with pytest.raises(TgiError) as error:
            _set_source(operation, owner_id, invalid_source)
        assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
        assert getattr(owner, operation.field_name) is wrapper
        assert wrapper.value == "1"
        if operation in _TIMING_OPERATIONS:
            assert (wrapper.minimum, wrapper.maximum) == (1.0, 5.0)


@pytest.mark.parametrize("operation", _TIMING_OPERATIONS, ids=[operation.name for operation in _TIMING_OPERATIONS])
@pytest.mark.parametrize("source", ["0", "6", "1.0 / 0.0"])
def test_single_shot_timing_setters_reject_out_of_bounds_or_nonfinite_source_atomically(
    operation: _SetterOperation, source: str
) -> None:
    owner = _owner(operation)
    owner_id = get_handle(owner)
    wrapper = getattr(owner, operation.field_name)
    wrapper.value = "3"
    wrapper.minimum = 1.0
    wrapper.maximum = 5.0

    with pytest.raises(TgiError) as error:
        operation.setter(owner_id, source)
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert wrapper.value == "3"
    assert (wrapper.minimum, wrapper.maximum) == (1.0, 5.0)


@pytest.mark.parametrize("operation", _TIMING_OPERATIONS, ids=[operation.name for operation in _TIMING_OPERATIONS])
def test_single_shot_timing_setters_retain_symbolic_sources_for_configured_evaluation(
    operation: _SetterOperation,
) -> None:
    owner_id = get_handle(_owner(operation))
    source = "CONFIGURED_SINGLE_SHOT_TIME"

    assert operation.setter(owner_id, source)
    assert operation.expression_getter(owner_id) == source
    with pytest.raises(TgiError) as error:
        operation.value_getter(owner_id)
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT


@pytest.mark.parametrize("source", ["0", "1", "1'b0", "1'b1", "8'h01"])
def test_single_shot_value_setter_accepts_only_resolved_zero_or_one_integer_values(source: str) -> None:
    operation = _OPERATIONS[-1]
    owner_id = get_handle(_owner(operation))
    expected = 0 if source in ("0", "1'b0") else 1

    assert operation.setter(owner_id, source)
    assert operation.value_getter(owner_id) == expected
    assert operation.expression_getter(owner_id) == source


@pytest.mark.parametrize("source", ["2", "8'h02", "-1", "0.5", "1.0", "1 +", "1'bx", "1'bz"])
def test_single_shot_value_setter_rejects_nonbinary_or_unresolved_values_atomically(source: str) -> None:
    operation = _OPERATIONS[-1]
    owner = _owner(operation)
    owner_id = get_handle(owner)
    wrapper = getattr(owner, operation.field_name)
    wrapper.value = "1"

    with pytest.raises(TgiError) as error:
        operation.setter(owner_id, source)
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert getattr(owner, operation.field_name) is wrapper
    assert wrapper.value == "1"


def test_single_shot_value_setter_retains_symbolic_source_until_configuration_resolution() -> None:
    operation = _OPERATIONS[-1]
    owner_id = get_handle(_owner(operation))
    source = "CONFIGURED_SINGLE_SHOT_VALUE"

    assert operation.setter(owner_id, source)
    assert operation.expression_getter(owner_id) == source
    with pytest.raises(TgiError) as error:
        operation.value_getter(owner_id)
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT


@pytest.mark.parametrize(
    "operation", _CLOCK_VALUE_OPERATIONS, ids=[operation.name for operation in _CLOCK_VALUE_OPERATIONS]
)
def test_clock_pulse_setters_retain_symbolic_source_until_configuration_resolution(
    operation: _SetterOperation,
) -> None:
    owner_id = get_handle(_owner(operation))
    source = "CONFIGURED_CLOCK_PULSE_VALUE"

    assert operation.setter(owner_id, source)
    assert operation.expression_getter(owner_id) == source
    with pytest.raises(TgiError) as error:
        operation.value_getter(owner_id)
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT


@pytest.mark.parametrize(
    "operation", _CLOCK_VALUE_OPERATIONS, ids=[operation.name for operation in _CLOCK_VALUE_OPERATIONS]
)
def test_clock_pulse_setters_keep_unknown_bit_literals_castable(operation: _SetterOperation) -> None:
    owner_id = get_handle(_owner(operation))

    for source in ("1'bx", "1'bz"):
        assert operation.setter(owner_id, source)
        assert operation.expression_getter(owner_id) == source
        assert operation.value_getter(owner_id) is False


@pytest.mark.parametrize("operation", _OPERATIONS, ids=_OPERATION_IDS)
def test_setters_reject_wrong_owner_and_wrong_wrapper_handles(operation: _SetterOperation) -> None:
    with pytest.raises(TgiError) as error:
        operation.setter("missing-driver-id", operation.source)
    assert error.value.fault_code == TgiFaultCode.INVALID_ID

    if operation.owner_type is ClockDriver:
        wrong_owner = _owner(_OPERATIONS[1])
    elif operation.owner_type is OtherClockDriver:
        wrong_owner = _owner(_OPERATIONS[0])
    else:
        wrong_owner = _owner(_OPERATIONS[0])
    with pytest.raises(TgiError) as error:
        operation.setter(get_handle(wrong_owner), operation.source)
    assert error.value.fault_code == TgiFaultCode.INVALID_ID

    owner = _owner(operation)
    wrong_wrapper = (
        UnsignedBitVectorExpression(value="1")
        if operation.wrapper_type is not UnsignedBitVectorExpression
        else RealExpression(value="1")
    )
    setattr(owner, operation.field_name, wrong_wrapper)
    owner_id = get_handle(owner)
    with pytest.raises(TgiError) as error:
        operation.setter(owner_id, operation.source)
    assert error.value.fault_code == TgiFaultCode.INVALID_ID
    assert getattr(owner, operation.field_name) is wrong_wrapper
    assert wrong_wrapper.value == "1"


@pytest.mark.parametrize("operation", _OPERATIONS, ids=_OPERATION_IDS)
def test_setters_do_not_create_missing_wrapper_for_invalid_source(operation: _SetterOperation) -> None:
    owner = _owner(operation)
    setattr(owner, operation.field_name, None)
    owner_id = get_handle(owner)

    invalid_source = "1'bx" if operation.name == "single-shot-value" else "1 +"
    with pytest.raises(TgiError) as error:
        operation.setter(owner_id, invalid_source)
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert getattr(owner, operation.field_name) is None


@pytest.mark.parametrize(("source", "expected"), [("2", False), ("3", True), ("-1", True), ("1'bx", False)])
def test_generic_expression_setter_accepts_clock_bit_cast_sources(source: str, expected: bool) -> None:
    expression = UnsignedBitExpression(value="1")
    expression_id = get_handle(expression)
    owner = ClockDriver(
        clock_period=ClockDriverType.ClockPeriod(value="4"),
        clock_pulse_offset=ClockDriverType.ClockPulseOffset(value="1"),
        clock_pulse_value=expression,
        clock_pulse_duration=ClockDriverType.ClockPulseDuration(value="2"),
    )
    owner_id = get_handle(owner)

    assert misc_api.setExpressionValue(expression_id, source)
    assert expression.value == source
    assert api.getClockDriverClockPulseValueExpression(owner_id) == source
    assert api.getClockDriverClockPulseValue(owner_id) is expected


def test_generic_expression_setter_rejects_malformed_clock_bit_source_atomically() -> None:
    expression = UnsignedBitExpression(value="1")
    expression_id = get_handle(expression)

    with pytest.raises(TgiError) as error:
        misc_api.setExpressionValue(expression_id, "1 +")
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert expression.value == "1"


def test_new_driver_setters_round_trip_sources_units_bounds_and_values_through_schema() -> None:
    clock = _owner(_OPERATIONS[0])
    other_clock = _owner(_OPERATIONS[1])
    shot = _owner(_OPERATIONS[-1])
    assert isinstance(clock, ClockDriver)
    assert isinstance(other_clock, OtherClockDriver)
    assert isinstance(shot, SingleShotDriver)
    operations = (_OPERATIONS[0], _OPERATIONS[1], _OPERATIONS[2], _OPERATIONS[3], _OPERATIONS[4])
    owners = (clock, other_clock, shot, shot, shot)
    for operation, owner in zip(operations, owners, strict=True):
        wrapper = getattr(owner, operation.field_name)
        if operation in _TIMING_OPERATIONS:
            wrapper.units = DelayValueUnitType.PS
            wrapper.minimum = 0.0
            wrapper.maximum = 10.0
        assert operation.setter(get_handle(owner), operation.source)

    clock_driver = Driver(default_value_or_clock_driver_or_single_shot_driver=clock)
    shot_driver = Driver(default_value_or_clock_driver_or_single_shot_driver=shot)
    root = Component(
        vendor="acme",
        library="test",
        name="remaining-driver-setters",
        version="1.0",
        model=Model(
            ports=Model.Ports(
                port=[
                    Port(
                        name="clock",
                        wire_or_transactional_or_structured=PortWireType(
                            direction=ComponentPortDirectionType.OUT,
                            drivers=Drivers(driver=[clock_driver]),
                        ),
                    ),
                    Port(
                        name="pulse",
                        wire_or_transactional_or_structured=PortWireType(
                            direction=ComponentPortDirectionType.OUT,
                            drivers=Drivers(driver=[shot_driver]),
                        ),
                    ),
                ]
            ),
        ),
        other_clock_drivers=OtherClocks(other_clock_driver=[other_clock]),
    )

    xml = XmlSerializer().render(root)
    _SCHEMA.assertValid(etree.fromstring(xml.encode()))
    parsed = XmlParser().from_string(xml, Component)
    parsed_clock = (
        parsed.model.ports.port[0]
        .wire_or_transactional_or_structured.drivers.driver[0]
        .default_value_or_clock_driver_or_single_shot_driver
    )
    parsed_shot = (
        parsed.model.ports.port[1]
        .wire_or_transactional_or_structured.drivers.driver[0]
        .default_value_or_clock_driver_or_single_shot_driver
    )
    parsed_other = parsed.other_clock_drivers.other_clock_driver[0]
    parsed_owners = (parsed_clock, parsed_other, parsed_shot, parsed_shot, parsed_shot)

    for operation, owner in zip(operations, parsed_owners, strict=True):
        owner_id = get_handle(owner)
        wrapper = getattr(owner, operation.field_name)
        assert wrapper.value == operation.source
        assert operation.expression_getter(owner_id) == operation.source
        assert operation.value_getter(owner_id) == operation.expected
        assert operation.id_getter(owner_id) == get_handle(wrapper)
        if operation in _TIMING_OPERATIONS:
            assert wrapper.units is DelayValueUnitType.PS
            assert (wrapper.minimum, wrapper.maximum) == (0.0, 10.0)

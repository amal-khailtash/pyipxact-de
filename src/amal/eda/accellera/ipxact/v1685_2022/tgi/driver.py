"""Driver category TGI functions (IEEE 1685-2022).

Implements BASE (F.7.41) and EXTENDED (F.7.42) public TGI functions for
``driver`` elements. A driver represents value-driving semantics for wire
ports – clock drivers, single-shot drivers, default values and optional range
and viewRef associations. Only the API defined in Annex F is exported (no more,
no less).

Mutator functions return ``True`` on success; remove* functions return ``False``
when the target element/attribute was absent. All functions raise
``TgiError`` with ``TgiFaultCode.INVALID_ID`` for invalid handles. Value/
expression getters return ``None`` when the element does not exist.
Clock timing getters evaluate finite real constants within declared bounds;
invalid or unresolved expressions raise ``TgiFaultCode.INVALID_ARGUMENT``.
Timing values retain the units declared on their source elements.
"""

# ruff: noqa: I001

from org.accellera.ipxact.v1685_2022 import (
    Driver,
    ClockDriver,
    SingleShotDriver,
    DefaultValue,
    DriverType,
    OtherClockDriver,
    RealExpression,
    UnsignedBitVectorExpression,
)
from org.accellera.ipxact.v1685_2022.clock_driver_type import ClockDriverType
from org.accellera.ipxact.v1685_2022.range import Range as RangeClass
from org.accellera.ipxact.v1685_2022.left import Left
from org.accellera.ipxact.v1685_2022.right import Right
from org.accellera.ipxact.v1685_2022.complex_base_expression import ComplexBaseExpression
from org.accellera.ipxact.v1685_2022.unsigned_bit_expression import UnsignedBitExpression

from ._expressions import _bit, _integer, _real, _xml_text
from .miscellaneous import (
    _expression_source,
    getExpression,
    getExpressionIntValue,
    getExpressionValue,
    setExpressionValue,
)
from collections.abc import Callable, Sequence

from .address_space import _register_owned_child, _remove_owned
from .component import _list_attr
from .port_map import _name
from ._model import _owned_list_ids
from ._attribute_references import resolve_attribute_reference

from .core import (
    TgiError,
    TgiFaultCode,
    resolve_handle,
    get_handle,
    register_parent,
    detach_child_by_handle,
)

__all__ = [
    # BASE (F.7.41)
    "getClockDriverClockPeriod",
    "getClockDriverClockPeriodExpression",
    "getClockDriverClockPeriodID",
    "getClockDriverClockPulseDuration",
    "getClockDriverClockPulseDurationExpression",
    "getClockDriverClockPulseDurationID",
    "getClockDriverClockPulseOffset",
    "getClockDriverClockPulseOffsetExpression",
    "getClockDriverClockPulseOffsetID",
    "getClockDriverClockPulseValue",
    "getClockDriverClockPulseValueExpression",
    "getClockDriverClockPulseValueID",
    "getDriverClockDriverID",
    "getDriverDefaultValue",
    "getDriverDefaultValueExpression",
    "getDriverDefaultValueID",
    "getDriverLeftID",
    "getDriverRange",
    "getDriverRangeExpression",
    "getDriverRightID",
    "getDriverSingleShotDriverID",
    "getDriverViewRefByID",
    "getDriverViewRefIDs",
    "getOtherClockDriverClockPeriod",
    "getOtherClockDriverClockPeriodExpression",
    "getOtherClockDriverClockPeriodID",
    "getOtherClockDriverClockPulseDuration",
    "getOtherClockDriverClockPulseDurationExpression",
    "getOtherClockDriverClockPulseDurationID",
    "getOtherClockDriverClockPulseOffset",
    "getOtherClockDriverClockPulseOffsetExpression",
    "getOtherClockDriverClockPulseOffsetID",
    "getOtherClockDriverClockPulseValue",
    "getOtherClockDriverClockPulseValueExpression",
    "getOtherClockDriverClockPulseValueID",
    "getSingleShotDriverSingleShotDuration",
    "getSingleShotDriverSingleShotDurationExpression",
    "getSingleShotDriverSingleShotDurationID",
    "getSingleShotDriverSingleShotOffset",
    "getSingleShotDriverSingleShotOffsetExpression",
    "getSingleShotDriverSingleShotOffsetID",
    "getSingleShotDriverSingleShotValue",
    "getSingleShotDriverSingleShotValueExpression",
    "getSingleShotDriverSingleShotValueID",
    # EXTENDED (F.7.42)
    "addDriverSingleShotDriver",
    "addDriverViewRef",
    "removeDriverClockDriver",
    "removeDriverRange",
    "removeDriverSingleShotDriver",
    "removeDriverViewRef",
    "setClockDriverClockPeriod",
    "setClockDriverClockPulseDuration",
    "setClockDriverClockPulseOffset",
    "setClockDriverClockPulseValue",
    "setDriverClockDriver",
    "setDriverSingleShotDriver",
    "setDriverDefaultValue",
    "setDriverRange",
    "setOtherClockDriverClockPeriod",
    "setOtherClockDriverClockPulseDuration",
    "setOtherClockDriverClockPulseOffset",
    "setOtherClockDriverClockPulseValue",
    "setSingleShotDriverSingleShotDuration",
    "setSingleShotDriverSingleShotOffset",
    "setSingleShotDriverSingleShotValue",
]


# ---------------------------------------------------------------------------
# Helpers (non-spec)
# ---------------------------------------------------------------------------


def _resolve_driver(driverID: str) -> Driver | None:
    obj = resolve_handle(driverID)
    return obj if isinstance(obj, Driver) else None


def _range_element[T: (Left, Right)](driver_id: str, attribute: str, expected: type[T]) -> T | None:
    """Resolve a range endpoint and restore its immediate ownership."""
    driver = _resolve_driver(driver_id)
    if driver is None:
        raise TgiError("Invalid driver handle", TgiFaultCode.INVALID_ID)
    if driver.range is None:
        return None
    if not isinstance(driver.range, RangeClass):
        raise TgiError("Invalid driver range element", TgiFaultCode.INVALID_ID)
    register_parent(driver.range, driver, ("range",), "single")
    endpoint = getattr(driver.range, attribute)
    if endpoint is None:
        return None
    if not isinstance(endpoint, expected):
        raise TgiError("Invalid range endpoint", TgiFaultCode.INVALID_ID)
    register_parent(endpoint, driver.range, (attribute,), "single")
    return endpoint


def _range_value(endpoint_id: str | None) -> int | None:
    """Evaluate an unsigned 32-bit range endpoint within declared bounds."""
    if endpoint_id is None:
        return None
    value = getExpressionIntValue(endpoint_id)
    endpoint = resolve_handle(endpoint_id)
    if not isinstance(endpoint, (Left, Right)):
        raise TgiError("Invalid range endpoint", TgiFaultCode.INVALID_ID)
    minimum, maximum = endpoint.minimum, endpoint.maximum
    if (
        not 0 <= value < (1 << 32)
        or (minimum is not None and value < minimum)
        or (maximum is not None and value > maximum)
        or (minimum is not None and maximum is not None and minimum > maximum)
    ):
        raise TgiError("Range endpoint outside unsigned integer bounds", TgiFaultCode.INVALID_ARGUMENT)
    return value


def _driver_expression[T: ComplexBaseExpression](
    driver_id: str,
    attribute: str,
    expected: type[T],
    driver_type: type[ClockDriver] | type[OtherClockDriver] | type[SingleShotDriver] = ClockDriver,
) -> T | None:
    """Resolve a typed driver expression element and retain its immediate owner."""
    driver = resolve_handle(driver_id)
    if not isinstance(driver, driver_type):
        raise TgiError("Invalid driver expression owner handle", TgiFaultCode.INVALID_ID)
    value = getattr(driver, attribute)
    if value is None:
        return None
    if not isinstance(value, expected):
        raise TgiError("Invalid driver expression element", TgiFaultCode.INVALID_ID)
    register_parent(value, driver, (attribute,), "single")
    return value


def _driver_timing_value[T: RealExpression](
    driver_id: str,
    attribute: str,
    expected: type[T],
    source: str | None,
    driver_type: type[ClockDriver] | type[OtherClockDriver] | type[SingleShotDriver] = ClockDriver,
) -> float | None:
    """Evaluate driver timing using the source element's real bounds."""
    if source is None:
        return None
    value = _driver_expression(driver_id, attribute, expected, driver_type)
    if value is None:
        return None
    return _real(source, minimum=value.minimum, maximum=value.maximum)


def _set_driver_expression[T: ComplexBaseExpression](
    driver_id: str,
    attribute: str,
    expected: type[T],
    source: str,
    driver_type: type[ClockDriver] | type[OtherClockDriver] | type[SingleShotDriver],
) -> bool:
    """Set driver source through generic validation, preserving existing wrappers."""
    current = _driver_expression(driver_id, attribute, expected, driver_type)
    if current is not None:
        _driver_source(source, current, driver_type)
        return setExpressionValue(get_handle(current), source)
    current = expected(value="")
    current.value = _driver_source(source, current, driver_type)
    driver = resolve_handle(driver_id)
    if not isinstance(driver, driver_type):
        raise TgiError("Invalid driver expression owner handle", TgiFaultCode.INVALID_ID)
    setattr(driver, attribute, current)
    register_parent(current, driver, (attribute,), "single")
    return True


def _driver_choice[T: (DefaultValue, ClockDriver, SingleShotDriver)](driver_id: str, expected: type[T]) -> T | None:
    """Resolve a generated Driver choice without replacing another valid branch."""
    driver = _resolve_driver(driver_id)
    if driver is None:
        raise TgiError("Invalid driver handle", TgiFaultCode.INVALID_ID)
    value = driver.default_value_or_clock_driver_or_single_shot_driver
    if value is None:
        return None
    if not isinstance(value, (DefaultValue, ClockDriver, SingleShotDriver)):
        raise TgiError("Invalid driver choice element", TgiFaultCode.INVALID_ID)
    register_parent(value, driver, ("default_value_or_clock_driver_or_single_shot_driver",), "single")
    return value if isinstance(value, expected) else None


def _driver_source(
    source: str,
    wrapper: ComplexBaseExpression,
    driver_type: type[ClockDriver] | type[OtherClockDriver] | type[SingleShotDriver],
) -> str:
    """Validate source with shared expression and single-shot logic constraints."""
    if isinstance(wrapper, UnsignedBitVectorExpression) and driver_type is SingleShotDriver:
        _xml_text(source)
        _integer(source, 1, deferred=True, decimal_literals=False)
    return _expression_source(source, wrapper)


def _replace_driver_choice(driver_id: str, choice: DefaultValue | ClockDriver | SingleShotDriver) -> bool:
    """Attach a validated choice and invalidate an alternative's removed handles."""
    driver = _resolve_driver(driver_id)
    if driver is None:
        raise TgiError("Invalid driver handle", TgiFaultCode.INVALID_ID)
    previous = driver.default_value_or_clock_driver_or_single_shot_driver
    if previous is not None and previous is not choice:
        register_parent(previous, driver, ("default_value_or_clock_driver_or_single_shot_driver",), "single")
        if not detach_child_by_handle(get_handle(previous)):
            raise TgiError("Invalid driver choice ownership", TgiFaultCode.INVALID_ID)
    driver.default_value_or_clock_driver_or_single_shot_driver = choice
    register_parent(choice, driver, ("default_value_or_clock_driver_or_single_shot_driver",), "single")
    return True


def _set_driver_choice[T: (ClockDriver, SingleShotDriver)](
    driver_id: str,
    choice: T,
    fields: Sequence[tuple[str, type[ComplexBaseExpression], str, Callable[[str, str], bool]]],
) -> bool:
    """Validate every field before applying the public low-level setters."""
    for attribute, expected, source, _setter in fields:
        wrapper = getattr(choice, attribute)
        if wrapper is None:
            wrapper = expected(value="")
        if not isinstance(wrapper, expected):
            raise TgiError("Invalid driver expression element", TgiFaultCode.INVALID_ID)
        _driver_source(source, wrapper, type(choice))
    choice_id = get_handle(choice)
    for _attribute, _expected, source, setter in fields:
        setter(choice_id, source)
    return _replace_driver_choice(driver_id, choice)


# ---------------------------------------------------------------------------
# BASE (F.7.41)
# ---------------------------------------------------------------------------


def getClockDriverClockPeriod(clockDriverID: str) -> float | None:
    """Return numeric value of ``clockPeriod``.

    Section: F.7.41.1.
    """
    source = getClockDriverClockPeriodExpression(clockDriverID)
    return _driver_timing_value(clockDriverID, "clock_period", ClockDriverType.ClockPeriod, source)


def getClockDriverClockPeriodExpression(clockDriverID: str) -> str | None:
    """Return expression string of ``clockPeriod`` if present.

    Section: F.7.41.2.
    """
    cp = _driver_expression(clockDriverID, "clock_period", ClockDriverType.ClockPeriod)
    return None if cp is None else _xml_text(cp.value)


def getClockDriverClockPeriodID(clockDriverID: str) -> str | None:
    """Return handle of ``clockPeriod`` element.

    Section: F.7.41.3.
    """
    cp = _driver_expression(clockDriverID, "clock_period", ClockDriverType.ClockPeriod)
    return None if cp is None else get_handle(cp)


def getClockDriverClockPulseDuration(clockDriverID: str) -> float | None:
    """Return numeric value of ``clockPulseDuration``.

    Section: F.7.41.4.
    """
    source = getClockDriverClockPulseDurationExpression(clockDriverID)
    return _driver_timing_value(clockDriverID, "clock_pulse_duration", ClockDriverType.ClockPulseDuration, source)


def getClockDriverClockPulseDurationExpression(clockDriverID: str) -> str | None:
    """Return expression for ``clockPulseDuration``.

    Section: F.7.41.5.
    """
    val = _driver_expression(clockDriverID, "clock_pulse_duration", ClockDriverType.ClockPulseDuration)
    return None if val is None else _xml_text(val.value)


def getClockDriverClockPulseDurationID(clockDriverID: str) -> str | None:
    """Return handle of ``clockPulseDuration``.

    Section: F.7.41.6.
    """
    val = _driver_expression(clockDriverID, "clock_pulse_duration", ClockDriverType.ClockPulseDuration)
    return None if val is None else get_handle(val)


def getClockDriverClockPulseOffset(clockDriverID: str) -> float | None:
    """Return numeric value of ``clockPulseOffset``.

    Section: F.7.41.7.
    """
    source = getClockDriverClockPulseOffsetExpression(clockDriverID)
    return _driver_timing_value(clockDriverID, "clock_pulse_offset", ClockDriverType.ClockPulseOffset, source)


def getClockDriverClockPulseOffsetExpression(clockDriverID: str) -> str | None:
    """Return expression of ``clockPulseOffset``.

    Section: F.7.41.8.
    """
    val = _driver_expression(clockDriverID, "clock_pulse_offset", ClockDriverType.ClockPulseOffset)
    return None if val is None else _xml_text(val.value)


def getClockDriverClockPulseOffsetID(clockDriverID: str) -> str | None:
    """Return handle of ``clockPulseOffset``.

    Section: F.7.41.9.
    """
    val = _driver_expression(clockDriverID, "clock_pulse_offset", ClockDriverType.ClockPulseOffset)
    return None if val is None else get_handle(val)


def getClockDriverClockPulseValue(clockDriverID: str) -> bool | None:
    """Return numeric bit value of ``clockPulseValue``.

    Section: F.7.41.10.
    """
    source = getClockDriverClockPulseValueExpression(clockDriverID)
    return None if source is None else _bit(source)


def getClockDriverClockPulseValueExpression(clockDriverID: str) -> str | None:
    """Return expression of ``clockPulseValue``.

    Section: F.7.41.11.
    """
    val = _driver_expression(clockDriverID, "clock_pulse_value", UnsignedBitExpression)
    return None if val is None else _xml_text(val.value)


def getClockDriverClockPulseValueID(clockDriverID: str) -> str | None:
    """Return handle of ``clockPulseValue`` element.

    Section: F.7.41.12.
    """
    val = _driver_expression(clockDriverID, "clock_pulse_value", UnsignedBitExpression)
    return None if val is None else get_handle(val)


def getDriverClockDriverID(driverID: str) -> str | None:
    """Return handle of ``clockDriver`` child of a driver.

    Section: F.7.41.13.
    """
    cd = _driver_choice(driverID, ClockDriver)
    return None if cd is None else get_handle(cd)


def getDriverDefaultValue(driverID: str) -> str | None:
    """Return the evaluated defaultValue as a string.

    Section: F.7.41.14.
    """
    value_id = getDriverDefaultValueID(driverID)
    return None if value_id is None else getExpressionValue(value_id)


def getDriverDefaultValueExpression(driverID: str) -> str | None:
    """Return expression of defaultValue.

    Section: F.7.41.15.
    """
    value_id = getDriverDefaultValueID(driverID)
    return None if value_id is None else getExpression(value_id)


def getDriverDefaultValueID(driverID: str) -> str | None:
    """Return handle of defaultValue element.

    Section: F.7.41.16.
    """
    dv = _driver_choice(driverID, DefaultValue)
    return None if dv is None else get_handle(dv)


def getDriverLeftID(driverID: str) -> str | None:
    """Return handle of range.left.

    Section: F.7.41.17.
    """
    endpoint = _range_element(driverID, "left", Left)
    return None if endpoint is None else get_handle(endpoint)


def getDriverRange(driverID: str) -> tuple[int | None, int | None]:
    """Return (leftValue, rightValue) of range.

    Evaluate SystemVerilog constants within unsigned 32-bit and declared bounds.
    Invalid or unresolved expressions raise INVALID_ARGUMENT; endpoint order is preserved.

    Section: F.7.41.18.
    """
    return (_range_value(getDriverLeftID(driverID)), _range_value(getDriverRightID(driverID)))


def getDriverRangeExpression(driverID: str) -> tuple[str | None, str | None]:
    """Return (leftExpression, rightExpression) of range.

    Section: F.7.41.19.
    """
    left_id, right_id = getDriverLeftID(driverID), getDriverRightID(driverID)
    return (None if left_id is None else getExpression(left_id), None if right_id is None else getExpression(right_id))


def getDriverRightID(driverID: str) -> str | None:
    """Return handle of range.right.

    Section: F.7.41.20.
    """
    endpoint = _range_element(driverID, "right", Right)
    return None if endpoint is None else get_handle(endpoint)


def getDriverSingleShotDriverID(driverID: str) -> str | None:
    """Return the singleShotDriver choice handle, if present.

    Section: F.7.41.21.
    """
    value = _driver_choice(driverID, SingleShotDriver)
    return None if value is None else get_handle(value)


def getDriverViewRefByID(driverID: str, viewRef: str) -> str:
    """Return the view targeted by a reference belonging to this driver.

    Section: F.7.41.22.
    """
    if viewRef not in getDriverViewRefIDs(driverID):
        raise TgiError("View reference does not belong to driver", TgiFaultCode.INVALID_ID)
    target = resolve_attribute_reference(viewRef, "viewRef")
    if target is None:
        raise TgiError("Driver view reference has no target", TgiFaultCode.NOT_FOUND)
    return target


def getDriverViewRefIDs(driverID: str) -> list[str]:
    """Return ordered handles to the driver's viewRef elements.

    Section: F.7.41.23.
    """
    driver = _resolve_driver(driverID)
    if driver is None:
        raise TgiError("Invalid driver handle", TgiFaultCode.INVALID_ID)
    return _owned_list_ids(driver, driver.view_ref, "view_ref")


def getOtherClockDriverClockPeriod(otherClockDriverID: str) -> float | None:
    """Return numeric value of ``clockPeriod`` on an otherClockDriver.

    Section: F.7.41.24.
    """
    source = getOtherClockDriverClockPeriodExpression(otherClockDriverID)
    return _driver_timing_value(
        otherClockDriverID, "clock_period", ClockDriverType.ClockPeriod, source, OtherClockDriver
    )


def getOtherClockDriverClockPeriodExpression(otherClockDriverID: str) -> str | None:
    """Return expression string of ``clockPeriod`` on an otherClockDriver.

    Section: F.7.41.25.
    """
    value = _driver_expression(otherClockDriverID, "clock_period", ClockDriverType.ClockPeriod, OtherClockDriver)
    return None if value is None else _xml_text(value.value)


def getOtherClockDriverClockPeriodID(otherClockDriverID: str) -> str | None:
    """Return handle of ``clockPeriod`` on an otherClockDriver.

    Section: F.7.41.26.
    """
    value = _driver_expression(otherClockDriverID, "clock_period", ClockDriverType.ClockPeriod, OtherClockDriver)
    return None if value is None else get_handle(value)


def getOtherClockDriverClockPulseDuration(otherClockDriverID: str) -> float | None:
    """Return numeric value of ``clockPulseDuration`` on an otherClockDriver.

    Section: F.7.41.27.
    """
    source = getOtherClockDriverClockPulseDurationExpression(otherClockDriverID)
    return _driver_timing_value(
        otherClockDriverID, "clock_pulse_duration", ClockDriverType.ClockPulseDuration, source, OtherClockDriver
    )


def getOtherClockDriverClockPulseDurationExpression(otherClockDriverID: str) -> str | None:
    """Return expression string of ``clockPulseDuration`` on an otherClockDriver.

    Section: F.7.41.28.
    """
    value = _driver_expression(
        otherClockDriverID, "clock_pulse_duration", ClockDriverType.ClockPulseDuration, OtherClockDriver
    )
    return None if value is None else _xml_text(value.value)


def getOtherClockDriverClockPulseDurationID(otherClockDriverID: str) -> str | None:
    """Return handle of ``clockPulseDuration`` on an otherClockDriver.

    Section: F.7.41.29.
    """
    value = _driver_expression(
        otherClockDriverID, "clock_pulse_duration", ClockDriverType.ClockPulseDuration, OtherClockDriver
    )
    return None if value is None else get_handle(value)


def getOtherClockDriverClockPulseOffset(otherClockDriverID: str) -> float | None:
    """Return numeric value of ``clockPulseOffset`` on an otherClockDriver.

    Section: F.7.41.30.
    """
    source = getOtherClockDriverClockPulseOffsetExpression(otherClockDriverID)
    return _driver_timing_value(
        otherClockDriverID, "clock_pulse_offset", ClockDriverType.ClockPulseOffset, source, OtherClockDriver
    )


def getOtherClockDriverClockPulseOffsetExpression(otherClockDriverID: str) -> str | None:
    """Return expression string of ``clockPulseOffset`` on an otherClockDriver.

    Section: F.7.41.31.
    """
    value = _driver_expression(
        otherClockDriverID, "clock_pulse_offset", ClockDriverType.ClockPulseOffset, OtherClockDriver
    )
    return None if value is None else _xml_text(value.value)


def getOtherClockDriverClockPulseOffsetID(otherClockDriverID: str) -> str | None:
    """Return handle of ``clockPulseOffset`` on an otherClockDriver.

    Section: F.7.41.32.
    """
    value = _driver_expression(
        otherClockDriverID, "clock_pulse_offset", ClockDriverType.ClockPulseOffset, OtherClockDriver
    )
    return None if value is None else get_handle(value)


def getOtherClockDriverClockPulseValue(otherClockDriverID: str) -> bool | None:
    """Return resolved bit value of ``clockPulseValue``.

    Section: F.7.41.33.
    """
    source = getOtherClockDriverClockPulseValueExpression(otherClockDriverID)
    return None if source is None else _bit(source)


def getOtherClockDriverClockPulseValueExpression(otherClockDriverID: str) -> str | None:
    """Return source expression of ``clockPulseValue``.

    Section: F.7.41.34.
    """
    value_id = getOtherClockDriverClockPulseValueID(otherClockDriverID)
    return None if value_id is None else getExpression(value_id)


def getOtherClockDriverClockPulseValueID(otherClockDriverID: str) -> str | None:
    """Return handle of ``clockPulseValue``.

    Section: F.7.41.35.
    """
    value = _driver_expression(otherClockDriverID, "clock_pulse_value", UnsignedBitExpression, OtherClockDriver)
    return None if value is None else get_handle(value)


def getSingleShotDriverSingleShotDuration(singleShotDriverID: str) -> float | None:
    """Return numeric value of ``singleShotDuration``.

    Section: F.7.41.36.
    """
    source = getSingleShotDriverSingleShotDurationExpression(singleShotDriverID)
    return _driver_timing_value(
        singleShotDriverID, "single_shot_duration", SingleShotDriver.SingleShotDuration, source, SingleShotDriver
    )


def getSingleShotDriverSingleShotDurationExpression(singleShotDriverID: str) -> str | None:
    """Return source expression of ``singleShotDuration``.

    Section: F.7.41.37.
    """
    value_id = getSingleShotDriverSingleShotDurationID(singleShotDriverID)
    return None if value_id is None else getExpression(value_id)


def getSingleShotDriverSingleShotDurationID(singleShotDriverID: str) -> str | None:
    """Return handle of ``singleShotDuration``.

    Section: F.7.41.38.
    """
    value = _driver_expression(
        singleShotDriverID, "single_shot_duration", SingleShotDriver.SingleShotDuration, SingleShotDriver
    )
    return None if value is None else get_handle(value)


def getSingleShotDriverSingleShotOffset(singleShotDriverID: str) -> float | None:
    """Return numeric value of ``singleShotOffset``.

    Section: F.7.41.39.
    """
    source = getSingleShotDriverSingleShotOffsetExpression(singleShotDriverID)
    return _driver_timing_value(
        singleShotDriverID, "single_shot_offset", SingleShotDriver.SingleShotOffset, source, SingleShotDriver
    )


def getSingleShotDriverSingleShotOffsetExpression(singleShotDriverID: str) -> str | None:
    """Return source expression of ``singleShotOffset``.

    Section: F.7.41.40.
    """
    value_id = getSingleShotDriverSingleShotOffsetID(singleShotDriverID)
    return None if value_id is None else getExpression(value_id)


def getSingleShotDriverSingleShotOffsetID(singleShotDriverID: str) -> str | None:
    """Return handle of ``singleShotOffset``.

    Section: F.7.41.41.
    """
    value = _driver_expression(
        singleShotDriverID, "single_shot_offset", SingleShotDriver.SingleShotOffset, SingleShotDriver
    )
    return None if value is None else get_handle(value)


def getSingleShotDriverSingleShotValue(singleShotDriverID: str) -> int | None:
    """Return the resolved logic value (zero or one).

    Section: F.7.41.42.
    """
    value_id = getSingleShotDriverSingleShotValueID(singleShotDriverID)
    if value_id is None:
        return None
    value = getExpressionIntValue(value_id)
    if value not in (0, 1):
        raise TgiError("Single-shot value must be zero or one", TgiFaultCode.INVALID_ARGUMENT)
    return value


def getSingleShotDriverSingleShotValueExpression(singleShotDriverID: str) -> str | None:
    """Return source expression of ``singleShotValue``.

    Section: F.7.41.43.
    """
    value_id = getSingleShotDriverSingleShotValueID(singleShotDriverID)
    return None if value_id is None else getExpression(value_id)


def getSingleShotDriverSingleShotValueID(singleShotDriverID: str) -> str | None:
    """Return handle of ``singleShotValue``.

    Section: F.7.41.44.
    """
    value = _driver_expression(singleShotDriverID, "single_shot_value", UnsignedBitVectorExpression, SingleShotDriver)
    return None if value is None else get_handle(value)


# ---------------------------------------------------------------------------
# EXTENDED (F.7.42)
# ---------------------------------------------------------------------------


def addDriverSingleShotDriver(driverID: str, offset: str, value: str, duration: str) -> str:
    """Add a complete singleShotDriver using its standard expression arguments.

    Section: F.7.42.1.
    """
    _driver_choice(driverID, SingleShotDriver)
    driver = _resolve_driver(driverID)
    if driver is None:
        raise TgiError("Invalid driver handle", TgiFaultCode.INVALID_ID)
    if driver.default_value_or_clock_driver_or_single_shot_driver is not None:
        raise TgiError("Driver already has a driving choice", TgiFaultCode.ALREADY_EXISTS)
    setDriverSingleShotDriver(driverID, offset, value, duration)
    shot_id = getDriverSingleShotDriverID(driverID)
    if shot_id is None:
        raise TgiError("Single-shot driver creation failed", TgiFaultCode.INTERNAL_ERROR)
    return shot_id


def addDriverViewRef(driverID: str, viewRef: str) -> str:
    """Add a unique NMTOKEN view reference and retain its Driver ownership.

    Section: F.7.42.2.
    """
    driver = _resolve_driver(driverID)
    if driver is None:
        raise TgiError("Invalid driver handle", TgiFaultCode.INVALID_ID)
    source = _name(viewRef, "NMTOKEN")
    for reference_id in getDriverViewRefIDs(driverID):
        reference = resolve_handle(reference_id)
        if not isinstance(reference, DriverType.ViewRef):
            raise TgiError("Invalid driver view reference", TgiFaultCode.INVALID_ID)
        if _name(reference.value, "NMTOKEN") == source:
            raise TgiError("Driver view reference already exists", TgiFaultCode.ALREADY_EXISTS)
    reference = DriverType.ViewRef(value=source)
    _list_attr(driver, "view_ref")
    driver.view_ref.append(reference)
    register_parent(reference, driver, ("view_ref",), "list")
    return get_handle(reference)


def removeDriverClockDriver(driverID: str) -> bool:
    """Remove the clockDriver choice from the given driver.

    Section: F.7.42.3.
    """
    clock_id = getDriverClockDriverID(driverID)
    return False if clock_id is None else detach_child_by_handle(clock_id)


def removeDriverRange(driverID: str) -> bool:
    """Remove the range child of a driver and invalidate its descendant handles.

    Section: F.7.42.4.
    """
    driver = _resolve_driver(driverID)
    if driver is None:
        raise TgiError("Invalid driver handle", TgiFaultCode.INVALID_ID)
    if driver.range is None:
        return False
    if not isinstance(driver.range, RangeClass):
        raise TgiError("Invalid driver range element", TgiFaultCode.INVALID_ID)
    register_parent(driver.range, driver, ("range",), "single")
    return detach_child_by_handle(get_handle(driver.range))


def removeDriverSingleShotDriver(driverID: str) -> bool:
    """Remove the singleShotDriver choice from the given driver.

    Section: F.7.42.5.
    """
    shot_id = getDriverSingleShotDriverID(driverID)
    return False if shot_id is None else detach_child_by_handle(shot_id)


def removeDriverViewRef(viewRefID: str) -> bool:
    """Remove a viewRef entry from its containing Driver element.

    Section: F.7.42.6.
    """
    reference = resolve_handle(viewRefID)
    if not isinstance(reference, DriverType.ViewRef):
        raise TgiError("Invalid driver view reference handle", TgiFaultCode.INVALID_ID)
    owner = _register_owned_child(reference, Driver)
    if owner is None or viewRefID not in getDriverViewRefIDs(get_handle(owner)):
        raise TgiError("Unowned driver view reference", TgiFaultCode.INVALID_ID)
    _list_attr(owner, "view_ref")
    return _remove_owned(viewRefID, DriverType.ViewRef, Driver, "driver view reference")


def setClockDriverClockPeriod(clockDriverID: str, clockPeriod: str) -> bool:
    """Set ``clockPeriod`` source on an existing clockDriver.

    Section: F.7.42.7.
    """
    return _set_driver_expression(clockDriverID, "clock_period", ClockDriverType.ClockPeriod, clockPeriod, ClockDriver)


def setClockDriverClockPulseDuration(clockDriverID: str, clockPulseDuration: str) -> bool:
    """Set ``clockPulseDuration`` source on an existing clockDriver.

    Section: F.7.42.8.
    """
    return _set_driver_expression(
        clockDriverID, "clock_pulse_duration", ClockDriverType.ClockPulseDuration, clockPulseDuration, ClockDriver
    )


def setClockDriverClockPulseOffset(clockDriverID: str, pulseOffset: str) -> bool:
    """Set ``clockPulseOffset`` source on an existing clockDriver.

    Section: F.7.42.9.
    """
    return _set_driver_expression(
        clockDriverID, "clock_pulse_offset", ClockDriverType.ClockPulseOffset, pulseOffset, ClockDriver
    )


def setClockDriverClockPulseValue(clockDriverID: str, clockPulseValue: str) -> bool:
    """Set ``clockPulseValue`` source on an existing clockDriver.

    Args:
        clockDriverID: Handle to the owning clockDriver element.
        clockPulseValue: Constant expression source.

    Returns:
        True when the expression is updated.

    Section: F.7.42.10.
    """
    # UnsignedBitExpression shares the standard one-bit cast with its numeric getter.
    return _set_driver_expression(
        clockDriverID, "clock_pulse_value", UnsignedBitExpression, clockPulseValue, ClockDriver
    )


def setDriverClockDriver(
    driverID: str, clockPeriod: str, clockPulseOffset: str, clockPulseValue: str, clockPulseDuration: str
) -> bool:
    """Set a complete clockDriver choice after validating all four expressions.

    Section: F.7.42.11.
    """
    choice = _driver_choice(driverID, ClockDriver)
    if choice is None:
        choice = ClockDriver(
            clock_period=ClockDriverType.ClockPeriod(value=""),
            clock_pulse_offset=ClockDriverType.ClockPulseOffset(value=""),
            clock_pulse_value=UnsignedBitExpression(value=""),
            clock_pulse_duration=ClockDriverType.ClockPulseDuration(value=""),
        )
    return _set_driver_choice(
        driverID,
        choice,
        (
            ("clock_period", ClockDriverType.ClockPeriod, clockPeriod, setClockDriverClockPeriod),
            ("clock_pulse_offset", ClockDriverType.ClockPulseOffset, clockPulseOffset, setClockDriverClockPulseOffset),
            ("clock_pulse_value", UnsignedBitExpression, clockPulseValue, setClockDriverClockPulseValue),
            (
                "clock_pulse_duration",
                ClockDriverType.ClockPulseDuration,
                clockPulseDuration,
                setClockDriverClockPulseDuration,
            ),
        ),
    )


def setDriverSingleShotDriver(
    driverID: str, singleShotOffset: str, singleShotValue: str, singleShotDuration: str
) -> bool:
    """Set a complete singleShotDriver choice after validating all three expressions.

    Section: F.7.42.12.
    """
    choice = _driver_choice(driverID, SingleShotDriver)
    if choice is None:
        choice = SingleShotDriver(
            single_shot_offset=SingleShotDriver.SingleShotOffset(value=""),
            single_shot_value=UnsignedBitVectorExpression(value=""),
            single_shot_duration=SingleShotDriver.SingleShotDuration(value=""),
        )
    return _set_driver_choice(
        driverID,
        choice,
        (
            (
                "single_shot_offset",
                SingleShotDriver.SingleShotOffset,
                singleShotOffset,
                setSingleShotDriverSingleShotOffset,
            ),
            ("single_shot_value", UnsignedBitVectorExpression, singleShotValue, setSingleShotDriverSingleShotValue),
            (
                "single_shot_duration",
                SingleShotDriver.SingleShotDuration,
                singleShotDuration,
                setSingleShotDriverSingleShotDuration,
            ),
        ),
    )


def setDriverDefaultValue(driverID: str, value: str) -> bool:
    """Set defaultValue source, replacing another driver choice after validation.

    Section: F.7.42.13.
    """
    current = _driver_choice(driverID, DefaultValue)
    if current is not None:
        return setExpressionValue(get_handle(current), value)
    default = DefaultValue(value="")
    default.value = _expression_source(value, default)
    return _replace_driver_choice(driverID, default)


def setDriverRange(driverID: str, range: Sequence[str]) -> bool:
    """Set ordered left/right expression sources, validating both before mutation.

    Section: F.7.42.14.
    """
    driver = _resolve_driver(driverID)
    if driver is None:
        raise TgiError("Invalid driver handle", TgiFaultCode.INVALID_ID)
    if not isinstance(range, Sequence) or isinstance(range, (str, bytes)) or len(range) != 2:
        raise TgiError("Driver range requires two expression strings", TgiFaultCode.INVALID_ARGUMENT)
    left = _range_element(driverID, "left", Left)
    right = _range_element(driverID, "right", Right)
    new_left = left if left is not None else Left(value="")
    new_right = right if right is not None else Right(value="")
    for endpoint, source in ((new_left, range[0]), (new_right, range[1])):
        if endpoint.minimum is not None and endpoint.maximum is not None and endpoint.minimum > endpoint.maximum:
            raise TgiError("Range endpoint bounds are reversed", TgiFaultCode.INVALID_ARGUMENT)
        _expression_source(source, endpoint)
    for endpoint, source in ((new_left, range[0]), (new_right, range[1])):
        setExpressionValue(get_handle(endpoint), source)
    if driver.range is None:
        driver.range = RangeClass(left=new_left, right=new_right)
    else:
        driver.range.left = new_left
        driver.range.right = new_right
    register_parent(driver.range, driver, ("range",), "single")
    register_parent(new_left, driver.range, ("left",), "single")
    register_parent(new_right, driver.range, ("right",), "single")
    return True


def setOtherClockDriverClockPeriod(otherClockDriverID: str, clockPeriod: str) -> bool:
    """Set ``clockPeriod`` source on an existing otherClockDriver.

    Section: F.7.42.15.
    """
    return _set_driver_expression(
        otherClockDriverID, "clock_period", ClockDriverType.ClockPeriod, clockPeriod, OtherClockDriver
    )


def setOtherClockDriverClockPulseDuration(otherClockDriverID: str, clockPulseDuration: str) -> bool:
    """Set ``clockPulseDuration`` source on an existing otherClockDriver.

    Section: F.7.42.16.
    """
    return _set_driver_expression(
        otherClockDriverID,
        "clock_pulse_duration",
        ClockDriverType.ClockPulseDuration,
        clockPulseDuration,
        OtherClockDriver,
    )


def setOtherClockDriverClockPulseOffset(otherClockDriverID: str, clockPulseOffset: str) -> bool:
    """Set ``clockPulseOffset`` source on an existing otherClockDriver.

    Section: F.7.42.17.
    """
    return _set_driver_expression(
        otherClockDriverID, "clock_pulse_offset", ClockDriverType.ClockPulseOffset, clockPulseOffset, OtherClockDriver
    )


def setOtherClockDriverClockPulseValue(otherClockDriverID: str, clockPulseValue: str) -> bool:
    """Set ``clockPulseValue`` source on an existing otherClockDriver.

    Args:
        otherClockDriverID: Handle to the owning otherClockDriver element.
        clockPulseValue: Constant expression source.

    Returns:
        True when the expression is updated.

    Section: F.7.42.18.
    """
    return _set_driver_expression(
        otherClockDriverID, "clock_pulse_value", UnsignedBitExpression, clockPulseValue, OtherClockDriver
    )


def setSingleShotDriverSingleShotDuration(singleShotDriverID: str, singleShotDuration: str) -> bool:
    """Set ``singleShotDuration`` source on an existing singleShotDriver.

    Args:
        singleShotDriverID: Handle to the owning singleShotDriver element.
        singleShotDuration: Constant expression source.

    Returns:
        True when the expression is updated.

    Section: F.7.42.19.
    """
    return _set_driver_expression(
        singleShotDriverID,
        "single_shot_duration",
        SingleShotDriver.SingleShotDuration,
        singleShotDuration,
        SingleShotDriver,
    )


def setSingleShotDriverSingleShotOffset(singleShotDriverID: str, singleShotOffset: str) -> bool:
    """Set ``singleShotOffset`` source on an existing singleShotDriver.

    Args:
        singleShotDriverID: Handle to the owning singleShotDriver element.
        singleShotOffset: Constant expression source.

    Returns:
        True when the expression is updated.

    Section: F.7.42.20.
    """
    return _set_driver_expression(
        singleShotDriverID, "single_shot_offset", SingleShotDriver.SingleShotOffset, singleShotOffset, SingleShotDriver
    )


def setSingleShotDriverSingleShotValue(singleShotDriverID: str, singleShotValue: str) -> bool:
    """Set ``singleShotValue`` source on an existing singleShotDriver.

    Args:
        singleShotDriverID: Handle to the owning singleShotDriver element.
        singleShotValue: Constant expression source.

    Returns:
        True when the expression is updated.

    Section: F.7.42.21.
    """
    return _set_driver_expression(
        singleShotDriverID, "single_shot_value", UnsignedBitVectorExpression, singleShotValue, SingleShotDriver
    )

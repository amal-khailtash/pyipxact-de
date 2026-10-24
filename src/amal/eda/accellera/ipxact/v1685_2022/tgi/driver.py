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
from org.accellera.ipxact.v1685_2022.single_shot_driver import SingleShotDriver as SingleShotDriverClass
from org.accellera.ipxact.v1685_2022.range import Range as RangeClass
from org.accellera.ipxact.v1685_2022.left import Left
from org.accellera.ipxact.v1685_2022.right import Right
from org.accellera.ipxact.v1685_2022.complex_base_expression import ComplexBaseExpression
from org.accellera.ipxact.v1685_2022.unsigned_bit_expression import UnsignedBitExpression

from ._expressions import _bit, _real, _xml_text
from .miscellaneous import (
    _expression_source,
    getExpression,
    getExpressionIntValue,
    getExpressionValue,
    setExpressionValue,
)
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


def _resolve_clock_driver(clockDriverID: str) -> ClockDriver | None:
    obj = resolve_handle(clockDriverID)
    return obj if isinstance(obj, ClockDriver) else None


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


def _set_driver_timing[T: RealExpression](
    driver_id: str,
    attribute: str,
    expected: type[T],
    source: str,
    driver_type: type[ClockDriver] | type[OtherClockDriver],
) -> bool:
    """Set timing source through generic validation, preserving existing wrappers."""
    current = _driver_expression(driver_id, attribute, expected, driver_type)
    if current is not None:
        return setExpressionValue(get_handle(current), source)
    current = expected(value="")
    current.value = _expression_source(source, current)
    driver = resolve_handle(driver_id)
    if not isinstance(driver, driver_type):
        raise TgiError("Invalid timing owner handle", TgiFaultCode.INVALID_ID)
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


def _resolve_single_shot(singleShotDriverID: str) -> SingleShotDriver | None:
    obj = resolve_handle(singleShotDriverID)
    return obj if isinstance(obj, SingleShotDriver) else None


def _ensure_clock(driver: Driver) -> ClockDriver:
    if driver.clock_driver is None:
        driver.clock_driver = ClockDriver(  # type: ignore[assignment]
            clock_period=ClockDriverType.ClockPeriod(),
            clock_pulse_offset=ClockDriverType.ClockPulseOffset(),
            clock_pulse_value=None,  # will be set by setter
            clock_pulse_duration=ClockDriverType.ClockPulseDuration(),
        )
        register_parent(driver.clock_driver, driver, ("clock_driver",), "single")
    return driver.clock_driver  # type: ignore[return-value]


def _ensure_single_shot(driver: Driver) -> SingleShotDriver:
    if driver.single_shot_driver is None:
        driver.single_shot_driver = SingleShotDriverClass(  # type: ignore[assignment]
            single_shot_offset=SingleShotDriverClass.SingleShotOffset(),
            single_shot_value=None,
            single_shot_duration=SingleShotDriverClass.SingleShotDuration(),
        )
        register_parent(driver.single_shot_driver, driver, ("single_shot_driver",), "single")
    return driver.single_shot_driver  # type: ignore[return-value]


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


def addDriverSingleShotDriver(driverID: str) -> str:
    """Create singleShotDriver (empty skeleton) if absent and return handle.

    Section: F.7.42.1.
    """
    d = _resolve_driver(driverID)
    if d is None:
        raise TgiError("Invalid driver handle", TgiFaultCode.INVALID_ID)
    ssd = _ensure_single_shot(d)
    return get_handle(ssd)


def addDriverViewRef(driverID: str, viewRef: str) -> str:
    """Append a ``viewRef`` value reference and return its handle.

    Section: F.7.42.2.
    """
    d = _resolve_driver(driverID)
    if d is None:
        raise TgiError("Invalid driver handle", TgiFaultCode.INVALID_ID)
    vr = DriverType.ViewRef(value=viewRef)
    d.view_ref.append(vr)  # type: ignore[attr-defined]
    register_parent(vr, d, ("view_ref",), "list")
    return get_handle(vr)


def removeDriverClockDriver(clockDriverID: str) -> bool:
    """Remove the clockDriver element.

    Section: F.7.42.3.
    """
    cd = _resolve_clock_driver(clockDriverID)
    if cd is None:
        return False
    return detach_child_by_handle(clockDriverID)


def removeDriverRange(driverID: str) -> bool:
    """Remove the range child of a driver.

    Section: F.7.42.4.
    """
    d = _resolve_driver(driverID)
    if d is None:
        raise TgiError("Invalid driver handle", TgiFaultCode.INVALID_ID)
    if d.range is None:
        return False
    d.range = None
    return True


def removeDriverSingleShotDriver(singleShotDriverID: str) -> bool:
    """Remove the singleShotDriver element.

    Section: F.7.42.5.
    """
    ssd = _resolve_single_shot(singleShotDriverID)
    if ssd is None:
        return False
    return detach_child_by_handle(singleShotDriverID)


def removeDriverViewRef(viewRefID: str) -> bool:
    """Remove a viewRef entry.

    Section: F.7.42.6.
    """
    obj = resolve_handle(viewRefID)
    if not isinstance(obj, DriverType.ViewRef):  # type: ignore[attr-defined]
        return False
    return detach_child_by_handle(viewRefID)


def setClockDriverClockPeriod(clockDriverID: str, clockPeriod: str) -> bool:
    """Set ``clockPeriod`` source on an existing clockDriver.

    Section: F.7.42.7.
    """
    return _set_driver_timing(clockDriverID, "clock_period", ClockDriverType.ClockPeriod, clockPeriod, ClockDriver)


def setClockDriverClockPulseDuration(clockDriverID: str, clockPulseDuration: str) -> bool:
    """Set ``clockPulseDuration`` source on an existing clockDriver.

    Section: F.7.42.8.
    """
    return _set_driver_timing(
        clockDriverID, "clock_pulse_duration", ClockDriverType.ClockPulseDuration, clockPulseDuration, ClockDriver
    )


def setClockDriverClockPulseOffset(clockDriverID: str, pulseOffset: str) -> bool:
    """Set ``clockPulseOffset`` source on an existing clockDriver.

    Section: F.7.42.9.
    """
    return _set_driver_timing(
        clockDriverID, "clock_pulse_offset", ClockDriverType.ClockPulseOffset, pulseOffset, ClockDriver
    )


def setClockDriverClockPulseValue(clockDriverID: str, value: int, expression: str | None = None) -> bool:
    """Set clockPulseValue fields.

    Section: F.7.42.10.
    """
    cd = _resolve_clock_driver(clockDriverID)
    if cd is None:
        raise TgiError("Invalid clockDriver handle", TgiFaultCode.INVALID_ID)
    # UnsignedBitExpression imported inside to avoid circular imports if any
    from org.accellera.ipxact.v1685_2022.unsigned_bit_expression import UnsignedBitExpression

    ub = cd.clock_pulse_value
    if ub is None:
        ub = UnsignedBitExpression()
        cd.clock_pulse_value = ub
        register_parent(ub, cd, ("clock_pulse_value",), "single")
    ub.value = value  # type: ignore[attr-defined]
    if expression is not None:
        ub.expression = expression  # type: ignore[attr-defined]
    return True


def setDriverClockDriver(driverID: str) -> str:
    """Ensure clockDriver exists (creating if necessary) and return its handle.

    Section: F.7.42.11.
    """
    d = _resolve_driver(driverID)
    if d is None:
        raise TgiError("Invalid driver handle", TgiFaultCode.INVALID_ID)
    cd = _ensure_clock(d)
    return get_handle(cd)


def setDriverSingleShotDriver(driverID: str) -> str:
    """Ensure singleShotDriver exists and return its handle.

    Section: F.7.42.12.
    """
    d = _resolve_driver(driverID)
    if d is None:
        raise TgiError("Invalid driver handle", TgiFaultCode.INVALID_ID)
    ssd = _ensure_single_shot(d)
    return get_handle(ssd)


def setDriverDefaultValue(driverID: str, value: int | str, expression: str | None = None) -> bool:
    """Set defaultValue contents (creating element if missing).

    Section: F.7.42.13.
    """
    d = _resolve_driver(driverID)
    if d is None:
        raise TgiError("Invalid driver handle", TgiFaultCode.INVALID_ID)
    dv = d.default_value
    if dv is None:
        dv = DefaultValue()
        d.default_value = dv
        register_parent(dv, d, ("default_value",), "single")
    dv.value = value  # type: ignore[attr-defined]
    if expression is not None:
        dv.expression = expression  # type: ignore[attr-defined]
    return True


def setDriverRange(
    driverID: str,
    leftValue: int,
    rightValue: int,
    leftExpression: str | None = None,
    rightExpression: str | None = None,
) -> bool:
    """Set range bounds creating range if required.

    Section: F.7.42.14.
    """
    d = _resolve_driver(driverID)
    if d is None:
        raise TgiError("Invalid driver handle", TgiFaultCode.INVALID_ID)
    rng = d.range
    if rng is None:
        rng = RangeClass(left=Left(), right=Right())
        d.range = rng
        register_parent(rng, d, ("range",), "single")
    if rng.left is None:
        rng.left = Left()
    if rng.right is None:
        rng.right = Right()
    rng.left.value = leftValue  # type: ignore[attr-defined]
    rng.right.value = rightValue  # type: ignore[attr-defined]
    if leftExpression is not None:
        rng.left.expression = leftExpression  # type: ignore[attr-defined]
    if rightExpression is not None:
        rng.right.expression = rightExpression  # type: ignore[attr-defined]
    return True


def setOtherClockDriverClockPeriod(otherClockDriverID: str, clockPeriod: str) -> bool:
    """Set ``clockPeriod`` source on an existing otherClockDriver.

    Section: F.7.42.15.
    """
    return _set_driver_timing(
        otherClockDriverID, "clock_period", ClockDriverType.ClockPeriod, clockPeriod, OtherClockDriver
    )


def setOtherClockDriverClockPulseDuration(otherClockDriverID: str, clockPulseDuration: str) -> bool:
    """Set ``clockPulseDuration`` source on an existing otherClockDriver.

    Section: F.7.42.16.
    """
    return _set_driver_timing(
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
    return _set_driver_timing(
        otherClockDriverID, "clock_pulse_offset", ClockDriverType.ClockPulseOffset, clockPulseOffset, OtherClockDriver
    )


def setOtherClockDriverClockPulseValue(driverID: str, value: int, expression: str | None = None) -> bool:
    """Ensure clockDriver then set clockPulseValue.

    Section: F.7.42.18.
    """
    d = _resolve_driver(driverID)
    if d is None:
        raise TgiError("Invalid driver handle", TgiFaultCode.INVALID_ID)
    cd = _ensure_clock(d)
    return setClockDriverClockPulseValue(get_handle(cd), value, expression)


def setSingleShotDriverSingleShotDuration(singleShotDriverID: str, value: float, expression: str | None = None) -> bool:
    """Set duration field of an existing singleShotDriver.

    Section: F.7.42.19.
    """
    ssd = _resolve_single_shot(singleShotDriverID)
    if ssd is None:
        raise TgiError("Invalid singleShotDriver handle", TgiFaultCode.INVALID_ID)
    if ssd.single_shot_duration is None:
        ssd.single_shot_duration = SingleShotDriverClass.SingleShotDuration()
    ssd.single_shot_duration.value = value  # type: ignore[attr-defined]
    if expression is not None:
        ssd.single_shot_duration.expression = expression  # type: ignore[attr-defined]
    return True


def setSingleShotDriverSingleShotOffset(singleShotDriverID: str, value: float, expression: str | None = None) -> bool:
    """Set offset field of an existing singleShotDriver.

    Section: F.7.42.20.
    """
    ssd = _resolve_single_shot(singleShotDriverID)
    if ssd is None:
        raise TgiError("Invalid singleShotDriver handle", TgiFaultCode.INVALID_ID)
    if ssd.single_shot_offset is None:
        ssd.single_shot_offset = SingleShotDriverClass.SingleShotOffset()
    ssd.single_shot_offset.value = value  # type: ignore[attr-defined]
    if expression is not None:
        ssd.single_shot_offset.expression = expression  # type: ignore[attr-defined]
    return True

"""Single-shot driver getters follow the TGI expression and ownership contracts."""

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
    UnsignedBitVectorExpression,
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
        "single_shot_duration",
        SingleShotDriver.SingleShotDuration,
        api.getSingleShotDriverSingleShotDuration,
        api.getSingleShotDriverSingleShotDurationExpression,
        api.getSingleShotDriverSingleShotDurationID,
    ),
    (
        "single_shot_offset",
        SingleShotDriver.SingleShotOffset,
        api.getSingleShotDriverSingleShotOffset,
        api.getSingleShotDriverSingleShotOffsetExpression,
        api.getSingleShotDriverSingleShotOffsetID,
    ),
)
_INVALID_TIMING_SOURCES = (
    "1 +",
    "UNRESOLVED_SINGLE_SHOT_TIME",
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


def _single_shot_driver(value: str | None = "1") -> SingleShotDriver:
    return SingleShotDriver(
        single_shot_offset=SingleShotDriver.SingleShotOffset(value="1", units=DelayValueUnitType.NS),
        single_shot_value=None if value is None else UnsignedBitVectorExpression(value=value),
        single_shot_duration=SingleShotDriver.SingleShotDuration(value="2", units=DelayValueUnitType.PS),
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
def test_single_shot_timing_getters_evaluate_and_preserve_source(
    field_name: str,
    wrapper_type: type[RealExpression],
    numeric_getter: Callable[[str], float | None],
    expression_getter: Callable[[str], str | None],
    id_getter: Callable[[str], str | None],
    source: str,
    expected: float,
) -> None:
    shot = _single_shot_driver()
    wrapper = wrapper_type(value=source)
    setattr(shot, field_name, wrapper)
    shot_id = get_handle(shot)

    assert numeric_getter(shot_id) == expected
    assert expression_getter(shot_id) == source
    wrapper_id = id_getter(shot_id)
    assert wrapper_id == get_handle(wrapper)
    owner = get_parent_info(wrapper_id)
    assert owner is not None
    assert (owner.parent_handle, owner.path, owner.container) == (shot_id, (field_name,), "single")


@pytest.mark.parametrize(
    ("field_name", "wrapper_type", "numeric_getter", "expression_getter", "id_getter"), _TIMING_FIELDS
)
@pytest.mark.parametrize("source", _INVALID_TIMING_SOURCES)
def test_single_shot_timing_getters_reject_invalid_or_nonfinite_expressions(
    field_name: str,
    wrapper_type: type[RealExpression],
    numeric_getter: Callable[[str], float | None],
    expression_getter: Callable[[str], str | None],
    id_getter: Callable[[str], str | None],
    source: str,
) -> None:
    shot = _single_shot_driver()
    setattr(shot, field_name, wrapper_type(value=source))
    with pytest.raises(TgiError) as error:
        numeric_getter(get_handle(shot))
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT


@pytest.mark.parametrize(
    ("field_name", "wrapper_type", "numeric_getter", "expression_getter", "id_getter"), _TIMING_FIELDS
)
@pytest.mark.parametrize(("source", "expected"), [("1", 1.0), ("5", 5.0)])
def test_single_shot_timing_getters_accept_inclusive_bounds(
    field_name: str,
    wrapper_type: type[RealExpression],
    numeric_getter: Callable[[str], float | None],
    expression_getter: Callable[[str], str | None],
    id_getter: Callable[[str], str | None],
    source: str,
    expected: float,
) -> None:
    shot = _single_shot_driver()
    setattr(shot, field_name, wrapper_type(value=source, minimum=1.0, maximum=5.0))
    assert numeric_getter(get_handle(shot)) == expected


@pytest.mark.parametrize(
    ("field_name", "wrapper_type", "numeric_getter", "expression_getter", "id_getter"), _TIMING_FIELDS
)
def test_single_shot_timing_getters_allow_infinite_declared_bounds(
    field_name: str,
    wrapper_type: type[RealExpression],
    numeric_getter: Callable[[str], float | None],
    expression_getter: Callable[[str], str | None],
    id_getter: Callable[[str], str | None],
) -> None:
    shot = _single_shot_driver()
    setattr(shot, field_name, wrapper_type(value="2", minimum=float("-inf"), maximum=float("inf")))
    assert numeric_getter(get_handle(shot)) == 2.0


@pytest.mark.parametrize(
    ("field_name", "wrapper_type", "numeric_getter", "expression_getter", "id_getter"), _TIMING_FIELDS
)
@pytest.mark.parametrize("source", ["0", "6"])
def test_single_shot_timing_getters_reject_values_outside_bounds(
    field_name: str,
    wrapper_type: type[RealExpression],
    numeric_getter: Callable[[str], float | None],
    expression_getter: Callable[[str], str | None],
    id_getter: Callable[[str], str | None],
    source: str,
) -> None:
    shot = _single_shot_driver()
    setattr(shot, field_name, wrapper_type(value=source, minimum=1.0, maximum=5.0))
    with pytest.raises(TgiError) as error:
        numeric_getter(get_handle(shot))
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT


@pytest.mark.parametrize(
    ("field_name", "wrapper_type", "numeric_getter", "expression_getter", "id_getter"), _TIMING_FIELDS
)
@pytest.mark.parametrize(("minimum", "maximum"), [(float("nan"), 5.0), (5.0, 4.0)])
def test_single_shot_timing_getters_reject_invalid_declared_bounds(
    field_name: str,
    wrapper_type: type[RealExpression],
    numeric_getter: Callable[[str], float | None],
    expression_getter: Callable[[str], str | None],
    id_getter: Callable[[str], str | None],
    minimum: float,
    maximum: float,
) -> None:
    shot = _single_shot_driver()
    setattr(shot, field_name, wrapper_type(value="3", minimum=minimum, maximum=maximum))
    with pytest.raises(TgiError) as error:
        numeric_getter(get_handle(shot))
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT


@pytest.mark.parametrize(
    ("field_name", "wrapper_type", "numeric_getter", "expression_getter", "id_getter"), _TIMING_FIELDS
)
def test_single_shot_timing_getters_return_none_for_absent_wrappers(
    field_name: str,
    wrapper_type: type[RealExpression],
    numeric_getter: Callable[[str], float | None],
    expression_getter: Callable[[str], str | None],
    id_getter: Callable[[str], str | None],
) -> None:
    shot = _single_shot_driver()
    setattr(shot, field_name, None)
    shot_id = get_handle(shot)
    assert numeric_getter(shot_id) is None
    assert expression_getter(shot_id) is None
    assert id_getter(shot_id) is None


@pytest.mark.parametrize(
    ("field_name", "wrapper_type", "numeric_getter", "expression_getter", "id_getter"), _TIMING_FIELDS
)
def test_single_shot_timing_getters_reject_wrong_wrappers(
    field_name: str,
    wrapper_type: type[RealExpression],
    numeric_getter: Callable[[str], float | None],
    expression_getter: Callable[[str], str | None],
    id_getter: Callable[[str], str | None],
) -> None:
    shot = _single_shot_driver()
    setattr(shot, field_name, UnsignedBitVectorExpression(value="1"))
    for getter in (numeric_getter, expression_getter, id_getter):
        with pytest.raises(TgiError) as error:
            getter(get_handle(shot))
        assert error.value.fault_code == TgiFaultCode.INVALID_ID


@pytest.mark.parametrize(
    ("source", "expected"),
    [("0", 0), ("1", 1), ("1'b0", 0), ("1'b1", 1), ("8'h00", 0), ("8'h01", 1)],
)
def test_single_shot_value_accepts_only_zero_or_one_integer_constants(source: str, expected: int) -> None:
    shot = _single_shot_driver(source)
    shot_id = get_handle(shot)

    assert api.getSingleShotDriverSingleShotValue(shot_id) == expected
    assert api.getSingleShotDriverSingleShotValueExpression(shot_id) == source
    value_id = api.getSingleShotDriverSingleShotValueID(shot_id)
    assert value_id == get_handle(shot.single_shot_value)
    owner = get_parent_info(value_id)
    assert owner is not None
    assert (owner.parent_handle, owner.path, owner.container) == (shot_id, ("single_shot_value",), "single")


@pytest.mark.parametrize("source", ["2", "8'h02", "-1", "0.5", "UNKNOWN_SINGLE_SHOT", "1 +", "1'bx", "1'bz"])
def test_single_shot_value_rejects_nonbinary_invalid_unknown_or_unresolved_values(source: str) -> None:
    shot_id = get_handle(_single_shot_driver(source))
    with pytest.raises(TgiError) as error:
        api.getSingleShotDriverSingleShotValue(shot_id)
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert api.getSingleShotDriverSingleShotValueExpression(shot_id) == source


def test_single_shot_value_handles_absence_and_wrong_wrapper() -> None:
    shot = _single_shot_driver(None)
    shot_id = get_handle(shot)
    assert api.getSingleShotDriverSingleShotValue(shot_id) is None
    assert api.getSingleShotDriverSingleShotValueExpression(shot_id) is None
    assert api.getSingleShotDriverSingleShotValueID(shot_id) is None

    shot.single_shot_value = RealExpression(value="1")
    for getter in (
        api.getSingleShotDriverSingleShotValue,
        api.getSingleShotDriverSingleShotValueExpression,
        api.getSingleShotDriverSingleShotValueID,
    ):
        with pytest.raises(TgiError) as error:
            getter(shot_id)
        assert error.value.fault_code == TgiFaultCode.INVALID_ID


def test_single_shot_getters_reject_invalid_foreign_and_stale_handles() -> None:
    other_clock_id = get_handle(
        OtherClockDriver(
            clock_period=None,
            clock_pulse_offset=None,
            clock_pulse_value=None,
            clock_pulse_duration=None,
            clock_name="external",
        )
    )
    clock_id = get_handle(
        ClockDriver(clock_period=None, clock_pulse_offset=None, clock_pulse_value=None, clock_pulse_duration=None)
    )
    getters = tuple(getter for field in _TIMING_FIELDS for getter in field[2:]) + (
        api.getSingleShotDriverSingleShotValue,
        api.getSingleShotDriverSingleShotValueExpression,
        api.getSingleShotDriverSingleShotValueID,
    )
    for invalid_id in ("missing-single-shot", other_clock_id, clock_id):
        for getter in getters:
            with pytest.raises(TgiError) as error:
                getter(invalid_id)
            assert error.value.fault_code == TgiFaultCode.INVALID_ID

    shot = _single_shot_driver()
    stale_id = get_handle(shot)
    parent = Driver(default_value_or_clock_driver_or_single_shot_driver=shot)
    register_parent(shot, parent, ("default_value_or_clock_driver_or_single_shot_driver",), "single")
    assert detach_child_by_handle(stale_id)
    assert resolve_handle(stale_id) is None
    for getter in getters:
        with pytest.raises(TgiError) as error:
            getter(stale_id)
        assert error.value.fault_code == TgiFaultCode.INVALID_ID


def test_single_shot_getter_signatures_exports_and_native_annotations() -> None:
    expected = {
        "getSingleShotDriverSingleShotDuration": float | None,
        "getSingleShotDriverSingleShotDurationExpression": str | None,
        "getSingleShotDriverSingleShotDurationID": str | None,
        "getSingleShotDriverSingleShotOffset": float | None,
        "getSingleShotDriverSingleShotOffsetExpression": str | None,
        "getSingleShotDriverSingleShotOffsetID": str | None,
        "getSingleShotDriverSingleShotValue": int | None,
        "getSingleShotDriverSingleShotValueExpression": str | None,
        "getSingleShotDriverSingleShotValueID": str | None,
    }
    for name, return_type in expected.items():
        function = getattr(api, name)
        assert getattr(tgi, name) is function
        assert name in api.__all__
        assert name in tgi.__all__
        signature = inspect.signature(function)
        assert list(signature.parameters) == ["singleShotDriverID"]
        assert signature.parameters["singleShotDriverID"].annotation is str
        hints = get_type_hints(function)
        assert hints["singleShotDriverID"] is str
        assert hints["return"] == return_type
        assert signature.return_annotation == return_type
        assert not isinstance(signature.return_annotation, str)


def test_single_shot_sources_units_bounds_and_ids_survive_schema_valid_round_trip() -> None:
    shot = SingleShotDriver(
        single_shot_offset=SingleShotDriver.SingleShotOffset(
            value=" 1 + 2 ", units=DelayValueUnitType.NS, minimum=0.0, maximum=3.0
        ),
        single_shot_value=UnsignedBitVectorExpression(value="1'b1"),
        single_shot_duration=SingleShotDriver.SingleShotDuration(
            value="2.50", units=DelayValueUnitType.PS, minimum=2.0, maximum=3.0
        ),
    )
    driver = Driver(default_value_or_clock_driver_or_single_shot_driver=shot, id="single-shot-driver-1")
    root = Component(
        vendor="acme",
        library="test",
        name="single-shot-timing",
        version="1.0",
        model=Model(
            ports=Model.Ports(
                port=[
                    Port(
                        name="pulse",
                        wire_or_transactional_or_structured=PortWireType(
                            direction=ComponentPortDirectionType.OUT,
                            drivers=Drivers(driver=[driver]),
                        ),
                    )
                ]
            )
        ),
    )
    shot_id = get_handle(shot)
    for field_name, _, number_getter, expression_getter, id_getter in _TIMING_FIELDS:
        wrapper = getattr(shot, field_name)
        assert number_getter(shot_id) == (2.5 if field_name == "single_shot_duration" else 3.0)
        assert expression_getter(shot_id) == wrapper.value
        assert id_getter(shot_id) == get_handle(wrapper)
    assert api.getSingleShotDriverSingleShotValue(shot_id) == 1
    assert api.getSingleShotDriverSingleShotValueExpression(shot_id) == "1'b1"
    assert api.getSingleShotDriverSingleShotValueID(shot_id) == get_handle(shot.single_shot_value)

    xml = XmlSerializer().render(root)
    _SCHEMA.assertValid(etree.fromstring(xml.encode()))
    parsed = XmlParser().from_string(xml, Component)
    parsed_shot = (
        parsed.model.ports.port[0]
        .wire_or_transactional_or_structured.drivers.driver[0]
        .default_value_or_clock_driver_or_single_shot_driver
    )
    parsed_id = get_handle(parsed_shot)
    parsed_driver = parsed.model.ports.port[0].wire_or_transactional_or_structured.drivers.driver[0]
    assert parsed_driver.id == "single-shot-driver-1"
    for field_name, _, number_getter, expression_getter, id_getter in _TIMING_FIELDS:
        wrapper = getattr(parsed_shot, field_name)
        expected_number = 2.5 if field_name == "single_shot_duration" else 3.0
        expected_unit = DelayValueUnitType.PS if field_name == "single_shot_duration" else DelayValueUnitType.NS
        assert number_getter(parsed_id) == expected_number
        assert expression_getter(parsed_id) == wrapper.value
        assert id_getter(parsed_id) == get_handle(wrapper)
        assert wrapper.units is expected_unit
        assert wrapper.value == ("2.50" if field_name == "single_shot_duration" else " 1 + 2 ")
    assert (parsed_shot.single_shot_duration.minimum, parsed_shot.single_shot_duration.maximum) == (2.0, 3.0)
    assert (parsed_shot.single_shot_offset.minimum, parsed_shot.single_shot_offset.maximum) == (0.0, 3.0)
    assert api.getSingleShotDriverSingleShotValue(parsed_id) == 1
    assert api.getSingleShotDriverSingleShotValueExpression(parsed_id) == "1'b1"
    assert api.getSingleShotDriverSingleShotValueID(parsed_id) == get_handle(parsed_shot.single_shot_value)

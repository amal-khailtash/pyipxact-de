"""Driver removers and structural setters preserve the generated model contract."""

from collections.abc import Callable, Iterator, Sequence
from inspect import signature
from typing import get_type_hints

import pytest
from lxml import etree

from amal.eda.accellera.ipxact.v1685_2022 import tgi
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
    Driver,
    Drivers,
    Left,
    Model,
    Port,
    PortWireType,
    Range,
    Right,
    SingleShotDriver,
    UnsignedBitExpression,
    UnsignedBitVectorExpression,
)
from org.accellera.ipxact.v1685_2022.driver_type import DriverType

_SCHEMA = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))
_VLNV_PREFIX = ("acme", "driver-tests")


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


def _single_shot_driver() -> SingleShotDriver:
    return SingleShotDriver(
        single_shot_offset=SingleShotDriver.SingleShotOffset(value="1"),
        single_shot_value=UnsignedBitVectorExpression(value="1"),
        single_shot_duration=SingleShotDriver.SingleShotDuration(value="2"),
    )


def _component(*drivers: Driver, name: str = "structural") -> Component:
    for driver in drivers:
        if driver.default_value_or_clock_driver_or_single_shot_driver is None:
            driver.default_value_or_clock_driver_or_single_shot_driver = DefaultValue(value="0")
    ports = [
        Port(
            name=f"data{index}",
            wire_or_transactional_or_structured=PortWireType(
                direction=ComponentPortDirectionType.IN,
                drivers=Drivers(driver=[driver]),
            ),
        )
        for index, driver in enumerate(drivers)
    ]
    return Component(
        vendor="acme",
        library="driver-tests",
        name=name,
        version="1.0",
        model=Model(
            views=Model.Views(view=[Model.Views.View(name="rtl"), Model.Views.View(name="gate")]),
            ports=Model.Ports(port=ports),
        ),
    )


def _round_trip(component: Component) -> Component:
    serialized = XmlDocument.serializer().render(component)
    xml_root = etree.fromstring(serialized.encode())
    assert _SCHEMA.validate(xml_root), str(_SCHEMA.error_log)
    loaded = XmlDocument.parser().from_string(serialized, Component)
    assert loaded == component
    return loaded


def _register(component: Component) -> tuple[str, list[Driver]]:
    root_id = get_handle(component)
    assert registry.register(component, (*_VLNV_PREFIX, component.name, component.version))
    assert registry.get_id((*_VLNV_PREFIX, component.name, component.version)) == root_id
    drivers = [port.wire_or_transactional_or_structured.drivers.driver[0] for port in component.model.ports.port]
    return root_id, drivers


def test_structural_driver_operations_have_annex_signatures_and_exports() -> None:
    expected = {
        "removeDriverClockDriver": (["driverID"], [str], bool, "F.7.42.3"),
        "removeDriverRange": (["driverID"], [str], bool, "F.7.42.4"),
        "removeDriverSingleShotDriver": (["driverID"], [str], bool, "F.7.42.5"),
        "removeDriverViewRef": (["viewRefID"], [str], bool, "F.7.42.6"),
        "setDriverDefaultValue": (["driverID", "value"], [str, str], bool, "F.7.42.13"),
        "setDriverRange": (["driverID", "range"], [str, Sequence[str]], bool, "F.7.42.14"),
    }

    for name, (parameter_names, parameter_types, return_type, section) in expected.items():
        function = getattr(api, name)
        assert getattr(tgi, name) is function
        assert name in api.__all__
        assert name in tgi.__all__
        function_signature = signature(function)
        assert list(function_signature.parameters) == parameter_names
        assert function_signature.return_annotation is return_type
        hints = get_type_hints(function)
        assert [hints[parameter] for parameter in parameter_names] == parameter_types
        assert hints["return"] is return_type
        assert f"Section: {section}." in (function.__doc__ or "")


@pytest.mark.parametrize(
    ("choice", "remove", "child_getter", "descendant_attr"),
    [
        (_clock_driver, api.removeDriverClockDriver, api.getDriverClockDriverID, "clock_period"),
        (_single_shot_driver, api.removeDriverSingleShotDriver, api.getDriverSingleShotDriverID, "single_shot_value"),
    ],
    ids=["clock-driver", "single-shot-driver"],
)
def test_choice_removers_take_driver_handle_and_invalidate_owned_subtrees(
    choice: Callable[[], ClockDriver | SingleShotDriver],
    remove: Callable[[str], bool],
    child_getter: Callable[[str], str | None],
    descendant_attr: str,
) -> None:
    selected = Driver(
        range=Range(left=Left(value="7"), right=Right(value="0")),
        view_ref=[DriverType.ViewRef(value="rtl")],
        default_value_or_clock_driver_or_single_shot_driver=choice(),
    )
    sibling = Driver(default_value_or_clock_driver_or_single_shot_driver=DefaultValue(value="1"))
    component = _round_trip(_component(selected, sibling))
    root_id, drivers = _register(component)
    selected, sibling = drivers
    selected_id, sibling_id = get_handle(selected), get_handle(sibling)
    selected_range = selected.range
    selected_range_id = get_handle(selected_range)
    child_id = child_getter(selected_id)
    assert child_id is not None
    child = resolve_handle(child_id)
    descendant = getattr(child, descendant_attr)
    descendant_id = get_handle(descendant)
    sibling_choice = sibling.default_value_or_clock_driver_or_single_shot_driver
    sibling_choice_id = api.getDriverDefaultValueID(sibling_id)
    assert sibling_choice_id == get_handle(sibling_choice)

    assert remove(selected_id)

    assert selected.default_value_or_clock_driver_or_single_shot_driver is None
    assert child_getter(selected_id) is None
    assert resolve_handle(child_id) is None
    assert resolve_handle(descendant_id) is None
    assert selected.range is selected_range
    assert resolve_handle(selected_range_id) is selected_range
    assert not remove(selected_id)
    assert get_parent_info(sibling_choice_id) is not None
    assert resolve_handle(sibling_choice_id) is sibling_choice
    assert api.getDriverDefaultValueID(sibling_id) == sibling_choice_id
    assert registry.get_vlnv(root_id) == (*_VLNV_PREFIX, component.name, component.version)


def test_remove_driver_range_invalidates_range_and_endpoints_without_touching_other_drivers() -> None:
    selected = Driver(range=Range(left=Left(value="7"), right=Right(value="0")))
    sibling = Driver(range=Range(left=Left(value="3"), right=Right(value="1")))
    component = _round_trip(_component(selected, sibling))
    root_id, drivers = _register(component)
    selected, sibling = drivers
    selected_id, sibling_id = get_handle(selected), get_handle(sibling)
    range_id = get_handle(selected.range)
    endpoint_ids = (get_handle(selected.range.left), get_handle(selected.range.right))
    sibling_range = sibling.range
    sibling_ids = (get_handle(sibling_range), get_handle(sibling_range.left), get_handle(sibling_range.right))

    assert api.removeDriverRange(selected_id)

    assert selected.range is None
    assert api.getDriverRangeExpression(selected_id) == (None, None)
    assert all(resolve_handle(handle) is None for handle in (range_id, *endpoint_ids))
    assert not api.removeDriverRange(selected_id)
    assert sibling.range is sibling_range
    assert all(resolve_handle(handle) is not None for handle in sibling_ids)
    assert api.getDriverRangeExpression(sibling_id) == ("3", "1")
    assert registry.get_vlnv(root_id) == (*_VLNV_PREFIX, component.name, component.version)
    assert _round_trip(component) == component


@pytest.mark.parametrize(
    ("remove", "empty_driver"),
    [
        (api.removeDriverClockDriver, Driver()),
        (api.removeDriverRange, Driver()),
        (api.removeDriverSingleShotDriver, Driver()),
    ],
    ids=["clock-driver", "range", "single-shot-driver"],
)
def test_driver_removers_report_absence_and_reject_non_driver_handles(
    remove: Callable[[str], bool], empty_driver: Driver
) -> None:
    driver_id = get_handle(empty_driver)
    assert not remove(driver_id)
    for invalid_id in ("missing-driver", get_handle(DriverType.ViewRef(value="rtl"))):
        with pytest.raises(TgiError) as error:
            remove(invalid_id)
        assert error.value.fault_code == TgiFaultCode.INVALID_ID


def test_remove_driver_view_ref_checks_owner_and_preserves_sibling_references() -> None:
    first = Driver(view_ref=[DriverType.ViewRef(value="rtl"), DriverType.ViewRef(value="gate")])
    other = Driver(view_ref=[DriverType.ViewRef(value="rtl")])
    component = _round_trip(_component(first, other))
    _, drivers = _register(component)
    first, other = drivers
    first_id, other_id = get_handle(first), get_handle(other)
    first_refs = list(first.view_ref)
    first_ref_ids = api.getDriverViewRefIDs(first_id)
    other_ref_id = api.getDriverViewRefIDs(other_id)[0]

    assert api.removeDriverViewRef(first_ref_ids[0])

    assert first.view_ref == [first_refs[1]]
    assert resolve_handle(first_ref_ids[0]) is None
    assert api.getDriverViewRefIDs(first_id) == [first_ref_ids[1]]
    assert get_parent_info(first_ref_ids[1]).parent_handle == first_id
    assert resolve_handle(other_ref_id) is other.view_ref[0]
    for invalid_id in (first_ref_ids[0], "missing-view-ref"):
        with pytest.raises(TgiError) as error:
            api.removeDriverViewRef(invalid_id)
        assert error.value.fault_code == TgiFaultCode.INVALID_ID
    assert _round_trip(component) == component


def test_remove_driver_view_ref_rejects_orphans_and_removes_from_its_actual_driver_owner() -> None:
    orphan = DriverType.ViewRef(value="rtl")
    first = Driver(view_ref=[DriverType.ViewRef(value="rtl")])
    second = Driver(view_ref=[DriverType.ViewRef(value="gate")])
    component = _component(first, second)
    _, drivers = _register(component)
    first_id, second_id = map(get_handle, drivers)
    orphan_id = get_handle(orphan)
    foreign_ref_id = api.getDriverViewRefIDs(second_id)[0]

    with pytest.raises(TgiError) as error:
        api.removeDriverViewRef(orphan_id)
    assert error.value.fault_code == TgiFaultCode.INVALID_ID

    assert api.removeDriverViewRef(foreign_ref_id)
    assert api.getDriverViewRefIDs(first_id) == [get_handle(first.view_ref[0])]
    assert api.getDriverViewRefIDs(second_id) == []
    assert resolve_handle(foreign_ref_id) is None


def test_set_driver_default_value_updates_existing_wrapper_in_place() -> None:
    default = DefaultValue(value="1")
    default.other_attributes = {"{urn:test}tag": "retain"}
    driver = Driver(default_value_or_clock_driver_or_single_shot_driver=default)
    component = _component(driver)
    _, (driver,) = _register(component)
    driver_id = get_handle(driver)
    default_id = get_handle(default)

    assert api.setDriverDefaultValue(driver_id, "8'h2a")

    assert driver.default_value_or_clock_driver_or_single_shot_driver is default
    assert default.value == "8'h2a"
    assert default.other_attributes == {"{urn:test}tag": "retain"}
    assert api.getDriverDefaultValueID(driver_id) == default_id
    assert api.getDriverDefaultValueExpression(driver_id) == "8'h2a"
    owner = get_parent_info(default_id)
    assert owner is not None
    assert (owner.parent_handle, owner.path, owner.container) == (
        driver_id,
        ("default_value_or_clock_driver_or_single_shot_driver",),
        "single",
    )
    assert _round_trip(component) == component


def test_set_driver_default_value_rejects_invalid_owner_handle() -> None:
    with pytest.raises(TgiError) as error:
        api.setDriverDefaultValue("missing-driver", "1")
    assert error.value.fault_code == TgiFaultCode.INVALID_ID


@pytest.mark.parametrize("choice", [_clock_driver, _single_shot_driver], ids=["clock", "single-shot"])
def test_set_driver_default_value_replaces_alternative_only_after_validation(
    choice: Callable[[], ClockDriver | SingleShotDriver],
) -> None:
    old_choice = choice()
    driver = Driver(default_value_or_clock_driver_or_single_shot_driver=old_choice)
    component = _component(driver)
    _, (driver,) = _register(component)
    driver_id = get_handle(driver)
    old_choice_id = get_handle(old_choice)
    old_descendant = old_choice.clock_period if isinstance(old_choice, ClockDriver) else old_choice.single_shot_value
    old_descendant_id = get_handle(old_descendant)
    before = XmlDocument.serializer().render(component)

    with pytest.raises(TgiError) as error:
        api.setDriverDefaultValue(driver_id, "1 +")
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert XmlDocument.serializer().render(component) == before
    assert resolve_handle(old_choice_id) is old_choice
    assert resolve_handle(old_descendant_id) is old_descendant

    assert api.setDriverDefaultValue(driver_id, "-1")

    replacement = driver.default_value_or_clock_driver_or_single_shot_driver
    assert isinstance(replacement, DefaultValue)
    assert replacement.value == "-1"
    assert resolve_handle(old_choice_id) is None
    assert resolve_handle(old_descendant_id) is None
    assert api.getDriverDefaultValueExpression(driver_id) == "-1"
    assert _round_trip(component) == component


def test_set_driver_default_value_retains_a_valid_symbolic_source() -> None:
    default = DefaultValue(value="WIDTH")
    driver = Driver(default_value_or_clock_driver_or_single_shot_driver=default)
    driver_id = get_handle(driver)
    default_id = get_handle(default)

    assert api.setDriverDefaultValue(driver_id, "DATA_WIDTH - 1")

    assert driver.default_value_or_clock_driver_or_single_shot_driver is default
    assert default.value == "DATA_WIDTH - 1"
    assert api.getDriverDefaultValueID(driver_id) == default_id
    assert api.getDriverDefaultValueExpression(driver_id) == "DATA_WIDTH - 1"


def test_set_driver_range_preserves_endpoint_identity_bounds_order_and_source() -> None:
    left = Left(value="7", minimum=0, maximum=31)
    right = Right(value="0", minimum=0, maximum=31)
    left.other_attributes = {"{urn:test}left": "keep"}
    right.other_attributes = {"{urn:test}right": "keep"}
    value_range = Range(left=left, right=right)
    driver = Driver(range=value_range)
    component = _component(driver)
    _, (driver,) = _register(component)
    driver_id = get_handle(driver)
    range_id = get_handle(value_range)
    left_id, right_id = get_handle(left), get_handle(right)

    assert api.setDriverRange(driver_id, ["8'hf", "2"])

    assert driver.range is value_range
    assert value_range.left is left
    assert value_range.right is right
    assert (left.value, right.value) == ("8'hf", "2")
    assert (left.minimum, left.maximum, right.minimum, right.maximum) == (0, 31, 0, 31)
    assert left.other_attributes == {"{urn:test}left": "keep"}
    assert right.other_attributes == {"{urn:test}right": "keep"}
    assert (api.getDriverLeftID(driver_id), api.getDriverRightID(driver_id)) == (left_id, right_id)
    assert api.getDriverRangeExpression(driver_id) == ("8'hf", "2")
    assert api.getDriverRange(driver_id) == (15, 2)
    assert get_handle(driver.range) == range_id
    assert _round_trip(component) == component


def test_set_driver_range_creates_owned_endpoints_and_preserves_descending_order() -> None:
    driver = Driver()
    driver_id = get_handle(driver)

    assert api.setDriverRange(driver_id, ("15", "0"))

    assert api.getDriverRangeExpression(driver_id) == ("15", "0")
    assert api.getDriverRange(driver_id) == (15, 0)
    value_range = driver.range
    assert value_range is not None
    assert api.getDriverLeftID(driver_id) == get_handle(value_range.left)
    assert api.getDriverRightID(driver_id) == get_handle(value_range.right)
    for handle, path in (
        (get_handle(value_range), ("range",)),
        (get_handle(value_range.left), ("left",)),
        (get_handle(value_range.right), ("right",)),
    ):
        owner = get_parent_info(handle)
        assert owner is not None
        assert owner.path == path


def test_set_driver_range_rejects_invalid_owner_handle() -> None:
    with pytest.raises(TgiError) as error:
        api.setDriverRange("missing-driver", ["1", "0"])
    assert error.value.fault_code == TgiFaultCode.INVALID_ID


@pytest.mark.parametrize("sources", [["5", "1 +"], ["5", "33'h1_0000_0000"]])
def test_set_driver_range_validates_both_endpoints_before_mutating(sources: list[str]) -> None:
    value_range = Range(
        left=Left(value="3", minimum=0, maximum=8),
        right=Right(value="1", minimum=0, maximum=8),
    )
    driver = Driver(range=value_range)
    driver_id = get_handle(driver)
    before = XmlDocument.serializer().render(driver)
    endpoint_ids = (get_handle(value_range.left), get_handle(value_range.right))

    with pytest.raises(TgiError) as error:
        api.setDriverRange(driver_id, sources)  # type: ignore[arg-type]

    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert XmlDocument.serializer().render(driver) == before
    assert driver.range is value_range
    assert (value_range.left.value, value_range.right.value) == ("3", "1")
    assert (get_handle(value_range.left), get_handle(value_range.right)) == endpoint_ids


def test_set_driver_range_retains_symbolic_sources_for_later_evaluation() -> None:
    driver = Driver()
    driver_id = get_handle(driver)

    assert api.setDriverRange(driver_id, ["DATA_WIDTH - 1", "INDEX"])

    assert api.getDriverRangeExpression(driver_id) == ("DATA_WIDTH - 1", "INDEX")
    with pytest.raises(TgiError) as error:
        api.getDriverRange(driver_id)
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT


def test_set_driver_range_rejects_declared_bound_violation_without_mutating() -> None:
    value_range = Range(left=Left(value="3", minimum=6, maximum=8), right=Right(value="1"))
    driver = Driver(range=value_range)
    driver_id = get_handle(driver)
    before = XmlDocument.serializer().render(driver)

    with pytest.raises(TgiError) as error:
        api.setDriverRange(driver_id, ["5", "2"])

    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert XmlDocument.serializer().render(driver) == before
    assert (value_range.left.value, value_range.right.value) == ("3", "1")


@pytest.mark.parametrize("sources", [["1"], ["1", "2", "3"], ["1", 2], "12"])
def test_set_driver_range_requires_exactly_two_string_sources_atomically(sources: object) -> None:
    driver = Driver(range=Range(left=Left(value="4"), right=Right(value="0")))
    driver_id = get_handle(driver)
    before = XmlDocument.serializer().render(driver)

    with pytest.raises(TgiError) as error:
        api.setDriverRange(driver_id, sources)  # type: ignore[arg-type]

    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert XmlDocument.serializer().render(driver) == before

"""Driver ranges and view references follow the generated IP-XACT model."""

import inspect
from collections.abc import Iterator
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
    Abstractor,
    AbstractorBusInterfaceType,
    AbstractorModelType,
    AbstractorModeType,
    AbstractorPortType,
    AbstractorPortWireType,
    AbstractorType,
    Component,
    ComponentInstantiationType,
    ComponentPortDirectionType,
    DefaultValue,
    Driver,
    Drivers,
    Left,
    LibraryRefType,
    Model,
    Port,
    PortWireType,
    Range,
    Right,
)
from org.accellera.ipxact.v1685_2022.driver_type import DriverType

_SCHEMA = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))


@pytest.fixture(autouse=True)
def clean_registry() -> Iterator[None]:
    registry.clear()
    yield
    registry.clear()


def _driver(left: str | None = "7", right: str | None = "0") -> Driver:
    value_range = None
    if left is not None or right is not None:
        value_range = Range(
            left=None if left is None else Left(value=left),
            right=None if right is None else Right(value=right),
        )
    return Driver(range=value_range)


def _component(name: str, driver: Driver, *view_names: str) -> Component:
    return Component(
        vendor="acme",
        library="test",
        name=name,
        version="1.0",
        model=Model(
            views=Model.Views(view=[Model.Views.View(name=view_name) for view_name in view_names]),
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


@pytest.mark.parametrize(
    ("left", "right", "expected"),
    [
        ("0", "0", (0, 0)),
        ("8'hff + 1", "32'hffff_ffff", (256, 0xFFFFFFFF)),
        ("2**4", "3 * 2", (16, 6)),
        ("32'h1_0000_0000", "0", (0, 0)),
        ("0", "7", (0, 7)),
    ],
)
def test_driver_range_evaluates_unsigned_constants_without_changing_source(
    left: str, right: str, expected: tuple[int | None, int | None]
) -> None:
    driver = _driver(left, right)
    driver_id = get_handle(driver)

    assert api.getDriverRange(driver_id) == expected
    assert api.getDriverRangeExpression(driver_id) == (left, right)


@pytest.mark.parametrize("endpoint", ["left", "right"])
@pytest.mark.parametrize("source", ["-1", "64'h1_0000_0000", "UNRESOLVED_WIDTH", "1 +", "1.5", "4'bxxxx"])
def test_driver_range_rejects_invalid_or_unresolved_unsigned_32_bit_expressions(endpoint: str, source: str) -> None:
    driver_id = get_handle(_driver(source, "0") if endpoint == "left" else _driver("0", source))

    expected_expression = (source, "0") if endpoint == "left" else ("0", source)
    assert api.getDriverRangeExpression(driver_id) == expected_expression
    with pytest.raises(TgiError) as error:
        api.getDriverRange(driver_id)
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT


def test_driver_range_honors_inclusive_declared_endpoint_bounds() -> None:
    driver = Driver(range=Range(left=Left(value="4", minimum=4, maximum=4), right=Right(value="8")))
    driver_id = get_handle(driver)
    assert api.getDriverRange(driver_id) == (4, 8)


@pytest.mark.parametrize(
    ("endpoint", "minimum", "maximum"),
    [("left", 5, 8), ("right", 5, 8), ("left", 8, 5), ("left", 0, 3)],
)
def test_driver_range_rejects_values_outside_or_reversed_declared_bounds(
    endpoint: str, minimum: int, maximum: int
) -> None:
    left = Left(value="4", minimum=minimum, maximum=maximum) if endpoint == "left" else Left(value="4")
    right = Right(value="4", minimum=minimum, maximum=maximum) if endpoint == "right" else Right(value="4")
    driver_id = get_handle(Driver(range=Range(left=left, right=right)))
    with pytest.raises(TgiError) as error:
        api.getDriverRange(driver_id)
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT


def test_driver_range_ids_are_owned_and_missing_endpoints_remain_optional() -> None:
    driver = _driver(None, "4'hf")
    driver_id = get_handle(driver)

    assert api.getDriverRange(driver_id) == (None, 15)
    assert api.getDriverRangeExpression(driver_id) == (None, "4'hf")
    assert api.getDriverLeftID(driver_id) is None
    right_id = api.getDriverRightID(driver_id)
    assert right_id == get_handle(driver.range.right)
    right_owner = get_parent_info(right_id)
    assert right_owner is not None
    assert (right_owner.parent_handle, right_owner.path, right_owner.container) == (
        get_handle(driver.range),
        ("right",),
        "single",
    )
    range_owner = get_parent_info(get_handle(driver.range))
    assert range_owner is not None
    assert (range_owner.parent_handle, range_owner.path, range_owner.container) == (
        driver_id,
        ("range",),
        "single",
    )

    empty_id = get_handle(Driver())
    assert api.getDriverRange(empty_id) == (None, None)
    assert api.getDriverRangeExpression(empty_id) == (None, None)
    assert api.getDriverLeftID(empty_id) is None
    assert api.getDriverRightID(empty_id) is None


@pytest.mark.parametrize(
    ("left", "right"),
    [("15", "0"), ("0", "15")],
)
def test_driver_range_preserves_ascending_and_descending_endpoint_order(left: str, right: str) -> None:
    driver_id = get_handle(_driver(left, right))
    assert api.getDriverRange(driver_id) == (int(left), int(right))
    assert api.getDriverRangeExpression(driver_id) == (left, right)


def test_driver_view_refs_return_ordered_owned_handles_and_resolve_local_targets() -> None:
    driver = Driver(view_ref=[DriverType.ViewRef(value="rtl"), DriverType.ViewRef(value="gate")])
    component = _component("views", driver, "rtl", "gate")
    registry.register(component, ("acme", "test", "views", "1.0"))
    driver_id = get_handle(driver)

    reference_ids = api.getDriverViewRefIDs(driver_id)
    assert reference_ids == [get_handle(reference) for reference in driver.view_ref]
    for reference_id in reference_ids:
        owner = get_parent_info(reference_id)
        assert owner is not None
        assert (owner.parent_handle, owner.path, owner.container) == (driver_id, ("view_ref",), "list")

    targets = [api.getDriverViewRefByID(driver_id, reference_id) for reference_id in reference_ids]
    assert [resolve_handle(target).name for target in targets] == ["rtl", "gate"]
    assert targets == [get_handle(view) for view in component.model.views.view]


def test_driver_view_ref_lookup_is_scoped_to_the_owning_component() -> None:
    first_driver = Driver(view_ref=[DriverType.ViewRef(value="rtl")])
    second_driver = Driver(view_ref=[DriverType.ViewRef(value="rtl")])
    first = _component("first", first_driver, "rtl")
    second = _component("second", second_driver, "rtl")
    registry.register(first, ("acme", "test", "first", "1.0"))
    registry.register(second, ("acme", "test", "second", "1.0"))

    first_driver_id = get_handle(first_driver)
    second_driver_id = get_handle(second_driver)
    first_ref_id = api.getDriverViewRefIDs(first_driver_id)[0]
    second_ref_id = api.getDriverViewRefIDs(second_driver_id)[0]
    first_target = api.getDriverViewRefByID(first_driver_id, first_ref_id)
    second_target = api.getDriverViewRefByID(second_driver_id, second_ref_id)
    assert first_target == get_handle(first.model.views.view[0])
    assert second_target == get_handle(second.model.views.view[0])
    assert first_target != second_target


def test_driver_view_ref_lookup_supports_abstractor_owned_views() -> None:
    driver = Driver(view_ref=[DriverType.ViewRef(value="rtl")])
    abstractor = Abstractor(
        vendor="acme",
        library="test",
        name="view-owner",
        version="1.0",
        abstractor_mode=AbstractorType.AbstractorMode(value=AbstractorModeType.DIRECT),
        bus_type=LibraryRefType(vendor="acme", library="test", name="bus", version="1.0"),
        abstractor_interfaces=AbstractorType.AbstractorInterfaces(
            abstractor_interface=[AbstractorBusInterfaceType(name="master"), AbstractorBusInterfaceType(name="slave")]
        ),
        model=AbstractorModelType(
            views=AbstractorModelType.Views(view=[AbstractorModelType.Views.View(name="rtl")]),
            ports=AbstractorModelType.Ports(
                port=[
                    AbstractorPortType(
                        name="data",
                        wire_or_transactional_or_structured=AbstractorPortWireType(
                            direction=ComponentPortDirectionType.IN,
                            drivers=Drivers(driver=[driver]),
                        ),
                    )
                ]
            ),
        ),
    )
    registry.register(abstractor, ("acme", "test", "view-owner", "1.0"))

    driver_id = get_handle(driver)
    view_ref_id = api.getDriverViewRefIDs(driver_id)[0]
    view_id = api.getDriverViewRefByID(driver_id, view_ref_id)
    assert resolve_handle(view_id).name == "rtl"
    assert resolve_handle(view_id) is abstractor.model.views.view[0]


def test_driver_view_ref_rejects_foreign_ids_and_missing_or_ambiguous_targets() -> None:
    driver = Driver(view_ref=[DriverType.ViewRef(value="rtl")])
    owner = _component("owner", driver, "rtl")
    foreign_ref = DriverType.ViewRef(value="rtl")
    foreign_driver = Driver(view_ref=[foreign_ref])
    registry.register(owner, ("acme", "test", "owner", "1.0"))
    registry.register(_component("foreign", foreign_driver, "rtl"), ("acme", "test", "foreign", "1.0"))

    driver_id = get_handle(driver)
    with pytest.raises(TgiError) as error:
        api.getDriverViewRefByID(driver_id, get_handle(foreign_ref))
    assert error.value.fault_code == TgiFaultCode.INVALID_ID

    missing_driver = Driver(view_ref=[DriverType.ViewRef(value="missing")])
    registry.register(_component("missing", missing_driver), ("acme", "test", "missing", "1.0"))
    missing_id = api.getDriverViewRefIDs(get_handle(missing_driver))[0]
    with pytest.raises(TgiError) as error:
        api.getDriverViewRefByID(get_handle(missing_driver), missing_id)
    assert error.value.fault_code == TgiFaultCode.NOT_FOUND

    ambiguous_driver = Driver(view_ref=[DriverType.ViewRef(value="rtl")])
    registry.register(_component("ambiguous", ambiguous_driver, "rtl", "rtl"), ("acme", "test", "ambiguous", "1.0"))
    ambiguous_id = api.getDriverViewRefIDs(get_handle(ambiguous_driver))[0]
    with pytest.raises(TgiError) as error:
        api.getDriverViewRefByID(get_handle(ambiguous_driver), ambiguous_id)
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT


def test_driver_range_and_view_getters_reject_invalid_handles() -> None:
    wrong_type_id = get_handle(DriverType.ViewRef(value="rtl"))
    for getter in (
        api.getDriverLeftID,
        api.getDriverRange,
        api.getDriverRangeExpression,
        api.getDriverRightID,
        api.getDriverViewRefIDs,
    ):
        for handle in ("missing-id", wrong_type_id):
            with pytest.raises(TgiError) as error:
                getter(handle)
            assert error.value.fault_code == TgiFaultCode.INVALID_ID

    with pytest.raises(TgiError) as error:
        api.getDriverViewRefByID("missing-id", "reference-id")
    assert error.value.fault_code == TgiFaultCode.INVALID_ID


def test_driver_range_and_view_source_survive_component_xml_round_trip() -> None:
    driver = _driver(" 8'h0f + 1 ", "0")
    driver.default_value_or_clock_driver_or_single_shot_driver = DefaultValue(value="0")
    driver.view_ref.append(DriverType.ViewRef(value="rtl"))
    component = _component("round-trip", driver, "rtl")
    component.model.views.view[0].component_instantiation_ref = "rtl"
    component.model.instantiations = Model.Instantiations(
        component_instantiation_or_design_instantiation_or_design_configuration_instantiation=[
            ComponentInstantiationType(name="rtl")
        ]
    )
    serialized = XmlDocument.serializer().render(component)
    assert _SCHEMA.validate(etree.fromstring(serialized.encode()))
    loaded = XmlDocument.parser().from_string(serialized, Component)
    registry.register(loaded, ("acme", "test", "round-trip", "1.0"))
    loaded_driver = loaded.model.ports.port[0].wire_or_transactional_or_structured.drivers.driver[0]
    loaded_driver_id = get_handle(loaded_driver)

    assert api.getDriverRangeExpression(loaded_driver_id) == (" 8'h0f + 1 ", "0")
    assert api.getDriverRange(loaded_driver_id) == (16, 0)
    view_ref_id = api.getDriverViewRefIDs(loaded_driver_id)[0]
    assert api.getDriverViewRefByID(loaded_driver_id, view_ref_id) == get_handle(loaded.model.views.view[0])


def test_driver_range_and_view_getter_signatures_exports_and_native_annotations() -> None:
    expected = {
        "getDriverLeftID": ([str], str | None),
        "getDriverRange": ([str], tuple[int | None, int | None]),
        "getDriverRangeExpression": ([str], tuple[str | None, str | None]),
        "getDriverRightID": ([str], str | None),
        "getDriverViewRefByID": ([str, str], str),
        "getDriverViewRefIDs": ([str], list[str]),
    }

    for name, (parameters, return_type) in expected.items():
        function = getattr(api, name)
        assert getattr(tgi, name) is function
        assert name in api.__all__
        assert name in tgi.__all__
        signature = inspect.signature(function)
        expected_parameters = ["driverID", "viewRef"] if name == "getDriverViewRefByID" else ["driverID"]
        assert list(signature.parameters) == expected_parameters
        assert all(parameter.default is inspect.Parameter.empty for parameter in signature.parameters.values())
        hints = get_type_hints(function)
        assert [hints[parameter] for parameter in signature.parameters] == parameters
        assert hints["return"] == return_type
        assert signature.return_annotation == return_type
        assert not isinstance(signature.return_annotation, str)

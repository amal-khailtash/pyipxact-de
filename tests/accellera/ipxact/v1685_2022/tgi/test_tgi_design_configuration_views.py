"""TGI contracts for design-configuration view selections."""

import inspect
from collections.abc import Iterator
from pathlib import Path
from typing import get_type_hints

import pytest
from lxml import etree

from amal.eda.accellera.ipxact.v1685_2022 import tgi
from amal.eda.accellera.ipxact.v1685_2022.tgi import configurable_element
from amal.eda.accellera.ipxact.v1685_2022.tgi import design_configuration as api
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
    ConfigurableElementValue,
    ConfigurableElementValues,
    ConfigurableLibraryRefType,
    DesignConfiguration,
    DesignConfigurationInstantiationType,
    InstanceName,
)

_REPO_ROOT = Path(__file__).resolve().parents[5]
_SCHEMA = etree.XMLSchema(etree.parse(str(_REPO_ROOT / "submodules/accellera-schemas/IPXACT/1685-2022/index.xsd")))
_API_FUNCTIONS = (
    "getDesignConfigurationViewConfigurationIDs",
    "getViewConfigurationConfigurableElementValueIDs",
    "getViewConfigurationInstanceName",
    "getViewConfigurationViewID",
    "getViewConfigurationViewRefByName",
    "setViewConfigurationInstanceName",
    "setViewConfigurationView",
)


@pytest.fixture(autouse=True)
def clean_registry() -> Iterator[None]:
    registry.clear()
    yield
    registry.clear()


def _view_configuration(
    instance_name: str,
    view_ref: str,
    values: tuple[tuple[str, str], ...] = (),
    *,
    configuration_id: str | None = None,
) -> DesignConfiguration.ViewConfiguration:
    value_objects = [
        ConfigurableElementValue(reference_id=reference_id, value=expression, id=f"{reference_id}_id")
        for reference_id, expression in values
    ]
    holder = ConfigurableElementValues(configurable_element_value=value_objects) if value_objects else None
    return DesignConfiguration.ViewConfiguration(
        instance_name=InstanceName(value=instance_name),
        view=DesignConfiguration.ViewConfiguration.View(view_ref=view_ref, configurable_element_values=holder),
        id=configuration_id,
    )


def _document(*view_configurations: DesignConfiguration.ViewConfiguration) -> DesignConfiguration:
    root = DesignConfiguration(
        vendor="vendor",
        library="library",
        name="configuration",
        version="1",
        view_configuration=list(view_configurations),
    )
    xml = XmlDocument.serializer().render(root)
    parsed = XmlDocument.parser().from_string(xml, DesignConfiguration)
    registry.register(parsed, ("vendor", "library", "configuration", "1"))
    return parsed


def _valid_round_trip(root: DesignConfiguration) -> str:
    xml = XmlDocument.serializer().render(root)
    _SCHEMA.assertValid(etree.fromstring(xml.encode()))
    assert XmlDocument.parser().from_string(xml, DesignConfiguration) == root
    return xml


def test_public_exports_and_native_runtime_annotations() -> None:
    expected = {
        "getDesignConfigurationViewConfigurationIDs": ([str], list[str]),
        "getViewConfigurationConfigurableElementValueIDs": ([str], list[str]),
        "getViewConfigurationInstanceName": ([str], str | None),
        "getViewConfigurationViewID": ([str], str | None),
        "getViewConfigurationViewRefByName": ([str], str | None),
        "setViewConfigurationInstanceName": ([str, str], bool),
        "setViewConfigurationView": ([str, str], bool),
    }

    for name in _API_FUNCTIONS:
        function = getattr(api, name)
        assert getattr(tgi, name) is function
        assert name in api.__all__
        assert name in tgi.__all__
        hints = get_type_hints(function)
        assert [hints[param] for param in inspect.signature(function).parameters] == expected[name][0]
        assert hints["return"] == expected[name][1]


def test_view_configuration_getters_preserve_order_and_restore_parsed_ownership() -> None:
    root = _document(
        _view_configuration("u0", "rtl", (("WIDTH", "16"), ("DEPTH", "8")), configuration_id="vc0"),
        _view_configuration("u1", "simulation", (("MODE", "fast"),), configuration_id="vc1"),
        _view_configuration("u2", "7segment", configuration_id="vc2"),
    )
    root_id = get_handle(root)
    configurations = root.view_configuration
    configuration_ids = api.getDesignConfigurationViewConfigurationIDs(root_id)
    assert configuration_ids == [get_handle(configuration) for configuration in configurations]
    assert [resolve_handle(handle) for handle in configuration_ids] == configurations
    for configuration_id in configuration_ids:
        parent = get_parent_info(configuration_id)
        assert parent is not None
        assert (parent.parent_handle, parent.path, parent.container) == (
            root_id,
            ("view_configuration",),
            "list",
        )
    assert [api.getViewConfigurationInstanceName(handle) for handle in configuration_ids] == ["u0", "u1", "u2"]
    assert [api.getViewConfigurationViewRefByName(handle) for handle in configuration_ids] == [
        "rtl",
        "simulation",
        "7segment",
    ]

    first_configuration = configurations[0]
    first_view = first_configuration.view
    assert first_view is not None
    view_id = api.getViewConfigurationViewID(configuration_ids[0])
    assert view_id == get_handle(first_view)
    assert resolve_handle(view_id) is first_view
    view_parent = get_parent_info(view_id)
    assert view_parent is not None
    assert (view_parent.parent_handle, view_parent.path, view_parent.container) == (
        configuration_ids[0],
        ("view",),
        "single",
    )
    assert api.getViewConfigurationViewRefByName(view_id) == "rtl"
    instance_name = first_configuration.instance_name
    instance_name_parent = get_parent_info(get_handle(instance_name))
    assert instance_name_parent is not None
    assert (instance_name_parent.parent_handle, instance_name_parent.path, instance_name_parent.container) == (
        configuration_ids[0],
        ("instance_name",),
        "single",
    )

    value_ids = api.getViewConfigurationConfigurableElementValueIDs(configuration_ids[0])
    assert value_ids == [
        get_handle(value) for value in first_view.configurable_element_values.configurable_element_value
    ]
    assert [
        resolve_handle(handle) for handle in value_ids
    ] == first_view.configurable_element_values.configurable_element_value
    assert [resolve_handle(value_id).reference_id for value_id in value_ids] == ["WIDTH", "DEPTH"]
    for value_id in value_ids:
        parent = get_parent_info(value_id)
        assert parent is not None
        assert parent.path == ("configurable_element_value",)
        assert parent.container == "list"
        assert parent.parent_handle == get_handle(first_view.configurable_element_values)

    # The generic configurable-element operation must see and remove overrides
    # through the restored ViewConfiguration -> View -> holder ownership chain.
    assert configurable_element.removeConfigurableElementValue(value_ids[0])
    assert resolve_handle(value_ids[0]) is None
    assert api.getViewConfigurationConfigurableElementValueIDs(configuration_ids[0]) == value_ids[1:]
    _valid_round_trip(root)


def test_root_collection_getter_resolves_design_configuration_instantiation_source() -> None:
    root = _document(
        _view_configuration("u0", "rtl", configuration_id="vc0"),
        _view_configuration("u1", "simulation", configuration_id="vc1"),
    )
    expected = api.getDesignConfigurationViewConfigurationIDs(get_handle(root))
    instantiation = DesignConfigurationInstantiationType(
        name="configured",
        design_configuration_ref=ConfigurableLibraryRefType(
            vendor="vendor", library="library", name="configuration", version="1"
        ),
    )

    assert api.getDesignConfigurationViewConfigurationIDs(get_handle(instantiation)) == expected

    missing_target = DesignConfigurationInstantiationType(
        name="missing",
        design_configuration_ref=ConfigurableLibraryRefType(
            vendor="vendor", library="library", name="absent", version="1"
        ),
    )
    with pytest.raises(TgiError) as unresolved:
        api.getDesignConfigurationViewConfigurationIDs(get_handle(missing_target))
    assert unresolved.value.fault_code == TgiFaultCode.NOT_FOUND


def test_view_configuration_getters_handle_missing_optional_intermediates_and_invalid_ids() -> None:
    root = _document(_view_configuration("u0", "rtl"))
    configuration = root.view_configuration[0]
    configuration_id = get_handle(configuration)
    assert api.getViewConfigurationConfigurableElementValueIDs(configuration_id) == []
    assert api.getViewConfigurationInstanceName(configuration_id) == "u0"
    assert api.getViewConfigurationViewID(configuration_id) == get_handle(configuration.view)
    assert api.getViewConfigurationViewRefByName(configuration_id) == "rtl"

    # Incomplete in-memory intermediate state is tolerated by the read APIs.
    configuration.view = None
    assert api.getViewConfigurationConfigurableElementValueIDs(configuration_id) == []
    assert api.getViewConfigurationViewID(configuration_id) is None
    assert api.getViewConfigurationViewRefByName(configuration_id) is None
    configuration.view = DesignConfiguration.ViewConfiguration.View(view_ref="rtl")
    configuration.instance_name = None
    assert api.getViewConfigurationInstanceName(configuration_id) is None

    wrong_kind = get_handle(DesignConfiguration(vendor="vendor", library="library", name="other", version="1"))
    for operation in (
        lambda: api.getViewConfigurationConfigurableElementValueIDs("missing-view-configuration"),
        lambda: api.getViewConfigurationInstanceName("missing-view-configuration"),
        lambda: api.getViewConfigurationViewID("missing-view-configuration"),
        lambda: api.getViewConfigurationViewRefByName("missing-view-configuration"),
        lambda: api.getViewConfigurationConfigurableElementValueIDs(wrong_kind),
        lambda: api.getViewConfigurationInstanceName(wrong_kind),
        lambda: api.getViewConfigurationViewID(wrong_kind),
        lambda: api.getViewConfigurationViewRefByName(wrong_kind),
    ):
        with pytest.raises(TgiError) as error:
            operation()
        assert error.value.fault_code == TgiFaultCode.INVALID_ID


def test_set_view_configuration_instance_name_preserves_wrappers_handles_and_schema() -> None:
    root = _document(
        _view_configuration("u0", "rtl", (("WIDTH", "16"),), configuration_id="vc0"),
        _view_configuration("u1", "rtl", configuration_id="vc1"),
    )
    configuration = root.view_configuration[0]
    configuration_id = get_handle(configuration)
    instance_name = configuration.instance_name
    instance_name_handle = get_handle(instance_name)
    view = configuration.view
    view_id = get_handle(view)
    value = view.configurable_element_values.configurable_element_value[0]
    value_id = get_handle(value)
    before_id = configuration.id

    assert api.setViewConfigurationInstanceName(configuration_id, " \t实例_α\n")
    assert configuration.instance_name is instance_name
    assert get_handle(configuration.instance_name) == instance_name_handle
    assert resolve_handle(instance_name_handle) is instance_name
    assert configuration.instance_name.value == "实例_α"
    assert configuration.id == before_id
    assert get_handle(configuration) == configuration_id
    assert configuration.view is view
    assert get_handle(configuration.view) == view_id
    assert resolve_handle(value_id) is value
    _valid_round_trip(root)


def test_set_view_configuration_instance_name_creates_missing_wrapper() -> None:
    root = _document(_view_configuration("u0", "rtl", configuration_id="vc0"))
    configuration = root.view_configuration[0]
    configuration.instance_name = None

    assert api.setViewConfigurationInstanceName(get_handle(configuration), "u1")
    assert configuration.instance_name is not None
    assert configuration.instance_name.value == "u1"
    parent = get_parent_info(get_handle(configuration.instance_name))
    assert parent is not None
    assert (parent.parent_handle, parent.path, parent.container) == (
        get_handle(configuration),
        ("instance_name",),
        "single",
    )
    _valid_round_trip(root)


@pytest.mark.parametrize("instance_name", ["", " \t\r\n", "2startsWithNumber", "contains space", "bad\x00name"])
def test_set_view_configuration_instance_name_rejects_invalid_xml_names_atomically(instance_name: str) -> None:
    root = _document(
        _view_configuration("u0", "rtl", (("WIDTH", "16"),), configuration_id="vc0"),
        _view_configuration("u1", "rtl", configuration_id="vc1"),
    )
    configuration = root.view_configuration[0]
    configuration_id = get_handle(configuration)
    original_instance_name = configuration.instance_name
    before = _valid_round_trip(root)

    with pytest.raises(TgiError) as error:
        api.setViewConfigurationInstanceName(configuration_id, instance_name)

    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert configuration.instance_name is original_instance_name
    assert _valid_round_trip(root) == before


def test_set_view_configuration_instance_name_rejects_root_wide_duplicates_atomically() -> None:
    root = _document(
        _view_configuration("u0", "rtl", configuration_id="vc0"),
        _view_configuration("u1", "simulation", configuration_id="vc1"),
    )
    configuration = root.view_configuration[1]
    original_instance_name = configuration.instance_name
    before = _valid_round_trip(root)

    with pytest.raises(TgiError) as error:
        api.setViewConfigurationInstanceName(get_handle(configuration), " \tu0\n")

    assert error.value.fault_code == TgiFaultCode.ALREADY_EXISTS
    assert configuration.instance_name is original_instance_name
    assert _valid_round_trip(root) == before


def test_set_view_configuration_view_preserves_nested_overrides_and_accepts_digit_first_nmtoken() -> None:
    root = _document(_view_configuration("u0", "rtl", (("WIDTH", "16"),), configuration_id="vc0"))
    configuration = root.view_configuration[0]
    configuration_id = get_handle(configuration)
    view = configuration.view
    view_id = get_handle(view)
    holder = view.configurable_element_values
    value = holder.configurable_element_value[0]
    value_id = get_handle(value)

    assert api.setViewConfigurationView(configuration_id, " 7segment_β ")
    assert configuration.view is view
    assert get_handle(configuration.view) == view_id
    assert resolve_handle(view_id) is view
    assert view.view_ref == "7segment_β"
    assert view.configurable_element_values is holder
    assert holder.configurable_element_value == [value]
    assert resolve_handle(value_id) is value
    assert get_handle(configuration) == configuration_id
    assert api.getViewConfigurationViewRefByName(view_id) == "7segment_β"
    _valid_round_trip(root)


@pytest.mark.parametrize("view_ref", ["", " \t\r\n", "contains space", "bad\x00name"])
def test_set_view_configuration_view_rejects_invalid_nmtoken_atomically(view_ref: str) -> None:
    root = _document(_view_configuration("u0", "rtl", (("WIDTH", "16"),), configuration_id="vc0"))
    configuration = root.view_configuration[0]
    view = configuration.view
    view_id = get_handle(view)
    before = _valid_round_trip(root)

    with pytest.raises(TgiError) as error:
        api.setViewConfigurationView(get_handle(configuration), view_ref)

    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert configuration.view is view
    assert get_handle(view) == view_id
    assert _valid_round_trip(root) == before


def test_set_view_configuration_view_creates_missing_wrapper_and_rejects_invalid_handles() -> None:
    root = _document(_view_configuration("u0", "rtl", configuration_id="vc0"))
    configuration = root.view_configuration[0]
    configuration.view = None
    configuration_id = get_handle(configuration)

    assert api.setViewConfigurationView(configuration_id, "7rtl")
    assert configuration.view is not None
    assert configuration.view.view_ref == "7rtl"
    assert api.getViewConfigurationViewID(configuration_id) == get_handle(configuration.view)
    _valid_round_trip(root)

    wrong_kind = get_handle(DesignConfiguration(vendor="vendor", library="library", name="other", version="1"))
    for operation in (
        lambda: api.setViewConfigurationView("missing-view-configuration", "rtl"),
        lambda: api.setViewConfigurationInstanceName("missing-view-configuration", "u1"),
        lambda: api.setViewConfigurationView(wrong_kind, "rtl"),
        lambda: api.setViewConfigurationInstanceName(wrong_kind, "u1"),
    ):
        with pytest.raises(TgiError) as error:
            operation()
        assert error.value.fault_code == TgiFaultCode.INVALID_ID


def test_collection_getter_rejects_invalid_document_handles() -> None:
    wrong_kind = get_handle(DesignConfiguration.ViewConfiguration.View(view_ref="rtl"))
    for handle in ("missing-design-configuration", wrong_kind):
        with pytest.raises(TgiError) as error:
            api.getDesignConfigurationViewConfigurationIDs(handle)
        assert error.value.fault_code == TgiFaultCode.INVALID_ID

"""Configurable element override edits preserve IP-XACT schema ownership."""

import pytest
from lxml import etree

from amal.eda.accellera.ipxact.v1685_2022.tgi import configurable_element as api
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import (
    TgiError,
    get_handle,
    registry,
    resolve_handle,
)
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import (
    Component,
    ComponentInstance,
    ComponentInstances,
    ConfigurableElementValues,
    ConfigurableLibraryRefType,
    Design,
    DesignConfiguration,
    InstanceName,
    LibraryRefType,
)

_SCHEMA = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))


@pytest.fixture(autouse=True)
def top_level_registry_only(monkeypatch):
    registry.clear()
    register = registry.register

    def register_document(element, *args, **kwargs):
        assert isinstance(element, (Component, Design, DesignConfiguration))
        return register(element, *args, **kwargs)

    monkeypatch.setattr(registry, "register", register_document)
    yield
    registry.clear()


def _instance(*, component_ref=None):
    return ComponentInstance(
        instance_name=InstanceName(value="u0"),
        component_ref=component_ref or ConfigurableLibraryRefType(vendor="v", library="l", name="leaf", version="1"),
    )


def _design(instance=None):
    return Design(
        vendor="v",
        library="l",
        name="top",
        version="1",
        component_instances=ComponentInstances(component_instance=[instance or _instance()]),
    )


def _configuration(view=None):
    return DesignConfiguration(
        vendor="v",
        library="l",
        name="configuration",
        version="1",
        design_ref=LibraryRefType(vendor="v", library="l", name="top", version="1"),
        view_configuration=[
            DesignConfiguration.ViewConfiguration(
                instance_name=InstanceName(value="u0"),
                view=view or DesignConfiguration.ViewConfiguration.View(view_ref="rtl"),
            )
        ],
    )


def _valid(root):
    xml = XmlDocument.serializer().render(root)
    _SCHEMA.assertValid(etree.fromstring(xml.encode()))
    assert XmlDocument.parser().from_string(xml, type(root)) == root
    return xml


def test_add_routes_library_reference_component_instance_and_direct_holder():
    holder = ConfigurableElementValues()
    reference = ConfigurableLibraryRefType(
        vendor="v", library="l", name="leaf", version="1", configurable_element_values=holder
    )
    instance = _instance(component_ref=reference)
    root = _design(instance)

    from_reference = api.addConfigurableElementValue(get_handle(reference), "  width\t", "16")
    from_instance = api.addConfigurableElementValue(get_handle(instance), "unresolvedParameter", "BASE + 1")
    from_holder = api.addConfigurableElementValue(get_handle(holder), "depth", "8")

    assert [item.reference_id for item in holder.configurable_element_value] == [
        "width",
        "unresolvedParameter",
        "depth",
    ]
    assert [resolve_handle(handle) for handle in (from_reference, from_instance, from_holder)] == list(
        holder.configurable_element_value
    )
    assert _valid(root)


@pytest.mark.parametrize(
    "reference_id,expression",
    [("   ", "1"), ("bad name", "1"), ("valid", "bad\x00xml")],
)
def test_add_validates_reference_name_and_xml_text_before_creating_holder(reference_id, expression):
    reference = _instance().component_ref
    root = _design(ComponentInstance(instance_name=InstanceName(value="u0"), component_ref=reference))
    before = _valid(root)

    with pytest.raises(TgiError):
        api.addConfigurableElementValue(get_handle(reference), reference_id, expression)

    assert reference.configurable_element_values is None
    assert _valid(root) == before


def test_add_rejects_duplicate_collapsed_reference_ids_atomically():
    reference = _instance().component_ref
    root = _design(ComponentInstance(instance_name=InstanceName(value="u0"), component_ref=reference))
    first = api.addConfigurableElementValue(get_handle(reference), "  width\t", "16")
    before = _valid(root)

    with pytest.raises(TgiError):
        api.addConfigurableElementValue(get_handle(reference), "width", "32")

    assert _valid(root) == before
    assert reference.configurable_element_values.configurable_element_value == [resolve_handle(first)]


def test_reference_id_setter_rejects_duplicate_without_mutating_holder():
    reference = _instance().component_ref
    root = _design(ComponentInstance(instance_name=InstanceName(value="u0"), component_ref=reference))
    api.addConfigurableElementValue(get_handle(reference), "width", "16")
    second_id = api.addConfigurableElementValue(get_handle(reference), "depth", "8")
    before = _valid(root)

    with pytest.raises(TgiError):
        api.setConfigurableElementValueReferenceID(second_id, "  width\t")

    second = resolve_handle(second_id)
    assert second.reference_id == "depth"
    assert _valid(root) == before


def test_override_value_edit_preserves_value_object_identity_and_other_attributes():
    reference = _instance().component_ref
    root = _design(ComponentInstance(instance_name=InstanceName(value="u0"), component_ref=reference))
    value_id = api.addConfigurableElementValue(get_handle(reference), "width", "16")
    value = resolve_handle(value_id)
    value.other_attributes["{urn:example}source"] = "override"
    before_value_id = get_handle(value)

    assert api.setConfigurableElementValueValue(value_id, "BASE & (WIDTH < 64)")

    assert resolve_handle(value_id) is value
    assert get_handle(reference.configurable_element_values.configurable_element_value[0]) == before_value_id
    assert value.value == "BASE & (WIDTH < 64)"
    assert value.other_attributes["{urn:example}source"] == "override"
    parsed = XmlDocument.parser().from_string(_valid(root), Design)
    parsed_value = parsed.component_instances.component_instance[0].component_ref
    assert parsed_value.configurable_element_values.configurable_element_value[0].value == value.value


@pytest.mark.parametrize("as_tuple", [False, True])
def test_remove_parsed_override_recovers_registered_owner_and_prunes_empty_holder(as_tuple):
    reference = _instance().component_ref
    api.addConfigurableElementValue(get_handle(reference), "width", "16")
    root = _design(ComponentInstance(instance_name=InstanceName(value="u0"), component_ref=reference))
    parsed = XmlDocument.parser().from_string(_valid(root), Design)
    registry.register(parsed, ["v", "l", "top", "1"])
    parsed_reference = parsed.component_instances.component_instance[0].component_ref
    holder = parsed_reference.configurable_element_values
    value = holder.configurable_element_value[0]
    if as_tuple:
        holder.configurable_element_value = tuple(holder.configurable_element_value)
    value_id = get_handle(value)
    holder_id = get_handle(holder)

    assert api.removeConfigurableElementValue(value_id)

    assert parsed_reference.configurable_element_values is None
    assert resolve_handle(value_id) is None
    assert resolve_handle(holder_id) is None
    assert _valid(parsed)


def test_view_override_requires_real_view_configuration_and_preserves_required_view_ref():
    config = _configuration()
    view_configuration = config.view_configuration[0]
    view = view_configuration.view

    value_id = api.addViewConfigurationConfigurableElementValue(
        get_handle(view_configuration), "localOverride", "(BASE + 2)"
    )

    assert isinstance(view.configurable_element_values, ConfigurableElementValues)
    assert view.view_ref == "rtl"
    assert resolve_handle(value_id).reference_id == "localOverride"
    assert _valid(config)

    with pytest.raises(TgiError):
        api.addViewConfigurationConfigurableElementValue(get_handle(_instance()), "width", "1")

    missing_view = _configuration().view_configuration[0]
    missing_view.view = None
    with pytest.raises(TgiError):
        api.addViewConfigurationConfigurableElementValue(get_handle(missing_view), "width", "1")
    assert missing_view.view is None

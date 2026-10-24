"""Schema and ownership contracts for design-configuration creation and removal."""

import inspect
from collections.abc import Iterator, Sequence
from pathlib import Path
from typing import get_type_hints

import pytest
from lxml import etree

from amal.eda.accellera.ipxact.v1685_2022 import tgi
from amal.eda.accellera.ipxact.v1685_2022.tgi import choice, configurable_element
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
    Choices,
    Component,
    ConfigurableElementValue,
    ConfigurableElementValues,
    ConfigurableLibraryRefType,
    DesignConfiguration,
    DesignConfigurationInstantiationType,
    InstanceName,
)

_SCHEMA = etree.XMLSchema(
    etree.parse(str(Path(__file__).resolve().parents[5] / "submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))
)


@pytest.fixture(autouse=True)
def clean_registry() -> Iterator[None]:
    registry.clear()
    yield
    registry.clear()


def _document(*, parsed: bool = False) -> DesignConfiguration:
    root = DesignConfiguration(vendor="v", library="l", name="configuration", version="1")
    if parsed:
        root.view_configuration = [
            DesignConfiguration.ViewConfiguration(
                instance_name=InstanceName(value="cpu"),
                view=DesignConfiguration.ViewConfiguration.View(
                    view_ref="rtl",
                    configurable_element_values=ConfigurableElementValues(
                        configurable_element_value=[
                            ConfigurableElementValue(reference_id="WIDTH", value="2 + 2"),
                            ConfigurableElementValue(reference_id="DEPTH", value="8"),
                        ]
                    ),
                ),
            )
        ]
        root.choices = Choices(
            choice=[
                Choices.Choice(
                    name="widths",
                    enumeration=[Choices.Choice.Enumeration(value="4"), Choices.Choice.Enumeration(value="8")],
                )
            ]
        )
        root = XmlDocument.parser().from_string(XmlDocument.serializer().render(root), DesignConfiguration)
    registry.register(root, ("v", "l", "configuration", "1"))
    return root


def _round_trip(root: DesignConfiguration) -> None:
    xml = XmlDocument.serializer().render(root)
    _SCHEMA.assertValid(etree.fromstring(xml.encode()))
    assert XmlDocument.parser().from_string(xml, DesignConfiguration) == root


def test_annex_signatures_and_exports() -> None:
    expected = {
        "getDesignConfigurationChoiceIDs": ("designConfigurationID",),
        "addDesignConfChoice": ("designConfID", "name", "enumerations"),
        "removeDesignConfChoice": ("choiceID",),
        "addDesignConfigurationViewConfiguration": ("designConfigurationID", "componentInstanceName", "viewName"),
        "removeDesignConfigurationViewConfiguration": ("viewConfigurationID",),
        "removeViewConfigurationConfigurableElementValue": ("configurableElementValueID",),
    }
    for name, parameters in expected.items():
        function = getattr(api, name)
        assert getattr(tgi, name) is function
        assert tuple(inspect.signature(function).parameters) == parameters
        assert "return" in get_type_hints(function)
    assert get_type_hints(api.addDesignConfChoice)["enumerations"] == Sequence[str]


def test_choices_create_required_enumerations_with_owned_handles() -> None:
    root = _document()
    root_id = get_handle(root)
    assert api.getDesignConfigurationChoiceIDs(root_id) == []
    first = api.addDesignConfChoice(root_id, " widths\t", ("2 + 2", "8"))
    second = api.addDesignConfChoice(root_id, "depths", ["16"])
    assert api.getDesignConfigurationChoiceIDs(root_id) == [first, second]
    assert resolve_handle(first).name == "widths"
    values = choice.getChoiceEnumerationIDs(first)
    assert [choice.getEnumerationValueExpression(value) for value in values] == ["2 + 2", "8"]
    assert resolve_handle(get_parent_info(first).parent_handle) is root.choices
    assert api.removeDesignConfChoice(first)
    assert all(resolve_handle(value) is None for value in [first, *values])
    assert api.getDesignConfigurationChoiceIDs(root_id) == [second]
    holder_id = get_handle(root.choices)
    assert api.removeDesignConfChoice(second)
    assert root.choices is None
    assert resolve_handle(holder_id) is None
    _round_trip(root)


@pytest.mark.parametrize(
    "name,values",
    [
        ("", ["4"]),
        ("two words", ["4"]),
        ("1width", ["4"]),
        ("width", []),
        ("width", "4"),
        ("width", [4]),
        ("width", [""]),
        ("width", ["\x00"]),
    ],
)
def test_invalid_choice_creation_is_atomic(name: str, values: object) -> None:
    root = _document()
    with pytest.raises(TgiError) as error:
        api.addDesignConfChoice(get_handle(root), name, values)
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert root.choices is None


def test_duplicate_choice_name_is_rejected_without_changing_holder() -> None:
    root = _document(parsed=True)
    holder = root.choices
    before = XmlDocument.serializer().render(root)
    with pytest.raises(TgiError) as error:
        api.addDesignConfChoice(get_handle(root), " widths\n", ["32"])
    assert error.value.fault_code == TgiFaultCode.ALREADY_EXISTS
    assert root.choices is holder
    assert XmlDocument.serializer().render(root) == before


def test_choice_getter_routes_configuration_instantiation_reference() -> None:
    root = _document(parsed=True)
    source = DesignConfigurationInstantiationType(
        name="source",
        design_configuration_ref=ConfigurableLibraryRefType(vendor="v", library="l", name="configuration", version="1"),
    )
    assert api.getDesignConfigurationChoiceIDs(get_handle(source)) == [get_handle(root.choices.choice[0])]


@pytest.mark.parametrize("parsed", [False, True])
def test_view_creation_reuses_setters_and_removal_invalidates_owned_subtree(parsed: bool) -> None:
    root = _document(parsed=parsed)
    vc_id = api.addDesignConfigurationViewConfiguration(get_handle(root), " gpu\t", "1rtl")
    assert api.getViewConfigurationInstanceName(vc_id) == "gpu"
    assert api.getViewConfigurationViewRefByName(vc_id) == "1rtl"
    vc = resolve_handle(vc_id)
    instance_id, view_id = get_handle(vc.instance_name), api.getViewConfigurationViewID(vc_id)
    _round_trip(root)
    assert api.removeDesignConfigurationViewConfiguration(vc_id)
    assert all(resolve_handle(handle) is None for handle in (vc_id, instance_id, view_id))
    assert not api.removeDesignConfigurationViewConfiguration(vc_id)
    _round_trip(root)


@pytest.mark.parametrize("instance,view", [("1cpu", "rtl"), ("cpu two", "rtl"), ("gpu", "two words"), ("gpu", "")])
def test_invalid_view_creation_is_atomic(instance: str, view: str) -> None:
    root = _document(parsed=True)
    before = XmlDocument.serializer().render(root)
    with pytest.raises(TgiError):
        api.addDesignConfigurationViewConfiguration(get_handle(root), instance, view)
    assert XmlDocument.serializer().render(root) == before


def test_duplicate_view_configuration_is_rejected() -> None:
    root = _document(parsed=True)
    with pytest.raises(TgiError) as error:
        api.addDesignConfigurationViewConfiguration(get_handle(root), " cpu\t", "gate")
    assert error.value.fault_code == TgiFaultCode.ALREADY_EXISTS
    assert len(root.view_configuration) == 1


def test_parsed_removal_discovers_owners_without_collection_getters() -> None:
    root = _document(parsed=True)
    ch = root.choices.choice[0]
    enum_ids = [get_handle(value) for value in ch.enumeration]
    assert api.removeDesignConfChoice(get_handle(ch))
    assert root.choices is None
    assert all(resolve_handle(handle) is None for handle in enum_ids)
    vc = root.view_configuration[0]
    nested_ids = [get_handle(vc.view), get_handle(vc.instance_name), get_handle(vc.view.configurable_element_values)]
    nested_ids.extend(get_handle(value) for value in vc.view.configurable_element_values.configurable_element_value)
    assert api.removeDesignConfigurationViewConfiguration(get_handle(vc))
    assert root.view_configuration == []
    assert all(resolve_handle(handle) is None for handle in nested_ids)
    _round_trip(root)


def test_view_override_removal_reuses_generic_removal_and_prunes_holder() -> None:
    root = _document(parsed=True)
    vc = root.view_configuration[0]
    holder = vc.view.configurable_element_values
    holder_id = get_handle(holder)
    values = [get_handle(value) for value in holder.configurable_element_value]
    assert api.removeViewConfigurationConfigurableElementValue(values[0])
    assert configurable_element.getConfigurableElementValueIDs(get_handle(vc)) == values[1:]
    assert api.removeViewConfigurationConfigurableElementValue(values[1])
    assert vc.view.configurable_element_values is None
    assert resolve_handle(holder_id) is None
    assert not api.removeViewConfigurationConfigurableElementValue(values[1])
    _round_trip(root)


def test_removers_reject_foreign_and_unowned_objects() -> None:
    component = Component(
        vendor="v",
        library="l",
        name="component",
        version="1",
        choices=Choices(choice=[Choices.Choice(name="foreign", enumeration=[Choices.Choice.Enumeration(value="1")])]),
    )
    registry.register(component, ("v", "l", "component", "1"))
    assert not api.removeDesignConfChoice(get_handle(component.choices.choice[0]))
    reference = ConfigurableLibraryRefType(
        vendor="v",
        library="l",
        name="target",
        version="1",
        configurable_element_values=ConfigurableElementValues(
            configurable_element_value=[ConfigurableElementValue(reference_id="WIDTH", value="4")]
        ),
    )
    values = configurable_element.getConfigurableElementValueIDs(get_handle(reference))
    assert not api.removeViewConfigurationConfigurableElementValue(values[0])
    assert not api.removeDesignConfigurationViewConfiguration(
        get_handle(
            DesignConfiguration.ViewConfiguration(
                instance_name=InstanceName(value="unowned"),
                view=DesignConfiguration.ViewConfiguration.View(view_ref="rtl"),
            )
        )
    )
    for function in (
        api.removeDesignConfChoice,
        api.removeDesignConfigurationViewConfiguration,
        api.removeViewConfigurationConfigurableElementValue,
    ):
        assert not function("missing")
        assert not function(get_handle(component))

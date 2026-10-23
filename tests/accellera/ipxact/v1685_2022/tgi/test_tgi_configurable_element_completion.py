"""Configurable element Annex F contracts, definition scope and source mapping."""

import inspect
from types import SimpleNamespace

import pytest
from lxml import etree

from amal.eda.accellera.ipxact.v1685_2022 import tgi
from amal.eda.accellera.ipxact.v1685_2022.tgi import component
from amal.eda.accellera.ipxact.v1685_2022.tgi import configurable_element as api
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import TgiError, get_handle, registry, resolve_handle
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import (
    Component,
    ComponentInstance,
    ComponentInstances,
    ComponentInstantiationType,
    ConfigurableElementValue,
    ConfigurableLibraryRefType,
    Design,
    DesignConfiguration,
    FormatType,
    InstanceName,
    LibraryRefType,
    ModelType,
    ModuleParameterType,
    ModuleParameterTypeResolve,
    Parameter,
    Parameters,
    ParameterTypeResolve,
    TypeParameter,
    TypeParameters,
    Value,
)

_SIGNATURES = {
    "getConfigurableElementIDs": ["unconfiguredElementID"],
    "getConfigurableElementValue": ["configurableElementID"],
    "getConfigurableElementValueExpression": ["configurableElementID"],
    "getConfigurableElementValueIDs": ["configuredElementID"],
    "getConfigurableElementValueReferenceID": ["configurableElementValueID"],
    "getConfigurableElementValueValueExpression": ["configurableElementValueID"],
    "getUnconfiguredID": ["configuredElementID"],
    "addConfigurableElementValue": ["configuredElementID", "referenceID", "expression"],
    "addViewConfigurationConfigurableElementValue": ["viewConfigurationID", "referenceID", "expression"],
    "removeConfigurableElementValue": ["configurableElementValueID"],
    "setConfigurableElementValue": ["configurableElementID", "expression"],
    "setConfigurableElementValueReferenceID": ["configurableElementValueID", "referenceID"],
    "setConfigurableElementValueValue": ["configurableElementValueID", "expression"],
}
_SCHEMA = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))


@pytest.fixture(autouse=True)
def registry_scope():
    registry.clear()
    yield
    registry.clear()


def _root(name="component"):
    return Component(vendor="v", library="l", name=name, version="1")


def _parameter(name="WIDTH", reference="width", expression="8", **kwargs):
    return Parameter(
        name=name, parameter_id=reference, value=Value(value=expression), resolve=ParameterTypeResolve.USER, **kwargs
    )


def _register(root):
    registry.register(root, tuple(getattr(root, field) for field in ("vendor", "library", "name", "version")))
    return get_handle(root)


def _valid(root, model):
    xml = XmlDocument.serializer().render(root)
    _SCHEMA.assertValid(etree.fromstring(xml.encode()))
    assert XmlDocument.parser().from_string(xml, model) == root
    return xml


@pytest.mark.parametrize("index,name", list(enumerate(_SIGNATURES)))
def test_exact_signatures_exports_docs_and_invalid_handles(index, name):
    function = getattr(api, name)
    assert getattr(tgi, name) is function
    assert list(inspect.signature(function).parameters) == _SIGNATURES[name]
    doc = inspect.getdoc(function)
    section = f"F.7.{31 if index < 7 else 32}.{index + 1 if index < 7 else index - 6}"
    assert f"Section: {section}." in doc
    assert "Returns:" in doc
    for parameter in _SIGNATURES[name]:
        assert f"{parameter}:" in doc
    for bad in ("missing", None, [], get_handle(SimpleNamespace())):
        arguments = [bad, *(["source"] * (len(_SIGNATURES[name]) - 1))]
        with pytest.raises(TgiError) as exc:
            function(*arguments)
        assert exc.value.fault_code == "INVALID_ID"


def test_definition_enumeration_filters_resolve_and_preserves_order():
    first = _parameter("FIRST", "first")
    generated = Parameter(
        name="GENERATED", parameter_id="generated", value=Value(value="2"), resolve=ParameterTypeResolve.GENERATED
    )
    immediate = Parameter(name="FIXED", parameter_id="fixed", value=Value(value="3"))
    root = _root()
    root.parameters = Parameters(parameter=[first, immediate, generated])
    assert api.getConfigurableElementIDs(get_handle(root)) == [get_handle(first), get_handle(generated)]
    assert api.getConfigurableElementIDs(get_handle(root.parameters)) == [get_handle(first), get_handle(generated)]
    first.parameter_id = None
    with pytest.raises(TgiError) as exc:
        api.getConfigurableElementIDs(get_handle(root))
    assert exc.value.fault_code == "INVALID_ARGUMENT"
    first.parameter_id = "generated"
    with pytest.raises(TgiError):
        api.getConfigurableElementIDs(get_handle(root))


def test_module_and_type_parameter_definitions_are_configurable():
    for parameter, holder in (
        (
            ModuleParameterType(
                name="WIDTH", parameter_id="width", value=Value(value="8"), resolve=ModuleParameterTypeResolve.USER
            ),
            ComponentInstantiationType.ModuleParameters(),
        ),
        (
            TypeParameter(
                name="TYPE",
                parameter_id="kind",
                value=Value(value="typename"),
                resolve=ModuleParameterTypeResolve.GENERATED,
            ),
            TypeParameters(),
        ),
    ):
        field = (
            "module_parameter" if isinstance(holder, ComponentInstantiationType.ModuleParameters) else "type_parameter"
        )
        setattr(holder, field, (parameter,))
        assert api.getConfigurableElementIDs(get_handle(holder)) == [get_handle(parameter)]
        assert api.getConfigurableElementValueExpression(get_handle(parameter)) == parameter.value.value
        assert api.setConfigurableElementValue(get_handle(parameter), "replacement")
        assert parameter.value.value == "replacement"


def test_default_edit_preserves_value_metadata_and_is_atomic():
    parameter = _parameter(type_value=FormatType.BYTE, minimum="0", maximum="20", expression="2 * 4")
    handle = get_handle(parameter)
    value_id = get_handle(parameter.value)
    parameter.value.other_attributes["{urn:test}marker"] = "retained"
    assert api.getConfigurableElementValue(handle) == "8"
    assert api.getConfigurableElementValueExpression(handle) == "2 * 4"
    assert api.setConfigurableElementValue(handle, "16")
    assert resolve_handle(value_id) is parameter.value
    assert parameter.value.other_attributes["{urn:test}marker"] == "retained"
    for expression in (None, "21", "8'bxxxx0000", "1 +", "1.5"):
        with pytest.raises(TgiError):
            api.setConfigurableElementValue(handle, expression)
        assert parameter.value.value == "16"
    parameter.resolve = ParameterTypeResolve.IMMEDIATE
    with pytest.raises(TgiError):
        api.setConfigurableElementValue(handle, "1")
    override = ConfigurableElementValue(reference_id="width", value="2")
    with pytest.raises(TgiError):
        api.getConfigurableElementValue(get_handle(override))
    with pytest.raises(TgiError):
        api.setConfigurableElementValue(get_handle(override), "3")
    assert override.value == "2"


def test_known_component_reference_filters_instantiation_parameters_and_ranges():
    root = _root()
    parameter = _parameter(type_value=FormatType.BYTE, maximum="10")
    root.parameters = Parameters(parameter=[parameter])
    root_id = _register(root)
    instantiation_id = component.addComponentComponentInstantiation(root_id, "rtl")
    nested = ModuleParameterType(
        name="INNER", parameter_id="inner", value=Value(value="2"), resolve=ModuleParameterTypeResolve.USER
    )
    resolve_handle(instantiation_id).module_parameters = ComponentInstantiationType.ModuleParameters(
        module_parameter=[nested]
    )
    reference = ConfigurableLibraryRefType(vendor="v", library="l", name="component", version="1")
    instance = ComponentInstance(instance_name=InstanceName(value="u0"), component_ref=reference)
    instance_id = get_handle(instance)
    override_id = api.addConfigurableElementValue(instance_id, "width", "9")
    assert api.getUnconfiguredID(instance_id) == root_id
    assert api.getUnconfiguredID(override_id) == get_handle(parameter)
    before = _valid(root, Component)
    for reference_id, expression in (("inner", "2"), ("absent", "2"), ("width", "11")):
        operation = api.setConfigurableElementValueValue if reference_id == "width" else api.addConfigurableElementValue
        args = (override_id, expression) if reference_id == "width" else (instance_id, reference_id, expression)
        with pytest.raises(TgiError):
            operation(*args)
    assert api.getConfigurableElementValueValueExpression(override_id) == "9"
    assert parameter.value.value == "8"
    assert _valid(root, Component) == before


def test_configured_view_source_and_override_scope_follow_selected_instantiation():
    root = _root()
    root_id = _register(root)
    instantiation_id = component.addComponentComponentInstantiation(root_id, "rtl")
    parameter = _parameter("VIEW_WIDTH", "view_width")
    instantiation = resolve_handle(instantiation_id)
    instantiation.parameters = Parameters(parameter=[parameter])
    selected = ModelType.Views.View(name="rtl_view", component_instantiation_ref="rtl")
    root.model.views = ModelType.Views(view=[selected])
    design = Design(
        vendor="v",
        library="l",
        name="design",
        version="1",
        component_instances=ComponentInstances(
            component_instance=[
                ComponentInstance(
                    instance_name=InstanceName(value="u0"),
                    component_ref=ConfigurableLibraryRefType(vendor="v", library="l", name="component", version="1"),
                )
            ]
        ),
    )
    _register(design)
    configured_view = DesignConfiguration.ViewConfiguration.View(view_ref="rtl_view")
    selection = DesignConfiguration.ViewConfiguration(instance_name=InstanceName(value="u0"), view=configured_view)
    configuration = DesignConfiguration(
        vendor="v",
        library="l",
        name="config",
        version="1",
        design_ref=LibraryRefType(vendor="v", library="l", name="design", version="1"),
        view_configuration=[selection],
    )
    _register(configuration)
    handle = api.addViewConfigurationConfigurableElementValue(get_handle(selection), "view_width", "16")
    assert api.getUnconfiguredID(get_handle(selection)) == get_handle(selected)
    assert api.getUnconfiguredID(handle) == get_handle(parameter)
    assert api.getConfigurableElementValueIDs(get_handle(selection)) == [handle]
    _valid(root, Component)
    _valid(design, Design)
    _valid(configuration, DesignConfiguration)
    with pytest.raises(TgiError):
        api.addViewConfigurationConfigurableElementValue(get_handle(selection), "unrelated", "2")
    assert api.removeConfigurableElementValue(handle)
    assert configured_view.configurable_element_values is None
    assert configured_view.view_ref == "rtl_view"
    _valid(configuration, DesignConfiguration)


def test_unconfigured_lookup_missing_references_never_returns_identity():
    reference = ConfigurableLibraryRefType(vendor="v", library="l", name="missing", version="1")
    handle = get_handle(reference)
    assert api.getUnconfiguredID(handle) is None
    assert api.getUnconfiguredID(get_handle(ConfigurableElementValue(reference_id="unknown", value="1"))) is None
    reference.name = ""
    with pytest.raises(TgiError):
        api.getUnconfiguredID(handle)
    with pytest.raises(TgiError):
        api.getUnconfiguredID(get_handle(_root()))


@pytest.mark.parametrize("numeric", [False, True])
def test_known_override_choices_are_checked_before_mutation(numeric):
    from org.accellera.ipxact.v1685_2022 import Choices

    root = _root()
    parameter = _parameter(
        expression="1" if numeric else "red", type_value=FormatType.INT if numeric else FormatType.STRING
    )
    parameter.choice_ref = "allowed"
    root.parameters = Parameters(parameter=[parameter])
    root.choices = Choices(
        choice=[
            Choices.Choice(
                name="allowed",
                enumeration=[
                    Choices.Choice.Enumeration(value="1" if numeric else '"red"'),
                    Choices.Choice.Enumeration(value="4" if numeric else '"blue"'),
                ],
            )
        ]
    )
    _register(root)
    instance = ComponentInstance(
        instance_name=InstanceName(value="u0"),
        component_ref=ConfigurableLibraryRefType(vendor="v", library="l", name="component", version="1"),
    )
    handle = api.addConfigurableElementValue(get_handle(instance), "width", "2 + 2" if numeric else '"blue"')
    before = api.getConfigurableElementValueValueExpression(handle)
    with pytest.raises(TgiError):
        api.setConfigurableElementValueValue(handle, "3" if numeric else '"green"')
    assert api.getConfigurableElementValueValueExpression(handle) == before
    assert parameter.value.value == ("1" if numeric else "red")
    _valid(root, Component)


@pytest.mark.parametrize(
    "kind",
    [
        "AbstractionDefinition",
        "BusDefinition",
        "Component",
        "Abstractor",
        "Design",
        "DesignConfiguration",
        "TypeDefinitions",
        "GeneratorChain",
    ],
)
def test_document_reference_handles_map_to_registered_source_documents(kind):
    from org.accellera.ipxact import v1685_2022 as model

    kwargs = {"vendor": "v", "library": "l", "name": kind, "version": "1"}
    if kind == "BusDefinition":
        kwargs.update(direct_connection=True, is_addressable=False)
    elif kind == "AbstractionDefinition":
        kwargs.update(
            bus_type=LibraryRefType(vendor="v", library="l", name="bus", version="1"),
            ports=model.AbstractionDefinition.Ports(),
        )
    elif kind == "Abstractor":
        kwargs.update(
            abstractor_mode=model.AbstractorType.AbstractorMode(value=model.AbstractorModeType.DIRECT),
            bus_type=LibraryRefType(vendor="v", library="l", name="bus", version="1"),
            abstractor_interfaces=model.AbstractorType.AbstractorInterfaces(),
        )
    root = getattr(model, kind)(**kwargs)
    root_id = _register(root)
    reference = ConfigurableLibraryRefType(vendor="v", library="l", name=kind, version="1")
    reference_id = get_handle(reference)
    assert api.getUnconfiguredID(reference_id) == root_id
    assert reference_id != root_id
    assert api.getConfigurableElementValueIDs(reference_id) == []
    assert registry.get_vlnv(reference_id) is None


def test_component_reference_cannot_resolve_to_wrong_registered_document_type():
    design = Design(vendor="v", library="l", name="wrong_type", version="1")
    _register(design)
    instance = ComponentInstance(
        instance_name=InstanceName(value="u0"),
        component_ref=ConfigurableLibraryRefType(vendor="v", library="l", name="wrong_type", version="1"),
    )
    with pytest.raises(TgiError) as exc:
        api.getUnconfiguredID(get_handle(instance))
    assert exc.value.fault_code == "INVALID_ARGUMENT"
    assert instance.component_ref.configurable_element_values is None


def test_unicode_reference_names_and_invalid_text_are_atomic():
    reference = ConfigurableLibraryRefType(vendor="v", library="l", name="offline", version="1")
    reference_id = get_handle(reference)
    for ref, expression in ((None, "1"), (1, "1"), ("valid", None), ("valid", False), ("valid", "bad\ud800")):
        with pytest.raises(TgiError):
            api.addConfigurableElementValue(reference_id, ref, expression)
        assert reference.configurable_element_values is None
    handle = api.addConfigurableElementValue(reference_id, " α:width \t", "")
    assert api.getConfigurableElementValueReferenceID(handle) == "α:width"
    assert api.getConfigurableElementValueValueExpression(handle) == ""
    for expression in (None, True, "bad\x00"):
        with pytest.raises(TgiError):
            api.setConfigurableElementValueValue(handle, expression)
        assert api.getConfigurableElementValueValueExpression(handle) == ""


def test_lookup_rejects_other_schema_version_with_same_vlnv():
    from org.accellera.ipxact.v1685_2014 import Component as Component2014

    root = Component2014(vendor="v", library="l", name="old", version="1")
    _register(root)
    reference = ConfigurableLibraryRefType(vendor="v", library="l", name="old", version="1")
    with pytest.raises(TgiError) as exc:
        api.getUnconfiguredID(get_handle(reference))
    assert exc.value.fault_code == "INVALID_ID"


@pytest.mark.parametrize("reference_kind", ["absent", "missing", "design"])
def test_known_selected_view_without_supported_scope_rejects_add_and_set(reference_kind):
    from org.accellera.ipxact.v1685_2022 import ConfigurableElementValues

    root = _root()
    _register(root)
    root.model = ModelType(
        views=ModelType.Views(view=[ModelType.Views.View(name="selected")]), instantiations=ModelType.Instantiations()
    )
    selected = root.model.views.view[0]
    if reference_kind == "missing":
        selected.component_instantiation_ref = "missing"
    elif reference_kind == "design":
        selected.design_instantiation_ref = "hierarchy"
    design = Design(
        vendor="v",
        library="l",
        name="design",
        version="1",
        component_instances=ComponentInstances(
            component_instance=[
                ComponentInstance(
                    instance_name=InstanceName(value="u0"),
                    component_ref=ConfigurableLibraryRefType(vendor="v", library="l", name="component", version="1"),
                )
            ]
        ),
    )
    _register(design)
    override = ConfigurableElementValue(reference_id="width", value="8")
    view = DesignConfiguration.ViewConfiguration.View(
        view_ref="selected",
        configurable_element_values=ConfigurableElementValues(configurable_element_value=[override]),
    )
    selection = DesignConfiguration.ViewConfiguration(instance_name=InstanceName(value="u0"), view=view)
    configuration = DesignConfiguration(
        vendor="v",
        library="l",
        name="config",
        version="1",
        design_ref=LibraryRefType(vendor="v", library="l", name="design", version="1"),
        view_configuration=[selection],
    )
    _register(configuration)
    for operation in (
        lambda: api.addViewConfigurationConfigurableElementValue(get_handle(selection), "other", "16"),
        lambda: api.setConfigurableElementValueValue(get_handle(override), "16"),
        lambda: api.setConfigurableElementValueReferenceID(get_handle(override), "other"),
    ):
        with pytest.raises(TgiError) as exc:
            operation()
        assert exc.value.fault_code == "INVALID_ARGUMENT"
        assert view.configurable_element_values.configurable_element_value == [override]
        assert override.reference_id == "width"
        assert override.value == "8"


def test_malformed_module_default_wrapper_faults_before_mutation():
    parameter = ModuleParameterType(
        name="P", parameter_id="p", resolve=ModuleParameterTypeResolve.USER, value=Value(value="8")
    )
    parameter.value = "malformed"
    for operation in (api.getConfigurableElementValue, api.getConfigurableElementValueExpression):
        with pytest.raises(TgiError):
            operation(get_handle(parameter))
    with pytest.raises(TgiError):
        api.setConfigurableElementValue(get_handle(parameter), "16")
    assert parameter.value == "malformed"

"""Module and type parameter edits retain generated wrappers and XML ownership."""

import pytest
from lxml import etree

from amal.eda.accellera.ipxact.v1685_2022.tgi import component
from amal.eda.accellera.ipxact.v1685_2022.tgi import module_parameter as api
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import (
    TgiError,
    get_handle,
    get_parent_info,
    registry,
    resolve_handle,
)
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import Component, FormatType, ModuleParameterType, TypeParameter, Value
from org.accellera.ipxact.v1685_2022.struct_port_type_defs import StructPortTypeDefs
from org.accellera.ipxact.v1685_2022.trans_type_def import TransTypeDef
from org.accellera.ipxact.v1685_2022.type_parameters import TypeParameters

_SCHEMA = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))


@pytest.fixture(autouse=True)
def top_level_registry_only(monkeypatch):
    registry.clear()
    register = registry.register

    def register_document(root, *args, **kwargs):
        assert isinstance(root, Component)
        return register(root, *args, **kwargs)

    monkeypatch.setattr(registry, "register", register_document)
    yield
    registry.clear()


def _root():
    return Component(vendor="v", library="l", name="component", version="1")


def _valid(root):
    xml = XmlDocument.serializer().render(root)
    _SCHEMA.assertValid(etree.fromstring(xml.encode()))
    assert XmlDocument.parser().from_string(xml, Component) == root
    return xml


def test_generated_module_parameter_container_and_wrapper_metadata_survive_edits():
    root = _root()
    instantiation = component.addComponentComponentInstantiation(get_handle(root), "rtl")
    parameter = api.addModuleParameter(instantiation, "WIDTH", "8")
    model = resolve_handle(parameter)
    value_id = get_handle(model.value)
    model.value.other_attributes["{urn:test}marker"] = "source_value"
    model.parameter_id = "width"
    api.setModuleParameterValue(parameter, "16")
    assert get_handle(model.value) == value_id
    assert model.value.other_attributes["{urn:test}marker"] == "source_value"
    assert model.parameter_id == "width"
    _valid(root)
    assert api.getModuleParameterIDs(instantiation) == [parameter]
    before = _valid(root)
    with pytest.raises(TgiError):
        api.addModuleParameter(instantiation, "WIDTH", "32")
    with pytest.raises(TgiError):
        api.setModuleParameterValue(parameter, None)
    assert _valid(root) == before
    holder_id = get_handle(resolve_handle(instantiation).module_parameters)
    assert api.removeModuleParameter(parameter)
    assert resolve_handle(instantiation).module_parameters is None
    assert resolve_handle(value_id) is None
    assert resolve_handle(holder_id) is None
    _valid(root)


def test_type_parameter_parents_create_typed_holders_and_preserve_source_expressions():
    parents = [
        TransTypeDef(),
        StructPortTypeDefs.StructPortTypeDef(type_name=StructPortTypeDefs.StructPortTypeDef.TypeName(value="TYPE")),
        TypeParameters(),
    ]
    for parent in parents:
        parameter = api.addModuleParameter(get_handle(parent), "ARGUMENT", "some_type")
        child = resolve_handle(parameter)
        assert isinstance(child, TypeParameter)
        assert api.getModuleParameterIDs(get_handle(parent)) == [parameter]
        assert api.getModuleParameterValueExpression(parameter) == "some_type"
        assert api.getModuleParameterValue(parameter) == "some_type"
        assert get_parent_info(parameter) is not None
        assert api.removeModuleParameter(parameter)
        assert resolve_handle(parameter) is None


def test_parsed_direct_parameter_removal_recovers_registered_component_owner():
    root = _root()
    instantiation = component.addComponentComponentInstantiation(get_handle(root), "rtl")
    api.addModuleParameter(instantiation, "WIDTH", "8")
    parsed = XmlDocument.parser().from_string(_valid(root), Component)
    registry.register(parsed, ["v", "l", "component", "1"])
    model_instances = parsed.model.instantiations
    instances = model_instances.component_instantiation_or_design_instantiation_or_design_configuration_instantiation
    instance = instances[0]
    parameter = instance.module_parameters.module_parameter[0]
    parameter_id, value_id, holder_id = (
        get_handle(parameter),
        get_handle(parameter.value),
        get_handle(instance.module_parameters),
    )
    assert api.removeModuleParameter(parameter_id)
    assert instance.module_parameters is None
    assert all(resolve_handle(handle) is None for handle in [parameter_id, value_id, holder_id])
    _valid(parsed)


def test_numeric_getter_evaluates_constants_without_changing_source_xml():
    parameter = ModuleParameterType(name="WIDTH", value=Value(value="8 * 4"), type_value=FormatType.INT)
    handle = get_handle(parameter)
    assert api.getModuleParameterValue(handle) == "32"
    assert api.getModuleParameterValueExpression(handle) == "8 * 4"
    assert parameter.value.value == "8 * 4"
    api.setModuleParameterValue(handle, "UNKNOWN_WIDTH + 1")
    assert api.getModuleParameterValueExpression(handle) == "UNKNOWN_WIDTH + 1"
    with pytest.raises(TgiError):
        api.getModuleParameterValue(handle)


@pytest.mark.parametrize("expression", ["128", "-129", "1.5", "1 +", '"text"', "4'bxxxx", ""])
def test_numeric_value_bounds_reject_invalid_updates_atomically(expression):
    parameter = ModuleParameterType(name="SMALL", value=Value(value="12"), type_value=FormatType.BYTE)
    handle = get_handle(parameter)
    with pytest.raises(TgiError):
        api.setModuleParameterValue(handle, expression)
    assert parameter.value.value == "12"


def test_remover_rejects_unrelated_owned_values():
    root = _root()
    instantiation = component.addComponentComponentInstantiation(get_handle(root), "rtl")
    parameter = api.addModuleParameter(instantiation, "WIDTH", "8")
    value_id = get_handle(resolve_handle(parameter).value)
    with pytest.raises(TgiError):
        api.removeModuleParameter(value_id)
    assert resolve_handle(value_id) is not None


def test_type_parameter_holder_roundtrip_in_structured_component():
    root = _root()
    port_id = component.addComponentStructuredStructPort(get_handle(root), "port", "TYPE", "in")
    port = resolve_handle(port_id)
    definition = port.wire_or_transactional_or_structured.struct_port_type_defs.struct_port_type_def[0]
    parameter_id = api.addModuleParameter(get_handle(definition), "WIDTH", "16")
    assert isinstance(resolve_handle(parameter_id), TypeParameter)
    _valid(root)
    api.setModuleParameterValue(parameter_id, "32")
    _valid(root)
    holder_id = get_handle(definition.type_parameters)
    assert api.removeModuleParameter(parameter_id)
    assert definition.type_parameters is None
    assert resolve_handle(holder_id) is None
    _valid(root)


@pytest.mark.parametrize("handle", ["missing", None, 123])
def test_invalid_parameter_and_container_handles_raise_faults(handle):
    for operation in [
        lambda: api.getModuleParameterIDs(handle),
        lambda: api.getModuleParameterValue(handle),
        lambda: api.getModuleParameterValueExpression(handle),
        lambda: api.addModuleParameter(handle, "NAME", "1"),
        lambda: api.setModuleParameterValue(handle, "1"),
    ]:
        with pytest.raises(TgiError):
            operation()

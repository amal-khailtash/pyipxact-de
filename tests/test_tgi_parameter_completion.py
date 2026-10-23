"""Parameter Annex F signatures, scoped references and typed container contracts."""

import inspect
from types import SimpleNamespace

import pytest

from amal.eda.accellera.ipxact.v1685_2022 import tgi
from amal.eda.accellera.ipxact.v1685_2022.tgi import parameter as api
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import TgiError, get_handle, registry, resolve_handle
from org.accellera.ipxact.v1685_2022 import (
    Component,
    ComponentInstantiationType,
    ConfigurableElementValue,
    File,
    FileSet,
    FileSetRef,
    FileSets,
    IpxactUri,
    ModelType,
    ModuleParameterType,
    Parameter,
    Parameters,
    Value,
)

_SIGNATURES = {
    "getModuleParameterDataTypeDefinitionRefByID": ["moduleParameterTypeID"],
    "getParameterChoiceRefByName": ["parameterBaseTypeID"],
    "getParameterIDFromReferenceID": ["parametizedID", "referenceID"],
    "getParameterIDs": ["parameterContainerElementID"],
    "getParameterNameFromReferenceID": ["parametizedID", "referenceID"],
    "getParameterValue": ["parameterID"],
    "getParameterValueExpression": ["parameterID"],
    "getParameterValueID": ["parameterID"],
    "addParameter": ["parameterContainerElementID", "name", "expression"],
    "removeConfigGroupsAttribute": ["parameterID"],
    "removeParameter": ["parameterID"],
    "setParameterValue": ["parameterID", "expression"],
}


@pytest.fixture(autouse=True)
def clear_registry():
    registry.clear()
    yield
    registry.clear()


def _root(name="component"):
    return Component(vendor="v", library="l", name=name, version="1")


@pytest.mark.parametrize("index,name", list(enumerate(_SIGNATURES)))
def test_signatures_exports_static_docs_and_invalid_ids(index, name):
    function = getattr(api, name)
    assert getattr(tgi, name) is function
    assert list(inspect.signature(function).parameters) == _SIGNATURES[name]
    assert all(
        parameter.default is inspect.Parameter.empty for parameter in inspect.signature(function).parameters.values()
    )
    doc = inspect.getdoc(function)
    for parameter in _SIGNATURES[name]:
        assert f"{parameter}:" in doc
    section = f"F.7.{65 if index < 8 else 66}.{index + 1 if index < 8 else index - 7}"
    assert f"Section: {section}." in doc
    assert "Returns:" in doc
    for bad in ("missing", None, [], get_handle(SimpleNamespace())):
        arguments = [bad, *(["missing"] * (len(_SIGNATURES[name]) - 1))]
        with pytest.raises(TgiError) as exc:
            function(*arguments)
        assert exc.value.fault_code == "INVALID_ID"


def test_holder_and_owners_use_direct_ordered_parameters_and_no_synthetic_fields():
    root = _root()
    handle = get_handle(root)
    assert api.getParameterIDs(handle) == []
    first = api.addParameter(handle, " First Name ", "")
    second = api.addParameter(handle, "SECOND", "source + expression")
    assert api.getParameterIDs(handle) == [first, second]
    assert api.getParameterIDs(get_handle(root.parameters)) == [first, second]
    assert resolve_handle(first).name == " First Name "
    assert api.getParameterValue(first) == ""
    assert api.getParameterValueExpression(second) == "source + expression"
    unsupported = SimpleNamespace(parameters=None)
    with pytest.raises(TgiError):
        api.addParameter(get_handle(unsupported), "BAD", "1")
    assert vars(unsupported) == {"parameters": None}
    malformed = _root()
    malformed.parameters = SimpleNamespace(parameter=[])
    with pytest.raises(TgiError) as exc:
        api.getParameterIDs(get_handle(malformed))
    assert exc.value.fault_code == "INVALID_ARGUMENT"


def test_choice_reference_is_declared_name_for_parameter_base_types():
    for parameter in (
        Parameter(name="P", value=Value(value="1")),
        ModuleParameterType(name="M", value=Value(value="1")),
    ):
        handle = get_handle(parameter)
        assert api.getParameterChoiceRefByName(handle) is None
        parameter.choice_ref = "OPTIONS"
        assert api.getParameterChoiceRefByName(handle) == "OPTIONS"
        parameter.config_groups = ("g1", "g2")
        assert api.removeConfigGroupsAttribute(handle)
        assert parameter.config_groups == []
        assert api.removeConfigGroupsAttribute(handle) is False


def test_reference_ids_resolve_parameter_id_within_supplied_scope():
    root = _root()
    other = _root("other")
    p = Parameter(name="WIDTH", value=Value(value="8"), parameter_id="width", id="xml_id")
    duplicate_elsewhere = Parameter(name="OTHER", value=Value(value="9"), parameter_id="width")
    root.parameters = Parameters(parameter=[p])
    other.parameters = Parameters(parameter=[duplicate_elsewhere])
    registry.register(root, ("v", "l", "component", "1"))
    registry.register(other, ("v", "l", "other", "1"))
    reference = ConfigurableElementValue(reference_id="width", value="16")
    reference_id = get_handle(reference)
    assert api.getParameterIDFromReferenceID(get_handle(root), reference_id) == get_handle(p)
    assert api.getParameterNameFromReferenceID(get_handle(root), reference_id) == "WIDTH"
    assert api.getParameterNameFromReferenceID(get_handle(other), reference_id) == "OTHER"
    assert api.getParameterIDFromReferenceID(get_handle(root.parameters), get_handle("width")) == get_handle(p)
    reference.reference_id = "xml_id"
    assert api.getParameterIDFromReferenceID(get_handle(root), reference_id) is None
    reference.reference_id = "absent"
    assert api.getParameterNameFromReferenceID(get_handle(root), reference_id) is None
    with pytest.raises(TgiError):
        api.getParameterIDFromReferenceID(get_handle(root), get_handle(p))
    reference.reference_id = "width"
    root.parameters.parameter.append(Parameter(name="ambiguous", value=Value(value="1"), parameter_id="width"))
    with pytest.raises(TgiError) as exc:
        api.getParameterIDFromReferenceID(get_handle(root), reference_id)
    assert exc.value.fault_code == "INVALID_ARGUMENT"


def test_module_data_type_file_resolves_only_own_instantiation_file_sets():
    root = _root()
    target = File(name=IpxactUri(value="defs/types.sv"))
    unrelated = File(name=IpxactUri(value="defs/types.sv"))
    root.file_sets = FileSets(
        file_set=[FileSet(name="selected", file=[target]), FileSet(name="other", file=[unrelated])]
    )
    parameter = ModuleParameterType(name="T", value=Value(value="kind"), data_type_definition="defs/types.sv")
    instantiation = ComponentInstantiationType(
        name="rtl",
        file_set_ref=[FileSetRef(local_name="selected")],
        module_parameters=ComponentInstantiationType.ModuleParameters(module_parameter=[parameter]),
    )
    root.model = ModelType(
        instantiations=ModelType.Instantiations(
            component_instantiation_or_design_instantiation_or_design_configuration_instantiation=[instantiation]
        )
    )
    registry.register(root, ("v", "l", "component", "1"))
    handle = get_handle(parameter)
    assert api.getModuleParameterDataTypeDefinitionRefByID(handle) == get_handle(target)
    parameter.data_type_definition = "missing"
    assert api.getModuleParameterDataTypeDefinitionRefByID(handle) is None
    parameter.data_type_definition = None
    assert api.getModuleParameterDataTypeDefinitionRefByID(handle) is None
    parameter.data_type_definition = "defs/types.sv"
    instantiation.file_set_ref.append(FileSetRef(local_name="other"))
    with pytest.raises(TgiError) as exc:
        api.getModuleParameterDataTypeDefinitionRefByID(handle)
    assert exc.value.fault_code == "INVALID_ARGUMENT"


def test_malformed_required_values_and_collections_fault_without_edits():
    holder = Parameters(parameter=[Parameter(name="P", value=Value(value="1"))])
    holder.parameter = [object()]
    before = list(holder.parameter)
    for operation in (
        lambda: api.getParameterIDs(get_handle(holder)),
        lambda: api.addParameter(get_handle(holder), "P", "1"),
    ):
        with pytest.raises(TgiError) as exc:
            operation()
        assert exc.value.fault_code == "INVALID_ARGUMENT"
        assert holder.parameter == before
    parameter = Parameter(name="P", value=Value(value="1"))
    handle = get_handle(parameter)
    parameter.value = "malformed"
    for operation in (api.getParameterValue, api.getParameterValueID, api.getParameterValueExpression):
        with pytest.raises(TgiError):
            operation(handle)
    with pytest.raises(TgiError):
        api.setParameterValue(handle, "2")
    assert parameter.value == "malformed"
    assert api.removeParameter(handle) is False


def test_reference_scope_supports_module_parameters_and_rejects_wrong_scope():
    parameter = ModuleParameterType(name="WIDTH", value=Value(value="8"), parameter_id="width")
    holder = ComponentInstantiationType.ModuleParameters(module_parameter=[parameter])
    owner = ComponentInstantiationType(name="rtl", module_parameters=holder)
    reference = ConfigurableElementValue(reference_id="width", value="16")
    for scope in (owner, holder):
        assert api.getParameterIDFromReferenceID(get_handle(scope), get_handle(reference)) == get_handle(parameter)
        assert api.getParameterNameFromReferenceID(get_handle(scope), get_handle(reference)) == "WIDTH"
    with pytest.raises(TgiError) as exc:
        api.getParameterIDFromReferenceID(get_handle(Value(value="wrong_scope")), get_handle(reference))
    assert exc.value.fault_code == "INVALID_ID"


def test_add_argument_validation_precedes_optional_holder_creation():
    root = _root()
    for name, expression in ((None, "1"), ("", "1"), (" \t", "1"), ("P", None), ("P", 3), ("P", "bad\x00")):
        with pytest.raises(TgiError) as exc:
            api.addParameter(get_handle(root), name, expression)
        assert exc.value.fault_code == "INVALID_ARGUMENT"
        assert root.parameters is None


def test_reference_resolution_does_not_search_nested_parameter_containers():
    from amal.eda.accellera.ipxact.v1685_2022.tgi import component

    root = _root()
    root_id = get_handle(root)
    api.addParameter(root_id, "ROOT", "1")
    nested_id = component.addComponentComponentInstantiation(root_id, "rtl")
    parameter_id = api.addParameter(nested_id, "NESTED", "2")
    resolve_handle(parameter_id).parameter_id = "nested"
    reference_id = get_handle(ConfigurableElementValue(reference_id="nested", value="3"))
    assert api.getParameterIDFromReferenceID(root_id, reference_id) is None
    assert api.getParameterNameFromReferenceID(root_id, reference_id) is None
    assert api.getParameterIDFromReferenceID(nested_id, reference_id) == parameter_id
    assert api.getParameterNameFromReferenceID(nested_id, reference_id) == "NESTED"

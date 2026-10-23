"""Focused BASE and EXTENDED module parameter behavior from TGI Annex F."""

from types import SimpleNamespace

import pytest

from amal.eda.accellera.ipxact.v1685_2022.tgi import module_parameter as api
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import TgiError, get_handle, resolve_handle
from org.accellera.ipxact.v1685_2022 import (
    ComponentInstantiationType,
    FormatType,
    ModuleParameterType,
    TypeParameter,
    Value,
)
from org.accellera.ipxact.v1685_2022.struct_port_type_defs import StructPortTypeDefs
from org.accellera.ipxact.v1685_2022.trans_type_def import TransTypeDef
from org.accellera.ipxact.v1685_2022.type_parameters import ServiceTypeDef, TypeParameters


def test_generated_module_and_type_parameter_holders_are_supported():
    module_holder = ComponentInstantiationType.ModuleParameters(
        module_parameter=[ModuleParameterType(name="WIDTH", value=Value(value="8"))]
    )
    type_holder = TypeParameters(type_parameter=[TypeParameter(name="T", value=Value(value="kind_t"))])
    struct_holder_type = StructPortTypeDefs.StructPortTypeDef.TypeParameters(
        type_parameter=[TypeParameter(name="S", value=Value(value="scalar_t"))]
    )

    for holder, parameter_type, source in (
        (module_holder, ModuleParameterType, "8"),
        (type_holder, TypeParameter, "kind_t"),
        (struct_holder_type, TypeParameter, "scalar_t"),
    ):
        ids = api.getModuleParameterIDs(get_handle(holder))
        assert len(ids) == 1
        parameter = resolve_handle(ids[0])
        assert isinstance(parameter, parameter_type)
        assert api.getModuleParameterValue(ids[0]) == source
        assert api.getModuleParameterValueExpression(ids[0]) == source


@pytest.mark.parametrize(
    "owner",
    [
        ComponentInstantiationType(name="rtl"),
        TransTypeDef(),
        ServiceTypeDef(type_name=ServiceTypeDef.TypeName(value="service_t")),
        StructPortTypeDefs.StructPortTypeDef(type_name=StructPortTypeDefs.StructPortTypeDef.TypeName(value="struct_t")),
    ],
)
def test_add_creates_the_schema_defined_parameter_and_holder(owner):
    parameter_id = api.addModuleParameter(get_handle(owner), "ARGUMENT", "source_t")
    parameter = resolve_handle(parameter_id)
    expected_type = ModuleParameterType if isinstance(owner, ComponentInstantiationType) else TypeParameter
    assert isinstance(parameter, expected_type)
    assert api.getModuleParameterIDs(get_handle(owner)) == [parameter_id]
    assert api.getModuleParameterValue(parameter_id) == "source_t"
    assert api.removeModuleParameter(parameter_id)
    assert resolve_handle(parameter_id) is None
    assert not api.removeModuleParameter(parameter_id)


def test_numeric_values_are_evaluated_while_source_text_is_retained():
    parameter = ModuleParameterType(name="WIDTH", value=Value(value="3 * 8"), type_value=FormatType.INT)
    parameter_id = get_handle(parameter)

    assert api.getModuleParameterValue(parameter_id) == "24"
    assert api.getModuleParameterValueExpression(parameter_id) == "3 * 8"
    assert api.setModuleParameterValue(parameter_id, "UNRESOLVED_WIDTH + 1")
    assert api.getModuleParameterValueExpression(parameter_id) == "UNRESOLVED_WIDTH + 1"
    with pytest.raises(TgiError):
        api.getModuleParameterValue(parameter_id)


def test_invalid_container_types_and_duplicate_names_do_not_mutate_models():
    with pytest.raises(TgiError):
        api.getModuleParameterIDs(get_handle(SimpleNamespace(module_parameter=[])))

    instantiation = ComponentInstantiationType(name="rtl")
    instantiation_id = get_handle(instantiation)
    parameter_id = api.addModuleParameter(instantiation_id, "WIDTH", "8")
    holder = instantiation.module_parameters
    with pytest.raises(TgiError):
        api.addModuleParameter(instantiation_id, "WIDTH", "16")
    assert instantiation.module_parameters is holder
    assert api.getModuleParameterIDs(instantiation_id) == [parameter_id]

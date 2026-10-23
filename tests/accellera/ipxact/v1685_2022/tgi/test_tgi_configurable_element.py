"""Configurable definitions and instance overrides are distinct IP-XACT objects."""

from amal.eda.accellera.ipxact.v1685_2022.tgi import configurable_element as api
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import get_handle, registry
from org.accellera.ipxact.v1685_2022 import (
    Component,
    ConfigurableLibraryRefType,
    Parameter,
    Parameters,
    ParameterTypeResolve,
    Value,
)


def test_configurable_definition_defaults_and_instance_override_traversal():
    parameter = Parameter(
        name="WIDTH", value=Value(value="10"), parameter_id="width", resolve=ParameterTypeResolve.USER
    )
    root = Component(
        vendor="v", library="l", name="component", version="1", parameters=Parameters(parameter=[parameter])
    )
    reference = ConfigurableLibraryRefType(vendor="v", library="l", name="component", version="1")
    root_id = get_handle(root)
    reference_id = get_handle(reference)
    registry.clear()
    try:
        registry.register(root, ("v", "l", "component", "1"))
        definitions = api.getConfigurableElementIDs(root_id)
        assert definitions == [get_handle(parameter)]
        assert api.getConfigurableElementValue(definitions[0]) == "10"
        assert api.getConfigurableElementValueExpression(definitions[0]) == "10"
        override_id = api.addConfigurableElementValue(reference_id, "width", "WIDTH * 2")
        assert api.getConfigurableElementValueIDs(reference_id) == [override_id]
        assert override_id != definitions[0]
        assert api.getConfigurableElementValueReferenceID(override_id) == "width"
        assert api.getConfigurableElementValueValueExpression(override_id) == "WIDTH * 2"
        assert api.getUnconfiguredID(reference_id) == root_id
        assert api.getUnconfiguredID(override_id) == definitions[0]
        assert api.getConfigurableElementValue(definitions[0]) == "10"
    finally:
        registry.clear()

"""Typed mixed instantiation traversal and removal preserve sibling alternatives."""

import pytest
from test_tgi_view_targets import document

from amal.eda.ipxact_de.tgi.ipxact.v1685_2022 import component, view
from amal.eda.ipxact_de.tgi.ipxact.v1685_2022.core import TgiError, get_handle, resolve_handle


@pytest.mark.parametrize("kind", ["Component", "Design", "DesignConfiguration"])
def test_typed_traversal_and_removal(kind):
    root = document()
    root_id = get_handle(root)
    getter = getattr(component, f"getComponent{kind}InstantiationIDs")
    handle = getter(root_id)[0]
    assert len(getter(root_id)) == 1
    view_id = component.addComponentView(root_id, "rtl")
    getattr(view, f"setView{kind}InstantiationRef")(view_id, "target")
    assert getattr(view, f"getView{kind}InstantiationRefByID")(view_id) == handle
    assert getattr(component, f"removeComponent{kind}Instantiation")(handle)
    assert resolve_handle(handle) is None
    assert getter(root_id) == []
    instances = root.model.instantiations
    assert len(instances.component_instantiation_or_design_instantiation_or_design_configuration_instantiation) == 2
    with pytest.raises(TgiError):
        getattr(view, f"getView{kind}InstantiationRefByID")(view_id)
    assert getattr(view, f"getView{kind}InstantiationRefByName")(view_id) == "target"


@pytest.mark.parametrize("kind", ["Component", "Design", "DesignConfiguration"])
def test_wrong_type_is_atomic(kind):
    root_id = get_handle(document())
    other = "Design" if kind == "Component" else "Component"
    child = getattr(component, f"getComponent{other}InstantiationIDs")(root_id)[0]
    with pytest.raises(TgiError):
        getattr(component, f"removeComponent{kind}Instantiation")(child)
    assert resolve_handle(child) is not None

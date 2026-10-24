"""View targets resolve by type and name within their owning component."""

import pytest

from amal.eda.accellera.ipxact.v1685_2022.tgi import component, view
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import TgiError, get_handle, resolve_handle
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import Component


def document():
    return XmlDocument.parser().from_string('''<component xmlns="http://www.accellera.org/XMLSchema/IPXACT/1685-2022">
<vendor>v</vendor><library>l</library><name>c</name><version>1</version><model><instantiations>
<componentInstantiation><name>target</name></componentInstantiation>
<designInstantiation><name>target</name><designRef vendor="v" library="l" name="d" version="1"/></designInstantiation>
<designConfigurationInstantiation><name>target</name>
<designConfigurationRef vendor="v" library="l" name="dc" version="1"/></designConfigurationInstantiation>
</instantiations></model></component>''', Component)


@pytest.mark.parametrize("kind", ["Component", "Design", "DesignConfiguration"])
def test_owned_view_target_and_faults(kind):
    root = document()
    root_id = get_handle(root)
    view_id = component.addComponentView(root_id, "rtl")
    getter = getattr(view, f"getView{kind}InstantiationRefByID")
    setter = getattr(view, f"setView{kind}InstantiationRef")
    assert getter(view_id) is None
    setter(view_id, "target")
    target_id = getter(view_id)
    assert resolve_handle(target_id).name == "target"
    assert type(resolve_handle(target_id)).__name__.startswith(kind)
    assert getter(view_id) == target_id
    setter(view_id, "missing")
    with pytest.raises(TgiError):
        getter(view_id)
    assert resolve_handle(target_id) is not None


def test_configuration_alias_matches_reference_getter():
    root_id = get_handle(document())
    view_id = component.addComponentView(root_id, "rtl")
    view.setViewDesignConfigurationInstantiationRef(view_id, "target")
    assert (view.getViewDesignConfigurationInstantiationID(view_id)
            == view.getViewDesignConfigurationInstantiationRefByID(view_id))


def test_owner_isolation_and_reference_removal_preserves_target():
    roots = [get_handle(document()), get_handle(document())]
    views = [component.addComponentView(root, "rtl") for root in roots]
    for handle in views:
        view.setViewComponentInstantiationRef(handle, "target")
    targets = [view.getViewComponentInstantiationRefByID(handle) for handle in views]
    assert targets[0] != targets[1]
    assert view.removeViewComponentInstantiationRef(views[0])
    assert resolve_handle(targets[0]) is not None


@pytest.mark.parametrize("kind", ["Component", "Design", "DesignConfiguration"])
def test_registered_parsed_view_restores_ownership(kind):
    from amal.eda.accellera.ipxact.v1685_2022.tgi.core import registry

    root = document()
    original_id = get_handle(root)
    handle = component.addComponentView(original_id, "rtl")
    getattr(view, f"setView{kind}InstantiationRef")(handle, "target")
    loaded = XmlDocument.parser().from_string(XmlDocument.serializer().render(root), Component)
    registry.clear()
    registry.register(loaded, ("v", "l", "c", "1"))
    parsed_view = get_handle(loaded.model.views.view[0])
    target = getattr(view, f"getView{kind}InstantiationRefByID")(parsed_view)
    assert resolve_handle(target).name == "target"
    assert component.removeComponentView(parsed_view)
    assert resolve_handle(target) is not None
    registry.clear()


def test_ambiguous_target_is_rejected():
    root = document()
    instantiations = root.model.instantiations
    items = instantiations.component_instantiation_or_design_instantiation_or_design_configuration_instantiation
    items.append(type(items[0])(name="target"))
    handle = component.addComponentView(get_handle(root), "rtl")
    view.setViewComponentInstantiationRef(handle, "target")
    with pytest.raises(TgiError):
        view.getViewComponentInstantiationRefByID(handle)


def test_unowned_referenced_view_is_rejected():
    from org.accellera.ipxact.v1685_2022.model_type import ModelType

    handle = get_handle(ModelType.Views.View(name="rtl", component_instantiation_ref="target"))
    with pytest.raises(TgiError):
        view.getViewComponentInstantiationRefByID(handle)

"""View targets resolve by type and name within their owning component."""

import pytest

from amal.eda.ipxact_de.tgi.ipxact.v1685_2022 import component, view
from amal.eda.ipxact_de.tgi.ipxact.v1685_2022.core import TgiError, get_handle, resolve_handle
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

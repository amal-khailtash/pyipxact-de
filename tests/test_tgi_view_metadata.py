"""Generated view metadata supports both root families and parsed ownership."""

import pytest
from lxml import etree

from amal.eda.ipxact_de.tgi.ipxact.v1685_2022 import view as api
from amal.eda.ipxact_de.tgi.ipxact.v1685_2022.core import TgiError, get_handle, get_parent_info, resolve_handle
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022.abstractor_model_type import AbstractorModelType
from org.accellera.ipxact.v1685_2022.model_type import ModelType


@pytest.mark.parametrize("cls", [ModelType.Views.View, AbstractorModelType.Views.View])
@pytest.mark.parametrize("parsed", [False, True])
def test_environment_lifecycle_and_xml(cls, parsed):
    view = cls(name="rtl")
    view_id = get_handle(view)
    assert api.getViewName(view_id) == "rtl"
    assert api.getViewEnvIdentifierIDs(view_id) == []
    first = api.addViewEnvIdentifier(view_id, "verilog:*Simulation:vendor")
    second = api.addViewEnvIdentifier(view_id, "::")
    resolve_handle(first).id = "environment"
    assert api.getViewEnvIdentifiers(view_id) == ["verilog:*Simulation:vendor", "::"]
    assert get_parent_info(first).path == ("env_identifier",)
    xml = XmlDocument.serializer().render(view)
    loaded = XmlDocument.parser().from_string(xml, cls)
    assert loaded == view
    if parsed:
        view = loaded
        view_id = get_handle(view)
        first, second = api.getViewEnvIdentifierIDs(view_id)
    assert api.removeViewEnvIdentifier(first)
    assert resolve_handle(first) is None
    assert resolve_handle(second) is not None
    assert api.getViewEnvIdentifiers(view_id) == ["::"]
    assert not api.removeViewEnvIdentifier(first)
    assert api.getViewName(view_id) == "rtl"
    assert XmlDocument.parser().from_string(XmlDocument.serializer().render(view), cls) == view


@pytest.mark.parametrize("value", ["", "verilog", "a:b", "a:b:c:d", "a:b:bad space", None, 7])
def test_bad_environment_syntax_is_atomic(value):
    view = ModelType.Views.View(name="rtl")
    with pytest.raises(TgiError):
        api.addViewEnvIdentifier(get_handle(view), value)
    assert view.env_identifier == []


@pytest.mark.parametrize("operation", [api.getViewName, api.getViewEnvIdentifierIDs, api.getViewEnvIdentifiers])
def test_invalid_view_handles(operation):
    with pytest.raises(TgiError):
        operation("missing")


def test_wrong_child_removal_is_atomic():
    view = ModelType.Views.View(name="rtl")
    view_id = get_handle(view)
    child = api.addViewEnvIdentifier(view_id, "verilog::")
    with pytest.raises(TgiError):
        api.removeViewEnvIdentifier(view_id)
    assert resolve_handle(child) is not None


def test_component_document_schema_validity():
    view = ModelType.Views.View(name="rtl")
    api.addViewEnvIdentifier(get_handle(view), "verilog:*Simulation:")
    rendered = XmlDocument.serializer().render(view)
    element = etree.fromstring(rendered.encode())
    ns = "http://www.accellera.org/XMLSchema/IPXACT/1685-2022"
    element.tag = f"{{{ns}}}view"
    xml = (f'<component xmlns="{ns}"><vendor>v</vendor><library>l</library>'
           '<name>c</name><version>1</version><model><views>').encode()
    xml += etree.tostring(element)+b'</views></model></component>'
    schema = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))
    assert schema.validate(etree.fromstring(xml)), schema.error_log


def test_view_removal_invalidates_environment_descendants():
    from amal.eda.ipxact_de.tgi.ipxact.v1685_2022 import component
    from org.accellera.ipxact.v1685_2022 import Component

    root_id = get_handle(Component(vendor="v", library="l", name="c", version="1"))
    view_id = component.addComponentView(root_id, "rtl")
    environment_id = api.addViewEnvIdentifier(view_id, "verilog::")
    assert component.removeComponentView(view_id)
    assert resolve_handle(environment_id) is None

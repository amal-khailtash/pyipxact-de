"""Generated instantiation creation preserves mixed ordering and immediate ownership."""
import pytest
from lxml import etree

from amal.eda.ipxact_de.tgi.ipxact.v1685_2022 import component
from amal.eda.ipxact_de.tgi.ipxact.v1685_2022.core import TgiError, get_handle, resolve_handle
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import Component


@pytest.mark.parametrize("kind", ["Component", "Design", "DesignConfiguration"])
def test_creation_xml_and_removal(kind):
    root = Component(vendor="v", library="l", name="c", version="1")
    root_id = get_handle(root)
    args = [root_id, "instance"] + ([] if kind == "Component" else [("v", "l", "target", "1")])
    child = getattr(component, f"addComponent{kind}Instantiation")(*args)
    assert getattr(component, f"getComponent{kind}InstantiationIDs")(root_id) == [child]
    xml = XmlDocument.serializer().render(root)
    schema = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))
    assert schema.validate(etree.fromstring(xml.encode())), schema.error_log
    assert XmlDocument.parser().from_string(xml, Component) == root
    assert getattr(component, f"removeComponent{kind}Instantiation")(child)
    assert resolve_handle(child) is None

@pytest.mark.parametrize("kind", ["Component", "Design", "DesignConfiguration"])
def test_empty_name_is_atomic(kind):
    root = Component(vendor="v", library="l", name="c", version="1")
    args = [get_handle(root), ""] + ([] if kind == "Component" else [("v", "l", "d", "1")])
    with pytest.raises(TgiError):
        getattr(component, f"addComponent{kind}Instantiation")(*args)
    assert root.model is None

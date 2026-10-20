"""Generic bus-mode choices retain their QName during XML round trips."""

import pytest
from lxml import etree

from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2014.bus_interface_type import BusInterfaceType as Bus2014
from org.accellera.ipxact.v1685_2022.bus_interface_type import BusInterfaceType as Bus2022


@pytest.mark.parametrize("version,model,mode", [
    ("1685-2014", Bus2014, "mirroredMaster"),
    ("1685-2022", Bus2022, "mirroredInitiator"),
])
def test_generic_choice_identity(version, model, mode):
    ns = f"http://www.accellera.org/XMLSchema/IPXACT/{version}"
    xml = (f'<busInterface xmlns="{ns}"><name>bus</name>'
           '<busType vendor="acme" library="bus" name="test" version="1"/>'
           f'<{mode}/></busInterface>')
    obj = XmlDocument.parser().from_string(xml, model)
    output = XmlDocument.serializer().render(obj)
    root = etree.fromstring(output.encode())
    assert len(root.findall(f"{{{ns}}}{mode}")) == 1
    assert root.find(f"{{{ns}}}{mode}").text is None

"""BASE interface/configuration reference attributes preserve source names."""

import pytest

from amal.eda.accellera.ipxact.v1685_2022 import tgi
from amal.eda.accellera.ipxact.v1685_2022.tgi import element_attribute as api
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import TgiError, get_handle
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import InterfaceType, ModeLinks, Parameter, ViewLinks


@pytest.mark.parametrize(
    "name,obj,expected",
    [
        ("getBusRefAttribute", InterfaceType(component_instance_ref="child", bus_ref="bus"), "bus"),
        ("getComponentInstanceRefAttribute", InterfaceType(component_instance_ref="child", bus_ref="bus"), "child"),
        ("getChoiceRefAttribute", Parameter(name="P", value="1", choice_ref="choice"), "choice"),
        ("getModeRefAttribute", ModeLinks.ModeLink.ExternalModeReference(mode_ref="mode"), "mode"),
        ("getViewRefAttribute", ViewLinks.ViewLink.ExternalViewReference(view_ref="view"), "view"),
    ],
)
def test_interface_reference(name, obj, expected):
    getter = getattr(api, name)
    before = XmlDocument.serializer().render(obj)
    assert getter(get_handle(obj)) == expected
    parsed = XmlDocument.parser().from_string(before, type(obj))
    assert getter(get_handle(parsed)) == expected
    assert getattr(tgi, name) is getter
    assert XmlDocument.serializer().render(obj) == before
    assert getter(get_handle(object())) is None
    with pytest.raises(TgiError):
        getter("missing")

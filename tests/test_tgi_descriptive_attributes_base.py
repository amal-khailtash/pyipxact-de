"""BASE descriptive XML attributes preserve strings and enum source values."""

import pytest

from amal.eda.accellera.ipxact.v1685_2022 import tgi
from amal.eda.accellera.ipxact.v1685_2022.tgi import element_attribute as api
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import TgiError, get_handle
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import (
    Choices,
    FileType,
    MonitorInterfaceType,
    Parameter,
    ParameterTypePrefix,
    SimpleFileType,
)


@pytest.mark.parametrize(
    "name,obj,field,expected",
    [
        (
            "getHelpAttribute",
            Choices.Choice.Enumeration(value="1", help="Select this value"),
            "help",
            "Select this value",
        ),
        ("getPromptAttribute", Parameter(name="P", value="1", prompt="Width?"), "prompt", "Width?"),
        ("getPrefixAttribute", Parameter(name="P", value="1", prefix=ParameterTypePrefix.KILO), "prefix", "kilo"),
        ("getUserAttribute", FileType(value=SimpleFileType.UNKNOWN, user="custom HDL"), "user", "custom HDL"),
        (
            "getPathAttribute",
            MonitorInterfaceType(component_instance_ref="child", bus_ref="bus", path="top/child/interface"),
            "path",
            "top/child/interface",
        ),
    ],
)
def test_descriptive_attribute(name, obj, field, expected):
    getter = getattr(api, name)
    before = XmlDocument.serializer().render(obj)
    assert getter(get_handle(obj)) == expected
    parsed = XmlDocument.parser().from_string(before, type(obj))
    assert getter(get_handle(parsed)) == expected
    assert XmlDocument.serializer().render(obj) == before
    assert getattr(tgi, name) is getter
    setattr(obj, field, None)
    assert getter(get_handle(obj)) is None
    assert getter(get_handle(object())) is None
    with pytest.raises(TgiError):
        getter("missing")


def test_empty_descriptive_values():
    assert api.getPromptAttribute(get_handle(Parameter(name="P", value="1", prompt=""))) == ""
    assert api.getHelpAttribute(get_handle(Choices.Choice.Enumeration(value="1", help=""))) == ""

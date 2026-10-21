"""BASE semantic attribute getters use XML attributes and enum lexical values."""

import pytest

from amal.eda.accellera.ipxact.v1685_2022 import tgi
from amal.eda.accellera.ipxact.v1685_2022.tgi import element_attribute as api
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import TgiError, get_handle
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import (
    ComponentPortDirectionType,
    DelayValueType,
    ModuleParameterType,
    PortWireType,
    RequiresDriver,
    RequiresDriverDriverType,
    TimingConstraint,
    Value,
)


@pytest.mark.parametrize(
    "name,obj,expected",
    [
        ("getDataTypeAttribute", ModuleParameterType(name="P", value=Value(value="1"), data_type="logic"), "logic"),
        (
            "getDataTypeDefinitionAttribute",
            ModuleParameterType(name="P", value=Value(value="1"), data_type_definition="types"),
            "types",
        ),
        ("getDelayTypeAttribute", TimingConstraint(value=50.0, clock_name="clk", delay_type=DelayValueType.MAX), "max"),
        ("getDirectionAttribute", PortWireType(direction=ComponentPortDirectionType.INOUT), "inout"),
        (
            "getDriverTypeAttribute",
            RequiresDriver(value=True, driver_type=RequiresDriverDriverType.SINGLE_SHOT),
            "singleShot",
        ),
    ],
)
def test_semantic_attribute(name, obj, expected):
    before = XmlDocument.serializer().render(obj)
    getter = getattr(api, name)
    assert getter(get_handle(obj)) == expected
    parsed = XmlDocument.parser().from_string(before, type(obj))
    assert getter(get_handle(parsed)) == expected
    assert XmlDocument.serializer().render(obj) == before
    assert getattr(tgi, name) is getter
    assert getter(get_handle(object())) is None
    with pytest.raises(TgiError):
        getter("missing")


def test_optional_semantic_attributes():
    obj = ModuleParameterType(name="P", value=Value(value="1"), data_type="")
    assert api.getDataTypeAttribute(get_handle(obj)) == ""
    assert api.getDataTypeDefinitionAttribute(get_handle(obj)) is None
    obj.data_type = None
    assert api.getDataTypeAttribute(get_handle(obj)) is None

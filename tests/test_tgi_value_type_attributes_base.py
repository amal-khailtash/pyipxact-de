"""Element attribute BASE value types and reset references retain source values."""

import pytest

from amal.eda.accellera.ipxact.v1685_2022 import tgi
from amal.eda.accellera.ipxact.v1685_2022.tgi import element_attribute as api
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import TgiError, get_handle
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import (
    ClockDriverType,
    DelayValueUnitType,
    FormatType,
    ModuleParameterType,
    ModuleParameterTypeUsageType,
    Parameter,
    ParameterTypeUnit,
    ResetTypeLinks,
    Value,
)


@pytest.mark.parametrize(
    "name,obj,expected",
    [
        ("getUnitAttribute", Parameter(name="P", value="1", unit=ParameterTypeUnit.HERTZ), "hertz"),
        ("getUnitsAttribute", ClockDriverType.ClockPeriod(value="10", units=DelayValueUnitType.NS), "ns"),
        (
            "getUsageTypeAttribute",
            ModuleParameterType(name="P", value=Value(value="1"), usage_type=ModuleParameterTypeUsageType.TYPED),
            "typed",
        ),
        ("getTypeAttribute", ModuleParameterType(name="P", value=Value(value="1"), type_value=FormatType.INT), "int"),
        (
            "getResetTypeRefAttribute",
            ResetTypeLinks.ResetTypeLink.ExternalResetTypeReference(reset_type_ref="reset"),
            "reset",
        ),
    ],
)
def test_value_type_attribute(name, obj, expected):
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


def test_absent_unit():
    assert api.getUnitAttribute(get_handle(Parameter(name="P", value="1"))) is None

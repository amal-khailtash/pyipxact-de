"""BASE configuration enum attributes preserve standard lexical values."""

import pytest

from amal.eda.accellera.ipxact.v1685_2022 import tgi
from amal.eda.accellera.ipxact.v1685_2022.tgi import element_attribute as api
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import TgiError, get_handle
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import (
    EnumeratedValueType,
    EnumeratedValueTypeUsage,
    FieldType,
    InstanceGeneratorType,
    InstanceGeneratorTypeScope,
    IpxactUri,
    Parameter,
    ParameterTypeResolve,
    SignType,
    UnsignedBitVectorExpression,
)
from org.accellera.ipxact.v1685_2022 import (
    TestableTestConstraint as ConstraintKind,
)


@pytest.mark.parametrize(
    "name,obj,expected",
    [
        ("getResolveAttribute", Parameter(name="P", value="1", resolve=ParameterTypeResolve.USER), "user"),
        (
            "getScopeAttribute",
            InstanceGeneratorType(
                name="gen", generator_exe=IpxactUri(value="run"), scope=InstanceGeneratorTypeScope.ENTITY
            ),
            "entity",
        ),
        ("getSignAttribute", Parameter(name="P", value="1", sign=SignType.SIGNED), "signed"),
        (
            "getTestConstraintAttribute",
            FieldType.FieldAccessPolicies.FieldAccessPolicy.Testable(
                value=True, test_constraint=ConstraintKind.RESTORE
            ),
            "restore",
        ),
        (
            "getUsageAttribute",
            EnumeratedValueType(
                name="V", value=UnsignedBitVectorExpression(value="1"), usage=EnumeratedValueTypeUsage.READ
            ),
            "read",
        ),
    ],
)
def test_configuration_attribute(name, obj, expected):
    before = XmlDocument.serializer().render(obj)
    getter = getattr(api, name)
    assert getter(get_handle(obj)) == expected
    parsed = XmlDocument.parser().from_string(before, type(obj))
    assert getter(get_handle(parsed)) == expected
    assert getattr(tgi, name) is getter
    assert XmlDocument.serializer().render(obj) == before
    assert getter(get_handle(object())) is None
    with pytest.raises(TgiError):
        getter("missing")


def test_default_configuration_attributes():
    assert api.getResolveAttribute(get_handle(Parameter(name="P", value="1"))) == "immediate"
    assert (
        api.getScopeAttribute(get_handle(InstanceGeneratorType(name="gen", generator_exe=IpxactUri(value="run"))))
        == "instance"
    )
    assert api.getSignAttribute(get_handle(Parameter(name="P", value="1"))) is None

"""BASE configuration lists and scalar source attributes follow WSDL types."""

import pytest

from amal.eda.accellera.ipxact.v1685_2022 import tgi
from amal.eda.accellera.ipxact.v1685_2022.tgi import element_attribute as api
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import TgiError, get_handle
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import ConstraintSet, Dim, Parameter, WireTypeDef


@pytest.mark.parametrize(
    "name,obj,expected",
    [
        (
            "getConfigGroupsAttribute",
            Parameter(name="P", value="1", config_groups=["groupA", "groupB"]),
            "groupA groupB",
        ),
        (
            "getConstrainedAttributeValues",
            WireTypeDef.TypeName(value="logic", constrained=["vector", "array"]),
            ["vector", "array"],
        ),
        ("getIndexVarAttribute", Dim(value="4", index_var="i"), "i"),
        ("getOrderFloatAttribute", Parameter(name="P", value="1", order=0.5), 0.5),
        ("getConstraintSetIdAttribute", ConstraintSet(constraint_set_id="timing"), "timing"),
    ],
)
def test_configuration_source_attribute(name, obj, expected):
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


def test_lists_are_copied_and_empty_values_preserved():
    obj = WireTypeDef.TypeName(value="logic", constrained=["vector", "array"])
    result = api.getConstrainedAttributeValues(get_handle(obj))
    result.clear()
    assert list(obj.constrained) == ["vector", "array"]
    obj.constrained = []
    assert api.getConstrainedAttributeValues(get_handle(obj)) == []
    assert api.getConfigGroupsAttribute(get_handle(Parameter(name="P", value="1"))) == ""
    assert api.getOrderFloatAttribute(get_handle(Parameter(name="P", value="1", order=0.0))) == 0.0

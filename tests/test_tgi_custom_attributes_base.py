"""Element attribute BASE custom/display source values survive XML reloads."""

import pytest

from amal.eda.accellera.ipxact.v1685_2022 import tgi
from amal.eda.accellera.ipxact.v1685_2022.tgi import element_attribute as api
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import TgiError, get_handle
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import (
    CellFunctionValueType,
    CellSpecification,
    Choices,
    IsFlowControlFlowType,
    Kind,
    KindType,
    QualifierType,
    ReadAction,
    ReadActionType,
)


@pytest.mark.parametrize(
    "name,obj,expected",
    [
        ("getCustomAttribute", Kind(value=KindType.CUSTOM, custom="protocol"), "protocol"),
        ("getOtherAttribute", CellSpecification.CellFunction(value=CellFunctionValueType.OTHER, other="cell"), "cell"),
        ("getModifyAttribute", ReadAction(value=ReadActionType.MODIFY, modify="action"), "action"),
        ("getTextAttribute", Choices.Choice.Enumeration(value="1", text="display"), "display"),
        (
            "getFlowTypeAttribute",
            QualifierType.IsFlowControl(value=True, flow_type=IsFlowControlFlowType.CREDIT_RETURN),
            "credit-return",
        ),
    ],
)
def test_custom_attribute(name, obj, expected):
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


def test_empty_custom_value():
    assert api.getCustomAttribute(get_handle(Kind(value=KindType.CUSTOM, custom=""))) == ""
    assert api.getCustomAttribute(get_handle(Kind(value=KindType.CUSTOM))) is None

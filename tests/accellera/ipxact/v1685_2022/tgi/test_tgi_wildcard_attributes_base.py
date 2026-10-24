"""BASE wildcard and ancillary attributes follow standard signatures."""

import pytest

from amal.eda.accellera.ipxact.v1685_2022 import tgi
from amal.eda.accellera.ipxact.v1685_2022.tgi import element_attribute as api
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import TgiError, get_handle
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import (
    ExecutableImage,
    FileType,
    IsResetLevel,
    QualifierType,
    SimpleFileType,
    StringExpression,
)


def test_wildcard_attributes_roundtrip():
    values = {"{urn:vendor}flag": "", "{urn:vendor}mode": "custom"}
    obj = StringExpression(value="source", other_attributes=values.copy())
    before = XmlDocument.serializer().render(obj)
    for current in (obj, XmlDocument.parser().from_string(before, StringExpression)):
        handle = get_handle(current)
        assert api.getOtherAttributes(handle) == list(current.other_attributes)
        assert all(name in api.getOtherAttributes(handle) for name in values)
        for name, value in values.items():
            assert api.getOtherAnyAttribute(handle, name) == value
        assert api.getOtherAnyAttribute(handle, "{urn:vendor}missing") is None
        names = api.getOtherAttributes(handle)
        names.clear()
        assert all(current.other_attributes[name] == value for name, value in values.items())
    assert tgi.getOtherAnyAttribute is api.getOtherAnyAttribute
    assert tgi.getOtherAttributes is api.getOtherAttributes
    assert XmlDocument.serializer().render(obj) == before
    assert api.getOtherAttributes(get_handle(object())) == []
    with pytest.raises(TgiError):
        api.getOtherAttributes("missing")
    with pytest.raises(TgiError):
        api.getOtherAnyAttribute("missing", "name")


@pytest.mark.parametrize(
    "name,obj,expected",
    [
        ("getLibextAttribute", FileType(value=SimpleFileType.USER, libext="sv"), "sv"),
        ("getLevelAttribute", QualifierType.IsReset(value=True, level=IsResetLevel.LOW), "low"),
        ("getImageTypeAttribute", ExecutableImage(name="image", image_id="boot", image_type="ELF"), "ELF"),
    ],
)
def test_ancillary_attribute(name, obj, expected):
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

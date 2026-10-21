"""BASE document-reference identity attributes preserve individual source parts."""

import pytest

from amal.eda.accellera.ipxact.v1685_2022 import tgi
from amal.eda.accellera.ipxact.v1685_2022.tgi import element_attribute as api
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import TgiError, get_handle
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import ConfigurableLibraryRefType, ExecutableImage


@pytest.mark.parametrize(
    "name,field",
    [
        ("getVendorAttribute", "vendor"),
        ("getLibraryAttribute", "library"),
        ("getNameAttribute", "name"),
        ("getVersionAttribute", "version"),
    ],
)
def test_vlnv_attribute(name, field):
    values = {"vendor": "vendor.example", "library": "lib", "name": "part", "version": "1.2"}
    obj = ConfigurableLibraryRefType(**values)
    getter = getattr(api, name)
    before = XmlDocument.serializer().render(obj)
    assert getter(get_handle(obj)) == values[field]
    parsed = XmlDocument.parser().from_string(before, type(obj))
    assert getter(get_handle(parsed)) == values[field]
    assert XmlDocument.serializer().render(obj) == before
    assert getattr(tgi, name) is getter
    assert getter(get_handle(object())) is None
    with pytest.raises(TgiError):
        getter("missing")


def test_image_id_source():
    obj = ExecutableImage(name="image", image_id="boot-image")
    before = XmlDocument.serializer().render(obj)
    getter = api.getImageIdAttribute
    assert getter(get_handle(obj)) == "boot-image"
    parsed = XmlDocument.parser().from_string(before, ExecutableImage)
    assert getter(get_handle(parsed)) == "boot-image"
    assert tgi.getImageIdAttribute is getter
    assert XmlDocument.serializer().render(obj) == before
    assert getter(get_handle(object())) is None
    with pytest.raises(TgiError):
        getter("missing")

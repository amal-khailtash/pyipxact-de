"""Generated XML attribute edits use metadata, schema types and defaults."""

import pytest

from amal.eda.accellera.ipxact.v1685_2022.tgi import element_attribute as api
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import TgiError, get_handle
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import Generator, IpxactUri, ModeRef, StringExpression
from org.accellera.ipxact.v1685_2022.wire_type_def import WireTypeDef


def test_camel_case_boolean_enum_and_default_removal_roundtrip():
    root = Generator(name="gen", generator_exe=IpxactUri(value="tool"))
    handle = get_handle(root)
    assert api.setHiddenBooleanAttribute(handle, True)
    assert api.getHiddenBooleanAttribute(handle) is True
    with pytest.raises(TgiError):
        api.setHiddenBooleanAttribute(handle, "true")
    assert root.hidden is True
    assert api.removeAttribute(handle, "hidden")
    assert root.hidden is False
    parsed = XmlDocument.parser().from_string(XmlDocument.serializer().render(root), Generator)
    assert parsed.hidden is False
    with pytest.raises(TgiError):
        api.removeAttribute(handle, "name")


def test_list_attributes_and_named_attribute_presence():
    obj = WireTypeDef.TypeName(value="wire")
    handle = get_handle(obj)
    assert api.addConstrainedAttribute(handle, "bits arrays")
    assert obj.constrained == ["bits", "arrays"]
    assert api.getConstrainedAttributeValues(handle) == ["bits", "arrays"]
    assert api.isSetAttribute(handle, "constrained")
    assert api.removeConstrainedAttribute(handle)
    assert obj.constrained == []


def test_numeric_attribute_strict_input():
    obj = ModeRef(value="run", priority=1)
    handle = get_handle(obj)
    assert api.setPriorityIntAttribute(handle, 3)
    assert api.getPriorityIntAttribute(handle) == 3
    for value in [True, "4", 1.5]:
        with pytest.raises(TgiError):
            api.setPriorityIntAttribute(handle, value)
    assert obj.priority == 3


def test_wildcard_attributes_roundtrip_and_atomic_invalid_value():
    obj = StringExpression(value="source")
    handle = get_handle(obj)
    assert api.setOtherAnyAttribute(handle, "{urn:vendor}flag", "yes")
    assert api.getOtherAnyAttribute(handle, "{urn:vendor}flag") == "yes"
    with pytest.raises(TgiError):
        api.setOtherAnyAttribute(handle, "{urn:vendor}flag", 2)
    parsed = XmlDocument.parser().from_string(XmlDocument.serializer().render(obj), StringExpression)
    assert parsed.other_attributes["{urn:vendor}flag"] == "yes"

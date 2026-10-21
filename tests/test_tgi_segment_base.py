"""Segment BASE values, source expressions and parsed child ownership."""

import pytest

from amal.eda.accellera.ipxact.v1685_2022 import tgi
from amal.eda.accellera.ipxact.v1685_2022.tgi import address_space as api
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import TgiError, detach_child_by_handle, get_handle, resolve_handle
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import (
    AddressSpaces,
    Component,
    UnsignedLongintExpression,
    UnsignedPositiveIntExpression,
    UnsignedPositiveLongintExpression,
)


@pytest.mark.parametrize("parsed", [False, True])
@pytest.mark.parametrize("field,name", [("address_offset", "AddressOffset"), ("range", "Range")])
@pytest.mark.parametrize("source,expected", [("0016", 16), ("0x20", 32), ("${SIZE}", None)])
def test_segment_base(field, name, source, expected, parsed):
    segment = AddressSpaces.AddressSpace.Segments.Segment(
        name="segment", address_offset=UnsignedLongintExpression(value="0"),
        range=UnsignedPositiveLongintExpression(value="64"),
    )
    getattr(segment, field).value = source
    space = AddressSpaces.AddressSpace(
        name="space", range=UnsignedPositiveLongintExpression(value="256"),
        width=UnsignedPositiveIntExpression(value="32"),
        segments=AddressSpaces.AddressSpace.Segments(segment=[segment]),
    )
    root = Component(
        vendor="v", library="l", name="c", version="1", address_spaces=AddressSpaces(address_space=[space])
    )
    if parsed:
        root = XmlDocument.parser().from_string(XmlDocument.serializer().render(root), Component)
        segment = root.address_spaces.address_space[0].segments.segment[0]
    handle = get_handle(segment)
    value, expression, child_id = [getattr(api, f"getSegment{name}{suffix}") for suffix in ("", "Expression", "ID")]
    before = XmlDocument.serializer().render(root)
    assert value(handle) == expected
    assert expression(handle) == source
    child = child_id(handle)
    assert child_id(handle) == child
    assert resolve_handle(child) is getattr(segment, field)
    assert getattr(tgi, f"getSegment{name}") is value
    assert XmlDocument.serializer().render(root) == before
    assert detach_child_by_handle(child)
    assert resolve_handle(child) is None
    for getter in (value, expression, child_id):
        assert getter(handle) is None
        for invalid in ("missing-segment", get_handle(root)):
            with pytest.raises(TgiError):
                getter(invalid)

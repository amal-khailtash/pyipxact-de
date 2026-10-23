"""Address-space edits retain schema types, ownership and XML ordering."""

import pytest
from lxml import etree

from amal.eda.accellera.ipxact.v1685_2022.tgi import address_space as api
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import TgiError, get_handle, resolve_handle
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import (
    AddressSpaces,
    Component,
    UnsignedPositiveIntExpression,
    UnsignedPositiveLongintExpression,
)


def _root():
    space = AddressSpaces.AddressSpace(
        name="space",
        range=UnsignedPositiveLongintExpression(value="256"),
        width=UnsignedPositiveIntExpression(value="32"),
    )
    return Component(
        vendor="v", library="l", name="c", version="1", address_spaces=AddressSpaces(address_space=[space])
    ), space


def _valid(root):
    schema = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))
    xml = XmlDocument.serializer().render(root)
    assert schema.validate(etree.fromstring(xml.encode())), schema.error_log
    return xml


def test_local_map_default_block_and_added_block_round_trip():
    root, space = _root()
    sid = get_handle(space)
    assert api.setAddressSpaceLocalMemoryMap(sid, "local", "boot", "0", "32", "32")
    lid = api.getAddressSpaceLocalMemoryMapID(sid)
    first = api.getLocalMemoryMapAddressBlockIDs(sid)
    assert len(first) == 1
    second = api.addLocalMemoryMapAddressBlock(lid, "data", "32", "32", "32")
    assert api.getLocalMemoryMapAddressBlockIDs(sid) == [*first, second]
    xml = _valid(root)
    parsed = XmlDocument.parser().from_string(xml, Component)
    parsed_sid = get_handle(parsed.address_spaces.address_space[0])
    assert len(api.getLocalMemoryMapAddressBlockIDs(parsed_sid)) == 2
    block = api.getLocalMemoryMapAddressBlockIDs(parsed_sid)[0]
    assert api.removeLocalMemoryMapAddressBlock(block)
    assert resolve_handle(block) is None
    _valid(parsed)


def test_atomic_range_and_width_edits_keep_child_handles():
    root, space = _root()
    sid = get_handle(space)
    rid = api.getAddressSpaceRangeID(sid)
    wid = api.getAddressSpaceWidthID(sid)
    api.setAddressSpaceRange(sid, "1 << 10")
    api.setAddressSpaceWidth(sid, "8 * 4")
    assert api.getAddressSpaceRange(sid) == 1024
    assert api.getAddressSpaceWidth(sid) == 32
    assert api.getAddressSpaceRangeID(sid) == rid
    assert api.getAddressSpaceWidthID(sid) == wid
    before = _valid(root)
    with pytest.raises(TgiError):
        api.setAddressSpaceRange(sid, "")
    assert _valid(root) == before


def test_reset_local_map_preserves_map_but_invalidates_replaced_blocks():
    root, space = _root()
    sid = get_handle(space)
    api.setAddressSpaceLocalMemoryMap(sid, "local", "boot", "0", "32", "32")
    lid = api.getAddressSpaceLocalMemoryMapID(sid)
    block = api.getLocalMemoryMapAddressBlockIDs(sid)[0]
    map_model = resolve_handle(lid)
    map_model.id = "local-map"
    before = _valid(root)
    with pytest.raises(TgiError):
        api.setAddressSpaceLocalMemoryMap(sid, "local", "broken", "0", "", "32")
    assert _valid(root) == before
    assert resolve_handle(block) is not None
    api.setAddressSpaceLocalMemoryMap(sid, "updated", "reset", "64", "32", "32")
    assert api.getAddressSpaceLocalMemoryMapID(sid) == lid
    assert resolve_handle(lid).id == "local-map"
    assert resolve_handle(block) is None
    assert resolve_handle(lid).name == "updated"
    _valid(root)


def test_unsigned_width_limits_do_not_use_signed_attribute_storage_limits():
    root, space = _root()
    sid = get_handle(space)
    api.setAddressSpaceWidth(sid, "32'hFFFFFFFF")
    assert api.getAddressSpaceWidth(sid) == (1 << 32) - 1
    _valid(root)
    before = api.getAddressSpaceWidthExpression(sid)
    with pytest.raises(TgiError):
        api.setAddressSpaceWidth(sid, str(1 << 32))
    assert api.getAddressSpaceWidthExpression(sid) == before


def test_explicit_zero_bound_is_preserved_by_segment_setters():
    from org.accellera.ipxact.v1685_2022 import UnsignedLongintExpression

    segment = AddressSpaces.AddressSpace.Segments.Segment(
        name="fixed",
        address_offset=UnsignedLongintExpression(value="0", minimum=0, maximum=0),
        range=UnsignedPositiveLongintExpression(value="1"),
    )
    handle = get_handle(segment)
    with pytest.raises(TgiError):
        api.setSegmentAddressOffset(handle, "1")
    assert api.getSegmentAddressOffsetExpression(handle) == "0"
    api.setSegmentAddressOffset(handle, "0")
    assert segment.address_offset.maximum == 0

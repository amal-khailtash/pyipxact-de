"""Annex F.7.7/F.7.8 access-handle generated-model lifecycle contracts."""

import pytest

from amal.eda.accellera.ipxact.v1685_2022.tgi import access_handle as api
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import TgiError, get_handle, resolve_handle
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import FieldType, PortAccessType1, RegisterFile


@pytest.mark.parametrize(
    "parent", [RegisterFile(name="rf", address_offset="0"), FieldType(name="f", bit_offset="0"), PortAccessType1()]
)
def test_handle_variant_follows_parent_schema_and_survives_xml(parent):
    parent_id = get_handle(parent)
    handle = api.addAccessHandle(parent_id, "top")
    assert api.getAccessHandleIDs(parent_id) == [handle]
    ah = resolve_handle(handle)
    rendered = XmlDocument.serializer().render(ah)
    assert "top" in rendered
    assert "pathSegments" in rendered
    assert api.getAccessHandleViewRefIDs(handle) == []
    view = api.addAccessHandleViewRef(handle, "rtl")
    assert api.getAccessHandleViewRefIDs(handle) == [view]
    assert api.removeAccessHandleViewRef(view)
    assert resolve_handle(view) is None
    if isinstance(parent, RegisterFile):
        segment = api.addAccessHandlePathSegment(handle, "leaf")
        assert len(api.getAccessHandlePathSegmentIDs(handle)) == 2
        assert api.removeAccessHandlePathSegment(segment)
        assert api.getAccessHandleForce(handle) is None
    else:
        assert api.getAccessHandleForce(handle) is True
        assert api.setAccessHandleForce(handle, False)
        assert api.getAccessHandleForce(handle) is False
        with pytest.raises(TgiError):
            api.setAccessHandleForce(handle, "false")
        sl = api.addAccessHandleSlice(handle, "leaf")
        assert len(api.getAccessHandleSliceIDs(handle)) == 2
        assert api.removeAccessHandleSlice(sl)
    if isinstance(parent, PortAccessType1):
        idx = api.addAccessHandleIndex(handle, "2")
        assert api.getAccessHandleIndicesIDs(handle) == [idx]
        assert api.removeAccessHandleIndex(idx)
    assert api.removeAccessHandle(handle)
    assert resolve_handle(handle) is None
    assert api.getAccessHandleIDs(parent_id) == []


def test_invalid_add_is_atomic():
    parent = RegisterFile(name="rf", address_offset="0")
    with pytest.raises(TgiError):
        api.addAccessHandle(get_handle(parent), "")
    assert parent.access_handles is None


@pytest.mark.parametrize(
    "parent", [RegisterFile(name="rf", address_offset="0"), FieldType(name="f", bit_offset="0"), PortAccessType1()]
)
def test_parsed_traversal_restores_child_removal_ownership(parent):
    original = api.addAccessHandle(get_handle(parent), "top")
    api.addAccessHandleViewRef(original, "rtl")
    model = resolve_handle(original)
    loaded = XmlDocument.parser().from_string(XmlDocument.serializer().render(model), type(model))
    handle = get_handle(loaded)
    view = api.getAccessHandleViewRefIDs(handle)[0]
    assert api.removeAccessHandleViewRef(view)
    assert not loaded.view_ref
    if isinstance(parent, RegisterFile):
        child = api.getAccessHandlePathSegmentIDs(handle)[0]
        assert api.removeAccessHandlePathSegment(child)
    else:
        child = api.getAccessHandleSliceIDs(handle)[0]
        assert api.removeAccessHandleSlice(child)
    assert resolve_handle(child) is None


def test_removers_do_not_detach_other_child_kinds():
    parent = RegisterFile(name="rf", address_offset="0")
    handle = api.addAccessHandle(get_handle(parent), "top")
    view = api.addAccessHandleViewRef(handle, "rtl")
    assert not api.removeAccessHandleSlice(view)
    assert not api.removeAccessHandleIndex(view)
    assert not api.removeAccessHandlePathSegment(view)
    assert resolve_handle(view) is not None


def test_removal_invalidates_owned_descendants_preserving_equal_sibling():
    parent = RegisterFile(name="rf", address_offset="0")
    first = api.addAccessHandle(get_handle(parent), "top")
    second = api.addAccessHandle(get_handle(parent), "top")
    segment = api.getAccessHandlePathSegmentIDs(first)[0]
    view = api.addAccessHandleViewRef(first, "rtl")
    assert api.removeAccessHandle(first)
    assert resolve_handle(segment) is None
    assert resolve_handle(view) is None
    assert api.getAccessHandleIDs(get_handle(parent)) == [second]


@pytest.mark.parametrize(
    "getter",
    [
        api.getAccessHandleForce,
        api.getAccessHandleIndicesIDs,
        api.getAccessHandlePathSegmentIDs,
        api.getAccessHandleSliceIDs,
        api.getAccessHandleViewRefIDs,
    ],
)
def test_invalid_handles_raise(getter):
    with pytest.raises(TgiError):
        getter("missing-access-handle")

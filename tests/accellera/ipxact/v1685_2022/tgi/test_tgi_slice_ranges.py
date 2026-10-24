"""Generated slice ranges preserve unsigned bounds, expressions and ownership."""

import inspect
from collections.abc import Sequence

import pytest

from amal.eda.accellera.ipxact.v1685_2022.tgi import slice_ as api
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import TgiError, get_handle, get_parent_info, resolve_handle
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import (
    Left,
    PortAccessHandle,
    PortSlicesType,
    PortSliceType,
    Range,
    Right,
    SlicedAccessHandle,
    SlicesType,
    SliceType,
)
from org.accellera.ipxact.v1685_2022.path_segment_type import PathSegmentType
from org.accellera.ipxact.v1685_2022.port_path_segment_type import PortPathSegmentType


def _slice(
    kind: type[SliceType] | type[PortSliceType], *, range_node: Range | None = None
) -> SliceType | PortSliceType:
    if kind is SliceType:
        segments = SliceType.PathSegments(path_segment=[PathSegmentType(value="sig")])
    else:
        segments = PortSliceType.PathSegments(path_segment=[PortPathSegmentType(value="sig")])
    return kind(path_segments=segments, range=range_node, id="slice-id")


@pytest.mark.parametrize("kind", [SliceType, PortSliceType])
def test_range_getters_evaluate_sources_restore_immediate_ownership(kind):
    range_node = Range(
        left=Left(value="8'h0f", minimum=0, maximum=15, other_attributes={"{urn:test}side": "left"}),
        right=Right(value="2**2", minimum=0, maximum=15, other_attributes={"{urn:test}side": "right"}),
    )
    item = _slice(kind, range_node=range_node)
    slice_id = get_handle(item)

    assert api.getSliceRange(slice_id) == (15, 4)
    assert api.getSliceRangeExpression(slice_id) == ("8'h0f", "2**2")
    left_id = api.getSliceRangeLeftID(slice_id)
    right_id = api.getSliceRangeRightID(slice_id)
    assert left_id is not None and right_id is not None
    assert api.getSliceRangeLeftID(slice_id) == left_id
    assert api.getSliceRangeRightID(slice_id) == right_id
    assert resolve_handle(left_id) is range_node.left
    assert resolve_handle(right_id) is range_node.right

    range_info = get_parent_info(get_handle(range_node))
    left_info = get_parent_info(left_id)
    right_info = get_parent_info(right_id)
    assert range_info is not None and range_info.parent_handle == slice_id and range_info.path == ("range",)
    assert left_info is not None and left_info.parent_handle == get_handle(range_node) and left_info.path == ("left",)
    assert (
        right_info is not None and right_info.parent_handle == get_handle(range_node) and right_info.path == ("right",)
    )


@pytest.mark.parametrize("kind", [SliceType, PortSliceType])
def test_absent_range_and_absent_endpoint_have_neutral_getters(kind):
    item = _slice(kind)
    slice_id = get_handle(item)

    assert api.getSliceRange(slice_id) == (None, None)
    assert api.getSliceRangeExpression(slice_id) == (None, None)
    assert api.getSliceRangeLeftID(slice_id) is None
    assert api.getSliceRangeRightID(slice_id) is None

    item.range = Range(left=None, right=Right(value="7"))
    assert api.getSliceRange(slice_id) == (None, 7)
    assert api.getSliceRangeExpression(slice_id) == (None, "7")
    assert api.getSliceRangeLeftID(slice_id) is None
    assert api.getSliceRangeRightID(slice_id) is not None


@pytest.mark.parametrize("kind", [SliceType, PortSliceType])
def test_set_range_creates_generated_range_and_preserves_endpoint_identity_metadata(kind):
    item = _slice(kind)
    slice_id = get_handle(item)

    assert api.setSliceRange(slice_id, ["7", "0"])
    range_node = item.range
    assert isinstance(range_node, Range)
    assert isinstance(range_node.left, Left)
    assert isinstance(range_node.right, Right)
    assert api.getSliceRange(slice_id) == (7, 0)
    assert api.getSliceRangeExpression(slice_id) == ("7", "0")
    range_id = get_handle(range_node)
    left_id = api.getSliceRangeLeftID(slice_id)
    right_id = api.getSliceRangeRightID(slice_id)
    assert left_id is not None and right_id is not None

    range_node.left.minimum = 0
    range_node.left.maximum = 15
    range_node.left.other_attributes = {"{urn:test}label": "left bound"}
    range_node.right.minimum = 0
    range_node.right.maximum = 15
    range_node.right.other_attributes = {"{urn:test}label": "right bound"}
    left_node, right_node = range_node.left, range_node.right

    assert api.setSliceRange(slice_id, ["8'hf", "(2 + 2)"])
    assert item.range is range_node
    assert api.getSliceRangeLeftID(slice_id) == left_id
    assert api.getSliceRangeRightID(slice_id) == right_id
    assert resolve_handle(range_id) is range_node
    assert resolve_handle(left_id) is left_node
    assert resolve_handle(right_id) is right_node
    assert api.getSliceRange(slice_id) == (15, 4)
    assert api.getSliceRangeExpression(slice_id) == ("8'hf", "(2 + 2)")
    assert (left_node.minimum, left_node.maximum) == (0, 15)
    assert (right_node.minimum, right_node.maximum) == (0, 15)
    assert left_node.other_attributes == {"{urn:test}label": "left bound"}
    assert right_node.other_attributes == {"{urn:test}label": "right bound"}


@pytest.mark.parametrize("kind", [SliceType, PortSliceType])
@pytest.mark.parametrize("sources", [("15", "0"), ("0", "15")])
def test_set_range_preserves_ascending_and_descending_endpoint_order(kind, sources):
    item = _slice(kind)
    slice_id = get_handle(item)

    assert api.setSliceRange(slice_id, sources)
    assert api.getSliceRange(slice_id) == tuple(map(int, sources))
    assert api.getSliceRangeExpression(slice_id) == sources


@pytest.mark.parametrize("kind", [SliceType, PortSliceType])
def test_set_range_applies_unsigned_32_bit_constant_semantics(kind):
    item = _slice(kind)
    slice_id = get_handle(item)

    assert api.setSliceRange(slice_id, ["32'h1_0000_0000", "0"])
    assert api.getSliceRangeExpression(slice_id) == ("32'h1_0000_0000", "0")
    assert api.getSliceRange(slice_id) == (0, 0)

    assert api.setSliceRange(slice_id, ["4294967296", "0"])
    assert api.getSliceRangeExpression(slice_id) == ("4294967296", "0")
    assert api.getSliceRange(slice_id) == (0, 0)


@pytest.mark.parametrize("kind", [SliceType, PortSliceType])
def test_unresolved_source_is_retained_and_numeric_getter_faults(kind):
    item = _slice(kind)
    slice_id = get_handle(item)

    assert api.setSliceRange(slice_id, ["DATA_WIDTH", "0"])
    assert api.getSliceRangeExpression(slice_id) == ("DATA_WIDTH", "0")
    with pytest.raises(TgiError):
        api.getSliceRange(slice_id)

    assert api.setSliceRange(slice_id, ["NaN", "inf"])
    assert api.getSliceRangeExpression(slice_id) == ("NaN", "inf")
    with pytest.raises(TgiError):
        api.getSliceRange(slice_id)


@pytest.mark.parametrize("kind", [SliceType, PortSliceType])
def test_invalid_range_sources_are_rejected_atomically(kind):
    range_node = Range(
        left=Left(value="7", minimum=0, maximum=15, other_attributes={"{urn:test}keep": "left"}),
        right=Right(value="0", minimum=0, maximum=15, other_attributes={"{urn:test}keep": "right"}),
    )
    item = _slice(kind, range_node=range_node)
    slice_id = get_handle(item)
    endpoints = (range_node.left, range_node.right)
    endpoint_ids = (get_handle(range_node.left), get_handle(range_node.right))

    invalid_sources = (
        ["1"],
        ["1", "2", "3"],
        "7:0",
        None,
        ["8'h0", object()],
        [float("nan"), "0"],
        [float("inf"), "0"],
        ["1.5", "0"],
        ["(", "0"],
        ["33'd4294967296", "0"],
        ["16", "0"],
    )
    for invalid in invalid_sources:
        try:
            api.setSliceRange(slice_id, invalid)
        except TgiError:
            pass
        else:
            pytest.fail(f"accepted invalid range sources: {invalid!r}")
        assert item.range is range_node
        assert (range_node.left, range_node.right) == endpoints
        assert (range_node.left.value, range_node.right.value) == ("7", "0")
        assert (get_handle(range_node.left), get_handle(range_node.right)) == endpoint_ids


@pytest.mark.parametrize("kind", [SliceType, PortSliceType])
def test_malformed_native_range_is_rejected_before_source_mutation(kind):
    malformed = Range(left="not a generated Left", right=Right(value="0"))
    item = _slice(kind, range_node=malformed)
    slice_id = get_handle(item)

    with pytest.raises(TgiError):
        api.setSliceRange(slice_id, ["3", "1"])
    assert item.range is malformed
    assert malformed.left == "not a generated Left"
    assert malformed.right.value == "0"


@pytest.mark.parametrize("kind", [SliceType, PortSliceType])
def test_invalid_declared_bounds_are_rejected_before_either_endpoint_changes(kind):
    range_node = Range(
        left=Left(value="7", minimum=0, maximum=7),
        right=Right(value="0", minimum=0, maximum=7),
    )
    item = _slice(kind, range_node=range_node)
    slice_id = get_handle(item)
    left_id, right_id = get_handle(range_node.left), get_handle(range_node.right)

    with pytest.raises(TgiError):
        api.setSliceRange(slice_id, ["6", "8"])
    assert (range_node.left.value, range_node.right.value) == ("7", "0")
    assert (get_handle(range_node.left), get_handle(range_node.right)) == (left_id, right_id)

    range_node.left.minimum = 8
    range_node.left.maximum = 7
    with pytest.raises(TgiError):
        api.setSliceRange(slice_id, ["6", "1"])
    assert (range_node.left.value, range_node.right.value) == ("7", "0")


@pytest.mark.parametrize("kind", [SliceType, PortSliceType])
def test_remove_range_requires_slice_owner_and_invalidates_only_range_subtree(kind):
    item = _slice(kind, range_node=Range(left=Left(value="3"), right=Right(value="0")))
    slice_id = get_handle(item)
    segment = item.path_segments.path_segment[0]
    segment_id = get_handle(segment)
    range_node = item.range
    assert isinstance(range_node, Range)
    range_id = get_handle(range_node)
    left_id = api.getSliceRangeLeftID(slice_id)
    right_id = api.getSliceRangeRightID(slice_id)
    assert left_id is not None and right_id is not None

    with pytest.raises(TgiError):
        api.removeSliceRange(range_id)
    assert item.range is range_node
    assert resolve_handle(range_id) is range_node

    assert api.removeSliceRange(slice_id)
    assert item.range is None
    assert resolve_handle(range_id) is None
    assert resolve_handle(left_id) is None
    assert resolve_handle(right_id) is None
    assert resolve_handle(segment_id) is segment
    assert item.path_segments.path_segment == [segment]
    assert api.getSliceRange(slice_id) == (None, None)
    assert api.removeSliceRange(slice_id) is False
    with pytest.raises(TgiError):
        api.removeSliceRange("missing-slice")


def test_slice_range_operations_have_exported_native_tgi_signatures():
    expected = {
        "getSliceRange": (("sliceID",), tuple[int | None, int | None]),
        "getSliceRangeExpression": (("sliceID",), tuple[str | None, str | None]),
        "getSliceRangeLeftID": (("sliceID",), str | None),
        "getSliceRangeRightID": (("sliceID",), str | None),
        "setSliceRange": (("sliceID", "range"), bool),
        "removeSliceRange": (("sliceID",), bool),
    }
    assert set(expected) <= set(api.__all__)
    for name, (parameter_names, return_type) in expected.items():
        signature = inspect.signature(getattr(api, name))
        assert tuple(signature.parameters) == parameter_names
        assert all(parameter.annotation is not inspect.Parameter.empty for parameter in signature.parameters.values())
        assert all(not isinstance(parameter.annotation, str) for parameter in signature.parameters.values())
        assert signature.return_annotation == return_type
    assert inspect.signature(api.setSliceRange).parameters["range"].annotation == Sequence[str]


@pytest.mark.parametrize("kind", [SliceType, PortSliceType])
def test_slice_ranges_round_trip_through_generated_access_handle_wrappers(kind):
    item = _slice(kind, range_node=Range(left=Left(value="8'hf"), right=Right(value="0")))
    if kind is SliceType:
        wrapper = SlicedAccessHandle(slices=SlicesType(slice=[item]))
        wrapper_type = SlicedAccessHandle
    else:
        wrapper = PortAccessHandle(slices=PortSlicesType(slice=[item]))
        wrapper_type = PortAccessHandle

    xml = XmlDocument.serializer().render(wrapper)
    parsed = XmlDocument.parser().from_string(xml, wrapper_type)
    parsed_slice = parsed.slices.slice[0]
    assert parsed_slice == item
    slice_id = get_handle(parsed_slice)
    assert api.getSliceRange(slice_id) == (15, 0)
    assert api.getSliceRangeExpression(slice_id) == ("8'hf", "0")


@pytest.mark.parametrize("kind", [SliceType, PortSliceType])
def test_slice_range_operations_reject_wrong_owner_and_unknown_ids(kind):
    item = _slice(kind)
    slice_id = get_handle(item)
    foreign_id = get_handle(Left(value="7"))
    unknown_id = "missing-slice"

    for invalid_id in (foreign_id, unknown_id):
        for getter in (
            api.getSliceRange,
            api.getSliceRangeExpression,
            api.getSliceRangeLeftID,
            api.getSliceRangeRightID,
        ):
            with pytest.raises(TgiError):
                getter(invalid_id)
        with pytest.raises(TgiError):
            api.setSliceRange(invalid_id, ["3", "0"])

    assert item.range is None
    assert resolve_handle(slice_id) is item

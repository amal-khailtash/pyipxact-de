"""Generated slice path segments preserve source text and ownership."""

import inspect
from collections.abc import Iterator

import pytest

from amal.eda.accellera.ipxact.v1685_2022.tgi import slice_ as api
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import (
    TgiError,
    TgiFaultCode,
    get_handle,
    get_parent_info,
    registry,
    resolve_handle,
)
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import (
    Left,
    PortAccessHandle,
    PortPathSegmentType,
    PortSlicesType,
    PortSliceType,
    SlicedAccessHandle,
    SlicesType,
    SliceType,
)
from org.accellera.ipxact.v1685_2022.path_segment_type import PathSegmentType


@pytest.fixture(autouse=True)
def clean_registry() -> Iterator[None]:
    registry.clear()
    yield
    registry.clear()


def _slice(kind: type[SliceType] | type[PortSliceType], values: list[str] | None = None) -> SliceType | PortSliceType:
    if kind is SliceType:
        path_segments = SliceType.PathSegments(path_segment=[PathSegmentType(value=value) for value in values or []])
    else:
        path_segments = PortSliceType.PathSegments(
            path_segment=[PortPathSegmentType(value=value) for value in values or []]
        )
    return kind(path_segments=path_segments)


@pytest.mark.parametrize("kind", [SliceType, PortSliceType])
def test_add_and_get_path_segments_preserve_source_order_and_restore_ownership(kind):
    item = _slice(kind, ['"u.sig[3]"', "PATH_NAME", "PATH_NAME"])
    slice_id = get_handle(item)

    first = api.addSlicePathSegment(slice_id, "string'(8'h41)")
    second = api.addSlicePathSegment(slice_id, "PATH_NAME")
    third = api.addSlicePathSegment(slice_id, '{"u.", "sig[3]"}')
    ids = api.getSlicePathSegmentIDs(slice_id)
    assert ids[:3] == [get_handle(segment) for segment in item.path_segments.path_segment[:3]]
    assert ids[3:] == [first, second, third]

    expected_type = PathSegmentType if kind is SliceType else PortPathSegmentType
    assert all(isinstance(resolve_handle(segment_id), expected_type) for segment_id in ids)
    assert [resolve_handle(segment_id).value for segment_id in ids] == [
        '"u.sig[3]"',
        "PATH_NAME",
        "PATH_NAME",
        "string'(8'h41)",
        "PATH_NAME",
        '{"u.", "sig[3]"}',
    ]

    holder_id = get_handle(item.path_segments)
    holder_info = get_parent_info(holder_id)
    assert holder_info is not None
    assert (holder_info.parent_handle, holder_info.path) == (slice_id, ("path_segments",))
    for segment_id in ids:
        segment_info = get_parent_info(segment_id)
        assert segment_info is not None
        assert (segment_info.parent_handle, segment_info.path) == (holder_id, ("path_segment",))
        assert resolve_handle(segment_id) in item.path_segments.path_segment


@pytest.mark.parametrize("kind", [SliceType, PortSliceType])
def test_add_creates_missing_required_path_segments_holder(kind):
    item = _slice(kind)
    item.path_segments = None
    slice_id = get_handle(item)

    segment_id = api.addSlicePathSegment(slice_id, '"top.unresolved"')

    assert item.path_segments is not None
    assert len(item.path_segments.path_segment) == 1
    segment = resolve_handle(segment_id)
    assert segment.value == '"top.unresolved"'
    assert api.getSlicePathSegmentIDs(slice_id) == [segment_id]


@pytest.mark.parametrize("kind", [SliceType, PortSliceType])
def test_add_rejects_invalid_text_and_wrong_model_types_atomically(kind):
    item = _slice(kind, ["kept"])
    slice_id = get_handle(item)
    holder = item.path_segments
    before = list(holder.path_segment)

    for value in (None, 7, object(), "7", '"unterminated', "control\x01character"):
        with pytest.raises(TgiError) as error:
            api.addSlicePathSegment(slice_id, value)
        assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
        assert item.path_segments is holder
        assert holder.path_segment == before

    with pytest.raises(TgiError) as error:
        api.getSlicePathSegmentIDs(get_handle(Left(value="1")))
    assert error.value.fault_code == TgiFaultCode.INVALID_ID


@pytest.mark.parametrize(
    ("kind", "wrong_segment"),
    [(SliceType, PortPathSegmentType(value="wrong")), (PortSliceType, PathSegmentType(value="wrong"))],
)
def test_getter_rejects_malformed_generated_path_segment_type(kind, wrong_segment):
    item = _slice(kind)
    item.path_segments.path_segment.append(wrong_segment)

    with pytest.raises(TgiError) as error:
        api.getSlicePathSegmentIDs(get_handle(item))
    assert error.value.fault_code == TgiFaultCode.INVALID_ID


@pytest.mark.parametrize("kind", [SliceType, PortSliceType])
def test_getter_rejects_malformed_path_segments_holder(kind):
    item = _slice(kind)
    item.path_segments = "not a generated PathSegments holder"

    with pytest.raises(TgiError) as error:
        api.getSlicePathSegmentIDs(get_handle(item))
    assert error.value.fault_code == TgiFaultCode.INVALID_ID


@pytest.mark.parametrize("kind", [SliceType, PortSliceType])
def test_path_segments_round_trip_as_generated_xml_with_original_text(kind):
    item = _slice(kind, ['"a & b"', "PATH_NAME", "PATH_NAME", '{"u.", "sig[3]"}'])
    if kind is SliceType:
        wrapper = SlicedAccessHandle(slices=SlicesType(slice=[item]))
        wrapper_type = SlicedAccessHandle
    else:
        wrapper = PortAccessHandle(slices=PortSlicesType(slice=[item]))
        wrapper_type = PortAccessHandle

    rendered = XmlDocument.serializer().render(wrapper)
    assert rendered.count("pathSegment") >= 3
    assert "PATH_NAME" in rendered
    assert "a &amp; b" in rendered
    parsed = XmlDocument.parser().from_string(rendered, wrapper_type)
    parsed_slice = parsed.slices.slice[0]
    assert parsed_slice == item
    segment_ids = api.getSlicePathSegmentIDs(get_handle(parsed_slice))
    assert [resolve_handle(segment_id).value for segment_id in segment_ids] == [
        '"a & b"',
        "PATH_NAME",
        "PATH_NAME",
        '{"u.", "sig[3]"}',
    ]


def test_parsed_location_slice_ownership_is_discovered_before_removal():
    first = _slice(SliceType, ["first.path"])
    second = _slice(SliceType, ["second.path"])
    parsed = XmlDocument.parser().from_string(
        XmlDocument.serializer().render(SlicesType(slice=[first, second])), SlicesType
    )
    location_id = get_handle(parsed)
    assert registry.register(parsed, ("test", "slices", "parsed-root", "1"))

    first, second = parsed.slice
    first_id, second_id = get_handle(first), get_handle(second)
    first_segment_id = get_handle(first.path_segments.path_segment[0])
    assert get_parent_info(first_id) is None

    assert api.removeLocationSlice(first_id)
    assert parsed.slice == [second]
    assert resolve_handle(first_id) is None
    assert resolve_handle(first_segment_id) is None
    assert resolve_handle(second_id) is not None
    assert api.getLocationSliceIDs(location_id) == [second_id]


@pytest.mark.parametrize("kind", [SliceType, PortSliceType])
def test_path_segment_add_and_remove_normalize_tuple_holders(kind):
    item = _slice(kind, ["first", "second"])
    first, second = item.path_segments.path_segment
    item.path_segments.path_segment = (first, second)
    slice_id = get_handle(item)

    first_id = get_handle(first)
    second_id = get_handle(second)
    added_id = api.addSlicePathSegment(slice_id, '"third"')
    assert isinstance(item.path_segments.path_segment, list)
    assert api.getSlicePathSegmentIDs(slice_id) == [first_id, second_id, added_id]

    item.path_segments.path_segment = tuple(item.path_segments.path_segment)
    assert api.removeSlicePathSegment(first_id)
    assert isinstance(item.path_segments.path_segment, list)
    assert item.path_segments.path_segment == [second, resolve_handle(added_id)]
    assert resolve_handle(second_id) is second


def test_location_slice_removal_normalizes_tuple_to_empty_list():
    first = _slice(SliceType, ['"first"'])
    second = _slice(SliceType, ['"second"'])
    location = SlicesType(slice=(first, second))
    location_id = get_handle(location)

    first_id, second_id = api.getLocationSliceIDs(location_id)
    assert isinstance(location.slice, tuple)
    assert api.removeLocationSlice(first_id)

    assert location.slice == [second]
    assert isinstance(location.slice, list)
    assert resolve_handle(first_id) is None
    assert resolve_handle(second_id) is second
    assert api.removeLocationSlice(second_id)
    assert location.slice == []


@pytest.mark.parametrize("kind", [SliceType, PortSliceType])
def test_removing_last_path_segment_keeps_required_holder_and_empty_list(kind):
    item = _slice(kind, ["only"])
    slice_id = get_handle(item)
    holder = item.path_segments
    segment_id = api.getSlicePathSegmentIDs(slice_id)[0]

    assert api.removeSlicePathSegment(segment_id)

    assert item.path_segments is holder
    assert holder.path_segment == []
    assert api.getSlicePathSegmentIDs(slice_id) == []
    assert resolve_handle(segment_id) is None
    assert resolve_handle(slice_id) is item


@pytest.mark.parametrize("kind", [SliceType, PortSliceType])
def test_path_segment_removal_rejects_foreign_and_orphan_handles(kind):
    item = _slice(kind, ["owned"])
    segment_id = api.getSlicePathSegmentIDs(get_handle(item))[0]
    unrelated = get_handle(Left(value="1"))
    orphan = get_handle(PathSegmentType(value="orphan"))

    for invalid_id in ("missing-segment", unrelated, orphan):
        with pytest.raises(TgiError) as error:
            api.removeSlicePathSegment(invalid_id)
        assert error.value.fault_code == TgiFaultCode.INVALID_ID

    assert resolve_handle(segment_id) is not None
    assert item.path_segments.path_segment == [resolve_handle(segment_id)]


def test_location_slice_getter_and_remover_validate_location_and_slice_types():
    location = SlicesType(slice=[_slice(SliceType, ["valid"])])
    location_id = get_handle(location)
    slice_id = api.getLocationSliceIDs(location_id)[0]
    wrong_id = get_handle(Left(value="1"))
    port_slice_id = get_handle(_slice(PortSliceType, ["not a location slice"]))

    with pytest.raises(TgiError) as error:
        api.getLocationSliceIDs(wrong_id)
    assert error.value.fault_code == TgiFaultCode.INVALID_ID
    with pytest.raises(TgiError) as error:
        api.removeLocationSlice(wrong_id)
    assert error.value.fault_code == TgiFaultCode.INVALID_ID
    with pytest.raises(TgiError) as error:
        api.removeLocationSlice(port_slice_id)
    assert error.value.fault_code == TgiFaultCode.INVALID_ID

    assert api.removeLocationSlice(slice_id)
    assert location.slice == []
    assert api.getLocationSliceIDs(location_id) == []
    assert resolve_handle(location_id) is location


def test_remove_location_slice_rejects_orphan_slice_handle():
    orphan = _slice(SliceType, ["orphan"])

    with pytest.raises(TgiError) as error:
        api.removeLocationSlice(get_handle(orphan))

    assert error.value.fault_code == TgiFaultCode.INVALID_ID
    assert orphan.path_segments.path_segment[0].value == "orphan"


def test_slice_path_and_location_operations_have_exported_native_signatures():
    expected = {
        "getSlicePathSegmentIDs": (("sliceID",), list[str]),
        "addSlicePathSegment": (("sliceID", "pathSegmentValue"), str),
        "removeSlicePathSegment": (("pathSegmentID",), bool),
        "getLocationSliceIDs": (("locationID",), list[str]),
        "removeLocationSlice": (("sliceID",), bool),
    }
    assert set(expected) <= set(api.__all__)
    for name, (parameter_names, return_type) in expected.items():
        signature = inspect.signature(getattr(api, name))
        assert tuple(signature.parameters) == parameter_names
        assert all(parameter.annotation is str for parameter in signature.parameters.values())
        assert all(not isinstance(parameter.annotation, str) for parameter in signature.parameters.values())
        assert signature.return_annotation == return_type

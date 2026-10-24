"""Field-slice ranges preserve source expressions and generated ownership."""

import inspect
from collections.abc import Iterator, Sequence
from typing import cast

import pytest
from lxml import etree

from amal.eda.accellera.ipxact.v1685_2022 import tgi
from amal.eda.accellera.ipxact.v1685_2022.tgi import miscellaneous as misc_api
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
    AddressBlockRef,
    AddressSpaces,
    Component,
    ComponentPortDirectionType,
    ComponentType,
    FieldMap,
    FieldMaps,
    FieldRef,
    Left,
    Model,
    Port,
    PortWireType,
    Range,
    RegisterRef,
    Right,
    SliceType,
    UnsignedPositiveIntExpression,
    UnsignedPositiveLongintExpression,
)
from org.accellera.ipxact.v1685_2022.path_segment_type import PathSegmentType

_SCHEMA = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))
_ModeFieldSlice = ComponentType.Modes.Mode.FieldSlice
_MapFieldSlice = FieldMap.FieldSlice
_Mode = ComponentType.Modes.Mode
_ModePortSlice = _Mode.PortSlice
_FieldSlice = _ModeFieldSlice | _MapFieldSlice
_FieldSliceType = type[_ModeFieldSlice] | type[_MapFieldSlice]


@pytest.fixture(autouse=True)
def clean_registry() -> Iterator[None]:
    registry.clear()
    yield
    registry.clear()


def _field_slice(kind: _FieldSliceType, range_node: Range | None = None) -> _FieldSlice:
    if kind is _ModeFieldSlice:
        return _ModeFieldSlice(
            name="control_enable",
            address_space_ref_or_memory_map_ref_or_memory_remap_ref=[
                _ModeFieldSlice.AddressSpaceRef(address_space_ref="register_space")
            ],
            address_block_ref=AddressBlockRef(address_block_ref="registers"),
            register_ref=RegisterRef(register_ref="control"),
            field_ref=FieldRef(field_ref="enable"),
            range=range_node,
        )
    return _MapFieldSlice(
        address_space_ref_or_memory_map_ref_or_memory_remap_ref=[
            _MapFieldSlice.AddressSpaceRef(address_space_ref="register_space")
        ],
        address_block_ref=AddressBlockRef(address_block_ref="registers"),
        register_ref=RegisterRef(register_ref="control"),
        field_ref=FieldRef(field_ref="enable"),
        range=range_node,
    )


def _component(mode_field_slice: _ModeFieldSlice | None = None, field_map: FieldMap | None = None) -> Component:
    port = Port(
        name="data_i",
        wire_or_transactional_or_structured=PortWireType(direction=ComponentPortDirectionType.IN),
    )
    if field_map is not None:
        port.field_maps = FieldMaps(field_map=[field_map])
    modes = None
    if mode_field_slice is not None:
        modes = ComponentType.Modes(mode=[_Mode(name="active", field_slice=[mode_field_slice])])
    return Component(
        vendor="acme",
        library="devices",
        name="field_slice_component",
        version="1.0",
        model=Model(ports=Model.Ports(port=[port])),
        modes=modes,
        address_spaces=AddressSpaces(
            address_space=[
                AddressSpaces.AddressSpace(
                    name="register_space",
                    range=UnsignedPositiveLongintExpression(value="4096"),
                    width=UnsignedPositiveIntExpression(value="32"),
                )
            ]
        ),
    )


def _round_trip(root: Component) -> Component:
    xml = XmlDocument.serializer().render(root)
    tree = etree.fromstring(xml.encode())
    assert _SCHEMA.validate(tree), _SCHEMA.error_log
    parsed = XmlDocument.parser().from_string(xml, Component)
    assert XmlDocument.serializer().render(parsed) == xml
    return parsed


@pytest.mark.parametrize("kind", [_ModeFieldSlice, _MapFieldSlice], ids=["mode", "field-map"])
def test_field_slice_range_getters_preserve_original_sources_and_endpoint_ownership(
    kind: _FieldSliceType,
) -> None:
    range_node = Range(
        left=Left(value="8'h0f", minimum=0, maximum=15, other_attributes={"{urn:test}side": "left"}),
        right=Right(value="WIDTH - 1", minimum=0, maximum=31, other_attributes={"{urn:test}side": "right"}),
    )
    item = _field_slice(kind, range_node)
    field_slice_id = get_handle(item)

    assert api.getFieldSliceRange(field_slice_id) == ("8'h0f", "WIDTH - 1")
    left_id = api.getFieldSliceRangeLeftID(field_slice_id)
    right_id = api.getFieldSliceRangeRightID(field_slice_id)
    assert left_id is not None and right_id is not None
    assert api.getFieldSliceRangeLeftID(field_slice_id) == left_id
    assert api.getFieldSliceRangeRightID(field_slice_id) == right_id
    assert resolve_handle(left_id) is range_node.left
    assert resolve_handle(right_id) is range_node.right

    range_info = get_parent_info(get_handle(range_node))
    left_info = get_parent_info(left_id)
    right_info = get_parent_info(right_id)
    assert range_info is not None and range_info.parent_handle == field_slice_id and range_info.path == ("range",)
    assert left_info is not None and left_info.parent_handle == get_handle(range_node) and left_info.path == ("left",)
    assert (
        right_info is not None and right_info.parent_handle == get_handle(range_node) and right_info.path == ("right",)
    )

    assert misc_api.getExpressionIntValue(left_id) == 15
    with pytest.raises(TgiError):
        misc_api.getExpressionIntValue(right_id)


@pytest.mark.parametrize("kind", [_ModeFieldSlice, _MapFieldSlice], ids=["mode", "field-map"])
def test_field_slice_range_getters_return_neutral_values_for_absent_range_or_endpoint(
    kind: _FieldSliceType,
) -> None:
    item = _field_slice(kind)
    field_slice_id = get_handle(item)

    assert api.getFieldSliceRange(field_slice_id) == (None, None)
    assert api.getFieldSliceRangeLeftID(field_slice_id) is None
    assert api.getFieldSliceRangeRightID(field_slice_id) is None

    item.range = Range(left=None, right=Right(value="7"))  # type: ignore[arg-type]
    assert api.getFieldSliceRange(field_slice_id) == (None, "7")
    assert api.getFieldSliceRangeLeftID(field_slice_id) is None
    assert api.getFieldSliceRangeRightID(field_slice_id) is not None


@pytest.mark.parametrize("kind", [_ModeFieldSlice, _MapFieldSlice], ids=["mode", "field-map"])
def test_field_slice_range_setter_creates_generated_endpoints_and_preserves_existing_identity(
    kind: _FieldSliceType,
) -> None:
    item = _field_slice(kind)
    field_slice_id = get_handle(item)
    assert api.setFieldSliceRange(field_slice_id, ["7", "0"])

    range_node = item.range
    assert isinstance(range_node, Range)
    assert isinstance(range_node.left, Left)
    assert isinstance(range_node.right, Right)
    assert api.getFieldSliceRange(field_slice_id) == ("7", "0")
    range_id = get_handle(range_node)
    left_id = api.getFieldSliceRangeLeftID(field_slice_id)
    right_id = api.getFieldSliceRangeRightID(field_slice_id)
    assert left_id is not None and right_id is not None

    range_node.left.minimum = 0
    range_node.left.maximum = 15
    range_node.left.other_attributes = {"{urn:test}label": "left bound"}
    range_node.right.minimum = 0
    range_node.right.maximum = 15
    range_node.right.other_attributes = {"{urn:test}label": "right bound"}
    left_node, right_node = range_node.left, range_node.right

    assert api.setFieldSliceRange(field_slice_id, ["8'hf", "(2 + 2)"])
    assert item.range is range_node
    assert api.getFieldSliceRange(field_slice_id) == ("8'hf", "(2 + 2)")
    assert api.getFieldSliceRangeLeftID(field_slice_id) == left_id
    assert api.getFieldSliceRangeRightID(field_slice_id) == right_id
    assert resolve_handle(range_id) is range_node
    assert resolve_handle(left_id) is left_node
    assert resolve_handle(right_id) is right_node
    assert (left_node.minimum, left_node.maximum) == (0, 15)
    assert (right_node.minimum, right_node.maximum) == (0, 15)
    assert left_node.other_attributes == {"{urn:test}label": "left bound"}
    assert right_node.other_attributes == {"{urn:test}label": "right bound"}


@pytest.mark.parametrize("kind", [_ModeFieldSlice, _MapFieldSlice], ids=["mode", "field-map"])
def test_field_slice_setter_keeps_unresolved_symbols_and_parser_sized_truncation(
    kind: _FieldSliceType,
) -> None:
    item = _field_slice(kind)
    field_slice_id = get_handle(item)

    assert api.setFieldSliceRange(field_slice_id, ["DATA_WIDTH", "32'h1_0000_0000"])
    assert api.getFieldSliceRange(field_slice_id) == ("DATA_WIDTH", "32'h1_0000_0000")
    left_id = api.getFieldSliceRangeLeftID(field_slice_id)
    right_id = api.getFieldSliceRangeRightID(field_slice_id)
    assert left_id is not None and right_id is not None
    with pytest.raises(TgiError):
        misc_api.getExpressionIntValue(left_id)
    assert misc_api.getExpressionIntValue(right_id) == 0


@pytest.mark.parametrize("kind", [_ModeFieldSlice, _MapFieldSlice], ids=["mode", "field-map"])
def test_field_slice_setter_rejects_invalid_sources_atomically(kind: _FieldSliceType) -> None:
    range_node = Range(
        left=Left(value="7", minimum=0, maximum=7, other_attributes={"{urn:test}keep": "left"}),
        right=Right(value="0", minimum=0, maximum=7, other_attributes={"{urn:test}keep": "right"}),
    )
    item = _field_slice(kind, range_node)
    field_slice_id = get_handle(item)
    original_endpoints = (range_node.left, range_node.right)
    original_ids = (get_handle(range_node.left), get_handle(range_node.right))
    invalid_sources: tuple[object, ...] = (
        ["1"],
        ["1", "2", "3"],
        "7:0",
        None,
        [1, "0"],
        ["1.5", "0"],
        ["(", "0"],
        ["4", "("],
        ["4'bx001", "0"],
        ["33'd4294967296", "0"],
        ["8", "0"],
    )

    for invalid in invalid_sources:
        with pytest.raises(TgiError) as error:
            api.setFieldSliceRange(field_slice_id, cast(Sequence[str], invalid))
        assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
        assert item.range is range_node
        assert (range_node.left, range_node.right) == original_endpoints
        assert (range_node.left.value, range_node.right.value) == ("7", "0")
        assert (get_handle(range_node.left), get_handle(range_node.right)) == original_ids

    range_node.left.minimum = 8
    range_node.left.maximum = 7
    with pytest.raises(TgiError) as error:
        api.setFieldSliceRange(field_slice_id, ["6", "1"])
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert (range_node.left.value, range_node.right.value) == ("7", "0")


@pytest.mark.parametrize("kind", [_ModeFieldSlice, _MapFieldSlice], ids=["mode", "field-map"])
def test_field_slice_range_rejects_malformed_generated_range_or_endpoint(kind: _FieldSliceType) -> None:
    malformed_ranges = (
        Range(left="not-a-Left", right=Right(value="0")),
        Range(left=Left(value="7"), right="not-a-Right"),
    )
    for malformed in malformed_ranges:
        item = _field_slice(kind, malformed)
        field_slice_id = get_handle(item)
        with pytest.raises(TgiError) as error:
            api.getFieldSliceRange(field_slice_id)
        assert error.value.fault_code == TgiFaultCode.INVALID_ID
        with pytest.raises(TgiError) as error:
            api.setFieldSliceRange(field_slice_id, ["3", "0"])
        assert error.value.fault_code == TgiFaultCode.INVALID_ID
        assert item.range is malformed


@pytest.mark.parametrize("kind", [_ModeFieldSlice, _MapFieldSlice], ids=["mode", "field-map"])
def test_field_slice_range_removal_uses_owner_and_invalidates_only_range_subtree(kind: _FieldSliceType) -> None:
    item = _field_slice(kind, Range(left=Left(value="3"), right=Right(value="0")))
    field_slice_id = get_handle(item)
    range_node = item.range
    assert isinstance(range_node, Range)
    range_id = get_handle(range_node)
    left_id = api.getFieldSliceRangeLeftID(field_slice_id)
    right_id = api.getFieldSliceRangeRightID(field_slice_id)
    address_block_ref_id = get_handle(item.address_block_ref)
    register_ref_id = get_handle(item.register_ref)
    field_ref_id = get_handle(item.field_ref)
    assert left_id is not None and right_id is not None

    with pytest.raises(TgiError) as error:
        api.removeFieldSliceRange(range_id)
    assert error.value.fault_code == TgiFaultCode.INVALID_ID
    assert item.range is range_node

    assert api.removeFieldSliceRange(field_slice_id)
    assert item.range is None
    assert resolve_handle(field_slice_id) is item
    assert resolve_handle(range_id) is None
    assert resolve_handle(left_id) is None
    assert resolve_handle(right_id) is None
    assert resolve_handle(address_block_ref_id) is item.address_block_ref
    assert resolve_handle(register_ref_id) is item.register_ref
    assert resolve_handle(field_ref_id) is item.field_ref
    assert api.getFieldSliceRange(field_slice_id) == (None, None)
    assert api.removeFieldSliceRange(field_slice_id) is False


def test_field_slice_range_exports_and_native_signatures_match_tgi_contract() -> None:
    expected: dict[str, tuple[tuple[str, ...], tuple[object, ...], object]] = {
        "getFieldSliceRange": (("fieldSliceID",), (str,), tuple[str | None, str | None]),
        "getFieldSliceRangeLeftID": (("fieldSliceID",), (str,), str | None),
        "getFieldSliceRangeRightID": (("fieldSliceID",), (str,), str | None),
        "setFieldSliceRange": (("fieldSliceID", "range"), (str, Sequence[str]), bool),
        "removeFieldSliceRange": (("fieldSliceID",), (str,), bool),
    }
    assert set(expected) <= set(api.__all__)
    for name, (parameter_names, parameter_types, return_type) in expected.items():
        function = getattr(api, name)
        assert getattr(tgi, name) is function
        signature = inspect.signature(function)
        assert tuple(signature.parameters) == parameter_names
        assert tuple(parameter.annotation for parameter in signature.parameters.values()) == parameter_types
        assert all(not isinstance(parameter.annotation, str) for parameter in signature.parameters.values())
        assert signature.return_annotation == return_type


@pytest.mark.parametrize("kind", [_ModeFieldSlice, _MapFieldSlice], ids=["mode", "field-map"])
def test_field_slice_range_operations_reject_wrong_model_handles(kind: _FieldSliceType) -> None:
    field_slice_id = get_handle(_field_slice(kind))
    foreign_ids = (
        get_handle(Left(value="7")),
        get_handle(SliceType(path_segments=SliceType.PathSegments(path_segment=[PathSegmentType(value="sig")]))),
        get_handle(_ModePortSlice(name="data_slice", port_ref=_ModePortSlice.PortRef(port_ref="data_i"))),
        "missing-field-slice",
    )

    for invalid_id in foreign_ids:
        for getter in (api.getFieldSliceRange, api.getFieldSliceRangeLeftID, api.getFieldSliceRangeRightID):
            with pytest.raises(TgiError) as error:
                getter(invalid_id)
            assert error.value.fault_code == TgiFaultCode.INVALID_ID
        with pytest.raises(TgiError) as error:
            api.setFieldSliceRange(invalid_id, ["3", "0"])
        assert error.value.fault_code == TgiFaultCode.INVALID_ID
        with pytest.raises(TgiError) as error:
            api.removeFieldSliceRange(invalid_id)
        assert error.value.fault_code == TgiFaultCode.INVALID_ID

    assert resolve_handle(field_slice_id) is not None


@pytest.mark.parametrize("kind", [_ModeFieldSlice, _MapFieldSlice], ids=["mode", "field-map"])
def test_field_slice_ranges_round_trip_in_schema_valid_component_documents(kind: _FieldSliceType) -> None:
    item = _field_slice(kind, Range(left=Left(value="8'h0f"), right=Right(value="WIDTH - 1")))
    if kind is _ModeFieldSlice:
        root = _component(mode_field_slice=cast(_ModeFieldSlice, item))
    else:
        root = _component(field_map=FieldMap(field_slice=cast(_MapFieldSlice, item)))

    parsed = _round_trip(root)
    if kind is _ModeFieldSlice:
        parsed_slice = parsed.modes.mode[0].field_slice[0]
    else:
        parsed_slice = parsed.model.ports.port[0].field_maps.field_map[0].field_slice
    field_slice_id = get_handle(parsed_slice)
    assert api.getFieldSliceRange(field_slice_id) == ("8'h0f", "WIDTH - 1")
    assert api.getFieldSliceRangeLeftID(field_slice_id) == get_handle(parsed_slice.range.left)
    assert api.getFieldSliceRangeRightID(field_slice_id) == get_handle(parsed_slice.range.right)


@pytest.mark.parametrize("kind", [_ModeFieldSlice, _MapFieldSlice], ids=["mode", "field-map"])
def test_parsed_field_slice_range_removal_invalidates_endpoints_without_prior_getters(
    kind: _FieldSliceType,
) -> None:
    item = _field_slice(kind, Range(left=Left(value="7"), right=Right(value="0")))
    if kind is _ModeFieldSlice:
        root = _round_trip(_component(mode_field_slice=cast(_ModeFieldSlice, item)))
        parsed_slice = root.modes.mode[0].field_slice[0]
    else:
        root = _round_trip(_component(field_map=FieldMap(field_slice=cast(_MapFieldSlice, item))))
        parsed_slice = root.model.ports.port[0].field_maps.field_map[0].field_slice

    range_node = parsed_slice.range
    range_id = get_handle(range_node)
    left_id = get_handle(range_node.left)
    right_id = get_handle(range_node.right)
    field_slice_id = get_handle(parsed_slice)

    assert api.removeFieldSliceRange(field_slice_id)
    assert parsed_slice.range is None
    assert resolve_handle(range_id) is None
    assert resolve_handle(left_id) is None
    assert resolve_handle(right_id) is None
    assert resolve_handle(field_slice_id) is parsed_slice

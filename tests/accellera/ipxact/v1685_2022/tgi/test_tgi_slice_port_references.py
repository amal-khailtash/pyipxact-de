"""Mode port-slice references preserve generated model ownership and XML semantics."""

import inspect
from collections.abc import Iterator, Sequence

import pytest
from lxml import etree

from amal.eda.accellera.ipxact.v1685_2022 import tgi
from amal.eda.accellera.ipxact.v1685_2022.tgi import _miscellaneous_part_select as part_select_api
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
    Component,
    ComponentPortDirectionType,
    ComponentType,
    Index,
    Indices,
    Left,
    Model,
    PartSelect,
    Port,
    PortWireType,
    Range,
    Right,
    SubPortReference,
)

_SCHEMA = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))
_PortSlice = ComponentType.Modes.Mode.PortSlice
_PortRef = _PortSlice.PortRef
_Mode = ComponentType.Modes.Mode


@pytest.fixture(autouse=True)
def clean_registry() -> Iterator[None]:
    registry.clear()
    yield
    registry.clear()


def _range(left: str, right: str) -> Range:
    return Range(left=Left(value=left), right=Right(value=right))


def _component(port_slice: _PortSlice) -> Component:
    return Component(
        vendor="acme",
        library="devices",
        name="slice_component",
        version="1.0",
        model=Model(
            ports=Model.Ports(
                port=[
                    Port(
                        name="data_i",
                        wire_or_transactional_or_structured=PortWireType(direction=ComponentPortDirectionType.IN),
                    )
                ]
            )
        ),
        modes=ComponentType.Modes(mode=[_Mode(name="active", port_slice=[port_slice])]),
    )


def _round_trip(root: Component) -> Component:
    xml = XmlDocument.serializer().render(root)
    tree = etree.fromstring(xml.encode())
    assert _SCHEMA.validate(tree), _SCHEMA.error_log
    parsed = XmlDocument.parser().from_string(xml, Component)
    assert XmlDocument.serializer().render(parsed) == xml
    return parsed


def _port_slice(
    *,
    port_ref: str = "data_i",
    sub_refs: Sequence[SubPortReference] = (),
    selection: PartSelect | None = None,
) -> _PortSlice:
    return _PortSlice(
        name="payload",
        port_ref=_PortRef(port_ref=port_ref),
        sub_port_reference=sub_refs,
        part_select=selection,
        id="port-slice-id",
    )


def _attach(root: Component, vlnv: tuple[str, str, str, str] = ("acme", "devices", "slice_component", "1.0")) -> None:
    registry.register(root, vlnv)


def _slice_id(root: Component) -> str:
    return get_handle(root.modes.mode[0].port_slice[0])


def test_exports_and_native_signatures_match_the_tgi_contract() -> None:
    expected = {
        "getPortSlicePartSelectID": ("portSliceID", str, str | None),
        "getPortSlicePortRefByName": ("portSliceID", str, str),
        "getPortSliceSubPortReferenceIDs": ("portSliceID", str, list[str]),
        "setPortSlicePortRef": (("portSliceID", "portRef"), (str, str), bool),
        "addPortSliceSubPortReference": (("portSliceID", "subPortRef"), (str, str), str),
        "removePortSliceSubPortReference": ("subPortReferenceID", str, bool),
        "removePortSlicePartSelect": ("portSliceID", str, bool),
    }
    for name, (arguments, argument_types, return_type) in expected.items():
        function = getattr(api, name)
        assert getattr(tgi, name) is function
        signature = inspect.signature(function)
        if isinstance(arguments, str):
            arguments, argument_types = (arguments,), (argument_types,)
        assert list(signature.parameters) == list(arguments)
        assert tuple(parameter.annotation for parameter in signature.parameters.values()) == tuple(argument_types)
        assert signature.return_annotation == return_type

    function = api.setPortSlicePartSelect
    assert tgi.setPortSlicePartSelect is function
    signature = inspect.signature(function)
    assert list(signature.parameters) == ["portSliceID", "range", "indices"]
    assert signature.parameters["portSliceID"].annotation is str
    assert signature.parameters["range"].annotation == Sequence[str] | None
    assert signature.parameters["indices"].annotation == Sequence[str] | None
    assert signature.return_annotation is bool


def test_port_slice_getters_return_reference_names_and_stable_child_handles() -> None:
    first = SubPortReference(sub_port_ref="payload.data")
    second = SubPortReference(sub_port_ref="payload.data")
    item = _port_slice(sub_refs=[first, second], selection=PartSelect(range_or_indices=[_range("7", "0")]))
    slice_id = get_handle(item)

    selection_id = api.getPortSlicePartSelectID(slice_id)
    assert selection_id == get_handle(item.part_select)
    assert api.getPortSlicePortRefByName(slice_id) == "data_i"
    assert api.getPortSliceSubPortReferenceIDs(slice_id) == ["payload.data", "payload.data"]
    assert api.getPortSliceSubPortReferenceIDs(slice_id) == ["payload.data", "payload.data"]
    assert api.getPortSlicePartSelectID(get_handle(_port_slice())) is None

    with pytest.raises(TgiError) as error:
        api.getPortSliceSubPortReferenceIDs(get_handle(Left(value="0")))
    assert error.value.fault_code == TgiFaultCode.INVALID_ID


def test_reference_mutations_use_generated_nodes_normalize_names_and_keep_wrapper_identity() -> None:
    initial_ref = _PortRef(port_ref="data_i")
    first = SubPortReference(sub_port_ref="payload")
    item = _port_slice(sub_refs=(first,), port_ref=initial_ref.port_ref)
    item.port_ref = initial_ref
    root = _component(item)
    _attach(root)
    slice_id = _slice_id(root)
    initial_ref_id = get_handle(initial_ref)
    item.id = "stable-port-slice"

    assert api.setPortSlicePortRef(slice_id, " \tdata_i\r\n")
    assert item.port_ref is initial_ref
    assert get_handle(item.port_ref) == initial_ref_id
    assert item.port_ref.port_ref == "data_i"
    assert item.id == "stable-port-slice"

    first_id = get_handle(first)
    assert api.addPortSliceSubPortReference(slice_id, " \tpayload.data\r\n") == get_handle(item.sub_port_reference[1])
    assert isinstance(item.sub_port_reference, list)
    assert item.sub_port_reference == [first, resolve_handle(get_handle(item.sub_port_reference[1]))]
    assert resolve_handle(first_id) is first
    assert [ref.sub_port_ref for ref in item.sub_port_reference] == ["payload", "payload.data"]
    parent = get_parent_info(get_handle(item.sub_port_reference[1]))
    assert parent is not None and parent.parent_handle == slice_id and parent.path == ("sub_port_reference",)
    _round_trip(root)


@pytest.mark.parametrize("value", [None, 0, "", " \t\r\n", "bad name", "control\x01char"])
def test_reference_mutators_reject_invalid_names_atomically(value: str | int | None) -> None:
    existing = SubPortReference(sub_port_ref="kept")
    item = _port_slice(sub_refs=[existing])
    slice_id = get_handle(item)
    ref = item.port_ref
    refs = list(item.sub_port_reference)

    with pytest.raises(TgiError) as error:
        api.setPortSlicePortRef(slice_id, value)
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert item.port_ref is ref
    assert item.port_ref.port_ref == "data_i"

    with pytest.raises(TgiError) as error:
        api.addPortSliceSubPortReference(slice_id, value)
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert item.sub_port_reference == refs

    with pytest.raises(TgiError) as error:
        api.setPortSlicePortRef("missing-port-slice", "valid_name")
    assert error.value.fault_code == TgiFaultCode.INVALID_ID


@pytest.mark.parametrize("parsed", [False, True], ids=["in-memory", "parsed-root"])
def test_sub_port_reference_removal_discovers_registered_root_and_invalidates_only_its_subtree(parsed: bool) -> None:
    first = SubPortReference(
        sub_port_ref="payload.first",
        id="remove-ref",
        part_select=PartSelect(range_or_indices=[_range("7", "0")]),
    )
    second = SubPortReference(sub_port_ref="payload.second", id="keep-ref")
    item = _port_slice(sub_refs=[first, second], selection=PartSelect(range_or_indices=[_range("15", "8")]))
    root = _component(item)
    if parsed:
        root = _round_trip(root)
    _attach(root)
    item = root.modes.mode[0].port_slice[0]
    first, second = item.sub_port_reference
    first_id = get_handle(first)
    removed_selection_id = get_handle(first.part_select)
    removed_parts = first.part_select.range_or_indices
    if not isinstance(removed_parts, (list, tuple)):
        removed_parts = [removed_parts]
    removed_range = next(child for child in removed_parts if isinstance(child, Range))
    removed_endpoint_id = get_handle(removed_range.left)
    second_id = get_handle(second)
    slice_id = _slice_id(root)
    retained_selection_id = get_handle(item.part_select)

    assert get_parent_info(first_id) is None
    assert api.removePortSliceSubPortReference(first_id)

    assert item.sub_port_reference == [second]
    assert isinstance(item.sub_port_reference, list)
    assert resolve_handle(first_id) is None
    assert resolve_handle(removed_selection_id) is None
    assert resolve_handle(removed_endpoint_id) is None
    assert resolve_handle(second_id) is second
    assert resolve_handle(slice_id) is item
    assert resolve_handle(retained_selection_id) is item.part_select
    assert api.getPortSliceSubPortReferenceIDs(slice_id) == ["payload.second"]
    _round_trip(root)


def test_sub_reference_mutation_normalizes_tuple_storage_and_removes_last_child() -> None:
    first = SubPortReference(sub_port_ref="payload.first")
    item = _port_slice(sub_refs=(first,))
    slice_id = get_handle(item)
    first_id = get_handle(first)
    added_id = api.addPortSliceSubPortReference(slice_id, "payload.second")
    assert isinstance(item.sub_port_reference, list)
    assert api.getPortSliceSubPortReferenceIDs(slice_id) == ["payload.first", "payload.second"]

    item.sub_port_reference = tuple(item.sub_port_reference)
    assert api.removePortSliceSubPortReference(first_id)
    assert isinstance(item.sub_port_reference, list)
    assert item.sub_port_reference == [resolve_handle(added_id)]
    assert resolve_handle(first_id) is None
    assert resolve_handle(added_id) is item.sub_port_reference[0]
    assert api.removePortSliceSubPortReference(added_id)
    assert item.sub_port_reference == []
    assert api.getPortSliceSubPortReferenceIDs(slice_id) == []


def test_part_select_set_preserves_wrappers_metadata_order_and_invalidates_removed_descendants() -> None:
    first_index = Index(value="3", id="kept-index")
    extra_index = Index(value="2", id="removed-index")
    indices = Indices(index=[first_index, extra_index])
    range_node = _range("7", "0")
    range_node.left.minimum = 0
    range_node.left.maximum = 15
    range_node.right.minimum = 0
    range_node.right.maximum = 15
    range_node.left.other_attributes = {"{urn:test}bound": "left"}
    selection = PartSelect(range_or_indices=(indices, range_node), id="kept-selection")
    item = _port_slice(selection=selection)
    slice_id = get_handle(item)
    selection_id = get_handle(selection)
    indices_id = get_handle(indices)
    range_id = get_handle(range_node)
    first_id = get_handle(first_index)
    extra_id = get_handle(extra_index)
    left_id = get_handle(range_node.left)
    right_id = get_handle(range_node.right)

    assert api.setPortSlicePartSelect(slice_id, ("15", "8"), ("4",))

    assert item.part_select is selection
    assert get_handle(item.part_select) == selection_id
    assert selection.id == "kept-selection"
    assert isinstance(selection.range_or_indices, list)
    assert selection.range_or_indices == [indices, range_node]
    assert range_node.left.other_attributes == {"{urn:test}bound": "left"}
    assert indices.index == [first_index]
    assert first_index.value == "4"
    assert resolve_handle(indices_id) is indices
    assert resolve_handle(range_id) is range_node
    assert resolve_handle(first_id) is first_index
    assert resolve_handle(extra_id) is None
    assert resolve_handle(left_id) is range_node.left
    assert resolve_handle(right_id) is range_node.right
    assert part_select_api.getPartSelectRangeExpression(selection_id) == ["15", "8"]
    assert part_select_api.getPartSelectIndicesExpression(selection_id) == ["4"]

    assert api.setPortSlicePartSelect(slice_id, None, ["LANE + 1", "WIDTH - 1"])
    assert selection.range_or_indices is indices
    assert resolve_handle(range_id) is None
    assert resolve_handle(left_id) is None
    assert resolve_handle(right_id) is None
    assert part_select_api.getPartSelectIndicesExpression(selection_id) == ["LANE + 1", "WIDTH - 1"]
    with pytest.raises(TgiError):
        part_select_api.getPartSelectIndices(selection_id)


@pytest.mark.parametrize(
    ("range_value", "indices_value"),
    [
        (("7",), None),
        (("7", "0", "1"), None),
        ("7:0", None),
        (("8'h0", object()), ("1",)),
        (("(", "0"), ("1",)),
        (("16", "0"), None),
        (None, None),
        (None, ()),
        (None, ("4294967296",)),
    ],
    ids=[
        "short-range",
        "long-range",
        "string-array",
        "non-string",
        "syntax",
        "bound",
        "empty",
        "empty-indices",
        "overflow",
    ],
)
def test_part_select_invalid_choices_fault_atomically(range_value: object, indices_value: object) -> None:
    bounded_range = _range("7", "0")
    bounded_range.left.minimum = 0
    bounded_range.left.maximum = 7
    bounded_range.right.minimum = 0
    bounded_range.right.maximum = 7
    selection = PartSelect(range_or_indices=[bounded_range, Indices(index=[Index(value="2")])], id="stable")
    item = _port_slice(selection=selection)
    slice_id = get_handle(item)
    before = list(selection.range_or_indices)
    before_ids = [get_handle(child) for child in before]

    with pytest.raises(TgiError) as error:
        api.setPortSlicePartSelect(slice_id, range_value, indices_value)
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert item.part_select is selection
    assert selection.range_or_indices == before
    assert [get_handle(child) for child in selection.range_or_indices] == before_ids


def test_part_select_numeric_bounds_and_symbolic_sources_follow_shared_part_select_rules() -> None:
    item = _port_slice()
    slice_id = get_handle(item)
    assert api.setPortSlicePartSelect(slice_id, ("WIDTH - 1", "0"), ("LANE + 1",))
    selection_id = api.getPortSlicePartSelectID(slice_id)
    assert selection_id is not None
    assert part_select_api.getPartSelectRangeExpression(selection_id) == ["WIDTH - 1", "0"]
    assert part_select_api.getPartSelectIndicesExpression(selection_id) == ["LANE + 1"]
    with pytest.raises(TgiError):
        part_select_api.getPartSelectRange(selection_id)
    with pytest.raises(TgiError):
        part_select_api.getPartSelectIndices(selection_id)


def test_part_select_rejects_reversed_existing_bounds_even_for_symbolic_sources() -> None:
    bounded_range = Range(left=Left(value="WIDTH", minimum=8, maximum=7), right=Right(value="0"))
    item = _port_slice(selection=PartSelect(range_or_indices=[bounded_range]))
    slice_id = get_handle(item)
    before = bounded_range.left.value

    with pytest.raises(TgiError) as error:
        api.setPortSlicePartSelect(slice_id, ("DATA_WIDTH - 1", "0"), None)
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert item.part_select.range_or_indices == [bounded_range]
    assert bounded_range.left.value == before


@pytest.mark.parametrize(
    "bad_index_collection", [None, 7, (Index(value="1"), object())], ids=["absent", "scalar", "invalid-child"]
)
def test_malformed_existing_sub_reference_and_indices_are_rejected_before_mutation(
    bad_index_collection: object,
) -> None:
    malformed_sub_ref = SubPortReference(sub_port_ref="valid")
    malformed_sub_ref.sub_port_ref = 42
    item = _port_slice(sub_refs=[malformed_sub_ref])
    slice_id = get_handle(item)
    original_refs = list(item.sub_port_reference)

    with pytest.raises(TgiError) as error:
        api.addPortSliceSubPortReference(slice_id, "payload.new")
    assert error.value.fault_code == TgiFaultCode.INVALID_ID
    assert item.sub_port_reference == original_refs

    malformed_indices = Indices(index=bad_index_collection)
    selection = PartSelect(range_or_indices=[malformed_indices])
    item.part_select = selection
    before = malformed_indices.index
    with pytest.raises(TgiError) as error:
        api.setPortSlicePartSelect(slice_id, ("3", "0"), ("2",))
    assert error.value.fault_code == TgiFaultCode.INVALID_ID
    assert item.part_select is selection
    assert malformed_indices.index is before or malformed_indices.index == before


def test_tuple_index_storage_is_normalized_when_part_select_is_mutated() -> None:
    first = Index(value="1")
    indices = Indices(index=(first,))
    item = _port_slice(selection=PartSelect(range_or_indices=[indices]))
    slice_id = get_handle(item)

    assert api.setPortSlicePartSelect(slice_id, None, ("2", "3"))

    assert isinstance(indices.index, list)
    assert [index.value for index in indices.index] == ["2", "3"]
    assert indices.index[0] is first


def test_part_select_removal_uses_port_slice_owner_and_invalidates_only_selection_subtree() -> None:
    selection = PartSelect(range_or_indices=[_range("7", "0"), Indices(index=[Index(value="1")])])
    sub_ref = SubPortReference(sub_port_ref="payload.data")
    item = _port_slice(selection=selection, sub_refs=[sub_ref])
    root = _component(item)
    _attach(root)
    slice_id = _slice_id(root)
    selection_id = get_handle(selection)
    range_id = get_handle(selection.range_or_indices[0])
    endpoint_id = get_handle(selection.range_or_indices[0].left)
    index_id = get_handle(selection.range_or_indices[1].index[0])
    sub_ref_id = get_handle(sub_ref)

    assert api.removePortSlicePartSelect(slice_id)
    assert item.part_select is None
    assert api.getPortSlicePartSelectID(slice_id) is None
    assert all(resolve_handle(handle) is None for handle in (selection_id, range_id, endpoint_id, index_id))
    assert resolve_handle(slice_id) is item
    assert resolve_handle(sub_ref_id) is sub_ref
    assert api.removePortSlicePartSelect(slice_id) is False
    _round_trip(root)


def test_port_slice_operations_reject_wrong_model_handles() -> None:
    other = Left(value="0")
    invalid_handle = get_handle(other)
    for call in (
        lambda: api.getPortSlicePartSelectID(invalid_handle),
        lambda: api.getPortSlicePortRefByName(invalid_handle),
        lambda: api.getPortSliceSubPortReferenceIDs(invalid_handle),
        lambda: api.setPortSlicePortRef(invalid_handle, "valid_name"),
        lambda: api.addPortSliceSubPortReference(invalid_handle, "valid_name"),
        lambda: api.setPortSlicePartSelect(invalid_handle, ("3", "0"), None),
        lambda: api.removePortSlicePartSelect(invalid_handle),
    ):
        with pytest.raises(TgiError) as error:
            call()
        assert error.value.fault_code == TgiFaultCode.INVALID_ID

    with pytest.raises(TgiError) as error:
        api.removePortSliceSubPortReference(invalid_handle)
    assert error.value.fault_code == TgiFaultCode.INVALID_ID

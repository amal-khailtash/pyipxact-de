"""Design ad-hoc port reference part-select TGI operations."""

import inspect
from collections.abc import Callable, Iterator, Sequence

import pytest
from lxml import etree

from amal.eda.accellera.ipxact.v1685_2022 import tgi
from amal.eda.accellera.ipxact.v1685_2022.tgi import _miscellaneous_part_select as part_select_api
from amal.eda.accellera.ipxact.v1685_2022.tgi import design as api
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
    AdHocConnection,
    AdHocConnections,
    ComponentInstance,
    ComponentInstances,
    ConfigurableLibraryRefType,
    Design,
    ExternalPortReference,
    Index,
    Indices,
    InstanceName,
    Left,
    PartSelect,
    Range,
    Right,
)

_SCHEMA = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))
_OWNER_IDS = ("external-port-reference", "internal-port-reference")
_OPERATIONS = {
    "external": (
        "getExternalPortReferencePartSelectID",
        "setExternalPortReferencePartSelect",
        "removeExternalPortReferencePartSelect",
    ),
    "internal": (
        "getInternalPortReferencePartSelectID",
        "setInternalPortReferencePartSelect",
        "removeInternalPortReferencePartSelect",
    ),
}


@pytest.fixture(autouse=True)
def clean_registry() -> Iterator[None]:
    registry.clear()
    yield
    registry.clear()


def _selection(selection_id: str = "retained-part-select") -> PartSelect:
    return PartSelect(
        range_or_indices=(
            Indices(
                index=[
                    Index(value="3", id=f"{selection_id}-retained-index"),
                    Index(value="5", id=f"{selection_id}-removed-index"),
                ]
            ),
            Range(
                left=Left(value="7", minimum=0, maximum=15, other_attributes={"{urn:test}marker": "left"}),
                right=Right(value="0", minimum=0, maximum=15),
            ),
        ),
        id=selection_id,
    )


def _design(external: PartSelect | None = None, internal: PartSelect | None = None, *, name: str = "design") -> Design:
    external_reference = ExternalPortReference(port_ref="top_data", part_select=external)
    internal_reference = AdHocConnection.PortReferences.InternalPortReference(
        port_ref="block_data",
        component_instance_ref="u_block",
        part_select=internal,
    )
    connection = AdHocConnection(
        name="data_link",
        port_references=AdHocConnection.PortReferences(
            internal_port_reference_or_external_port_reference=[internal_reference, external_reference]
        ),
    )
    return Design(
        vendor="acme",
        library="test",
        name=name,
        version="1.0",
        component_instances=ComponentInstances(
            component_instance=[
                ComponentInstance(
                    instance_name=InstanceName(value="u_block"),
                    component_ref=ConfigurableLibraryRefType(
                        vendor="acme", library="blocks", name="block", version="1"
                    ),
                )
            ]
        ),
        ad_hoc_connections=AdHocConnections(ad_hoc_connection=[connection]),
    )


def _registered_case(
    owner_kind: str,
    *,
    external: PartSelect | None = None,
    internal: PartSelect | None = None,
    name: str = "design",
) -> tuple[Design, ExternalPortReference | AdHocConnection.PortReferences.InternalPortReference]:
    root = _design(external, internal, name=name)
    registry.register(root, (root.vendor, root.library, root.name, root.version))
    references = root.ad_hoc_connections.ad_hoc_connection[0].port_references
    if owner_kind == "external":
        owner = references.internal_port_reference_or_external_port_reference[1]
        assert isinstance(owner, ExternalPortReference)
    else:
        owner = references.internal_port_reference_or_external_port_reference[0]
        assert isinstance(owner, AdHocConnection.PortReferences.InternalPortReference)
    return root, owner


def _operation(owner_kind: str, operation_index: int) -> Callable[..., object]:
    return getattr(api, _OPERATIONS[owner_kind][operation_index])


@pytest.mark.parametrize("owner_kind", ("external", "internal"), ids=_OWNER_IDS)
def test_part_select_getters_and_removers_handle_absent_and_invalid_owners(owner_kind: str) -> None:
    root, owner = _registered_case(owner_kind)
    owner_id = get_handle(owner)
    getter, setter, remover = (_operation(owner_kind, index) for index in range(3))

    assert getter(owner_id) is None
    assert remover(owner_id) is False
    assert resolve_handle(get_handle(root)) is root

    for operation in (getter, remover):
        with pytest.raises(TgiError) as error:
            operation("stale-design-owner")
        assert error.value.fault_code == TgiFaultCode.INVALID_ID
    with pytest.raises(TgiError) as error:
        setter("stale-design-owner", ("7", "0"), ("1",))
    assert error.value.fault_code == TgiFaultCode.INVALID_ID

    wrong_root, wrong_owner = _registered_case(
        "internal" if owner_kind == "external" else "external", name="wrong-owner"
    )
    with pytest.raises(TgiError) as error:
        getter(get_handle(wrong_owner))
    assert error.value.fault_code == TgiFaultCode.INVALID_ID
    with pytest.raises(TgiError) as error:
        setter(get_handle(wrong_owner), ("7", "0"), ("1",))
    assert error.value.fault_code == TgiFaultCode.INVALID_ID
    with pytest.raises(TgiError) as error:
        remover(get_handle(wrong_owner))
    assert error.value.fault_code == TgiFaultCode.INVALID_ID
    assert resolve_handle(get_handle(wrong_root)) is wrong_root


@pytest.mark.parametrize("owner_kind", ("external", "internal"), ids=_OWNER_IDS)
def test_set_part_select_preserves_wrapper_identity_metadata_and_source_expressions(owner_kind: str) -> None:
    selection = _selection()
    root, owner = _registered_case(
        owner_kind,
        external=selection if owner_kind == "external" else None,
        internal=selection if owner_kind == "internal" else None,
    )
    owner_id = get_handle(owner)
    selection_id = get_handle(selection)
    indices, range_node = selection.range_or_indices
    indices_id = get_handle(indices)
    index_id, removed_index_id = [get_handle(index) for index in indices.index]
    range_id = get_handle(range_node)
    left_id, right_id = get_handle(range_node.left), get_handle(range_node.right)
    assert _operation(owner_kind, 1)(owner_id, ("WIDTH - 1", "8'h0"), ("LANE + 1",)) is True
    assert _operation(owner_kind, 0)(owner_id) == selection_id
    info = get_parent_info(selection_id)
    assert info is not None and info.parent_handle == owner_id and info.path == ("part_select",)
    assert owner.part_select is selection
    assert selection.id == "retained-part-select"
    assert selection.range_or_indices == [indices, range_node]
    assert resolve_handle(indices_id) is indices
    assert resolve_handle(range_id) is range_node
    assert resolve_handle(index_id) is indices.index[0]
    assert resolve_handle(removed_index_id) is None
    assert indices.index == [resolve_handle(index_id)]
    assert resolve_handle(left_id) is range_node.left
    assert resolve_handle(right_id) is range_node.right
    assert range_node.left.value == "WIDTH - 1"
    assert range_node.right.value == "8'h0"
    assert range_node.left.other_attributes == {"{urn:test}marker": "left"}
    assert part_select_api.getPartSelectIndicesExpression(selection_id) == ["LANE + 1"]
    assert part_select_api.getPartSelectRangeExpression(selection_id) == ["WIDTH - 1", "8'h0"]
    assert resolve_handle(get_handle(root)) is root


@pytest.mark.parametrize("owner_kind", ("external", "internal"), ids=_OWNER_IDS)
def test_part_select_alternative_switches_invalidate_removed_subtrees(owner_kind: str) -> None:
    selection = _selection()
    root, owner = _registered_case(
        owner_kind,
        external=selection if owner_kind == "external" else None,
        internal=selection if owner_kind == "internal" else None,
    )
    owner_id = get_handle(owner)
    selection_id = get_handle(selection)
    indices, range_node = selection.range_or_indices
    indices_id = get_handle(indices)
    index_id = get_handle(indices.index[0])
    range_id, left_id, right_id = get_handle(range_node), get_handle(range_node.left), get_handle(range_node.right)

    assert _operation(owner_kind, 1)(owner_id, None, ("PORT_INDEX + 1",)) is True
    assert owner.part_select is selection
    assert _operation(owner_kind, 0)(owner_id) == selection_id
    assert selection.range_or_indices is indices
    assert part_select_api.getPartSelectIndicesExpression(selection_id) == ["PORT_INDEX + 1"]
    assert resolve_handle(range_id) is None
    assert resolve_handle(left_id) is None
    assert resolve_handle(right_id) is None
    assert resolve_handle(index_id) is indices.index[0]

    assert _operation(owner_kind, 1)(owner_id, ("15", "8"), None) is True
    assert owner.part_select is selection
    assert isinstance(selection.range_or_indices, Range)
    assert resolve_handle(indices_id) is None
    assert resolve_handle(index_id) is None
    assert part_select_api.getPartSelectRangeExpression(selection_id) == ["15", "8"]
    assert resolve_handle(get_handle(root)) is root


@pytest.mark.parametrize("owner_kind", ("external", "internal"), ids=_OWNER_IDS)
@pytest.mark.parametrize(
    "range_value,indices_value",
    [
        (("7",), None),
        ("7:0", None),
        (("7", object()), ("1",)),
        (("WIDTH +", "0"), ("1",)),
        (("16", "0"), None),
        (None, ("-1",)),
        (None, ("1 +",)),
        (None, ("4294967296",)),
        (None, None),
        (None, ()),
    ],
    ids=(
        "short-range",
        "string-range",
        "non-string",
        "syntax",
        "bound",
        "negative-index",
        "index-syntax",
        "overflow",
        "empty",
        "empty-indices",
    ),
)
def test_invalid_part_select_inputs_are_rejected_atomically(
    owner_kind: str, range_value: object, indices_value: object
) -> None:
    selection = _selection()
    root, owner = _registered_case(
        owner_kind,
        external=selection if owner_kind == "external" else None,
        internal=selection if owner_kind == "internal" else None,
    )
    owner_id = get_handle(owner)
    selection_id = get_handle(selection)
    before = tuple(selection.range_or_indices)
    before_ids = tuple(get_handle(child) for child in before)
    old_indices, old_range = before
    old_sources = tuple(index.value for index in old_indices.index), old_range.left.value, old_range.right.value

    with pytest.raises(TgiError) as error:
        _operation(owner_kind, 1)(owner_id, range_value, indices_value)
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert _operation(owner_kind, 0)(owner_id) == selection_id
    assert owner.part_select is selection
    assert tuple(selection.range_or_indices) == before
    assert tuple(get_handle(child) for child in selection.range_or_indices) == before_ids
    assert (
        tuple(index.value for index in old_indices.index),
        old_range.left.value,
        old_range.right.value,
    ) == old_sources
    assert resolve_handle(get_handle(root)) is root


@pytest.mark.parametrize("owner_kind", ("external", "internal"), ids=_OWNER_IDS)
def test_malformed_part_select_children_fault_without_replacing_owner(owner_kind: str) -> None:
    selection = PartSelect(range_or_indices=object(), id="malformed")
    root, owner = _registered_case(
        owner_kind,
        external=selection if owner_kind == "external" else None,
        internal=selection if owner_kind == "internal" else None,
    )
    owner_id = get_handle(owner)

    for operation_index in (0, 1, 2):
        with pytest.raises(TgiError) as error:
            if operation_index == 1:
                _operation(owner_kind, operation_index)(owner_id, ("7", "0"), ("1",))
            else:
                _operation(owner_kind, operation_index)(owner_id)
        assert error.value.fault_code == TgiFaultCode.INVALID_ID
        assert owner.part_select is selection
        assert selection.range_or_indices is not None
    assert resolve_handle(get_handle(root)) is root


@pytest.mark.parametrize("owner_kind", ("external", "internal"), ids=_OWNER_IDS)
def test_remove_part_select_invalidates_wrapper_and_descendants(owner_kind: str) -> None:
    selection = _selection()
    root, owner = _registered_case(
        owner_kind,
        external=selection if owner_kind == "external" else None,
        internal=selection if owner_kind == "internal" else None,
    )
    owner_id = get_handle(owner)
    selection_id = get_handle(selection)
    indices, range_node = selection.range_or_indices
    child_handles = (
        get_handle(indices),
        *(get_handle(index) for index in indices.index),
        get_handle(range_node),
        get_handle(range_node.left),
        get_handle(range_node.right),
    )

    assert _operation(owner_kind, 2)(owner_id) is True
    assert owner.part_select is None
    assert _operation(owner_kind, 0)(owner_id) is None
    assert resolve_handle(selection_id) is None
    assert all(resolve_handle(handle) is None for handle in child_handles)
    assert _operation(owner_kind, 2)(owner_id) is False
    assert resolve_handle(get_handle(root)) is root


def test_parsed_design_references_round_trip_keep_ownership_and_remove_part_selects() -> None:
    root = _design(_selection("external-selection"), _selection("internal-selection"), name="parsed-design")
    xml = XmlDocument.serializer().render(root)
    assert _SCHEMA.validate(etree.fromstring(xml.encode())), _SCHEMA.error_log
    parsed = XmlDocument.parser().from_string(xml, Design)
    assert XmlDocument.serializer().render(parsed) == xml
    registry.register(parsed, (parsed.vendor, parsed.library, parsed.name, parsed.version))
    references = parsed.ad_hoc_connections.ad_hoc_connection[0].port_references
    internal, external = references.internal_port_reference_or_external_port_reference
    external_id = get_handle(external)
    internal_id = get_handle(internal)
    external_selection_id = api.getExternalPortReferencePartSelectID(external_id)
    internal_selection_id = api.getInternalPortReferencePartSelectID(internal_id)
    assert external_selection_id is not None and internal_selection_id is not None
    for selection_id, owner_id in ((external_selection_id, external_id), (internal_selection_id, internal_id)):
        info = get_parent_info(selection_id)
        assert info is not None and info.parent_handle == owner_id and info.path == ("part_select",)
        assert part_select_api.getPartSelectRangeExpression(selection_id) == ["7", "0"]
        assert part_select_api.getPartSelectIndicesExpression(selection_id) == ["3", "5"]

    assert api.removeExternalPortReferencePartSelect(external_id)
    assert api.removeInternalPortReferencePartSelect(internal_id)
    assert resolve_handle(external_selection_id) is None
    assert resolve_handle(internal_selection_id) is None
    xml_without_parts = XmlDocument.serializer().render(parsed)
    assert _SCHEMA.validate(etree.fromstring(xml_without_parts.encode())), _SCHEMA.error_log
    assert "partSelect" not in xml_without_parts


def test_design_part_select_operations_are_exported_with_annex_signatures() -> None:
    expected = {
        "getExternalPortReferencePartSelectID": (
            ("externalPortReferenceID",),
            (str,),
            str | None,
        ),
        "getInternalPortReferencePartSelectID": (
            ("internalPortReferenceID",),
            (str,),
            str | None,
        ),
        "setExternalPortReferencePartSelect": (
            ("externalPortReferenceID", "range", "indices"),
            (str, Sequence[str] | None, Sequence[str] | None),
            bool,
        ),
        "setInternalPortReferencePartSelect": (
            ("internalPortReferenceID", "range", "indices"),
            (str, Sequence[str] | None, Sequence[str] | None),
            bool,
        ),
        "removeExternalPortReferencePartSelect": (
            ("externalPortReferenceID",),
            (str,),
            bool,
        ),
        "removeInternalPortReferencePartSelect": (
            ("internalPortReferenceID",),
            (str,),
            bool,
        ),
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

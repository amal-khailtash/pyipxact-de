"""TGI traversal and removal of Design ad-hoc port references."""

import inspect
from collections.abc import Iterator, Sequence
from typing import cast

import pytest
from lxml import etree

from amal.eda.accellera.ipxact.v1685_2022 import tgi
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
    InstanceName,
    PartSelect,
    Range,
    SubPortReference,
)
from org.accellera.ipxact.v1685_2022.left import Left
from org.accellera.ipxact.v1685_2022.right import Right

_SCHEMA = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))
_OWNER_IDS = ("external-port-reference", "internal-port-reference")
_OPERATIONS = {
    "external": (
        "getExternalPortReferencePortRefByName",
        "getExternalPortReferenceSubPortReferenceIDs",
        "removeExternalPortReferenceSubPortReference",
    ),
    "internal": (
        "getInternalPortReferencePortRefByName",
        "getInternalPortReferenceSubPortReferenceIDs",
        "removeInternalPortReferenceSubPortReference",
    ),
}
_PORT_REFERENCE_IDS = (
    "getAdHocConnectionExternalPortReferenceIDs",
    "getAdHocConnectionInternalPortReferenceIDs",
)


@pytest.fixture(autouse=True)
def clean_registry() -> Iterator[None]:
    registry.clear()
    yield
    registry.clear()


def _part_select() -> PartSelect:
    return PartSelect(range_or_indices=Range(left=Left(value="7"), right=Right(value="0")))


def _external(
    name: str = "top_data.007",
    *,
    refs: Sequence[SubPortReference] = (),
    part_select: PartSelect | None = None,
) -> ExternalPortReference:
    return ExternalPortReference(port_ref=name, sub_port_reference=refs, part_select=part_select)


def _internal(
    name: str = "core_data.003",
    *,
    refs: Sequence[SubPortReference] = (),
    part_select: PartSelect | None = None,
) -> AdHocConnection.PortReferences.InternalPortReference:
    return AdHocConnection.PortReferences.InternalPortReference(
        port_ref=name,
        component_instance_ref="u_core_3",
        sub_port_reference=refs,
        part_select=part_select,
    )


def _design(
    references: Sequence[ExternalPortReference | AdHocConnection.PortReferences.InternalPortReference],
    *,
    name: str = "port_reference_design",
) -> Design:
    return Design(
        vendor="acme",
        library="connections",
        name=name,
        version="1.0",
        component_instances=ComponentInstances(
            component_instance=[
                ComponentInstance(
                    instance_name=InstanceName(value="u_core_3"),
                    component_ref=ConfigurableLibraryRefType(vendor="acme", library="blocks", name="core", version="1"),
                )
            ]
        ),
        ad_hoc_connections=AdHocConnections(
            ad_hoc_connection=[
                AdHocConnection(
                    name="mixed_data",
                    port_references=AdHocConnection.PortReferences(
                        internal_port_reference_or_external_port_reference=references
                    ),
                )
            ]
        ),
    )


def _case(
    owner_kind: str,
    *,
    external_refs: Sequence[SubPortReference] = (),
    internal_refs: Sequence[SubPortReference] = (),
    external_part_select: PartSelect | None = None,
    internal_part_select: PartSelect | None = None,
    name: str = "port_reference_design",
) -> tuple[
    Design,
    AdHocConnection,
    ExternalPortReference | AdHocConnection.PortReferences.InternalPortReference,
]:
    external = _external(refs=external_refs, part_select=external_part_select)
    internal = _internal(refs=internal_refs, part_select=internal_part_select)
    root = _design((internal, external), name=name)
    registry.register(root, (root.vendor, root.library, root.name, root.version))
    connection = root.ad_hoc_connections.ad_hoc_connection[0]
    owner = connection.port_references.internal_port_reference_or_external_port_reference[
        1 if owner_kind == "external" else 0
    ]
    return root, connection, owner


def _operation(owner_kind: str, operation_index: int):
    return getattr(api, _OPERATIONS[owner_kind][operation_index])


@pytest.mark.parametrize("owner_kind", ("external", "internal"), ids=_OWNER_IDS)
def test_connection_and_port_reference_getters_follow_generated_mixed_holder(owner_kind: str) -> None:
    external_refs = (
        SubPortReference(sub_port_ref="outer.payload.007"),
        SubPortReference(sub_port_ref="outer.payload.007"),
    )
    internal_refs = (
        SubPortReference(sub_port_ref="inner.payload.003"),
        SubPortReference(sub_port_ref="inner.payload.003"),
    )
    root, connection, selected_owner = _case(owner_kind, external_refs=external_refs, internal_refs=internal_refs)
    connection_id = get_handle(connection)
    port_refs = connection.port_references
    holder = port_refs.internal_port_reference_or_external_port_reference
    internal, external = holder

    external_ids = api.getAdHocConnectionExternalPortReferenceIDs(connection_id)
    internal_ids = api.getAdHocConnectionInternalPortReferenceIDs(connection_id)
    assert external_ids == [get_handle(external)]
    assert internal_ids == [get_handle(internal)]
    for reference_id in (*external_ids, *internal_ids):
        info = get_parent_info(reference_id)
        assert info is not None
        assert info.parent_handle == get_handle(port_refs)
        assert info.path == ("internal_port_reference_or_external_port_reference",)

    expected_name = "top_data.007" if owner_kind == "external" else "core_data.003"
    assert _operation(owner_kind, 0)(get_handle(selected_owner)) == expected_name
    reference_ids = _operation(owner_kind, 1)(get_handle(selected_owner))
    expected_refs = external_refs if owner_kind == "external" else internal_refs
    assert [resolve_handle(reference_id) for reference_id in reference_ids] == list(expected_refs)
    assert [resolve_handle(reference_id).sub_port_ref for reference_id in reference_ids] == [
        reference.sub_port_ref for reference in expected_refs
    ]
    if owner_kind == "internal":
        assert api.getInternalPortReferenceComponentInstanceRefByName(get_handle(internal)) == "u_core_3"
    assert resolve_handle(get_handle(root)) is root


@pytest.mark.parametrize("owner_kind", ("external", "internal"), ids=_OWNER_IDS)
def test_reads_accept_tuple_storage_without_normalizing_and_fault_on_invalid_handles(owner_kind: str) -> None:
    external_refs = (
        SubPortReference(sub_port_ref="external.payload.1"),
        SubPortReference(sub_port_ref="external.payload.1"),
    )
    internal_refs = (
        SubPortReference(sub_port_ref="internal.payload.1"),
        SubPortReference(sub_port_ref="internal.payload.1"),
    )
    root, connection, owner = _case(owner_kind, external_refs=external_refs, internal_refs=internal_refs)
    port_references = connection.port_references
    port_references.internal_port_reference_or_external_port_reference = tuple(
        port_references.internal_port_reference_or_external_port_reference
    )
    owner_refs = owner.sub_port_reference
    owner.sub_port_reference = tuple(owner_refs)

    assert _operation(owner_kind, 1)(get_handle(owner)) == [get_handle(reference) for reference in owner_refs]
    assert isinstance(owner.sub_port_reference, tuple)
    assert isinstance(port_references.internal_port_reference_or_external_port_reference, tuple)
    with pytest.raises(TgiError) as error:
        _operation(owner_kind, 0)("stale-owner")
    assert error.value.fault_code == TgiFaultCode.INVALID_ID
    with pytest.raises(TgiError) as error:
        getattr(api, _PORT_REFERENCE_IDS[0])("stale-connection")
    assert error.value.fault_code == TgiFaultCode.INVALID_ID
    assert resolve_handle(get_handle(root)) is root


@pytest.mark.parametrize("owner_kind", ("external", "internal"), ids=_OWNER_IDS)
def test_reference_names_are_returned_verbatim_and_wrong_reference_types_fault(owner_kind: str) -> None:
    root, _connection, owner = _case(owner_kind)
    owner_id = get_handle(owner)
    name_getter = _operation(owner_kind, 0)
    assert name_getter(owner_id) == ("top_data.007" if owner_kind == "external" else "core_data.003")

    other_kind = "internal" if owner_kind == "external" else "external"
    _, _, wrong_owner = _case(other_kind, name="wrong_owner")
    with pytest.raises(TgiError) as error:
        name_getter(get_handle(wrong_owner))
    assert error.value.fault_code == TgiFaultCode.INVALID_ID
    with pytest.raises(TgiError) as error:
        _operation(owner_kind, 0)("stale-port-reference")
    assert error.value.fault_code == TgiFaultCode.INVALID_ID
    if owner_kind == "internal":
        with pytest.raises(TgiError) as error:
            api.getInternalPortReferenceComponentInstanceRefByName(get_handle(wrong_owner))
        assert error.value.fault_code == TgiFaultCode.INVALID_ID
    assert resolve_handle(get_handle(root)) is root


@pytest.mark.parametrize("owner_kind", ("external", "internal"), ids=_OWNER_IDS)
def test_name_getters_reject_malformed_reference_sources(owner_kind: str) -> None:
    root, _connection, owner = _case(owner_kind)
    owner.port_ref = object()
    with pytest.raises(TgiError) as error:
        _operation(owner_kind, 0)(get_handle(owner))
    assert error.value.fault_code == TgiFaultCode.INVALID_ID

    if owner_kind == "internal":
        owner.component_instance_ref = object()
        with pytest.raises(TgiError) as error:
            api.getInternalPortReferenceComponentInstanceRefByName(get_handle(owner))
        assert error.value.fault_code == TgiFaultCode.INVALID_ID
    assert resolve_handle(get_handle(root)) is root


@pytest.mark.parametrize("owner_kind", ("external", "internal"), ids=_OWNER_IDS)
def test_sub_port_reference_removal_preserves_siblings_and_part_selects(owner_kind: str) -> None:
    first = SubPortReference(sub_port_ref="payload.first", part_select=_part_select())
    second = SubPortReference(sub_port_ref="payload.second", part_select=_part_select())
    owner_select = _part_select()
    root, _connection, owner = _case(
        owner_kind,
        external_refs=(first, second) if owner_kind == "external" else (),
        internal_refs=(first, second) if owner_kind == "internal" else (),
        external_part_select=owner_select if owner_kind == "external" else None,
        internal_part_select=owner_select if owner_kind == "internal" else None,
    )
    owner_id = get_handle(owner)
    first_id, second_id = get_handle(first), get_handle(second)
    first_part_select_id, second_part_select_id = get_handle(first.part_select), get_handle(second.part_select)
    owner_part_select_id = get_handle(owner_select)

    assert _operation(owner_kind, 1)(owner_id) == [first_id, second_id]
    assert _operation(owner_kind, 2)(first_id) is True
    assert _operation(owner_kind, 1)(owner_id) == [second_id]
    assert resolve_handle(first_id) is None
    assert resolve_handle(first_part_select_id) is None
    assert resolve_handle(second_id) is second
    assert resolve_handle(second_part_select_id) is second.part_select
    assert resolve_handle(owner_part_select_id) is owner_select
    assert owner.sub_port_reference == [second]
    assert resolve_handle(get_handle(root)) is root


@pytest.mark.parametrize("owner_kind", ("external", "internal"), ids=_OWNER_IDS)
def test_sub_port_reference_removal_normalizes_tuple_and_rejects_orphans_wrong_owner_and_stale(
    owner_kind: str,
) -> None:
    first = SubPortReference(sub_port_ref="payload.first")
    second = SubPortReference(sub_port_ref="payload.second")
    root, _connection, owner = _case(
        owner_kind,
        external_refs=(first, second) if owner_kind == "external" else (),
        internal_refs=(first, second) if owner_kind == "internal" else (),
    )
    owner.sub_port_reference = tuple(owner.sub_port_reference)
    first_id, second_id = get_handle(first), get_handle(second)
    remover = _operation(owner_kind, 2)

    assert remover(first_id) is True
    assert isinstance(owner.sub_port_reference, list)
    assert owner.sub_port_reference == [second]
    assert resolve_handle(first_id) is None
    assert resolve_handle(second_id) is second
    with pytest.raises(TgiError) as error:
        remover(first_id)
    assert error.value.fault_code == TgiFaultCode.INVALID_ID

    other_kind = "internal" if owner_kind == "external" else "external"
    _, _, wrong_owner = _case(other_kind, name="wrong_owner")
    wrong_reference = wrong_owner.sub_port_reference
    if not wrong_reference:
        wrong_reference = [SubPortReference(sub_port_ref="payload.wrong")]
        wrong_owner.sub_port_reference = wrong_reference
    wrong_id = get_handle(wrong_reference[0])
    with pytest.raises(TgiError) as error:
        remover(wrong_id)
    assert error.value.fault_code == TgiFaultCode.INVALID_ID

    orphan = SubPortReference(sub_port_ref="payload.orphan")
    with pytest.raises(TgiError) as error:
        remover(get_handle(orphan))
    assert error.value.fault_code == TgiFaultCode.INVALID_ID
    assert resolve_handle(get_handle(root)) is root


@pytest.mark.parametrize("owner_kind", ("external", "internal"), ids=_OWNER_IDS)
@pytest.mark.parametrize("has_sibling", [False, True], ids=("empty-path", "valid-sibling"))
def test_sub_port_reference_removal_rejects_child_in_wrong_owner_field(owner_kind: str, has_sibling: bool) -> None:
    sibling = SubPortReference(sub_port_ref="payload.keep") if has_sibling else None
    root, _connection, owner = _case(
        owner_kind,
        external_refs=(sibling,) if sibling is not None and owner_kind == "external" else (),
        internal_refs=(sibling,) if sibling is not None and owner_kind == "internal" else (),
    )
    wrong_field_child = SubPortReference(sub_port_ref="payload.wrong-field")
    owner.part_select = cast(PartSelect, wrong_field_child)
    wrong_field_id = get_handle(wrong_field_child)
    original_sub_references = owner.sub_port_reference
    sibling_id = get_handle(sibling) if sibling is not None else None

    with pytest.raises(TgiError) as error:
        _operation(owner_kind, 2)(wrong_field_id)
    assert error.value.fault_code == TgiFaultCode.INVALID_ID
    assert owner.part_select is wrong_field_child
    assert owner.sub_port_reference is original_sub_references
    assert owner.sub_port_reference == ((sibling,) if sibling is not None else ())
    assert resolve_handle(wrong_field_id) is wrong_field_child
    assert sibling_id is None or resolve_handle(sibling_id) is sibling
    assert resolve_handle(get_handle(root)) is root


@pytest.mark.parametrize("owner_kind", ("external", "internal"), ids=_OWNER_IDS)
@pytest.mark.parametrize(
    "malformation",
    ("scalar-list", "wrong-child", "non-string-source"),
    ids=("scalar-list", "wrong-child", "non-string-source"),
)
def test_malformed_sub_port_reference_lists_fault_with_invalid_id(owner_kind: str, malformation: str) -> None:
    root, _connection, owner = _case(
        owner_kind,
        external_refs=(SubPortReference(sub_port_ref="valid"),) if owner_kind == "external" else (),
        internal_refs=(SubPortReference(sub_port_ref="valid"),) if owner_kind == "internal" else (),
    )
    if malformation == "scalar-list":
        owner.sub_port_reference = object()
    elif malformation == "wrong-child":
        owner.sub_port_reference = [object()]
    else:
        owner.sub_port_reference = [SubPortReference(sub_port_ref=object())]
    with pytest.raises(TgiError) as error:
        _operation(owner_kind, 1)(get_handle(owner))
    assert error.value.fault_code == TgiFaultCode.INVALID_ID
    assert resolve_handle(get_handle(root)) is root


def test_malformed_connection_reference_holder_and_mixed_members_fault() -> None:
    root, connection, _owner = _case("external")
    connection_id = get_handle(connection)
    holder = connection.port_references
    connection.port_references = object()
    for name in _PORT_REFERENCE_IDS:
        with pytest.raises(TgiError) as error:
            getattr(api, name)(connection_id)
        assert error.value.fault_code == TgiFaultCode.INVALID_ID

    connection.port_references = None
    assert api.getAdHocConnectionExternalPortReferenceIDs(connection_id) == []
    assert api.getAdHocConnectionInternalPortReferenceIDs(connection_id) == []
    connection.port_references = holder
    for invalid in (None, object(), (object(),)):
        holder.internal_port_reference_or_external_port_reference = invalid
        for name in _PORT_REFERENCE_IDS:
            with pytest.raises(TgiError) as error:
                getattr(api, name)(connection_id)
            assert error.value.fault_code == TgiFaultCode.INVALID_ID
    assert resolve_handle(get_handle(root)) is root


def test_parsed_design_port_reference_round_trip_and_owner_discovery_removal() -> None:
    internal_first = SubPortReference(sub_port_ref="core.payload.1", part_select=_part_select(), id="internal-first")
    internal_second = SubPortReference(sub_port_ref="core.payload.2", id="internal-second")
    external_first = SubPortReference(sub_port_ref="top.payload.1", part_select=_part_select(), id="external-first")
    external_second = SubPortReference(sub_port_ref="top.payload.2", id="external-second")
    root = _design(
        (
            _internal(
                refs=(internal_first, internal_second),
                part_select=_part_select(),
            ),
            _external(
                refs=(external_first, external_second),
                part_select=_part_select(),
            ),
        )
    )
    xml = XmlDocument.serializer().render(root)
    assert _SCHEMA.validate(etree.fromstring(xml.encode())), _SCHEMA.error_log
    parsed = XmlDocument.parser().from_string(xml, Design)
    assert XmlDocument.serializer().render(parsed) == xml
    registry.register(parsed, (parsed.vendor, parsed.library, parsed.name, parsed.version))
    connection = parsed.ad_hoc_connections.ad_hoc_connection[0]
    internal, external = connection.port_references.internal_port_reference_or_external_port_reference
    external_ids = api.getAdHocConnectionExternalPortReferenceIDs(get_handle(connection))
    internal_ids = api.getAdHocConnectionInternalPortReferenceIDs(get_handle(connection))
    assert external_ids == [get_handle(external)]
    assert internal_ids == [get_handle(internal)]
    external_first_id = get_handle(external.sub_port_reference[0])
    internal_first_id = get_handle(internal.sub_port_reference[0])
    external_first_part_select_id = get_handle(external.sub_port_reference[0].part_select)
    internal_first_part_select_id = get_handle(internal.sub_port_reference[0].part_select)
    assert api.removeExternalPortReferenceSubPortReference(external_first_id)
    assert api.removeInternalPortReferenceSubPortReference(internal_first_id)
    assert resolve_handle(external_first_id) is None
    assert resolve_handle(internal_first_id) is None
    assert resolve_handle(external_first_part_select_id) is None
    assert resolve_handle(internal_first_part_select_id) is None
    for owner, refs, reference_ids, operation_name in (
        (external, external.sub_port_reference, external_ids, _OPERATIONS["external"][1]),
        (internal, internal.sub_port_reference, internal_ids, _OPERATIONS["internal"][1]),
    ):
        assert owner.sub_port_reference == refs
        actual_ids = getattr(api, operation_name)(reference_ids[0])
        assert [resolve_handle(child_id) for child_id in actual_ids] == list(refs)
        for ref in refs:
            info = get_parent_info(get_handle(ref))
            assert info is not None
            assert info.parent_handle == reference_ids[0]
            assert info.path == ("sub_port_reference",)
    assert api.getExternalPortReferencePartSelectID(external_ids[0]) is not None
    assert api.getInternalPortReferencePartSelectID(internal_ids[0]) is not None
    for owner, remove in (
        (external, api.removeExternalPortReferenceSubPortReference),
        (internal, api.removeInternalPortReferenceSubPortReference),
    ):
        child_id = get_handle(owner.sub_port_reference[0])
        assert remove(child_id)
        assert resolve_handle(child_id) is None
    xml_after = XmlDocument.serializer().render(parsed)
    assert _SCHEMA.validate(etree.fromstring(xml_after.encode())), _SCHEMA.error_log
    assert XmlDocument.serializer().render(XmlDocument.parser().from_string(xml_after, Design)) == xml_after


def test_design_port_reference_traversal_exports_and_native_signatures_match_annex() -> None:
    expected: dict[str, tuple[tuple[str, ...], tuple[object, ...], object]] = {
        "getAdHocConnectionExternalPortReferenceIDs": (("adHocConnectionID",), (str,), list[str]),
        "getAdHocConnectionInternalPortReferenceIDs": (("adHocConnectionID",), (str,), list[str]),
        "getExternalPortReferencePortRefByName": (("externalPortReferenceID",), (str,), str),
        "getInternalPortReferencePortRefByName": (("internalPortReferenceID",), (str,), str),
        "getInternalPortReferenceComponentInstanceRefByName": (("internalPortReferenceID",), (str,), str),
        "getExternalPortReferenceSubPortReferenceIDs": (("externalPortReferenceID",), (str,), list[str]),
        "getInternalPortReferenceSubPortReferenceIDs": (("internalPortReferenceID",), (str,), list[str]),
        "removeExternalPortReferenceSubPortReference": (("subPortRefID",), (str,), bool),
        "removeInternalPortReferenceSubPortReference": (("subPortRefID",), (str,), bool),
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

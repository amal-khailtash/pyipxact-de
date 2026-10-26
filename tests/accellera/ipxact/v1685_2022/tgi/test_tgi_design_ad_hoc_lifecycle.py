"""Design ad-hoc connection and port-reference lifecycle operations."""

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
    ComplexTiedValueExpression,
    ComponentInstance,
    ComponentInstances,
    ConfigurableLibraryRefType,
    Design,
    ExternalPortReference,
    InstanceName,
    PartSelect,
    Range,
    SubPortReference,
    VendorExtensions,
)
from org.accellera.ipxact.v1685_2022.left import Left
from org.accellera.ipxact.v1685_2022.right import Right

_SCHEMA = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))
_OWNER_IDS = ("external-port-reference", "internal-port-reference")
_Reference = ExternalPortReference | AdHocConnection.PortReferences.InternalPortReference
_REMOVERS = {
    "external": api.removeAdHocConnectionExternalPortReference,
    "internal": api.removeAdHocConnectionInternalPortReference,
}


@pytest.fixture(autouse=True)
def clean_registry() -> Iterator[None]:
    registry.clear()
    yield
    registry.clear()


def _part_select() -> PartSelect:
    return PartSelect(range_or_indices=Range(left=Left(value="7"), right=Right(value="0")))


def _internal(
    port_ref: str = "core_data",
    component_instance_ref: str = "u_core",
    *,
    sub_refs: Sequence[SubPortReference] = (),
    part_select: PartSelect | None = None,
) -> AdHocConnection.PortReferences.InternalPortReference:
    return AdHocConnection.PortReferences.InternalPortReference(
        component_instance_ref=component_instance_ref,
        port_ref=port_ref,
        sub_port_reference=sub_refs,
        part_select=part_select,
    )


def _external(
    port_ref: str = "top_data",
    *,
    sub_refs: Sequence[SubPortReference] = (),
    part_select: PartSelect | None = None,
) -> ExternalPortReference:
    return ExternalPortReference(port_ref=port_ref, sub_port_reference=sub_refs, part_select=part_select)


def _connection(
    name: str = "data_link",
    references: Sequence[_Reference] = (),
) -> AdHocConnection:
    return AdHocConnection(
        name=name,
        port_references=AdHocConnection.PortReferences(internal_port_reference_or_external_port_reference=references),
    )


def _design(
    connections: Sequence[AdHocConnection] = (),
    *,
    name: str = "lifecycle_design",
    has_instances: bool = True,
) -> Design:
    return Design(
        vendor="acme",
        library="connections",
        name=name,
        version="1.0",
        component_instances=(
            ComponentInstances(
                component_instance=[
                    ComponentInstance(
                        instance_name=InstanceName(value="u_core"),
                        component_ref=ConfigurableLibraryRefType(
                            vendor="acme", library="blocks", name="core", version="1"
                        ),
                    )
                ]
            )
            if has_instances
            else None
        ),
        ad_hoc_connections=AdHocConnections(ad_hoc_connection=connections) if connections else None,
    )


def _registered_case(
    references: Sequence[_Reference] = (), *, name: str = "lifecycle_design"
) -> tuple[Design, AdHocConnection]:
    connection = _connection(references=references)
    root = _design([connection], name=name)
    registry.register(root, (root.vendor, root.library, root.name, root.version))
    return root, connection


def test_endpoint_adders_normalize_inputs_and_preserve_schema_order_and_ownership() -> None:
    initial_internal = _internal("core_data")
    first_external = _external("top_data")
    root, connection = _registered_case((initial_internal, first_external))
    connection_id = get_handle(connection)
    holder = connection.port_references
    holder_id = get_handle(holder)
    initial_children = tuple(holder.internal_port_reference_or_external_port_reference)

    internal_id = api.addAdHocConnectionInternalPortReference(connection_id, " \tu_core\r\n", " \tcore_data\n")
    external_id = api.addAdHocConnectionExternalPortReference(connection_id, " \ttop_data\r\n")
    repeated_id = api.addAdHocConnectionExternalPortReference(connection_id, "top_data")

    mixed = holder.internal_port_reference_or_external_port_reference
    assert isinstance(mixed, list)
    assert mixed[:2] == [initial_internal, resolve_handle(internal_id)]
    assert mixed[2:] == [first_external, resolve_handle(external_id), resolve_handle(repeated_id)]
    assert resolve_handle(internal_id).component_instance_ref == "u_core"
    assert resolve_handle(internal_id).port_ref == "core_data"
    assert resolve_handle(external_id).port_ref == "top_data"
    assert resolve_handle(repeated_id).port_ref == "top_data"
    assert api.getAdHocConnectionInternalPortReferenceIDs(connection_id) == [
        get_handle(initial_internal),
        internal_id,
    ]
    assert api.getAdHocConnectionExternalPortReferenceIDs(connection_id) == [
        get_handle(first_external),
        external_id,
        repeated_id,
    ]
    assert holder_id == get_handle(connection.port_references)
    for reference_id in (internal_id, external_id, repeated_id):
        info = get_parent_info(reference_id)
        assert info is not None and info.parent_handle == holder_id
        assert info.path == ("internal_port_reference_or_external_port_reference",)
    assert tuple(initial_children) == (initial_internal, first_external)
    assert resolve_handle(get_handle(root)) is root


@pytest.mark.parametrize("owner_kind", ("external", "internal"), ids=_OWNER_IDS)
def test_endpoint_adders_normalize_tuple_storage_and_reject_invalid_existing_order(owner_kind: str) -> None:
    internal = _internal()
    external = _external()
    root, connection = _registered_case((internal, external))
    connection_id = get_handle(connection)
    connection.port_references.internal_port_reference_or_external_port_reference = tuple(
        connection.port_references.internal_port_reference_or_external_port_reference
    )
    if owner_kind == "internal":
        new_id = api.addAdHocConnectionInternalPortReference(connection_id, "u_core", "core_data")
        assert isinstance(connection.port_references.internal_port_reference_or_external_port_reference, list)
        assert connection.port_references.internal_port_reference_or_external_port_reference == [
            internal,
            resolve_handle(new_id),
            external,
        ]
    else:
        new_id = api.addAdHocConnectionExternalPortReference(connection_id, "top_data")
        assert isinstance(connection.port_references.internal_port_reference_or_external_port_reference, list)
        assert connection.port_references.internal_port_reference_or_external_port_reference == [
            internal,
            external,
            resolve_handle(new_id),
        ]
    assert resolve_handle(get_handle(root)) is root

    malformed_root, malformed_connection = _registered_case(
        (_external("early_external"), _internal("late_internal")), name=f"bad_order_{owner_kind}"
    )
    before = tuple(malformed_connection.port_references.internal_port_reference_or_external_port_reference)
    add = (
        api.addAdHocConnectionInternalPortReference
        if owner_kind == "internal"
        else api.addAdHocConnectionExternalPortReference
    )
    with pytest.raises(TgiError) as error:
        if owner_kind == "internal":
            add(get_handle(malformed_connection), "u_core", "core_data")
        else:
            add(get_handle(malformed_connection), "top_data")
    assert error.value.fault_code == TgiFaultCode.INVALID_ID
    assert tuple(malformed_connection.port_references.internal_port_reference_or_external_port_reference) == before
    assert resolve_handle(get_handle(malformed_root)) is malformed_root


@pytest.mark.parametrize("owner_kind", ("external", "internal"), ids=_OWNER_IDS)
@pytest.mark.parametrize("malformation", ("non-sequence", "wrong-child"), ids=("non-sequence", "wrong-child"))
def test_endpoint_adders_reject_malformed_existing_reference_collections(owner_kind: str, malformation: str) -> None:
    root, connection = _registered_case((_internal(), _external()))
    holder = connection.port_references
    malformed = object() if malformation == "non-sequence" else [object()]
    holder.internal_port_reference_or_external_port_reference = malformed
    add = (
        api.addAdHocConnectionInternalPortReference
        if owner_kind == "internal"
        else api.addAdHocConnectionExternalPortReference
    )

    with pytest.raises(TgiError) as error:
        if owner_kind == "internal":
            add(get_handle(connection), "u_core", "core_data")
        else:
            add(get_handle(connection), "top_data")
    assert error.value.fault_code == TgiFaultCode.INVALID_ID
    assert holder.internal_port_reference_or_external_port_reference is malformed
    assert resolve_handle(get_handle(root)) is root


@pytest.mark.parametrize(
    "operation,arguments",
    [
        ("external", ("bad port",)),
        ("external", ("data·i",)),
        ("internal", ("bad instance", "core_data")),
        ("internal", ("u_core", "bad port")),
        ("internal", ("u_core", "data·i")),
    ],
    ids=("external-space", "external-port-name", "instance-name", "internal-space", "internal-port-name"),
)
def test_endpoint_adders_validate_all_name_sources_before_mutation(operation: str, arguments: tuple[str, ...]) -> None:
    initial_internal = _internal()
    initial_external = _external()
    root, connection = _registered_case((initial_internal, initial_external))
    before = tuple(connection.port_references.internal_port_reference_or_external_port_reference)
    before_ids = tuple(get_handle(child) for child in before)

    with pytest.raises(TgiError) as error:
        if operation == "external":
            api.addAdHocConnectionExternalPortReference(get_handle(connection), arguments[0])
        else:
            api.addAdHocConnectionInternalPortReference(get_handle(connection), arguments[0], arguments[1])
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert tuple(connection.port_references.internal_port_reference_or_external_port_reference) == before
    assert tuple(get_handle(child) for child in before) == before_ids
    assert resolve_handle(get_handle(root)) is root


@pytest.mark.parametrize("builder", ("internal", "external"), ids=("internal-builder", "external-builder"))
def test_design_ad_hoc_builders_create_typed_connections_without_connectivity_resolution(builder: str) -> None:
    root = _design(has_instances=False)
    registry.register(root, (root.vendor, root.library, root.name, root.version))
    design_id = get_handle(root)

    if builder == "internal":
        connection_id = api.addDesignAdHocConnection(design_id, " internal_link ", "missing_instance", " core_data ")
        connection = resolve_handle(connection_id)
        assert connection.name == "internal_link"
        (internal,) = connection.port_references.internal_port_reference_or_external_port_reference
        assert isinstance(internal, AdHocConnection.PortReferences.InternalPortReference)
        assert internal.component_instance_ref == "missing_instance"
        assert internal.port_ref == "core_data"
        reference_id = api.getAdHocConnectionInternalPortReferenceIDs(connection_id)[0]
        assert reference_id == get_handle(internal)
        expected_path = "internal_port_reference_or_external_port_reference"
    else:
        connection_id = api.addDesignExternalAdHocConnection(design_id, " external_link ", " top_data ")
        connection = resolve_handle(connection_id)
        assert connection.name == "external_link"
        (external,) = connection.port_references.internal_port_reference_or_external_port_reference
        assert isinstance(external, ExternalPortReference)
        assert external.port_ref == "top_data"
        reference_id = api.getAdHocConnectionExternalPortReferenceIDs(connection_id)[0]
        assert reference_id == get_handle(external)
        expected_path = "internal_port_reference_or_external_port_reference"

    assert api.getDesignAdHocConnectionIDs(design_id) == [connection_id]
    connection_info = get_parent_info(connection_id)
    assert connection_info is not None
    assert connection_info.parent_handle == get_handle(root.ad_hoc_connections)
    assert connection_info.path == ("ad_hoc_connection",)
    reference_info = get_parent_info(reference_id)
    assert reference_info is not None and reference_info.parent_handle == get_handle(connection.port_references)
    assert reference_info.path == (expected_path,)


@pytest.mark.parametrize(
    "builder,invalid",
    [
        ("internal", "bad-connection-name"),
        ("internal", "bad-port-name"),
        ("internal", "bad-instance-name"),
        ("external", "bad-connection-name"),
        ("external", "bad-port-name"),
    ],
    ids=("internal-name", "internal-port", "internal-instance", "external-name", "external-port"),
)
def test_design_ad_hoc_builders_validate_before_creating_containers(builder: str, invalid: str) -> None:
    root = _design(has_instances=False)
    registry.register(root, (root.vendor, root.library, root.name, root.version))
    design_id = get_handle(root)

    name = "bad·name" if invalid == "bad-connection-name" else "external_link"
    port_ref = "bad port" if invalid == "bad-port-name" else "top_data"
    instance_ref = "bad instance" if invalid == "bad-instance-name" else "unknown_instance"
    with pytest.raises(TgiError) as error:
        if builder == "internal":
            api.addDesignAdHocConnection(design_id, name, instance_ref, port_ref)
        else:
            api.addDesignExternalAdHocConnection(design_id, name, port_ref)
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert root.ad_hoc_connections is None
    assert api.getDesignAdHocConnectionIDs(design_id) == []


@pytest.mark.parametrize("builder", ("internal", "external"), ids=("internal-builder", "external-builder"))
def test_design_ad_hoc_builders_reject_duplicate_normalized_names_atomically(builder: str) -> None:
    existing = _connection("existing", (_internal(),))
    root = _design([existing])
    registry.register(root, (root.vendor, root.library, root.name, root.version))
    design_id = get_handle(root)
    holder = root.ad_hoc_connections
    connections = tuple(holder.ad_hoc_connection)
    connection_ids = tuple(get_handle(connection) for connection in connections)

    with pytest.raises(TgiError) as error:
        if builder == "internal":
            api.addDesignAdHocConnection(design_id, " existing \n", "u_core", "new_port")
        else:
            api.addDesignExternalAdHocConnection(design_id, "\texisting ", "new_port")
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert root.ad_hoc_connections is holder
    assert tuple(holder.ad_hoc_connection) == connections
    assert tuple(get_handle(connection) for connection in holder.ad_hoc_connection) == connection_ids


@pytest.mark.parametrize("builder", ("internal", "external"), ids=("internal-builder", "external-builder"))
def test_design_ad_hoc_builders_reject_malformed_existing_connection_names(builder: str) -> None:
    existing = _connection("existing", (_internal(),))
    root = _design([existing])
    registry.register(root, (root.vendor, root.library, root.name, root.version))
    design_id = get_handle(root)
    existing.name = object()
    connections = tuple(root.ad_hoc_connections.ad_hoc_connection)

    with pytest.raises(TgiError) as error:
        if builder == "internal":
            api.addDesignAdHocConnection(design_id, "new_internal", "u_core", "new_port")
        else:
            api.addDesignExternalAdHocConnection(design_id, "new_external", "new_port")
    assert error.value.fault_code == TgiFaultCode.INVALID_ID
    assert tuple(root.ad_hoc_connections.ad_hoc_connection) == connections


def test_removers_enforce_model_owner_invalidate_descendants_and_preserve_siblings() -> None:
    external_sub = SubPortReference(sub_port_ref="payload", part_select=_part_select())
    internal_sub = SubPortReference(sub_port_ref="payload", part_select=_part_select())
    external = _external("top_data", sub_refs=(external_sub,), part_select=_part_select())
    internal = _internal("core_data", sub_refs=(internal_sub,), part_select=_part_select())
    connection = _connection("first", (internal, external))
    sibling_connection = _connection("sibling", (_internal("other_data"),))
    root = _design([connection, sibling_connection])
    holder = connection.port_references
    registry.register(root, (root.vendor, root.library, root.name, root.version))
    design_id = get_handle(root)
    connection_id = get_handle(connection)
    internal_id = api.getAdHocConnectionInternalPortReferenceIDs(connection_id)[0]
    external_id = api.getAdHocConnectionExternalPortReferenceIDs(connection_id)[0]
    nested_handles = (
        get_handle(internal_sub),
        get_handle(internal_sub.part_select),
        get_handle(external_sub),
        get_handle(external_sub.part_select),
        get_handle(internal.part_select),
        get_handle(external.part_select),
    )

    assert api.removeAdHocConnectionExternalPortReference(external_id)
    assert connection.port_references.internal_port_reference_or_external_port_reference == [internal]
    assert resolve_handle(nested_handles[0]) is internal_sub
    assert resolve_handle(nested_handles[1]) is internal_sub.part_select
    assert all(resolve_handle(handle) is None for handle in nested_handles[2:4])
    assert resolve_handle(nested_handles[4]) is internal.part_select
    with pytest.raises(TgiError) as error:
        api.removeAdHocConnectionExternalPortReference(external_id)
    assert error.value.fault_code == TgiFaultCode.INVALID_ID
    with pytest.raises(TgiError) as error:
        api.removeAdHocConnectionExternalPortReference(internal_id)
    assert error.value.fault_code == TgiFaultCode.INVALID_ID

    assert api.removeAdHocConnectionInternalPortReference(internal_id)
    assert connection.port_references is holder
    assert connection.port_references.internal_port_reference_or_external_port_reference == []
    assert resolve_handle(nested_handles[4]) is None
    assert resolve_handle(nested_handles[5]) is None
    assert api.getDesignAdHocConnectionIDs(design_id) == [connection_id, get_handle(sibling_connection)]
    assert resolve_handle(get_handle(sibling_connection)) is sibling_connection

    with pytest.raises(TgiError) as error:
        api.removeAdHocConnectionInternalPortReference(external_id)
    assert error.value.fault_code == TgiFaultCode.INVALID_ID
    with pytest.raises(TgiError) as error:
        api.removeAdHocConnectionExternalPortReference("stale-reference")
    assert error.value.fault_code == TgiFaultCode.INVALID_ID
    assert resolve_handle(get_handle(root)) is root


@pytest.mark.parametrize("owner_kind", ("external", "internal"), ids=_OWNER_IDS)
def test_endpoint_removers_reject_orphans_and_references_in_wrong_connection_field(owner_kind: str) -> None:
    root, connection = _registered_case()
    holder = connection.port_references
    original_references = holder.internal_port_reference_or_external_port_reference
    wrong_field_reference: _Reference
    if owner_kind == "external":
        wrong_field_reference = _external("wrong_field")
        connection.vendor_extensions = cast(VendorExtensions, wrong_field_reference)
    else:
        wrong_field_reference = _internal("wrong_field")
        connection.tied_value = cast(ComplexTiedValueExpression, wrong_field_reference)
    wrong_field_id = get_handle(wrong_field_reference)
    remover = _REMOVERS[owner_kind]

    with pytest.raises(TgiError) as error:
        remover(wrong_field_id)
    assert error.value.fault_code == TgiFaultCode.INVALID_ID
    assert connection.port_references is holder
    assert holder.internal_port_reference_or_external_port_reference is original_references
    assert tuple(original_references) == ()
    if owner_kind == "external":
        assert connection.vendor_extensions is wrong_field_reference
    else:
        assert connection.tied_value is wrong_field_reference
    assert resolve_handle(wrong_field_id) is wrong_field_reference

    orphan = _external("orphan") if owner_kind == "external" else _internal("orphan")
    with pytest.raises(TgiError) as error:
        remover(get_handle(orphan))
    assert error.value.fault_code == TgiFaultCode.INVALID_ID
    assert resolve_handle(get_handle(root)) is root


def test_connection_removal_invalidates_tree_and_rejects_stale_or_wrong_model() -> None:
    sub_reference = SubPortReference(sub_port_ref="payload", part_select=_part_select())
    external = _external("top_data", sub_refs=(sub_reference,), part_select=_part_select())
    connection = _connection("remove_me", (external,))
    sibling = _connection("keep_me", (_internal("core_data"),))
    root = _design([connection, sibling])
    registry.register(root, (root.vendor, root.library, root.name, root.version))
    design_id = get_handle(root)
    connection_id = api.getDesignAdHocConnectionIDs(design_id)[0]
    handles = (
        connection_id,
        get_handle(connection.port_references),
        get_handle(external),
        get_handle(external.part_select),
        get_handle(sub_reference),
        get_handle(sub_reference.part_select),
    )

    assert api.removeDesignAdHocConnection(connection_id)
    assert api.getDesignAdHocConnectionIDs(design_id) == [get_handle(sibling)]
    assert all(resolve_handle(handle) is None for handle in handles)
    with pytest.raises(TgiError) as error:
        api.removeDesignAdHocConnection(connection_id)
    assert error.value.fault_code == TgiFaultCode.INVALID_ID
    with pytest.raises(TgiError) as error:
        api.removeDesignAdHocConnection(get_handle(external))
    assert error.value.fault_code == TgiFaultCode.INVALID_ID
    assert resolve_handle(get_handle(sibling)) is sibling


def test_parsed_design_ad_hoc_lifecycle_round_trips_after_addition_and_removal() -> None:
    original_connection = _connection("existing", (_internal(), _external()))
    root = _design([original_connection])
    xml = XmlDocument.serializer().render(root)
    assert _SCHEMA.validate(etree.fromstring(xml.encode())), _SCHEMA.error_log
    parsed = XmlDocument.parser().from_string(xml, Design)
    assert XmlDocument.serializer().render(parsed) == xml
    registry.register(parsed, (parsed.vendor, parsed.library, parsed.name, parsed.version))
    design_id = get_handle(parsed)
    parsed_connection = parsed.ad_hoc_connections.ad_hoc_connection[0]
    connection_id = api.getDesignAdHocConnectionIDs(design_id)[0]
    original_internal, original_external = (
        parsed_connection.port_references.internal_port_reference_or_external_port_reference
    )

    added_internal_id = api.addAdHocConnectionInternalPortReference(connection_id, "u_core", "core_data")
    added_external_id = api.addAdHocConnectionExternalPortReference(connection_id, "top_data")
    built_internal_id = api.addDesignAdHocConnection(design_id, "built_internal", "u_core", "core_data")
    built_external_id = api.addDesignExternalAdHocConnection(design_id, "built_external", "top_data")
    ordered_ids = api.getDesignAdHocConnectionIDs(design_id)
    assert ordered_ids == [connection_id, built_internal_id, built_external_id]
    assert api.getAdHocConnectionInternalPortReferenceIDs(connection_id) == [
        get_handle(original_internal),
        added_internal_id,
    ]
    assert api.getAdHocConnectionExternalPortReferenceIDs(connection_id) == [
        get_handle(original_external),
        added_external_id,
    ]
    xml_after_add = XmlDocument.serializer().render(parsed)
    assert _SCHEMA.validate(etree.fromstring(xml_after_add.encode())), _SCHEMA.error_log
    parsed_after_add = XmlDocument.parser().from_string(xml_after_add, Design)
    assert XmlDocument.serializer().render(parsed_after_add) == xml_after_add

    assert api.removeAdHocConnectionInternalPortReference(added_internal_id)
    assert api.removeAdHocConnectionExternalPortReference(added_external_id)
    assert api.removeDesignAdHocConnection(built_internal_id)
    assert api.removeDesignAdHocConnection(built_external_id)
    xml_after_remove = XmlDocument.serializer().render(parsed)
    assert _SCHEMA.validate(etree.fromstring(xml_after_remove.encode())), _SCHEMA.error_log
    assert (
        XmlDocument.serializer().render(XmlDocument.parser().from_string(xml_after_remove, Design)) == xml_after_remove
    )


def test_design_ad_hoc_lifecycle_operations_export_annex_signatures() -> None:
    expected = {
        "addAdHocConnectionExternalPortReference": (
            ("adHocConnectionID", "portRef"),
            (str, str),
            str,
        ),
        "addAdHocConnectionInternalPortReference": (
            ("adHocConnectionID", "componentInstanceRef", "portRef"),
            (str, str, str),
            str,
        ),
        "removeAdHocConnectionExternalPortReference": (("externalPortReferenceID",), (str,), bool),
        "removeAdHocConnectionInternalPortReference": (("internalPortReferenceID",), (str,), bool),
        "getDesignAdHocConnectionIDs": (("designID",), (str,), list[str]),
        "removeDesignAdHocConnection": (("adHocConnectionID",), (str,), bool),
        "addDesignAdHocConnection": (
            ("designID", "name", "componentInstanceRef", "portRef"),
            (str, str, str, str),
            str,
        ),
        "addDesignExternalAdHocConnection": (("designID", "name", "portRef"), (str, str, str), str),
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

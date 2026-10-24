"""Design active, hierarchical, and excluded interface lifecycle operations."""

import inspect
from collections.abc import Callable, Iterator, Sequence
from pathlib import Path

import pytest
from lxml import etree

from amal.eda.accellera.ipxact.v1685_2022 import tgi
from amal.eda.accellera.ipxact.v1685_2022.tgi import design as api
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import (
    TgiError,
    TgiFaultCode,
    get_handle,
    get_parent_info,
    register_parent,
    registry,
    resolve_handle,
)
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import (
    ActiveInterface,
    ComponentInstance,
    ComponentInstances,
    ConfigurableLibraryRefType,
    Description,
    Design,
    HierInterfaceType,
    InstanceName,
    Interconnection,
    Interconnections,
)

_REPO_ROOT = Path(__file__).resolve().parents[5]
_SCHEMA = etree.XMLSchema(etree.parse(str(_REPO_ROOT / "submodules/accellera-schemas/IPXACT/1685-2022/index.xsd")))
_API_FUNCTIONS = (
    "getActiveinterfaceExcludePortIDs",
    "getInterconnectionActiveInterfaceIDs",
    "getInterconnectionHierInterfaceIDs",
    "addActiveInterfaceExcludePort",
    "addInterconnectionActiveInterface",
    "addInterconnectionHierInterface",
    "removeActiveInterfaceExcludePort",
    "removeInterconnectionActiveInterface",
    "removeInterconnectionHierInterface",
)
_ExcludePort = ActiveInterface.ExcludePorts.ExcludePort


@pytest.fixture(autouse=True)
def clean_registry() -> Iterator[None]:
    registry.clear()
    yield
    registry.clear()


def _active(
    instance: str = "u0",
    bus: str = "bus0",
    *,
    exclude_ports: Sequence[_ExcludePort] = (),
    description: str | None = None,
) -> ActiveInterface:
    excludes = ActiveInterface.ExcludePorts(exclude_port=exclude_ports) if exclude_ports else None
    return ActiveInterface(
        component_instance_ref=instance,
        bus_ref=bus,
        exclude_ports=excludes,
        description=Description(value=description) if description is not None else None,
    )


def _connection(
    name: str = "wire",
    *,
    active_interfaces: Sequence[ActiveInterface] = (),
    hier_interfaces: Sequence[HierInterfaceType] = (),
    description: str | None = None,
) -> Interconnection:
    return Interconnection(
        name=name,
        active_interface=active_interfaces,
        hier_interface=hier_interfaces,
        description=Description(value=description) if description is not None else None,
    )


def _design(connection: Interconnection, *, name: str = "interface_lifecycle") -> Design:
    instance_names = sorted({interface.component_instance_ref for interface in connection.active_interface})
    return Design(
        vendor="vendor",
        library="library",
        name=name,
        version="1",
        component_instances=ComponentInstances(
            component_instance=[
                ComponentInstance(
                    instance_name=InstanceName(value=instance_name),
                    component_ref=ConfigurableLibraryRefType(
                        vendor="vendor", library="library", name="component", version="1"
                    ),
                )
                for instance_name in instance_names
            ]
        ),
        interconnections=Interconnections(interconnection_or_monitor_interconnection=[connection]),
    )


def _registered_case(
    *,
    active_interfaces: Sequence[ActiveInterface] | None = None,
    hier_interfaces: Sequence[HierInterfaceType] = (),
    name: str = "interface_lifecycle",
) -> tuple[Design, Interconnection]:
    if active_interfaces is None:
        active_interfaces = (_active("u0", "bus0"), _active("u1", "bus1"))
    connection = _connection("wire", active_interfaces=active_interfaces, hier_interfaces=hier_interfaces)
    root = _design(connection, name=name)
    registry.register(root, (root.vendor, root.library, root.name, root.version))
    return root, connection


def _register_parsed(root: Design) -> Design:
    xml = XmlDocument.serializer().render(root)
    assert _SCHEMA.validate(etree.fromstring(xml.encode())), _SCHEMA.error_log
    parsed = XmlDocument.parser().from_string(xml, Design)
    registry.register(parsed, (parsed.vendor, parsed.library, parsed.name, parsed.version))
    return parsed


def test_public_exports_and_annex_f_signatures() -> None:
    expected = {
        "getActiveinterfaceExcludePortIDs": (("activeInterfaceID",), (str,), list[str]),
        "getInterconnectionActiveInterfaceIDs": (("interconnectionID",), (str,), list[str]),
        "getInterconnectionHierInterfaceIDs": (("interconnectionID",), (str,), list[str]),
        "addActiveInterfaceExcludePort": (("activeInterfaceID", "excludePort"), (str, str), str),
        "addInterconnectionActiveInterface": (
            ("interconnectionID", "componentInstanceRef", "busInterfaceRef"),
            (str, str, str),
            str,
        ),
        "addInterconnectionHierInterface": (("interconnectionID", "busInterfaceRef"), (str, str), str),
        "removeActiveInterfaceExcludePort": (("excludePortID",), (str,), bool),
        "removeInterconnectionActiveInterface": (("activeInterfaceID",), (str,), bool),
        "removeInterconnectionHierInterface": (("hierInterfaceID",), (str,), bool),
    }

    assert set(expected) == set(_API_FUNCTIONS)
    assert set(expected) <= set(api.__all__)
    assert set(expected) <= set(tgi.__all__)
    sections = {
        "getActiveinterfaceExcludePortIDs": "F.7.37.1",
        "getInterconnectionActiveInterfaceIDs": "F.7.37.21",
        "getInterconnectionHierInterfaceIDs": "F.7.37.22",
        "addActiveInterfaceExcludePort": "F.7.38.1",
        "addInterconnectionActiveInterface": "F.7.38.10",
        "addInterconnectionHierInterface": "F.7.38.11",
        "removeActiveInterfaceExcludePort": "F.7.38.13",
        "removeInterconnectionActiveInterface": "F.7.38.24",
        "removeInterconnectionHierInterface": "F.7.38.25",
    }
    for name, (parameter_names, parameter_types, return_type) in expected.items():
        function = getattr(api, name)
        assert getattr(tgi, name) is function
        signature = inspect.signature(function)
        assert tuple(signature.parameters) == parameter_names
        assert tuple(parameter.annotation for parameter in signature.parameters.values()) == parameter_types
        assert all(not isinstance(parameter.annotation, str) for parameter in signature.parameters.values())
        assert signature.return_annotation == return_type
        assert f"Section: {sections[name]}." in inspect.getdoc(function)


def test_getters_read_tuple_collections_and_register_immediate_ownership() -> None:
    first_exclude = _ExcludePort(value="old_a")
    second_exclude = _ExcludePort(value="old_b")
    first_active = _active("u0", "bus0", exclude_ports=(first_exclude, second_exclude))
    second_active = _active("u1", "bus1")
    first_hier = HierInterfaceType(bus_ref="top_bus")
    second_hier = HierInterfaceType(bus_ref="other_bus")
    root, connection = _registered_case(
        active_interfaces=(first_active, second_active), hier_interfaces=(first_hier, second_hier)
    )
    active_tuple = tuple(connection.active_interface)
    hier_tuple = tuple(connection.hier_interface)
    exclude_tuple = tuple(first_active.exclude_ports.exclude_port)
    connection.active_interface = active_tuple
    connection.hier_interface = hier_tuple
    first_active.exclude_ports.exclude_port = exclude_tuple

    active_ids = api.getInterconnectionActiveInterfaceIDs(get_handle(connection))
    hier_ids = api.getInterconnectionHierInterfaceIDs(get_handle(connection))
    exclude_ids = api.getActiveinterfaceExcludePortIDs(get_handle(first_active))

    assert active_ids == [get_handle(first_active), get_handle(second_active)]
    assert hier_ids == [get_handle(first_hier), get_handle(second_hier)]
    assert exclude_ids == [get_handle(first_exclude), get_handle(second_exclude)]
    assert connection.active_interface is active_tuple
    assert connection.hier_interface is hier_tuple
    assert first_active.exclude_ports.exclude_port is exclude_tuple
    expected_parent_paths = (
        (get_handle(first_active), get_handle(connection), ("active_interface",)),
        (get_handle(first_hier), get_handle(connection), ("hier_interface",)),
        (get_handle(first_exclude), get_handle(first_active.exclude_ports), ("exclude_port",)),
    )
    for child_id, parent_id, path in expected_parent_paths:
        info = get_parent_info(child_id)
        assert info is not None
        assert (info.parent_handle, info.path, info.container) == (parent_id, path, "list")
    assert resolve_handle(get_handle(root)) is root


@pytest.mark.parametrize(
    "getter,owner",
    [
        (api.getActiveinterfaceExcludePortIDs, "wrong_active"),
        (api.getInterconnectionActiveInterfaceIDs, "wrong_interconnection"),
        (api.getInterconnectionHierInterfaceIDs, "wrong_interconnection"),
    ],
)
def test_getters_reject_wrong_owner_and_stale_handles(getter: Callable[[str], list[str]], owner: str) -> None:
    root, connection = _registered_case()
    wrong_owner = connection if owner == "wrong_active" else root
    with pytest.raises(TgiError) as error:
        getter(get_handle(wrong_owner))
    assert error.value.fault_code == TgiFaultCode.INVALID_ID
    with pytest.raises(TgiError) as error:
        getter("stale-interface-owner")
    assert error.value.fault_code == TgiFaultCode.INVALID_ID


@pytest.mark.parametrize(
    "kind,malformation",
    [
        ("exclude-holder", "wrong-type"),
        ("exclude-list", "non-sequence"),
        ("exclude-list", "wrong-child"),
        ("active-list", "non-sequence"),
        ("active-list", "wrong-child"),
        ("hier-list", "non-sequence"),
        ("hier-list", "wrong-child"),
    ],
)
def test_getters_reject_malformed_holders_collections_and_children(kind: str, malformation: str) -> None:
    root, connection = _registered_case()
    active = connection.active_interface[0]
    malformed = object() if malformation == "non-sequence" else [object()]
    if kind == "exclude-holder":
        active.exclude_ports = malformed  # type: ignore[assignment]
        getter = api.getActiveinterfaceExcludePortIDs
        owner_id = get_handle(active)
    elif kind == "exclude-list":
        if active.exclude_ports is None:
            active.exclude_ports = ActiveInterface.ExcludePorts()
        active.exclude_ports.exclude_port = malformed  # type: ignore[assignment]
        getter = api.getActiveinterfaceExcludePortIDs
        owner_id = get_handle(active)
    elif kind == "active-list":
        connection.active_interface = malformed  # type: ignore[assignment]
        getter = api.getInterconnectionActiveInterfaceIDs
        owner_id = get_handle(connection)
    else:
        connection.hier_interface = malformed  # type: ignore[assignment]
        getter = api.getInterconnectionHierInterfaceIDs
        owner_id = get_handle(connection)

    with pytest.raises(TgiError) as error:
        getter(owner_id)
    assert error.value.fault_code == TgiFaultCode.INVALID_ID
    assert resolve_handle(get_handle(root)) is root


def test_adders_collapse_names_preserve_existing_metadata_and_append_in_order() -> None:
    first_exclude = _ExcludePort(value="keep_port")
    first_active = _active("u0", "bus0", exclude_ports=(first_exclude,), description="Keep this interface")
    second_active = _active("u1", "bus1", description="Keep this sibling")
    existing_hier = HierInterfaceType(bus_ref="top_bus")
    root, connection = _registered_case(
        active_interfaces=(first_active, second_active), hier_interfaces=(existing_hier,)
    )
    connection.description = Description(value="Keep connection documentation")
    existing_actives = tuple(connection.active_interface)
    existing_hier_interfaces = tuple(connection.hier_interface)
    holder = first_active.exclude_ports

    exclude_id = api.addActiveInterfaceExcludePort(get_handle(first_active), " \tnew_port\r\n")
    active_id = api.addInterconnectionActiveInterface(get_handle(connection), " \tu_new\n", "\tnew_bus ")
    hier_id = api.addInterconnectionHierInterface(get_handle(connection), " \ttop_new\r\n")

    added_exclude = resolve_handle(exclude_id)
    added_active = resolve_handle(active_id)
    added_hier = resolve_handle(hier_id)
    assert isinstance(added_exclude, _ExcludePort) and added_exclude.value == "new_port"
    assert isinstance(added_active, ActiveInterface)
    assert (added_active.component_instance_ref, added_active.bus_ref) == ("u_new", "new_bus")
    assert isinstance(added_hier, HierInterfaceType) and added_hier.bus_ref == "top_new"
    assert connection.active_interface == [*existing_actives, added_active]
    assert connection.hier_interface == [*existing_hier_interfaces, added_hier]
    assert first_active.exclude_ports is holder
    assert holder.exclude_port == [first_exclude, added_exclude]
    assert first_active.description == Description(value="Keep this interface")
    assert second_active.description == Description(value="Keep this sibling")
    assert connection.description == Description(value="Keep connection documentation")
    for child_id, parent_id, path in (
        (exclude_id, get_handle(holder), ("exclude_port",)),
        (active_id, get_handle(connection), ("active_interface",)),
        (hier_id, get_handle(connection), ("hier_interface",)),
    ):
        info = get_parent_info(child_id)
        assert info is not None and (info.parent_handle, info.path, info.container) == (parent_id, path, "list")
    assert resolve_handle(get_handle(root)) is root


def test_adders_create_and_retain_required_exclude_holder_and_do_not_resolve_endpoints() -> None:
    active = _active("u_existing", "bus_existing")
    connection = _connection("unresolved", active_interfaces=(active,))
    root = _design(connection)
    # Editing validates XML names, while connectivity resolution belongs to later validation.
    root.component_instances.component_instance.clear()
    registry.register(root, (root.vendor, root.library, root.name, root.version))

    exclude_id = api.addActiveInterfaceExcludePort(get_handle(active), "port_new")
    active_id = api.addInterconnectionActiveInterface(get_handle(connection), "missing_instance", "missing_bus")
    hier_id = api.addInterconnectionHierInterface(get_handle(connection), "unresolved_hier_bus")

    assert active.exclude_ports is not None
    assert active.exclude_ports.exclude_port == [resolve_handle(exclude_id)]
    assert (resolve_handle(active_id).component_instance_ref, resolve_handle(active_id).bus_ref) == (
        "missing_instance",
        "missing_bus",
    )
    assert resolve_handle(hier_id).bus_ref == "unresolved_hier_bus"


def test_interface_name_values_follow_their_schema_name_types() -> None:
    _root, connection = _registered_case()
    active_id = api.addInterconnectionActiveInterface(get_handle(connection), "u·new", "bus·new")
    active = resolve_handle(active_id)
    assert (active.component_instance_ref, active.bus_ref) == ("u·new", "bus·new")


@pytest.mark.parametrize(
    "operation,arguments",
    [
        ("exclude", ("bad port",)),
        ("exclude", ("data·i",)),
        ("active", ("bad instance", "bus")),
        ("active", ("instance", "bad bus")),
        ("active", ("1bad", "bus")),
        ("hier", ("bad bus",)),
        ("hier", ("1bad",)),
    ],
    ids=("exclude-space", "exclude-name", "instance-space", "bus-space", "instance-name", "hier-space", "hier-name"),
)
def test_adders_reject_invalid_names_before_mutation(operation: str, arguments: tuple[str, ...]) -> None:
    active = _active("u0", "bus0", exclude_ports=(_ExcludePort(value="before"),))
    root, connection = _registered_case(active_interfaces=(active, _active("u1", "bus1")))
    active_before = tuple(connection.active_interface)
    hier_before = tuple(connection.hier_interface)
    exclude_before = tuple(active.exclude_ports.exclude_port)

    with pytest.raises(TgiError) as error:
        if operation == "exclude":
            api.addActiveInterfaceExcludePort(get_handle(active), arguments[0])
        elif operation == "active":
            api.addInterconnectionActiveInterface(get_handle(connection), arguments[0], arguments[1])
        else:
            api.addInterconnectionHierInterface(get_handle(connection), arguments[0])

    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert tuple(connection.active_interface) == active_before
    assert tuple(connection.hier_interface) == hier_before
    assert tuple(active.exclude_ports.exclude_port) == exclude_before
    assert resolve_handle(get_handle(root)) is root


@pytest.mark.parametrize(
    "operation,field,malformation",
    [
        ("exclude", "exclude_ports", "wrong-holder"),
        ("exclude", "exclude_port", "non-sequence"),
        ("exclude", "exclude_port", "wrong-child"),
        ("active", "active_interface", "non-sequence"),
        ("active", "active_interface", "wrong-child"),
        ("hier", "hier_interface", "non-sequence"),
        ("hier", "hier_interface", "wrong-child"),
    ],
)
def test_adders_reject_malformed_collections_atomically(operation: str, field: str, malformation: str) -> None:
    active = _active("u0", "bus0", exclude_ports=(_ExcludePort(value="existing"),))
    root, connection = _registered_case(active_interfaces=(active, _active("u1", "bus1")))
    owner = active if field == "exclude_ports" else active.exclude_ports if field == "exclude_port" else connection
    malformed = object() if malformation in ("non-sequence", "wrong-holder") else [object()]
    setattr(owner, field, malformed)
    before_holder = active.exclude_ports
    before_active = connection.active_interface
    before_hier = connection.hier_interface

    with pytest.raises(TgiError) as error:
        if operation == "exclude":
            api.addActiveInterfaceExcludePort(get_handle(active), "new_port")
        elif operation == "active":
            api.addInterconnectionActiveInterface(get_handle(connection), "u_new", "bus_new")
        else:
            api.addInterconnectionHierInterface(get_handle(connection), "top_new")

    assert error.value.fault_code == TgiFaultCode.INVALID_ID
    assert active.exclude_ports is before_holder
    assert getattr(owner, field) is malformed
    assert connection.active_interface is before_active
    assert connection.hier_interface is before_hier
    assert resolve_handle(get_handle(root)) is root


@pytest.mark.parametrize("field", ("active_interface", "hier_interface"), ids=("active", "hier"))
def test_adders_normalize_tuple_storage_without_replacing_existing_children(field: str) -> None:
    active = _active("u0", "bus0")
    hierarchical = HierInterfaceType(bus_ref="top_bus")
    root, connection = _registered_case(active_interfaces=(active,), hier_interfaces=(hierarchical,))
    original = tuple(getattr(connection, field))
    setattr(connection, field, original)

    if field == "active_interface":
        new_id = api.addInterconnectionActiveInterface(get_handle(connection), "u_new", "bus_new")
        expected = [active, resolve_handle(new_id)]
    else:
        new_id = api.addInterconnectionHierInterface(get_handle(connection), "top_new")
        expected = [hierarchical, resolve_handle(new_id)]

    assert isinstance(getattr(connection, field), list)
    assert getattr(connection, field) == expected
    assert tuple(getattr(connection, field)[:1]) == original
    assert resolve_handle(get_handle(root)) is root


def test_exclude_port_adder_normalizes_tuple_storage_and_keeps_the_holder() -> None:
    existing = _ExcludePort(value="old_port")
    active = _active("u0", "bus0", exclude_ports=(existing,))
    root, _connection_value = _registered_case(active_interfaces=(active, _active("u1", "bus1")))
    holder = active.exclude_ports
    original = tuple(holder.exclude_port)
    holder.exclude_port = original

    new_id = api.addActiveInterfaceExcludePort(get_handle(active), "new_port")

    assert active.exclude_ports is holder
    assert isinstance(holder.exclude_port, list)
    assert holder.exclude_port == [existing, resolve_handle(new_id)]
    assert tuple(holder.exclude_port[:1]) == original
    assert resolve_handle(get_handle(root)) is root


def test_removers_require_real_membership_preserve_empty_holders_and_invalidate_removed_trees() -> None:
    first_exclude = _ExcludePort(value="remove_port")
    keep_exclude = _ExcludePort(value="keep_port")
    first = _active("u0", "bus0", exclude_ports=(first_exclude, keep_exclude))
    second = _active("u1", "bus1", exclude_ports=(_ExcludePort(value="sibling_port"),))
    hierarchical = HierInterfaceType(bus_ref="top_bus")
    sibling_hierarchical = HierInterfaceType(bus_ref="other_top_bus")
    connection = _connection(
        "remove_one",
        active_interfaces=(first, second),
        hier_interfaces=(hierarchical, sibling_hierarchical),
    )
    root = _register_parsed(_design(connection))
    parsed_connection = root.interconnections.interconnection_or_monitor_interconnection[0]
    active_ids = api.getInterconnectionActiveInterfaceIDs(get_handle(parsed_connection))
    hier_ids = api.getInterconnectionHierInterfaceIDs(get_handle(parsed_connection))
    parsed_first = resolve_handle(active_ids[0])
    parsed_second = resolve_handle(active_ids[1])
    parsed_holder = parsed_first.exclude_ports
    exclude_ids = api.getActiveinterfaceExcludePortIDs(active_ids[0])
    removed_exclude_id, kept_exclude_id = exclude_ids
    removed_active_id = active_ids[0]
    removed_hier_id = hier_ids[0]
    removed_active_descendants = (get_handle(parsed_first.exclude_ports), removed_exclude_id, kept_exclude_id)
    parsed_active_children = tuple(parsed_connection.active_interface)
    parsed_hier_children = tuple(parsed_connection.hier_interface)
    parsed_connection.active_interface = parsed_active_children
    parsed_connection.hier_interface = parsed_hier_children
    parsed_holder.exclude_port = tuple(parsed_holder.exclude_port)

    assert api.removeActiveInterfaceExcludePort(removed_exclude_id)
    assert parsed_first.exclude_ports is parsed_holder
    assert parsed_holder.exclude_port == [resolve_handle(kept_exclude_id)]
    assert resolve_handle(removed_exclude_id) is None
    assert resolve_handle(kept_exclude_id) is not None

    assert api.removeInterconnectionActiveInterface(removed_active_id)
    assert parsed_connection.active_interface == [parsed_second]
    assert resolve_handle(removed_active_id) is None
    assert resolve_handle(removed_active_descendants[0]) is None
    assert resolve_handle(kept_exclude_id) is None
    assert resolve_handle(get_handle(parsed_second)) is parsed_second

    assert api.removeInterconnectionHierInterface(removed_hier_id)
    assert parsed_connection.hier_interface == [parsed_hier_children[1]]
    assert resolve_handle(removed_hier_id) is None
    assert resolve_handle(get_handle(parsed_hier_children[1])) is parsed_hier_children[1]
    assert parsed_active_children == (parsed_first, parsed_second)
    assert parsed_connection.active_interface == [parsed_second]
    assert api.getDesignInterconnectionIDs(get_handle(root)) == [get_handle(parsed_connection)]


def test_removers_discover_direct_ownership_in_a_registered_parsed_design() -> None:
    first = _active("u0", "bus0", exclude_ports=(_ExcludePort(value="remove_me"), _ExcludePort(value="keep_me")))
    second = _active("u1", "bus1")
    hierarchical = HierInterfaceType(bus_ref="top_bus")
    parsed = _register_parsed(
        _design(_connection("direct_removal", active_interfaces=(first, second), hier_interfaces=(hierarchical,)))
    )
    parsed_connection = parsed.interconnections.interconnection_or_monitor_interconnection[0]
    parsed_first = parsed_connection.active_interface[0]
    exclude = parsed_first.exclude_ports.exclude_port[0]
    kept_exclude = parsed_first.exclude_ports.exclude_port[1]
    active = parsed_first
    kept_active = parsed_connection.active_interface[1]

    exclude_id = get_handle(exclude)
    active_id = get_handle(active)
    hier_interface = parsed_connection.hier_interface[0]
    hier_id = get_handle(hier_interface)
    assert get_parent_info(exclude_id) is None
    assert get_parent_info(active_id) is None
    assert get_parent_info(hier_id) is None

    assert api.removeActiveInterfaceExcludePort(exclude_id)
    assert api.removeInterconnectionActiveInterface(active_id)
    assert api.removeInterconnectionHierInterface(hier_id)
    assert parsed_first.exclude_ports.exclude_port == [kept_exclude]
    assert parsed_connection.active_interface == [kept_active]
    assert parsed_connection.hier_interface == []
    assert resolve_handle(exclude_id) is None
    assert resolve_handle(active_id) is None
    assert resolve_handle(hier_id) is None


@pytest.mark.parametrize("operation", ("exclude", "active", "hier"))
def test_removers_reject_malformed_owner_collections_without_detaching_children(operation: str) -> None:
    active = _active("u0", "bus0", exclude_ports=(_ExcludePort(value="keep_port"),))
    root, connection = _registered_case(
        active_interfaces=(active, _active("u1", "bus1")), hier_interfaces=(HierInterfaceType(bus_ref="top"),)
    )
    if operation == "exclude":
        child = active.exclude_ports.exclude_port[0]
        child_id = api.getActiveinterfaceExcludePortIDs(get_handle(active))[0]
        active.exclude_ports = object()  # type: ignore[assignment]
        remove = api.removeActiveInterfaceExcludePort
    elif operation == "active":
        child = connection.active_interface[0]
        child_id = api.getInterconnectionActiveInterfaceIDs(get_handle(connection))[0]
        connection.active_interface = object()  # type: ignore[assignment]
        remove = api.removeInterconnectionActiveInterface
    else:
        child = connection.hier_interface[0]
        child_id = api.getInterconnectionHierInterfaceIDs(get_handle(connection))[0]
        connection.hier_interface = object()  # type: ignore[assignment]
        remove = api.removeInterconnectionHierInterface

    with pytest.raises(TgiError) as error:
        remove(child_id)
    assert error.value.fault_code == TgiFaultCode.INVALID_ID
    assert resolve_handle(child_id) is child
    assert resolve_handle(get_handle(root)) is root


def test_removing_the_last_exclude_port_retains_its_empty_required_holder() -> None:
    active = _active("u0", "bus0", exclude_ports=(_ExcludePort(value="only_port"),))
    _root, _connection_value = _registered_case(active_interfaces=(active, _active("u1", "bus1")))
    holder = active.exclude_ports
    exclude_id = api.getActiveinterfaceExcludePortIDs(get_handle(active))[0]

    assert api.removeActiveInterfaceExcludePort(exclude_id)
    assert active.exclude_ports is holder
    assert holder.exclude_port == []
    assert resolve_handle(exclude_id) is None


def test_removers_reject_orphans_stale_handles_and_misparented_children() -> None:
    first = _active("u0", "bus0")
    second = _active("u1", "bus1")
    root, connection = _registered_case(active_interfaces=(first, second))
    other_connection = _connection("other_wire", active_interfaces=(_active("u2", "bus2"),))
    root.interconnections.interconnection_or_monitor_interconnection.append(other_connection)
    active_ids = api.getInterconnectionActiveInterfaceIDs(get_handle(connection))
    first_id, second_id = active_ids

    # A forged owner link must not detach an object from a different connection.
    register_parent(resolve_handle(first_id), other_connection, ("active_interface",), "list")
    with pytest.raises(TgiError) as error:
        api.removeInterconnectionActiveInterface(first_id)
    assert error.value.fault_code == TgiFaultCode.INVALID_ID
    assert tuple(connection.active_interface) == (first, second)
    assert resolve_handle(first_id) is first

    with pytest.raises(TgiError) as error:
        api.removeInterconnectionHierInterface(first_id)
    assert error.value.fault_code == TgiFaultCode.INVALID_ID
    orphan = _ExcludePort(value="orphan")
    with pytest.raises(TgiError) as error:
        api.removeActiveInterfaceExcludePort(get_handle(orphan))
    assert error.value.fault_code == TgiFaultCode.INVALID_ID
    with pytest.raises(TgiError) as error:
        api.removeInterconnectionActiveInterface("stale-active-interface")
    assert error.value.fault_code == TgiFaultCode.INVALID_ID
    with pytest.raises(TgiError) as error:
        api.removeInterconnectionHierInterface("stale-hier-interface")
    assert error.value.fault_code == TgiFaultCode.INVALID_ID
    with pytest.raises(TgiError) as error:
        api.removeActiveInterfaceExcludePort("stale-exclude-port")
    assert error.value.fault_code == TgiFaultCode.INVALID_ID
    assert resolve_handle(second_id) is second
    assert resolve_handle(get_handle(root)) is root


def test_parsed_design_round_trips_with_interface_edits_and_removals() -> None:
    first = _active("u0", "bus0", exclude_ports=(_ExcludePort(value="old_port"),))
    second = _active("u1", "bus1")
    connection = _connection(
        "valid_wire",
        active_interfaces=(first, second),
        hier_interfaces=(HierInterfaceType(bus_ref="top_bus"),),
        description="Connection documentation",
    )
    parsed = _register_parsed(_design(connection, name="round_trip"))
    parsed_connection = parsed.interconnections.interconnection_or_monitor_interconnection[0]
    connection_id = get_handle(parsed_connection)
    active_ids = api.getInterconnectionActiveInterfaceIDs(connection_id)
    first_active = resolve_handle(active_ids[0])

    added_exclude = api.addActiveInterfaceExcludePort(active_ids[0], "new_port")
    added_active = api.addInterconnectionActiveInterface(connection_id, "u0", "bus2")
    added_hier = api.addInterconnectionHierInterface(connection_id, "new_top_bus")
    xml_after_add = XmlDocument.serializer().render(parsed)
    assert _SCHEMA.validate(etree.fromstring(xml_after_add.encode())), _SCHEMA.error_log
    parsed_after_add = XmlDocument.parser().from_string(xml_after_add, Design)
    assert XmlDocument.serializer().render(parsed_after_add) == xml_after_add
    assert parsed_connection.description == Description(value="Connection documentation")
    assert first_active.exclude_ports.exclude_port[-1].value == "new_port"
    assert resolve_handle(added_exclude).value == "new_port"
    assert resolve_handle(added_active).component_instance_ref == "u0"
    assert resolve_handle(added_hier).bus_ref == "new_top_bus"

    assert api.removeActiveInterfaceExcludePort(added_exclude)
    assert api.removeInterconnectionActiveInterface(added_active)
    assert api.removeInterconnectionHierInterface(added_hier)
    xml_after_remove = XmlDocument.serializer().render(parsed)
    assert _SCHEMA.validate(etree.fromstring(xml_after_remove.encode())), _SCHEMA.error_log
    assert (
        XmlDocument.serializer().render(XmlDocument.parser().from_string(xml_after_remove, Design)) == xml_after_remove
    )
    assert api.getInterconnectionActiveInterfaceIDs(connection_id) == active_ids
    assert api.getInterconnectionHierInterfaceIDs(connection_id) == [get_handle(parsed_connection.hier_interface[0])]
    assert resolve_handle(added_exclude) is None
    assert resolve_handle(added_active) is None
    assert resolve_handle(added_hier) is None

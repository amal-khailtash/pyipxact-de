"""Monitor interface endpoint TGI contracts from IEEE 1685-2022."""

import inspect
from collections.abc import Iterator, Sequence
from copy import deepcopy
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
    MonitorInterconnection,
    MonitorInterfaceType,
)

_REPO_ROOT = Path(__file__).resolve().parents[5]
_SCHEMA = etree.XMLSchema(etree.parse(str(_REPO_ROOT / "submodules/accellera-schemas/IPXACT/1685-2022/index.xsd")))
_XSD_NS = "http://www.w3.org/2001/XMLSchema"
_IPXACT_NS = "http://www.accellera.org/XMLSchema/IPXACT/1685-2022"
_SIMPLE_TYPES = etree.parse(str(_REPO_ROOT / "submodules/accellera-schemas/IPXACT/1685-2022/simpleTypes.xsd"))
_INSTANCE_PATH_TYPE = _SIMPLE_TYPES.find(f"{{{_XSD_NS}}}simpleType[@name='instancePath']")
assert _INSTANCE_PATH_TYPE is not None
_INSTANCE_PATH_SCHEMA_ROOT = etree.Element(
    f"{{{_XSD_NS}}}schema",
    nsmap={"xs": _XSD_NS, "ipxact": _IPXACT_NS},
    attrib={"targetNamespace": _IPXACT_NS, "elementFormDefault": "qualified"},
)
_INSTANCE_PATH_SCHEMA_ROOT.append(deepcopy(_INSTANCE_PATH_TYPE))
etree.SubElement(
    _INSTANCE_PATH_SCHEMA_ROOT,
    f"{{{_XSD_NS}}}element",
    name="path",
    type="ipxact:instancePath",
)
_INSTANCE_PATH_SCHEMA = etree.XMLSchema(_INSTANCE_PATH_SCHEMA_ROOT)
_API_FUNCTIONS = (
    "getMonitorInterconnectionMonitorInterfaceIDs",
    "getMonitorInterconnectionMonitoredActiveInterfaceID",
    "addMonitorInterconnectionMonitorInterface",
    "removeMonitorInterconnectionMonitorInterface",
    "setInterconnectionActiveInterface",
    "setInterconnectionHierInterface",
    "setMonitorInterconnectionMonitoredActiveInterface",
    "setMonitoredActiveInterfacePath",
)


@pytest.fixture(autouse=True)
def clean_registry() -> Iterator[None]:
    registry.clear()
    yield
    registry.clear()


def _monitor_interface(
    instance: str = "u0",
    bus: str = "bus0",
    *,
    path: str | None = None,
    description: str | None = None,
) -> MonitorInterfaceType:
    return MonitorInterfaceType(
        component_instance_ref=instance,
        bus_ref=bus,
        path=path,
        description=Description(value=description) if description is not None else None,
    )


def _monitor_connection(
    name: str = "monitor_wire",
    *,
    monitored: MonitorInterfaceType | None = None,
    monitors: Sequence[MonitorInterfaceType] = (),
    description: str | None = None,
) -> MonitorInterconnection:
    return MonitorInterconnection(
        name=name,
        monitored_active_interface=monitored or _monitor_interface(),
        monitor_interface=monitors,
        description=Description(value=description) if description is not None else None,
    )


def _design(*connections: MonitorInterconnection | Interconnection, name: str = "monitor_endpoints") -> Design:
    root = Design(
        vendor="vendor",
        library="library",
        name=name,
        version="1",
        component_instances=ComponentInstances(
            component_instance=[
                ComponentInstance(
                    instance_name=InstanceName(value=instance),
                    component_ref=ConfigurableLibraryRefType(
                        vendor="vendor", library="library", name="component", version="1"
                    ),
                )
                for instance in ("u0", "u1", "u2")
            ]
        ),
        interconnections=Interconnections(interconnection_or_monitor_interconnection=list(connections)),
    )
    return root


def _registered(*connections: MonitorInterconnection | Interconnection) -> Design:
    root = _design(*connections)
    registry.register(root, (root.vendor, root.library, root.name, root.version))
    return root


def _register_parsed(root: Design) -> Design:
    xml = XmlDocument.serializer().render(root)
    _SCHEMA.assertValid(etree.fromstring(xml.encode()))
    parsed = XmlDocument.parser().from_string(xml, Design)
    registry.register(parsed, (parsed.vendor, parsed.library, parsed.name, parsed.version))
    return parsed


def _round_trip(root: Design) -> str:
    xml = XmlDocument.serializer().render(root)
    _SCHEMA.assertValid(etree.fromstring(xml.encode()))
    parsed = XmlDocument.parser().from_string(xml, Design)
    assert XmlDocument.serializer().render(parsed) == xml
    return xml


def _instance_path_is_schema_valid(value: str) -> bool:
    element = etree.Element(f"{{{_IPXACT_NS}}}path")
    element.text = value
    return _INSTANCE_PATH_SCHEMA.validate(element)


def test_public_exports_and_annex_f_signatures() -> None:
    expected = {
        "getMonitorInterconnectionMonitorInterfaceIDs": (
            ("monitorInterconnectionID",),
            (str,),
            list[str],
            "F.7.37.26",
        ),
        "getMonitorInterconnectionMonitoredActiveInterfaceID": (
            ("monitorInterconnectionID",),
            (str,),
            str | None,
            "F.7.37.27",
        ),
        "addMonitorInterconnectionMonitorInterface": (
            ("monitorInterconnectionID", "componentInstanceRef", "busInterfaceRef"),
            (str, str, str),
            str,
            "F.7.38.12",
        ),
        "removeMonitorInterconnectionMonitorInterface": (
            ("monitorInterfaceID",),
            (str,),
            bool,
            "F.7.38.28",
        ),
        "setInterconnectionActiveInterface": (
            ("interconnectionID", "componentInstanceRef", "busRef"),
            (str, str, str),
            bool,
            "F.7.38.33",
        ),
        "setInterconnectionHierInterface": (("interconnectionID", "busRef"), (str, str), bool, "F.7.38.34"),
        "setMonitorInterconnectionMonitoredActiveInterface": (
            ("monitorInterconnectionID", "componentInstanceRef", "busRef"),
            (str, str, str),
            bool,
            "F.7.38.35",
        ),
        "setMonitoredActiveInterfacePath": (
            ("monitoredActiveInterfaceID", "path"),
            (str, str),
            bool,
            "F.7.38.36",
        ),
    }

    assert set(_API_FUNCTIONS) == set(expected)
    assert set(expected) <= set(api.__all__)
    assert set(expected) <= set(tgi.__all__)
    for name, (parameter_names, parameter_types, return_type, section) in expected.items():
        function = getattr(api, name)
        assert getattr(tgi, name) is function
        signature = inspect.signature(function)
        assert tuple(signature.parameters) == parameter_names
        assert tuple(parameter.annotation for parameter in signature.parameters.values()) == parameter_types
        assert all(not isinstance(parameter.annotation, str) for parameter in signature.parameters.values())
        assert signature.return_annotation == return_type
        assert f"Section: {section}." in inspect.getdoc(function)


def test_monitor_getters_register_owned_children_and_accept_tuple_lists() -> None:
    first = _monitor_interface("u1", "bus1", description="first monitor")
    second = _monitor_interface("u2", "bus2", path="nested/u2", description="second monitor")
    monitored = _monitor_interface("u0", "bus0", path="top/u0")
    connection = _monitor_connection(monitored=monitored, monitors=(first, second))
    root = _registered(connection)
    child_tuple = tuple(connection.monitor_interface)
    connection.monitor_interface = child_tuple

    monitor_ids = api.getMonitorInterconnectionMonitorInterfaceIDs(get_handle(connection))
    monitored_id = api.getMonitorInterconnectionMonitoredActiveInterfaceID(get_handle(connection))

    assert monitor_ids == [get_handle(first), get_handle(second)]
    assert monitored_id == get_handle(monitored)
    assert connection.monitor_interface is child_tuple
    info = get_parent_info(monitor_ids[0])
    assert info is not None
    assert (info.parent_handle, info.path, info.container) == (get_handle(connection), ("monitor_interface",), "list")
    info = get_parent_info(monitored_id)
    assert info is not None
    assert (info.parent_handle, info.path, info.container) == (
        get_handle(connection),
        ("monitored_active_interface",),
        "single",
    )
    assert resolve_handle(get_handle(root)) is root


@pytest.mark.parametrize(
    "field,bad_value",
    [("monitor_interface", object()), ("monitor_interface", [object()])],
    ids=("non-sequence", "wrong-child"),
)
def test_monitor_getter_rejects_malformed_child_collection(field: str, bad_value: object) -> None:
    connection = _monitor_connection(monitors=(_monitor_interface("u1", "bus1"),))
    _registered(connection)
    setattr(connection, field, bad_value)

    with pytest.raises(TgiError) as error:
        api.getMonitorInterconnectionMonitorInterfaceIDs(get_handle(connection))
    assert error.value.fault_code == TgiFaultCode.INVALID_ID


def test_monitor_getters_reject_wrong_owner_type_and_stale_handles() -> None:
    ordinary = Interconnection(name="ordinary")
    monitor = _monitor_connection()
    _registered(ordinary, monitor)

    for getter in (
        api.getMonitorInterconnectionMonitorInterfaceIDs,
        api.getMonitorInterconnectionMonitoredActiveInterfaceID,
    ):
        with pytest.raises(TgiError) as wrong_type:
            getter(get_handle(ordinary))
        assert wrong_type.value.fault_code == TgiFaultCode.INVALID_ID
        with pytest.raises(TgiError) as stale:
            getter("stale-monitor-interconnection")
        assert stale.value.fault_code == TgiFaultCode.INVALID_ID


@pytest.mark.parametrize("malformed", [object(), Description(value="wrong wrapper type")])
def test_monitored_active_getter_and_setter_reject_malformed_wrapper_atomically(malformed: object) -> None:
    connection = _monitor_connection(monitors=(_monitor_interface("u1", "bus1"),))
    _registered(connection)
    connection.monitored_active_interface = malformed  # type: ignore[assignment]

    with pytest.raises(TgiError) as getter_error:
        api.getMonitorInterconnectionMonitoredActiveInterfaceID(get_handle(connection))
    assert getter_error.value.fault_code == TgiFaultCode.INVALID_ID

    with pytest.raises(TgiError) as setter_error:
        api.setMonitorInterconnectionMonitoredActiveInterface(get_handle(connection), "u2", "new_bus")
    assert setter_error.value.fault_code == TgiFaultCode.INVALID_ID
    assert connection.monitored_active_interface is malformed


def test_monitored_active_setter_creates_missing_required_wrapper_and_registers_ownership() -> None:
    connection = _monitor_connection(monitors=(_monitor_interface("u1", "bus1"),))
    root = _registered(connection)
    connection.monitored_active_interface = None  # type: ignore[assignment]

    assert api.setMonitorInterconnectionMonitoredActiveInterface(get_handle(connection), "u2", "bus2")

    monitored = connection.monitored_active_interface
    assert (monitored.component_instance_ref, monitored.bus_ref) == ("u2", "bus2")
    info = get_parent_info(get_handle(monitored))
    assert info is not None
    assert (info.parent_handle, info.path, info.container) == (
        get_handle(connection),
        ("monitored_active_interface",),
        "single",
    )
    assert resolve_handle(get_handle(root)) is root


def test_monitor_adder_collapses_names_normalizes_tuple_and_preserves_siblings() -> None:
    existing = _monitor_interface("u1", "bus1", description="preserve me")
    connection = _monitor_connection(monitors=(existing,))
    root = _registered(connection)
    original = tuple(connection.monitor_interface)
    connection.monitor_interface = original

    added_id = api.addMonitorInterconnectionMonitorInterface(get_handle(connection), " \tu2\r\n", " bus2 ")
    added = resolve_handle(added_id)

    assert isinstance(added, MonitorInterfaceType)
    assert (added.component_instance_ref, added.bus_ref) == ("u2", "bus2")
    assert isinstance(connection.monitor_interface, list)
    assert connection.monitor_interface == [existing, added]
    assert connection.monitor_interface[0] is existing
    assert existing.description == Description(value="preserve me")
    info = get_parent_info(added_id)
    assert info is not None
    assert (info.parent_handle, info.path, info.container) == (get_handle(connection), ("monitor_interface",), "list")
    assert resolve_handle(get_handle(root)) is root


@pytest.mark.parametrize(
    "instance,bus",
    [("bad instance", "bus"), ("u1", "bad bus"), ("1bad", "bus")],
    ids=("instance-space", "bus-space", "name-start"),
)
def test_monitor_adder_rejects_invalid_names_atomically(instance: str, bus: str) -> None:
    existing = _monitor_interface("u1", "bus1")
    connection = _monitor_connection(monitors=(existing,))
    _registered(connection)
    before = connection.monitor_interface
    before_children = tuple(before)

    with pytest.raises(TgiError) as error:
        api.addMonitorInterconnectionMonitorInterface(get_handle(connection), instance, bus)

    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert connection.monitor_interface is before
    assert tuple(connection.monitor_interface) == before_children


@pytest.mark.parametrize(
    "malformed",
    [object(), [ActiveInterface(component_instance_ref="u2", bus_ref="bus2")]],
    ids=("non-sequence", "wrong-child"),
)
def test_monitor_adder_rejects_malformed_collection_atomically(malformed: object) -> None:
    connection = _monitor_connection(monitors=(_monitor_interface("u1", "bus1"),))
    _registered(connection)
    connection.monitor_interface = malformed  # type: ignore[assignment]

    with pytest.raises(TgiError) as error:
        api.addMonitorInterconnectionMonitorInterface(get_handle(connection), "u2", "bus2")

    assert error.value.fault_code == TgiFaultCode.INVALID_ID
    assert connection.monitor_interface is malformed


def test_monitor_adder_accepts_schema_valid_unicode_names_and_unresolved_references() -> None:
    connection = _monitor_connection()
    _registered(connection)

    child_id = api.addMonitorInterconnectionMonitorInterface(get_handle(connection), "missing_界", "bus·new")
    child = resolve_handle(child_id)

    assert isinstance(child, MonitorInterfaceType)
    assert (child.component_instance_ref, child.bus_ref) == ("missing_界", "bus·new")


def test_monitor_remover_discovers_parsed_owner_without_getter_first_and_invalidates_child() -> None:
    removed = _monitor_interface("u1", "bus1", description="removed tree")
    sibling = _monitor_interface("u2", "bus2", description="keep sibling")
    connection = _monitor_connection(monitors=(removed, sibling))
    root = _register_parsed(_design(connection))
    parsed_connection = root.interconnections.interconnection_or_monitor_interconnection[0]
    parsed_removed, parsed_sibling = parsed_connection.monitor_interface
    removed_id = get_handle(parsed_removed)
    description_id = get_handle(parsed_removed.description)
    sibling_id = get_handle(parsed_sibling)
    assert get_parent_info(removed_id) is None

    assert api.removeMonitorInterconnectionMonitorInterface(removed_id)

    assert parsed_connection.monitor_interface == [parsed_sibling]
    assert resolve_handle(removed_id) is None
    assert resolve_handle(description_id) is None
    assert resolve_handle(sibling_id) is parsed_sibling
    assert parsed_sibling.description == Description(value="keep sibling")


def test_monitor_remover_requires_list_membership_and_rejects_monitored_child() -> None:
    monitored = _monitor_interface("u0", "bus0")
    listed = _monitor_interface("u1", "bus1")
    connection = _monitor_connection(monitored=monitored, monitors=(listed,))
    _registered(connection)

    for invalid_id in (get_handle(monitored), get_handle(_monitor_interface("u2", "orphan_bus")), "stale-monitor"):
        with pytest.raises(TgiError) as error:
            api.removeMonitorInterconnectionMonitorInterface(invalid_id)
        assert error.value.fault_code == TgiFaultCode.INVALID_ID
    assert tuple(connection.monitor_interface) == (listed,)
    assert connection.monitored_active_interface is monitored
    assert resolve_handle(get_handle(monitored)) is monitored


@pytest.mark.parametrize(
    "field,bad_value",
    [("monitor_interface", object()), ("monitor_interface", [object()])],
    ids=("non-sequence", "wrong-child"),
)
def test_monitor_remover_rejects_malformed_list_without_detaching(field: str, bad_value: object) -> None:
    child = _monitor_interface("u1", "bus1")
    connection = _monitor_connection(monitors=(child,))
    _registered(connection)
    child_id = get_handle(child)
    setattr(connection, field, bad_value)

    with pytest.raises(TgiError) as error:
        api.removeMonitorInterconnectionMonitorInterface(child_id)

    assert error.value.fault_code == TgiFaultCode.INVALID_ID
    assert resolve_handle(child_id) is child


def test_interconnection_setters_replace_only_first_endpoint_and_invalidate_old_subtrees() -> None:
    first_active = ActiveInterface(
        component_instance_ref="u0", bus_ref="bus0", description=Description(value="old active")
    )
    second_active = ActiveInterface(
        component_instance_ref="u1", bus_ref="bus1", description=Description(value="keep active")
    )
    first_hier = HierInterfaceType(bus_ref="top0", description=Description(value="old hier"))
    second_hier = HierInterfaceType(bus_ref="top1", description=Description(value="keep hier"))
    connection = Interconnection(
        name="set_endpoints", active_interface=(first_active, second_active), hier_interface=(first_hier, second_hier)
    )
    root = _registered(connection)
    first_active_id = get_handle(first_active)
    first_active_description_id = get_handle(first_active.description)
    second_active_id = get_handle(second_active)
    first_hier_id = get_handle(first_hier)
    first_hier_description_id = get_handle(first_hier.description)
    second_hier_id = get_handle(second_hier)
    active_tuple = connection.active_interface
    hier_tuple = connection.hier_interface

    assert api.setInterconnectionActiveInterface(get_handle(connection), "u2", "new_bus")
    assert api.setInterconnectionHierInterface(get_handle(connection), "new_top")

    replacement_active, retained_active = connection.active_interface
    replacement_hier, retained_hier = connection.hier_interface
    assert (replacement_active.component_instance_ref, replacement_active.bus_ref) == ("u2", "new_bus")
    assert (replacement_hier.bus_ref, retained_hier.bus_ref) == ("new_top", "top1")
    assert retained_active is second_active and retained_hier is second_hier
    assert retained_active.description == Description(value="keep active")
    assert retained_hier.description == Description(value="keep hier")
    assert resolve_handle(first_active_id) is None
    assert resolve_handle(first_active_description_id) is None
    assert resolve_handle(first_hier_id) is None
    assert resolve_handle(first_hier_description_id) is None
    assert resolve_handle(second_active_id) is second_active
    assert resolve_handle(second_hier_id) is second_hier
    for new_child, field in ((replacement_active, ("active_interface",)), (replacement_hier, ("hier_interface",))):
        info = get_parent_info(get_handle(new_child))
        assert info is not None
        assert (info.parent_handle, info.path, info.container) == (get_handle(connection), field, "list")
    assert active_tuple == (first_active, second_active)
    assert hier_tuple == (first_hier, second_hier)
    assert resolve_handle(get_handle(root)) is root


def test_interconnection_setters_create_first_endpoint_for_empty_lists_and_validate_atomically() -> None:
    connection = Interconnection(name="empty_endpoints")
    root = _registered(connection)

    assert api.setInterconnectionActiveInterface(get_handle(connection), "u0", "bus0")
    assert api.setInterconnectionHierInterface(get_handle(connection), "top0")
    assert len(connection.active_interface) == len(connection.hier_interface) == 1
    assert (connection.active_interface[0].component_instance_ref, connection.active_interface[0].bus_ref) == (
        "u0",
        "bus0",
    )
    assert connection.hier_interface[0].bus_ref == "top0"
    active_before = connection.active_interface
    hier_before = connection.hier_interface
    with pytest.raises(TgiError) as invalid_active:
        api.setInterconnectionActiveInterface(get_handle(connection), "1bad", "bus")
    assert invalid_active.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    with pytest.raises(TgiError) as invalid_hier:
        api.setInterconnectionHierInterface(get_handle(connection), "bad bus")
    assert invalid_hier.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert connection.active_interface is active_before
    assert connection.hier_interface is hier_before
    assert resolve_handle(get_handle(root)) is root


@pytest.mark.parametrize(
    "operation,wrong_owner,stale_id",
    [
        ("active", "monitor", "stale-interconnection"),
        ("hier", "monitor", "stale-interconnection"),
        ("monitored", "ordinary", "stale-monitor-interconnection"),
    ],
)
def test_endpoint_setters_reject_wrong_and_stale_owner_ids(operation: str, wrong_owner: str, stale_id: str) -> None:
    ordinary = Interconnection(
        name="ordinary",
        active_interface=[ActiveInterface(component_instance_ref="u0", bus_ref="bus0")],
        hier_interface=[HierInterfaceType(bus_ref="top_bus")],
    )
    monitor = _monitor_connection(monitors=(_monitor_interface("u1", "bus1"),))
    _registered(ordinary, monitor)
    wrong_id = get_handle(monitor if wrong_owner == "monitor" else ordinary)
    for owner_id in (wrong_id, stale_id):
        with pytest.raises(TgiError) as error:
            if operation == "active":
                api.setInterconnectionActiveInterface(owner_id, "u2", "bus2")
            elif operation == "hier":
                api.setInterconnectionHierInterface(owner_id, "top2")
            else:
                api.setMonitorInterconnectionMonitoredActiveInterface(owner_id, "u2", "bus2")
        assert error.value.fault_code == TgiFaultCode.INVALID_ID


@pytest.mark.parametrize(
    "field,malformed",
    [
        ("active_interface", object()),
        ("active_interface", [HierInterfaceType(bus_ref="wrong_child")]),
        ("hier_interface", object()),
        ("hier_interface", [ActiveInterface(component_instance_ref="u1", bus_ref="wrong_child")]),
    ],
    ids=("active-non-sequence", "active-wrong-child", "hier-non-sequence", "hier-wrong-child"),
)
def test_interconnection_setters_reject_malformed_lists_atomically(field: str, malformed: object) -> None:
    connection = Interconnection(
        name="malformed_endpoints",
        active_interface=[ActiveInterface(component_instance_ref="u0", bus_ref="bus0")],
        hier_interface=[HierInterfaceType(bus_ref="top_bus")],
    )
    _registered(connection)
    setattr(connection, field, malformed)

    with pytest.raises(TgiError) as error:
        if field == "active_interface":
            api.setInterconnectionActiveInterface(get_handle(connection), "u2", "bus2")
        else:
            api.setInterconnectionHierInterface(get_handle(connection), "top2")

    assert error.value.fault_code == TgiFaultCode.INVALID_ID
    assert getattr(connection, field) is malformed


def test_monitored_active_setter_replaces_single_child_and_invalidates_old_tree() -> None:
    monitored = _monitor_interface("u0", "bus0", path="top/u0", description="remove subtree")
    monitor = _monitor_interface("u1", "bus1", description="keep list child")
    connection = _monitor_connection(monitored=monitored, monitors=(monitor,), description="keep owner")
    root = _registered(connection)
    monitored_id = get_handle(monitored)
    old_description_id = get_handle(monitored.description)
    monitor_id = get_handle(monitor)

    assert api.setMonitorInterconnectionMonitoredActiveInterface(get_handle(connection), "u2", "new_bus")

    replacement = connection.monitored_active_interface
    assert replacement is not monitored
    assert (replacement.component_instance_ref, replacement.bus_ref, replacement.path) == ("u2", "new_bus", None)
    assert tuple(connection.monitor_interface) == (monitor,)
    assert connection.description == Description(value="keep owner")
    assert resolve_handle(monitored_id) is None
    assert resolve_handle(old_description_id) is None
    assert resolve_handle(monitor_id) is monitor
    info = get_parent_info(get_handle(replacement))
    assert info is not None
    assert (info.parent_handle, info.path, info.container) == (
        get_handle(connection),
        ("monitored_active_interface",),
        "single",
    )
    assert resolve_handle(get_handle(root)) is root


@pytest.mark.parametrize("instance,bus", [("bad instance", "bus"), ("u1", "bad bus")])
def test_monitored_active_setter_rejects_invalid_names_before_replacing(instance: str, bus: str) -> None:
    monitored = _monitor_interface("u0", "bus0", description="preserve")
    connection = _monitor_connection(monitored=monitored, monitors=(_monitor_interface("u1", "bus1"),))
    _registered(connection)
    old_id = get_handle(monitored)

    with pytest.raises(TgiError) as error:
        api.setMonitorInterconnectionMonitoredActiveInterface(get_handle(connection), instance, bus)

    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert connection.monitored_active_interface is monitored
    assert resolve_handle(old_id) is monitored


def test_monitored_active_path_preserves_object_metadata_and_accepts_schema_trailing_slash() -> None:
    monitored = _monitor_interface("u0", "bus0", description="preserve me")
    connection = _monitor_connection(monitored=monitored, monitors=(_monitor_interface("u1", "bus1"),))
    root = _registered(connection)
    monitored_id = get_handle(monitored)

    assert api.setMonitoredActiveInterfacePath(monitored_id, "  top/u0/  ")

    assert connection.monitored_active_interface is monitored
    assert monitored.path == "top/u0/"
    assert monitored.description == Description(value="preserve me")
    assert get_handle(monitored) == monitored_id
    assert resolve_handle(monitored_id) is monitored
    assert _round_trip(root)


@pytest.mark.parametrize("path", ["", "u0//u1", "1bad", "bad path", "u0/with?query"])
def test_monitored_active_path_rejects_invalid_schema_values_atomically(path: str) -> None:
    monitored = _monitor_interface("u0", "bus0", path="valid/path")
    connection = _monitor_connection(monitored=monitored)
    _registered(connection)
    monitored_id = get_handle(monitored)

    with pytest.raises(TgiError) as error:
        api.setMonitoredActiveInterfacePath(monitored_id, path)

    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert monitored.path == "valid/path"
    assert connection.monitored_active_interface is monitored


@pytest.mark.parametrize("path", [None, 17, "u0\x01"])
def test_monitored_active_path_rejects_non_string_and_xml_illegal_text(path: object) -> None:
    monitored = _monitor_interface("u0", "bus0", path="valid/path")
    connection = _monitor_connection(monitored=monitored)
    _registered(connection)
    monitored_id = get_handle(monitored)

    with pytest.raises(TgiError) as error:
        api.setMonitoredActiveInterfacePath(monitored_id, path)  # type: ignore[arg-type]

    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert monitored.path == "valid/path"


@pytest.mark.parametrize("path", ["u0/1", "u0/u1/", "u·0", "  u0/1  "])
def test_monitored_active_path_behavior_matches_isolated_instance_path_schema(path: str) -> None:
    schema_accepts = _instance_path_is_schema_valid(path)
    monitored = _monitor_interface("u0", "bus0", path="before")
    connection = _monitor_connection(monitored=monitored, monitors=(_monitor_interface("u1", "bus1"),))
    _registered(connection)

    if schema_accepts:
        assert api.setMonitoredActiveInterfacePath(get_handle(monitored), path)
        assert monitored.path == " ".join(path.split())
        assert _instance_path_is_schema_valid(monitored.path)
    else:
        with pytest.raises(TgiError) as error:
            api.setMonitoredActiveInterfacePath(get_handle(monitored), path)
        assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
        assert monitored.path == "before"


def test_monitored_active_path_rejects_list_or_orphan_interface_of_same_generated_type() -> None:
    listed = _monitor_interface("u1", "bus1")
    orphan = _monitor_interface("u2", "bus2")
    connection = _monitor_connection(monitors=(listed,))
    _registered(connection)

    for child in (listed, orphan):
        before = child.path
        with pytest.raises(TgiError) as error:
            api.setMonitoredActiveInterfacePath(get_handle(child), "valid/path")
        assert error.value.fault_code == TgiFaultCode.INVALID_ID
        assert child.path == before


def test_parsed_monitor_and_interconnection_edits_round_trip_as_schema_valid_xml() -> None:
    monitor_connection = _monitor_connection(
        monitored=_monitor_interface("u0", "bus0", description="monitored"),
        monitors=(_monitor_interface("u1", "bus1"),),
        description="monitor connection",
    )
    ordinary = Interconnection(
        name="wire",
        active_interface=[ActiveInterface(component_instance_ref="u0", bus_ref="bus0")],
        hier_interface=[HierInterfaceType(bus_ref="initial_top_bus")],
    )
    root = _register_parsed(_design(monitor_connection, ordinary, name="parsed_endpoint_edits"))
    parsed_monitor, parsed_ordinary = root.interconnections.interconnection_or_monitor_interconnection
    monitor_id = get_handle(parsed_monitor)
    ordinary_id = get_handle(parsed_ordinary)
    old_monitored_id = get_handle(parsed_monitor.monitored_active_interface)
    old_active_id = get_handle(parsed_ordinary.active_interface[0])

    added_id = api.addMonitorInterconnectionMonitorInterface(monitor_id, "u2", "bus2")
    assert api.setMonitorInterconnectionMonitoredActiveInterface(monitor_id, "u1", "bus_new")
    assert api.setMonitoredActiveInterfacePath(get_handle(parsed_monitor.monitored_active_interface), "nested/u1/")
    assert api.setInterconnectionActiveInterface(ordinary_id, "u2", "bus_new")
    assert api.setInterconnectionHierInterface(ordinary_id, "top_bus")
    xml = _round_trip(root)

    assert resolve_handle(old_monitored_id) is None
    assert resolve_handle(old_active_id) is None
    assert resolve_handle(added_id) is not None
    assert "nested/u1/" in xml
    parsed_again = XmlDocument.parser().from_string(xml, Design)
    round_trip_monitor, round_trip_ordinary = parsed_again.interconnections.interconnection_or_monitor_interconnection
    assert round_trip_monitor.monitored_active_interface.path == "nested/u1/"
    assert round_trip_monitor.monitor_interface[-1].component_instance_ref == "u2"
    assert round_trip_ordinary.active_interface[0].component_instance_ref == "u2"
    assert round_trip_ordinary.hier_interface[0].bus_ref == "top_bus"

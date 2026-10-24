"""Design configuration interconnection TGI contracts from IEEE 1685-2022."""

import inspect
from collections.abc import Iterator
from pathlib import Path
from typing import get_type_hints

import pytest
from lxml import etree

from amal.eda.accellera.ipxact.v1685_2022 import tgi
from amal.eda.accellera.ipxact.v1685_2022.tgi import design as design_api
from amal.eda.accellera.ipxact.v1685_2022.tgi import design_configuration as dc_api
from amal.eda.accellera.ipxact.v1685_2022.tgi import instantiation as instantiation_api
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
    Design,
    DesignConfiguration,
    DesignConfigurationInstantiationType,
    InstanceName,
    Interconnection,
    Interconnections,
    LibraryRefType,
    MonitorInterconnection,
    MonitorInterfaceType,
)

_REPO_ROOT = Path(__file__).resolve().parents[5]
_SCHEMA = etree.XMLSchema(etree.parse(str(_REPO_ROOT / "submodules/accellera-schemas/IPXACT/1685-2022/index.xsd")))
_ABSTRACTOR_VLNV = ("vendor", "library", "abstractor", "1")
_API_FUNCTIONS = (
    "getDesignConfigurationInterconnectionConfigurationIDs",
    "getInterconnectionConfigurationInterconnectionRefByID",
    "getInterconnectionConfigurationInterconnectionRefByName",
    "addDesignConfigurationInterconnectionConfiguration",
    "removeDesignConfigurationInterconnectionConfiguration",
    "setInterconnectionConfigurationInterconnectionRef",
)


@pytest.fixture(autouse=True)
def clean_registry() -> Iterator[None]:
    registry.clear()
    yield
    registry.clear()


def _abstractor_group(
    name: str,
) -> DesignConfiguration.InterconnectionConfiguration.AbstractorInstances:
    group_type = DesignConfiguration.InterconnectionConfiguration.AbstractorInstances
    instance_type = group_type.AbstractorInstance
    return group_type(
        abstractor_instance=[
            instance_type(
                instance_name=name,
                abstractor_ref=ConfigurableLibraryRefType(
                    vendor=_ABSTRACTOR_VLNV[0],
                    library=_ABSTRACTOR_VLNV[1],
                    name=_ABSTRACTOR_VLNV[2],
                    version=_ABSTRACTOR_VLNV[3],
                ),
                view_name="rtl",
            )
        ]
    )


def _design_configuration(
    *references: str,
    root_name: str = "configuration",
    design_ref: LibraryRefType | None = None,
) -> DesignConfiguration:
    root = DesignConfiguration(
        vendor="vendor",
        library="library",
        name=root_name,
        version="1",
        design_ref=design_ref,
        interconnection_configuration=[
            DesignConfiguration.InterconnectionConfiguration(
                interconnection_ref=reference,
                abstractor_instances=[_abstractor_group(f"{reference}_abstractor")],
            )
            for reference in references
        ],
    )
    parsed = XmlDocument.parser().from_string(XmlDocument.serializer().render(root), DesignConfiguration)
    registry.register(parsed, ("vendor", "library", root_name, "1"))
    return parsed


def _design(*connections: Interconnection | MonitorInterconnection, name: str = "design") -> Design:
    component_names = {
        interface.component_instance_ref
        for connection in connections
        for interface in (
            [*connection.active_interface, *connection.hier_interface]
            if isinstance(connection, Interconnection)
            else [connection.monitored_active_interface, *connection.monitor_interface]
        )
    }
    root = Design(
        vendor="vendor",
        library="library",
        name=name,
        version="1",
        component_instances=ComponentInstances(
            component_instance=[
                ComponentInstance(
                    instance_name=InstanceName(value=component_name),
                    component_ref=ConfigurableLibraryRefType(
                        vendor="vendor", library="library", name="component", version="1"
                    ),
                )
                for component_name in sorted(component_names)
            ]
        ),
        interconnections=Interconnections(interconnection_or_monitor_interconnection=list(connections)),
    )
    return XmlDocument.parser().from_string(XmlDocument.serializer().render(root), Design)


def _ordinary_connection(name: str) -> Interconnection:
    return Interconnection(
        name=name,
        active_interface=[
            ActiveInterface(component_instance_ref="u0", bus_ref="bus0"),
            ActiveInterface(component_instance_ref="u1", bus_ref="bus1"),
        ],
    )


def _monitor_connection(name: str) -> MonitorInterconnection:
    return MonitorInterconnection(
        name=name,
        monitored_active_interface=MonitorInterfaceType(component_instance_ref="u0", bus_ref="bus0"),
        monitor_interface=[MonitorInterfaceType(component_instance_ref="u1", bus_ref="bus1")],
    )


def _valid_round_trip(root: DesignConfiguration | Design) -> str:
    xml = XmlDocument.serializer().render(root)
    parsed_xml = etree.fromstring(xml.encode())
    _SCHEMA.assertValid(parsed_xml)
    model_type = type(root)
    assert XmlDocument.parser().from_string(xml, model_type) == root
    return xml


def test_public_exports_and_native_runtime_annotations() -> None:
    expected = {
        "getDesignConfigurationInterconnectionConfigurationIDs": ([str], list[str]),
        "getInterconnectionConfigurationInterconnectionRefByID": ([str], str),
        "getInterconnectionConfigurationInterconnectionRefByName": ([str], str | None),
        "addDesignConfigurationInterconnectionConfiguration": (
            [str, str, tuple[str, str, str, str], str, str],
            str,
        ),
        "removeDesignConfigurationInterconnectionConfiguration": ([str], bool),
        "setInterconnectionConfigurationInterconnectionRef": ([str, str], bool),
    }

    for name in _API_FUNCTIONS:
        function = getattr(dc_api, name)
        assert getattr(tgi, name) is function
        assert name in dc_api.__all__
        assert name in tgi.__all__
        hints = get_type_hints(function)
        assert [hints[param] for param in inspect.signature(function).parameters] == expected[name][0]
        assert hints["return"] == expected[name][1]


def test_interconnection_configuration_ids_accept_roots_and_resolved_instantiations() -> None:
    root = _design_configuration("connection_a", "connection_b")
    root_id = get_handle(root)
    expected = [get_handle(item) for item in root.interconnection_configuration]
    assert dc_api.getDesignConfigurationInterconnectionConfigurationIDs(root_id) == expected
    for interconnection_configuration_id in expected:
        parent = get_parent_info(interconnection_configuration_id)
        assert parent is not None
        assert (parent.parent_handle, parent.path, parent.container) == (
            root_id,
            ("interconnection_configuration",),
            "list",
        )

    instantiation = DesignConfigurationInstantiationType(
        name="configured",
        design_configuration_ref=ConfigurableLibraryRefType(
            vendor="vendor", library="library", name="configuration", version="1"
        ),
    )
    instantiation_id = get_handle(instantiation)
    resolved_root_id = instantiation_api.getDesignConfigurationInstantiationDesignConfigurationRefByID(instantiation_id)
    assert resolved_root_id == root_id
    assert dc_api.getDesignConfigurationInterconnectionConfigurationIDs(resolved_root_id) == expected
    assert dc_api.getDesignConfigurationInterconnectionConfigurationIDs(instantiation_id) == expected


def test_interconnection_configuration_ids_report_invalid_instantiation_references() -> None:
    missing = DesignConfigurationInstantiationType(
        name="missing",
        design_configuration_ref=ConfigurableLibraryRefType(
            vendor="vendor", library="library", name="absent", version="1"
        ),
    )
    with pytest.raises(TgiError) as unresolved:
        instantiation_api.getDesignConfigurationInstantiationDesignConfigurationRefByID(get_handle(missing))
    assert unresolved.value.fault_code == TgiFaultCode.NOT_FOUND
    with pytest.raises(TgiError) as unresolved_collection:
        dc_api.getDesignConfigurationInterconnectionConfigurationIDs(get_handle(missing))
    assert unresolved_collection.value.fault_code == TgiFaultCode.NOT_FOUND

    wrong_type = Design(vendor="vendor", library="library", name="not_configuration", version="1")
    registry.register(wrong_type, ("vendor", "library", "target", "1"))
    wrong = DesignConfigurationInstantiationType(
        name="wrong",
        design_configuration_ref=ConfigurableLibraryRefType(
            vendor="vendor", library="library", name="target", version="1"
        ),
    )
    with pytest.raises(TgiError) as wrong_target:
        instantiation_api.getDesignConfigurationInstantiationDesignConfigurationRefByID(get_handle(wrong))
    assert wrong_target.value.fault_code == TgiFaultCode.NOT_FOUND
    with pytest.raises(TgiError) as wrong_collection_target:
        dc_api.getDesignConfigurationInterconnectionConfigurationIDs(get_handle(wrong))
    assert wrong_collection_target.value.fault_code == TgiFaultCode.NOT_FOUND

    for invalid_id in ("missing-handle", get_handle(wrong_type)):
        with pytest.raises(TgiError) as invalid:
            dc_api.getDesignConfigurationInterconnectionConfigurationIDs(invalid_id)
        assert invalid.value.fault_code == TgiFaultCode.INVALID_ID


@pytest.mark.parametrize("connection_type", ["ordinary", "monitor"])
def test_interconnection_ref_by_id_resolves_owned_connection_kinds(connection_type: str) -> None:
    connection = _ordinary_connection("ordinary") if connection_type == "ordinary" else _monitor_connection("monitored")
    target = connection.name
    design = _design(connection)
    parsed_connection = design.interconnections.interconnection_or_monitor_interconnection[0]
    registry.register(design, ("vendor", "library", "design", "1"))
    root = _design_configuration(
        target,
        design_ref=LibraryRefType(vendor="vendor", library="library", name="design", version="1"),
    )
    ic_id = dc_api.getDesignConfigurationInterconnectionConfigurationIDs(get_handle(root))[0]

    assert dc_api.getInterconnectionConfigurationInterconnectionRefByID(ic_id) == get_handle(parsed_connection)
    assert dc_api.getInterconnectionConfigurationInterconnectionRefByName(ic_id) == target
    _valid_round_trip(design)
    _valid_round_trip(root)


def test_interconnection_ref_name_is_stored_text_and_by_id_rejects_unresolved_targets() -> None:
    root = _design_configuration("missing_connection")
    ic_id = dc_api.getDesignConfigurationInterconnectionConfigurationIDs(get_handle(root))[0]
    assert dc_api.getInterconnectionConfigurationInterconnectionRefByName(ic_id) == "missing_connection"
    with pytest.raises(TgiError) as missing:
        dc_api.getInterconnectionConfigurationInterconnectionRefByID(ic_id)
    assert missing.value.fault_code == TgiFaultCode.NOT_FOUND

    no_design = _design_configuration("connection", root_name="without_design")
    no_design_ic_id = dc_api.getDesignConfigurationInterconnectionConfigurationIDs(get_handle(no_design))[0]
    with pytest.raises(TgiError) as absent_design:
        dc_api.getInterconnectionConfigurationInterconnectionRefByID(no_design_ic_id)
    assert absent_design.value.fault_code == TgiFaultCode.NOT_FOUND


def test_interconnection_category_operations_reject_invalid_handles_and_wrong_kinds() -> None:
    root = _design_configuration("connection")
    root_id = get_handle(root)
    ic_id = dc_api.getDesignConfigurationInterconnectionConfigurationIDs(root_id)[0]
    design = _design()
    design_id = get_handle(design)

    for operation in (
        lambda handle: dc_api.addDesignConfigurationInterconnectionConfiguration(
            handle, "new_connection", _ABSTRACTOR_VLNV, "abstractor", "rtl"
        ),
        lambda handle: dc_api.setInterconnectionConfigurationInterconnectionRef(handle, "updated"),
    ):
        for invalid_id in ("missing-handle", design_id):
            with pytest.raises(TgiError) as invalid:
                operation(invalid_id)
            assert invalid.value.fault_code == TgiFaultCode.INVALID_ID

    for operation in (
        dc_api.getInterconnectionConfigurationInterconnectionRefByID,
        dc_api.getInterconnectionConfigurationInterconnectionRefByName,
        dc_api.setInterconnectionConfigurationInterconnectionRef,
    ):
        for invalid_id in ("missing-handle", root_id):
            with pytest.raises(TgiError) as invalid:
                if operation is dc_api.setInterconnectionConfigurationInterconnectionRef:
                    operation(invalid_id, "updated")
                else:
                    operation(invalid_id)
            assert invalid.value.fault_code == TgiFaultCode.INVALID_ID

    assert not dc_api.removeDesignConfigurationInterconnectionConfiguration("missing-handle")
    assert not dc_api.removeDesignConfigurationInterconnectionConfiguration(root_id)
    for operation in (design_api.getDesignInterconnectionIDs, design_api.getDesignMonitorInterconnectionIDs):
        for invalid_id in ("missing-handle", root_id):
            with pytest.raises(TgiError) as invalid:
                operation(invalid_id)
            assert invalid.value.fault_code == TgiFaultCode.INVALID_ID

    assert ic_id == get_handle(root.interconnection_configuration[0])


def test_interconnection_ref_by_id_rejects_ambiguous_names() -> None:
    design = _design(_ordinary_connection("shared"), _monitor_connection("shared"))
    registry.register(design, ("vendor", "library", "design", "1"))
    root = _design_configuration(
        "shared",
        design_ref=LibraryRefType(vendor="vendor", library="library", name="design", version="1"),
    )
    ic_id = dc_api.getDesignConfigurationInterconnectionConfigurationIDs(get_handle(root))[0]
    with pytest.raises(TgiError) as ambiguous:
        dc_api.getInterconnectionConfigurationInterconnectionRefByID(ic_id)
    assert ambiguous.value.fault_code == TgiFaultCode.NOT_FOUND


def test_interconnection_ref_by_id_collapses_xml_name_whitespace_without_changing_by_name() -> None:
    design = _design(_ordinary_connection("connection"))
    registry.register(design, ("vendor", "library", "design", "1"))
    root = _design_configuration(
        "connection",
        design_ref=LibraryRefType(vendor="vendor", library="library", name="design", version="1"),
    )
    ic = root.interconnection_configuration[0]
    ic.interconnection_ref = " \tconnection\r\n"
    ic_id = get_handle(ic)

    assert dc_api.getInterconnectionConfigurationInterconnectionRefByName(ic_id) == " \tconnection\r\n"
    assert dc_api.getInterconnectionConfigurationInterconnectionRefByID(ic_id) == get_handle(
        design.interconnections.interconnection_or_monitor_interconnection[0]
    )
    _SCHEMA.assertValid(etree.fromstring(XmlDocument.serializer().render(root).encode()))


def test_add_interconnection_configuration_creates_required_group_and_instance() -> None:
    root = _design_configuration("existing")
    root_id = get_handle(root)
    created_id = dc_api.addDesignConfigurationInterconnectionConfiguration(
        root_id, "new_connection", _ABSTRACTOR_VLNV, "new_abstractor", "rtl"
    )
    created = resolve_handle(created_id)
    assert created is root.interconnection_configuration[-1]
    assert created.interconnection_ref == "new_connection"
    groups = dc_api.getInterconnectionConfigurationAbstractorsInstancesIDs(created_id)
    assert len(groups) == 1
    instances = dc_api.getAbstractorInstancesAbstractorInstanceIDs(groups[0])
    assert len(instances) == 1
    instance = resolve_handle(instances[0])
    assert (instance.instance_name, instance.view_name) == ("new_abstractor", "rtl")
    assert (
        instance.abstractor_ref.vendor,
        instance.abstractor_ref.library,
        instance.abstractor_ref.name,
        instance.abstractor_ref.version,
    ) == _ABSTRACTOR_VLNV
    parent = get_parent_info(created_id)
    assert parent is not None
    assert (parent.parent_handle, parent.path, parent.container) == (
        root_id,
        ("interconnection_configuration",),
        "list",
    )
    _valid_round_trip(root)


@pytest.mark.parametrize(
    ("interconnection_ref", "abstractor_vlnv", "instance_name", "view_name"),
    [
        ("bad name", _ABSTRACTOR_VLNV, "instance", "rtl"),
        ("connection", ("vendor", "library", "bad\x00name", "1"), "instance", "rtl"),
        ("connection", _ABSTRACTOR_VLNV, "bad name", "rtl"),
        ("connection", _ABSTRACTOR_VLNV, "instance", "bad name"),
        ("connection", _ABSTRACTOR_VLNV, "\x00", "rtl"),
    ],
)
def test_add_interconnection_configuration_rejects_invalid_values_atomically(
    interconnection_ref: str,
    abstractor_vlnv: tuple[str, str, str, str],
    instance_name: str,
    view_name: str,
) -> None:
    root = _design_configuration("existing")
    root_id = get_handle(root)
    before = _valid_round_trip(root)
    children = list(root.interconnection_configuration)

    with pytest.raises(TgiError) as error:
        dc_api.addDesignConfigurationInterconnectionConfiguration(
            root_id, interconnection_ref, abstractor_vlnv, instance_name, view_name
        )

    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert root.interconnection_configuration == children
    assert _valid_round_trip(root) == before


def test_add_interconnection_configuration_rejects_duplicate_reference_and_root_instance_name() -> None:
    root = _design_configuration("taken")
    root_id = get_handle(root)
    before = _valid_round_trip(root)
    with pytest.raises(TgiError) as duplicate_ref:
        dc_api.addDesignConfigurationInterconnectionConfiguration(
            root_id, "\ttaken\n", _ABSTRACTOR_VLNV, "other", "rtl"
        )
    assert duplicate_ref.value.fault_code == TgiFaultCode.ALREADY_EXISTS
    assert _valid_round_trip(root) == before

    with pytest.raises(TgiError) as duplicate_instance:
        dc_api.addDesignConfigurationInterconnectionConfiguration(
            root_id, "another", _ABSTRACTOR_VLNV, "taken_abstractor", "rtl"
        )
    assert duplicate_instance.value.fault_code == TgiFaultCode.ALREADY_EXISTS
    assert len(root.interconnection_configuration) == 1
    assert _valid_round_trip(root) == before


def test_remove_interconnection_configuration_discovers_parsed_owner_and_invalidates_descendants() -> None:
    design = _design(_ordinary_connection("referenced"))
    registry.register(design, ("vendor", "library", "design", "1"))
    root = _design_configuration(
        "referenced",
        "sibling",
        design_ref=LibraryRefType(vendor="vendor", library="library", name="design", version="1"),
    )
    removed = root.interconnection_configuration[0]
    sibling = root.interconnection_configuration[1]
    removed_id = get_handle(removed)
    group_id = dc_api.getInterconnectionConfigurationAbstractorsInstancesIDs(removed_id)[0]
    instance_id = dc_api.getAbstractorInstancesAbstractorInstanceIDs(group_id)[0]
    reference_id = get_handle(removed)
    sibling_id = get_handle(sibling)

    assert dc_api.removeDesignConfigurationInterconnectionConfiguration(removed_id)
    assert root.interconnection_configuration == [sibling]
    assert resolve_handle(removed_id) is None
    assert resolve_handle(group_id) is None
    assert resolve_handle(instance_id) is None
    assert resolve_handle(reference_id) is None
    assert resolve_handle(sibling_id) is sibling
    assert registry.get_id(("vendor", "library", "design", "1")) == get_handle(design)
    assert not dc_api.removeDesignConfigurationInterconnectionConfiguration(removed_id)
    assert not dc_api.removeDesignConfigurationInterconnectionConfiguration("missing-interconnection-configuration")
    _valid_round_trip(root)


def test_set_interconnection_ref_normalizes_name_and_preserves_children_and_handles() -> None:
    root = _design_configuration("before")
    ic = root.interconnection_configuration[0]
    ic_id = get_handle(ic)
    group_id = dc_api.getInterconnectionConfigurationAbstractorsInstancesIDs(ic_id)[0]
    instance_id = dc_api.getAbstractorInstancesAbstractorInstanceIDs(group_id)[0]
    ic_handle_before = get_handle(ic)
    group = resolve_handle(group_id)
    instance = resolve_handle(instance_id)

    assert dc_api.setInterconnectionConfigurationInterconnectionRef(ic_id, "\t更新_connection\r\n")
    assert ic.interconnection_ref == "更新_connection"
    assert get_handle(ic) == ic_handle_before
    assert resolve_handle(group_id) is group
    assert resolve_handle(instance_id) is instance
    assert dc_api.getInterconnectionConfigurationInterconnectionRefByName(ic_id) == "更新_connection"
    _valid_round_trip(root)


@pytest.mark.parametrize("invalid_name", ["", " \t\r\n ", "bad name", "bad/name", "bad\x00name"])
def test_set_interconnection_ref_rejects_invalid_xml_names_without_mutation(invalid_name: str) -> None:
    root = _design_configuration("original")
    ic = root.interconnection_configuration[0]
    before = _valid_round_trip(root)
    with pytest.raises(TgiError) as error:
        dc_api.setInterconnectionConfigurationInterconnectionRef(get_handle(ic), invalid_name)
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert ic.interconnection_ref == "original"
    assert _valid_round_trip(root) == before


def test_set_interconnection_ref_enforces_design_configuration_scope_uniqueness() -> None:
    root = _design_configuration("first", "second")
    first, second = root.interconnection_configuration
    before = _valid_round_trip(root)
    with pytest.raises(TgiError) as duplicate:
        dc_api.setInterconnectionConfigurationInterconnectionRef(get_handle(second), "\tfirst\n")
    assert duplicate.value.fault_code == TgiFaultCode.ALREADY_EXISTS
    assert second.interconnection_ref == "second"
    assert _valid_round_trip(root) == before


def test_design_interconnection_getters_filter_mixed_order_and_restore_immediate_ownership() -> None:
    root = _design(
        _ordinary_connection("normal_first"),
        _monitor_connection("monitor_first"),
        _ordinary_connection("normal_second"),
        _monitor_connection("monitor_second"),
    )
    _valid_round_trip(root)
    design_id = get_handle(root)
    parsed = root.interconnections.interconnection_or_monitor_interconnection
    normal_first, monitor_first, normal_second, monitor_second = parsed

    normal_ids = design_api.getDesignInterconnectionIDs(design_id)
    monitor_ids = design_api.getDesignMonitorInterconnectionIDs(design_id)
    assert normal_ids == [get_handle(normal_first), get_handle(normal_second)]
    assert monitor_ids == [get_handle(monitor_first), get_handle(monitor_second)]
    assert [resolve_handle(handle) for handle in normal_ids] == [normal_first, normal_second]
    assert [resolve_handle(handle) for handle in monitor_ids] == [monitor_first, monitor_second]
    for handle in [*normal_ids, *monitor_ids]:
        parent = get_parent_info(handle)
        assert parent is not None
        assert (parent.parent_handle, parent.path, parent.container) == (
            get_handle(root.interconnections),
            ("interconnection_or_monitor_interconnection",),
            "list",
        )


def test_design_interconnection_getters_return_empty_for_absent_collection() -> None:
    root = Design(vendor="vendor", library="library", name="empty", version="1")
    design_id = get_handle(root)
    assert design_api.getDesignInterconnectionIDs(design_id) == []
    assert design_api.getDesignMonitorInterconnectionIDs(design_id) == []

"""TGI contracts for design-configuration collections."""

import inspect
from collections.abc import Iterator
from pathlib import Path
from typing import get_type_hints

import pytest
from lxml import etree

from amal.eda.accellera.ipxact.v1685_2022 import tgi
from amal.eda.accellera.ipxact.v1685_2022.tgi import design_configuration as api
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import (
    TgiError,
    TgiFaultCode,
    get_handle,
    get_parent_info,
    registry,
    resolve_handle,
)
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import ConfigurableLibraryRefType, DesignConfiguration

_REPO_ROOT = Path(__file__).resolve().parents[5]
_SCHEMA = etree.XMLSchema(etree.parse(str(_REPO_ROOT / "submodules/accellera-schemas/IPXACT/1685-2022/index.xsd")))
_API_FUNCTIONS = (
    "getAbstractorInstancesAbstractorInstanceIDs",
    "getAbstractorInstancesInterfaceRefIDs",
    "getInterconnectionConfigurationAbstractorsInstancesIDs",
    "addAbstractorInstancesInterfaceRef",
    "removeAbstractorInstancesInterfaceRef",
    "addInterconnectionConfigurationAbstractorInstances",
    "removeInterconnectionConfigurationAbstractorInstances",
)


@pytest.fixture(autouse=True)
def clean_registry() -> Iterator[None]:
    registry.clear()
    yield
    registry.clear()


def _abstractor_instance(
    name: str,
) -> DesignConfiguration.InterconnectionConfiguration.AbstractorInstances.AbstractorInstance:
    return DesignConfiguration.InterconnectionConfiguration.AbstractorInstances.AbstractorInstance(
        instance_name=name,
        abstractor_ref=ConfigurableLibraryRefType(vendor="vendor", library="library", name="abstractor", version="1"),
        view_name="rtl",
    )


def _abstractor_group(
    name: str, interface_refs: tuple[tuple[str, str], ...] = ()
) -> DesignConfiguration.InterconnectionConfiguration.AbstractorInstances:
    group_type = DesignConfiguration.InterconnectionConfiguration.AbstractorInstances
    return group_type(
        interface_ref=[
            group_type.InterfaceRef(component_ref=component, bus_ref=bus) for component, bus in interface_refs
        ],
        abstractor_instance=[_abstractor_instance(name)],
    )


def _document(
    *interconnections: tuple[str, tuple[tuple[str, tuple[tuple[str, str], ...]], ...]],
) -> DesignConfiguration:
    root = DesignConfiguration(
        vendor="vendor",
        library="library",
        name="configuration",
        version="1",
        interconnection_configuration=[
            DesignConfiguration.InterconnectionConfiguration(
                interconnection_ref=connection_name,
                abstractor_instances=[_abstractor_group(name, refs) for name, refs in groups],
            )
            for connection_name, groups in interconnections
        ],
    )
    xml = XmlDocument.serializer().render(root)
    parsed = XmlDocument.parser().from_string(xml, DesignConfiguration)
    registry.register(parsed, ("vendor", "library", "configuration", "1"))
    return parsed


def _valid_round_trip(root: DesignConfiguration) -> str:
    xml = XmlDocument.serializer().render(root)
    _SCHEMA.assertValid(etree.fromstring(xml.encode()))
    assert XmlDocument.parser().from_string(xml, DesignConfiguration) == root
    return xml


def _group(
    root: DesignConfiguration, interconnection_index: int = 0, group_index: int = 0
) -> DesignConfiguration.InterconnectionConfiguration.AbstractorInstances:
    return root.interconnection_configuration[interconnection_index].abstractor_instances[group_index]


def test_public_exports_and_native_runtime_annotations() -> None:
    expected = {
        "getAbstractorInstancesAbstractorInstanceIDs": ([str], list[str]),
        "getAbstractorInstancesInterfaceRefIDs": ([str], list[str]),
        "getInterconnectionConfigurationAbstractorsInstancesIDs": ([str], list[str]),
        "addAbstractorInstancesInterfaceRef": ([str, str, str], str),
        "removeAbstractorInstancesInterfaceRef": ([str], bool),
        "addInterconnectionConfigurationAbstractorInstances": ([str, tuple[str, str, str, str], str, str], str),
        "removeInterconnectionConfigurationAbstractorInstances": ([str], bool),
    }

    for name in _API_FUNCTIONS:
        function = getattr(api, name)
        assert getattr(tgi, name) is function
        assert name in api.__all__
        assert name in tgi.__all__
        hints = get_type_hints(function)
        assert [hints[param] for param in inspect.signature(function).parameters] == expected[name][0]
        assert hints["return"] == expected[name][1]


def test_collection_getters_preserve_order_and_restore_parsed_ownership() -> None:
    root = _document(
        (
            "connection_a",
            (("first", (("u0", "bus0"), ("u1", "bus1"))), ("second", (("u2", "bus2"),))),
        ),
        ("connection_b", (("third", (("u3", "bus3"),)),)),
    )
    connection = root.interconnection_configuration[0]
    group = connection.abstractor_instances[0]

    group_ids = api.getInterconnectionConfigurationAbstractorsInstancesIDs(get_handle(connection))
    instance_ids = api.getAbstractorInstancesAbstractorInstanceIDs(group_ids[0])
    interface_ids = api.getAbstractorInstancesInterfaceRefIDs(group_ids[0])

    assert group_ids == [get_handle(item) for item in connection.abstractor_instances]
    assert instance_ids == [get_handle(item) for item in group.abstractor_instance]
    assert interface_ids == [get_handle(item) for item in group.interface_ref]
    assert [resolve_handle(handle) for handle in interface_ids] == group.interface_ref
    assert [resolve_handle(handle) for handle in instance_ids] == group.abstractor_instance

    group_parent = get_parent_info(group_ids[0])
    instance_parent = get_parent_info(instance_ids[0])
    interface_parent = get_parent_info(interface_ids[0])
    assert group_parent is not None
    assert (group_parent.parent_handle, group_parent.path, group_parent.container) == (
        get_handle(connection),
        ("abstractor_instances",),
        "list",
    )
    assert instance_parent is not None
    assert (instance_parent.parent_handle, instance_parent.path, instance_parent.container) == (
        group_ids[0],
        ("abstractor_instance",),
        "list",
    )
    assert interface_parent is not None
    assert (interface_parent.parent_handle, interface_parent.path, interface_parent.container) == (
        group_ids[0],
        ("interface_ref",),
        "list",
    )

    # The getter handles acquired from the parsed tree must have a usable direct owner.
    sibling_id = interface_ids[1]
    assert api.removeAbstractorInstancesInterfaceRef(interface_ids[0])
    assert group.interface_ref == [group.interface_ref[0]]
    assert resolve_handle(interface_ids[0]) is None
    assert resolve_handle(sibling_id) is group.interface_ref[0]
    assert api.getAbstractorInstancesInterfaceRefIDs(group_ids[0]) == [sibling_id]
    _valid_round_trip(root)


def test_add_interface_ref_normalizes_xml_whitespace_accepts_unicode_and_round_trips() -> None:
    root = _document(("connection", (("group", ()),)))
    group = _group(root)

    interface_ref_id = api.addAbstractorInstancesInterfaceRef(get_handle(group), "\t组件_α\n", " 总线_β\r")
    added = resolve_handle(interface_ref_id)
    assert added is group.interface_ref[0]
    assert (added.component_ref, added.bus_ref) == ("组件_α", "总线_β")
    assert api.getAbstractorInstancesInterfaceRefIDs(get_handle(group)) == [interface_ref_id]
    _valid_round_trip(root)


@pytest.mark.parametrize(
    ("component_ref", "bus_ref"),
    [
        ("", "bus"),
        (" \t\r\n ", "bus"),
        ("bad name", "bus"),
        ("component", ""),
        ("component", "bad name"),
        ("component\x00", "bus"),
        ("component", "bus\x00"),
    ],
)
def test_add_interface_ref_rejects_invalid_names_atomically(component_ref: str, bus_ref: str) -> None:
    root = _document(("connection", (("group", (("u0", "bus0"),)),)))
    group = _group(root)
    before = _valid_round_trip(root)
    original_children = list(group.interface_ref)

    with pytest.raises(TgiError) as error:
        api.addAbstractorInstancesInterfaceRef(get_handle(group), component_ref, bus_ref)

    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert group.interface_ref == original_children
    assert _valid_round_trip(root) == before


def test_interface_ref_pair_is_unique_within_connection_and_reusable_across_connections() -> None:
    root = _document(
        (
            "connection_a",
            (("first", (("u0", "bus0"),)), ("second", (("u1", "bus1"),))),
        ),
        ("connection_b", (("third", (("u2", "bus2"),)),)),
    )
    duplicate_target = _group(root, group_index=1)
    before = _valid_round_trip(root)

    with pytest.raises(TgiError) as error:
        api.addAbstractorInstancesInterfaceRef(get_handle(duplicate_target), "\tu0 ", " bus0\n")

    assert error.value.fault_code == TgiFaultCode.ALREADY_EXISTS
    assert [(item.component_ref, item.bus_ref) for item in duplicate_target.interface_ref] == [("u1", "bus1")]
    assert _valid_round_trip(root) == before

    other_connection = _group(root, interconnection_index=1)
    added_id = api.addAbstractorInstancesInterfaceRef(get_handle(other_connection), "u0", "bus0")
    assert resolve_handle(added_id) is other_connection.interface_ref[-1]
    _valid_round_trip(root)


def test_interface_ref_removal_checks_owner_and_invalidates_only_removed_subtree() -> None:
    root = _document(("connection", (("first", (("u0", "bus0"), ("u1", "bus1"))),)))
    group = _group(root)
    removed, sibling = group.interface_ref
    removed_id = get_handle(removed)
    sibling_id = get_handle(sibling)
    wrong_kind_id = get_handle(root)
    unowned_id = get_handle(
        DesignConfiguration.InterconnectionConfiguration.AbstractorInstances.InterfaceRef(
            component_ref="u9", bus_ref="bus9"
        )
    )

    assert api.removeAbstractorInstancesInterfaceRef(removed_id)
    assert resolve_handle(removed_id) is None
    assert resolve_handle(sibling_id) is sibling
    assert group.interface_ref == [sibling]
    assert not api.removeAbstractorInstancesInterfaceRef(removed_id)
    assert not api.removeAbstractorInstancesInterfaceRef("missing-interface-ref")
    assert not api.removeAbstractorInstancesInterfaceRef(wrong_kind_id)
    assert not api.removeAbstractorInstancesInterfaceRef(unowned_id)
    _valid_round_trip(root)


def test_add_interconnection_group_uses_annex_argument_order_and_creates_required_instance() -> None:
    root = _document(("connection", (("seed", ()),)))
    connection = root.interconnection_configuration[0]

    group_id = api.addInterconnectionConfigurationAbstractorInstances(
        get_handle(connection), ("vendor_α", "library_β", "abstractor_γ", "7"), "  实例_δ\t", " view_ε "
    )
    group = resolve_handle(group_id)
    assert group is connection.abstractor_instances[1]
    instance_ids = api.getAbstractorInstancesAbstractorInstanceIDs(group_id)
    assert len(instance_ids) == 1
    instance = resolve_handle(instance_ids[0])
    assert (instance.instance_name, instance.view_name) == ("实例_δ", "view_ε")
    assert (
        instance.abstractor_ref.vendor,
        instance.abstractor_ref.library,
        instance.abstractor_ref.name,
        instance.abstractor_ref.version,
    ) == ("vendor_α", "library_β", "abstractor_γ", "7")
    assert api.getInterconnectionConfigurationAbstractorsInstancesIDs(get_handle(connection)) == [
        get_handle(item) for item in connection.abstractor_instances
    ]
    _valid_round_trip(root)


@pytest.mark.parametrize(
    ("vlnv", "instance_name", "view_name"),
    [
        (("vendor", "library", "abstractor"), "new", "rtl"),
        (("vendor", "library", "abstractor", ""), "new", "rtl"),
        (("vendor", "library", "abstractor\x00", "1"), "new", "rtl"),
        (("vendor", "library", "abstractor", "1"), "bad name", "rtl"),
        (("vendor", "library", "abstractor", "1"), "new", "bad\x00view"),
    ],
)
def test_add_interconnection_group_rejects_bad_values_without_partial_group(
    vlnv: tuple[object, ...], instance_name: str, view_name: str
) -> None:
    root = _document(("connection", (("seed", ()),)))
    connection = root.interconnection_configuration[0]
    before = _valid_round_trip(root)
    original_children = list(connection.abstractor_instances)

    with pytest.raises(TgiError) as error:
        api.addInterconnectionConfigurationAbstractorInstances(get_handle(connection), vlnv, instance_name, view_name)

    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert connection.abstractor_instances == original_children
    assert _valid_round_trip(root) == before


def test_add_interconnection_group_rejects_root_wide_duplicate_instance_name_atomically() -> None:
    root = _document(
        (
            "connection_a",
            (("already_used", ()),),
        ),
        ("connection_b", (("other", ()),)),
    )
    other_connection = root.interconnection_configuration[1]
    before = _valid_round_trip(root)
    original_children = list(other_connection.abstractor_instances)

    with pytest.raises(TgiError) as error:
        api.addInterconnectionConfigurationAbstractorInstances(
            get_handle(other_connection), ("vendor", "library", "abstractor", "1"), "already_used", "rtl"
        )

    assert error.value.fault_code == TgiFaultCode.ALREADY_EXISTS
    assert other_connection.abstractor_instances == original_children
    assert _valid_round_trip(root) == before


def test_interconnection_group_removal_recovers_parsed_owner_and_invalidates_descendants() -> None:
    root = _document(("connection", (("remove_me", ()), ("keep_me", ()))))
    connection = root.interconnection_configuration[0]
    removed = connection.abstractor_instances[0]
    sibling = connection.abstractor_instances[1]
    removed_id = get_handle(removed)
    sibling_id = get_handle(sibling)
    instance = removed.abstractor_instance[0]
    instance_id = get_handle(instance)
    reference_id = get_handle(instance.abstractor_ref)
    sibling_instance_id = get_handle(sibling.abstractor_instance[0])
    wrong_kind_id = get_handle(root)
    unowned_id = get_handle(DesignConfiguration.InterconnectionConfiguration.AbstractorInstances())

    assert api.removeInterconnectionConfigurationAbstractorInstances(removed_id)
    assert connection.abstractor_instances == [sibling]
    assert resolve_handle(removed_id) is None
    assert resolve_handle(instance_id) is None
    assert resolve_handle(reference_id) is None
    assert resolve_handle(sibling_id) is sibling
    assert resolve_handle(sibling_instance_id) is sibling.abstractor_instance[0]
    assert not api.removeInterconnectionConfigurationAbstractorInstances(removed_id)
    assert not api.removeInterconnectionConfigurationAbstractorInstances("missing-group")
    assert not api.removeInterconnectionConfigurationAbstractorInstances(wrong_kind_id)
    assert not api.removeInterconnectionConfigurationAbstractorInstances(unowned_id)
    _valid_round_trip(root)


@pytest.mark.parametrize("wrong_kind", [False, True])
def test_collection_getters_reject_missing_or_wrong_kind_handles(wrong_kind: bool) -> None:
    root = _document(("connection", (("group", (("u0", "bus0"),)),)))
    bad_handle = get_handle(root) if wrong_kind else "missing"
    calls = [
        lambda: api.getAbstractorInstancesAbstractorInstanceIDs(bad_handle),
        lambda: api.getAbstractorInstancesInterfaceRefIDs(bad_handle),
        lambda: api.getInterconnectionConfigurationAbstractorsInstancesIDs(bad_handle),
        lambda: api.addAbstractorInstancesInterfaceRef(bad_handle, "u1", "bus1"),
        lambda: api.addInterconnectionConfigurationAbstractorInstances(
            bad_handle, ("vendor", "library", "abstractor", "1"), "new", "rtl"
        ),
    ]

    for call in calls:
        with pytest.raises(TgiError) as error:
            call()
        assert error.value.fault_code == TgiFaultCode.INVALID_ID

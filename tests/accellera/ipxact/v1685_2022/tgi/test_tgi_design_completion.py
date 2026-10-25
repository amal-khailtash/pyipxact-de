"""Design choice, connection, and scoped generator identity contracts."""

import inspect
from collections.abc import Callable, Iterator, Sequence
from contextvars import Context

import pytest
from lxml import etree

from amal.eda.accellera.ipxact.v1685_2022 import tgi
from amal.eda.accellera.ipxact.v1685_2022.tgi import _generator_context as context_api
from amal.eda.accellera.ipxact.v1685_2022.tgi import design as api
from amal.eda.accellera.ipxact.v1685_2022.tgi._generator_context import generator_context
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
    Choices,
    ComponentInstance,
    ComponentInstances,
    ConfigurableLibraryRefType,
    Design,
    InstanceName,
    Interconnection,
    Interconnections,
    MonitorInterconnection,
    MonitorInterfaceType,
    Parameters,
    ParameterType,
    Value,
)

_SCHEMA = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))
_API_FUNCTIONS = (
    "getDesignChoiceIDs",
    "getDesignID",
    "addDesignChoice",
    "addDesignInterconnection",
    "addDesignMonitorInterconnection",
    "removeDesignChoice",
    "removeDesignInterconnection",
    "removeDesignMonitorConnection",
)


@pytest.fixture(autouse=True)
def clean_registry() -> Iterator[None]:
    registry.clear()
    yield
    registry.clear()


def _design(
    *,
    name: str = "design_completion",
    choices: Choices | None = None,
    connections: list[Interconnection | MonitorInterconnection] | None = None,
) -> Design:
    return Design(
        vendor="acme",
        library="systems",
        name=name,
        version="1.0",
        component_instances=ComponentInstances(
            component_instance=[
                ComponentInstance(
                    instance_name=InstanceName(value=f"u{index}"),
                    component_ref=ConfigurableLibraryRefType(
                        vendor="acme", library="blocks", name=f"block{index}", version="1.0"
                    ),
                )
                for index in range(4)
            ]
        ),
        choices=choices,
        interconnections=(
            Interconnections(interconnection_or_monitor_interconnection=connections)
            if connections is not None
            else None
        ),
    )


def _register(root: Design) -> Design:
    registry.register(root, (root.vendor, root.library, root.name, root.version))
    return root


def _registered(*, name: str = "design_completion") -> Design:
    return _register(_design(name=name))


def _parse_registered(root: Design) -> Design:
    xml = XmlDocument.serializer().render(root)
    _SCHEMA.assertValid(etree.fromstring(xml.encode()))
    parsed = XmlDocument.parser().from_string(xml, Design)
    return _register(parsed)


def _schema_round_trip(root: Design) -> str:
    xml = XmlDocument.serializer().render(root)
    _SCHEMA.assertValid(etree.fromstring(xml.encode()))
    parsed = XmlDocument.parser().from_string(xml, Design)
    assert XmlDocument.serializer().render(parsed) == xml
    return xml


def test_public_exports_and_annex_f_signatures() -> None:
    expected = {
        "getDesignChoiceIDs": (("designID",), (str,), list[str], "F.7.37.13"),
        "getDesignID": (("top",), (bool,), str | None, "F.7.37.15"),
        "addDesignChoice": (
            ("designID", "name", "enumerations"),
            (str, str, Sequence[str]),
            str,
            "F.7.38.5",
        ),
        "addDesignInterconnection": (
            (
                "designID",
                "name",
                "componentInstanceRef1",
                "busInterfaceRef1",
                "componentInstanceRef2",
                "busInterfaceRef2",
            ),
            (str, str, str, str, str, str),
            str,
            "F.7.38.8",
        ),
        "addDesignMonitorInterconnection": (
            (
                "designID",
                "name",
                "componentInstanceRef1",
                "activeInterfaceBusInterfaceRef",
                "componentInstanceRef2",
                "interfaceBusInterfaceRef",
            ),
            (str, str, str, str, str, str),
            str,
            "F.7.38.9",
        ),
        "removeDesignChoice": (("choiceID",), (str,), bool, "F.7.38.18"),
        "removeDesignInterconnection": (("interconnectionID",), (str,), bool, "F.7.38.20"),
        "removeDesignMonitorConnection": (("monitorInterconnectionID",), (str,), bool, "F.7.38.21"),
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


def test_choice_add_and_get_register_ordered_ownership_and_round_trip() -> None:
    root = _registered()
    design_id = get_handle(root)

    assert api.getDesignChoiceIDs(design_id) == []
    first_id = api.addDesignChoice(design_id, "  data_mode\n", ["0", " MODE + 1 "])
    second_id = api.addDesignChoice(design_id, "parity", ("EVEN", "ODD"))
    first = resolve_handle(first_id)
    second = resolve_handle(second_id)

    assert api.getDesignChoiceIDs(design_id) == [first_id, second_id]
    assert first.name == "data_mode"
    assert [item.value for item in first.enumeration] == ["0", " MODE + 1 "]
    assert second.name == "parity"
    assert [item.value for item in second.enumeration] == ["EVEN", "ODD"]
    with pytest.raises(TgiError) as duplicate:
        api.addDesignChoice(design_id, "\tdata_mode \n", ["2"])
    assert duplicate.value.fault_code == TgiFaultCode.ALREADY_EXISTS
    assert api.getDesignChoiceIDs(design_id) == [first_id, second_id]
    info = get_parent_info(first_id)
    assert info is not None
    assert info.parent_handle == get_handle(root.choices)
    assert info.path == ("choice",)
    assert info.container == "list"
    _schema_round_trip(root)


def test_choice_getter_accepts_tuple_storage_and_rejects_malformed_collections() -> None:
    first = Choices.Choice(name="first", enumeration=[Choices.Choice.Enumeration(value="0")])
    second = Choices.Choice(name="second", enumeration=[Choices.Choice.Enumeration(value="1")])
    root = _register(_design(choices=Choices(choice=(first, second))))
    design_id = get_handle(root)
    expected = [get_handle(first), get_handle(second)]
    assert api.getDesignChoiceIDs(design_id) == expected
    assert isinstance(root.choices.choice, tuple)

    root.choices.choice = [first, object()]
    with pytest.raises(TgiError) as error:
        api.getDesignChoiceIDs(design_id)
    assert error.value.fault_code == TgiFaultCode.INVALID_ID


@pytest.mark.parametrize(
    ("name", "enumerations"),
    [
        ("", ["0"]),
        ("   ", ["0"]),
        ("valid", []),
        ("valid", "0"),
        ("valid", [" "]),
        ("valid", [None]),
        ("valid", [1]),
    ],
    ids=(
        "empty-name",
        "whitespace-name",
        "empty-enumerations",
        "string-sequence",
        "blank-enumeration",
        "none-value",
        "integer-value",
    ),
)
def test_add_choice_rejects_malformed_input_atomically(name: str, enumerations: object) -> None:
    root = _registered()
    design_id = get_handle(root)
    before = root.choices

    with pytest.raises(TgiError) as error:
        api.addDesignChoice(design_id, name, enumerations)

    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert root.choices is before
    assert api.getDesignChoiceIDs(design_id) == []


def test_choice_removal_prunes_empty_holder_invalidates_removed_handle_and_preserves_siblings() -> None:
    root = _parse_registered(
        _design(
            choices=Choices(
                choice=[
                    Choices.Choice(name="first", enumeration=[Choices.Choice.Enumeration(value="0")]),
                    Choices.Choice(name="second", enumeration=[Choices.Choice.Enumeration(value="1")]),
                ]
            )
        )
    )
    # Removal starts from child handles in a parsed document without first calling a getter.
    first_id, second_id = (get_handle(child) for child in root.choices.choice)

    assert api.removeDesignChoice(first_id) is True
    assert resolve_handle(first_id) is None
    assert resolve_handle(second_id) is root.choices.choice[0]
    assert api.getDesignChoiceIDs(get_handle(root)) == [second_id]
    _schema_round_trip(root)
    assert api.removeDesignChoice(second_id) is True
    assert root.choices is None
    assert resolve_handle(get_handle(root)) is root
    assert resolve_handle(second_id) is None


def test_choice_removal_refuses_parameter_references_and_rejects_wrong_or_orphan_handles() -> None:
    choice = Choices.Choice(name="select", enumeration=[Choices.Choice.Enumeration(value="A")])
    root = _register(_design(choices=Choices(choice=[choice])))
    choice_id = api.getDesignChoiceIDs(get_handle(root))[0]
    root.parameters = Parameters(parameter=[ParameterType(name="MODE", choice_ref="select", value=Value(value="A"))])
    assert api.removeDesignChoice(choice_id) is False
    assert resolve_handle(choice_id) is choice

    standalone = get_handle(Choices.Choice(name="orphan", enumeration=[Choices.Choice.Enumeration(value="0")]))
    for wrong_id in (get_handle(root), standalone):
        with pytest.raises(TgiError) as error:
            api.removeDesignChoice(wrong_id)
        assert error.value.fault_code == TgiFaultCode.INVALID_ID


def test_mixed_connection_addition_preserves_shared_order_names_and_schema_round_trip() -> None:
    root = _registered()
    design_id = get_handle(root)
    ordinary_id = api.addDesignInterconnection(design_id, "ordinary", "u0", "bus0", "u1", "bus1")
    monitor_id = api.addDesignMonitorInterconnection(design_id, "monitor", "u0", "bus0", "u1", "bus1")
    last_id = api.addDesignInterconnection(design_id, "last", "u2", "bus2", "u3", "bus3")

    assert api.getDesignInterconnectionIDs(design_id) == [ordinary_id, last_id]
    assert api.getDesignMonitorInterconnectionIDs(design_id) == [monitor_id]
    children = root.interconnections.interconnection_or_monitor_interconnection
    assert [child.name for child in children] == ["ordinary", "monitor", "last"]
    assert isinstance(children[0], Interconnection)
    assert isinstance(children[1], MonitorInterconnection)
    assert [interface.component_instance_ref for interface in children[0].active_interface] == ["u0", "u1"]
    assert children[1].monitored_active_interface.component_instance_ref == "u0"
    assert [interface.component_instance_ref for interface in children[1].monitor_interface] == ["u1"]
    info = get_parent_info(monitor_id)
    assert info is not None
    assert info.parent_handle == get_handle(root.interconnections)
    assert info.path == ("interconnection_or_monitor_interconnection",)
    assert _schema_round_trip(root)


def test_parsed_mixed_connections_can_be_removed_before_getters() -> None:
    root = _parse_registered(
        _design(
            name="parsed_connections",
            connections=[
                Interconnection(
                    name="ordinary",
                    active_interface=[
                        ActiveInterface(component_instance_ref="u0", bus_ref="bus0"),
                        ActiveInterface(component_instance_ref="u1", bus_ref="bus1"),
                    ],
                ),
                MonitorInterconnection(
                    name="monitor",
                    monitored_active_interface=MonitorInterfaceType(component_instance_ref="u0", bus_ref="bus0"),
                    monitor_interface=[MonitorInterfaceType(component_instance_ref="u1", bus_ref="bus1")],
                ),
            ],
        )
    )
    ordinary_id, monitor_id = (
        get_handle(child) for child in root.interconnections.interconnection_or_monitor_interconnection
    )

    assert api.removeDesignInterconnection(ordinary_id) is True
    assert api.removeDesignMonitorConnection(monitor_id) is True
    assert root.interconnections is None
    assert resolve_handle(ordinary_id) is None
    assert resolve_handle(monitor_id) is None
    assert resolve_handle(get_handle(root)) is root


def test_connection_additions_normalize_tuple_storage_without_reordering_and_validate_malformed_children() -> None:
    existing = Interconnection(
        name="existing",
        active_interface=[],
    )
    root = _register(_design(connections=[existing]))
    root.interconnections.interconnection_or_monitor_interconnection = (existing,)
    design_id = get_handle(root)
    added_id = api.addDesignMonitorInterconnection(design_id, "new", "u0", "bus0", "u1", "bus1")
    assert root.interconnections.interconnection_or_monitor_interconnection == [existing, resolve_handle(added_id)]

    malformed = _register(_design(name="malformed", connections=[existing]))
    malformed.interconnections.interconnection_or_monitor_interconnection = [object()]
    with pytest.raises(TgiError) as error:
        api.addDesignInterconnection(get_handle(malformed), "new", "u0", "bus0", "u1", "bus1")
    assert error.value.fault_code == TgiFaultCode.INVALID_ID


@pytest.mark.parametrize(
    "operation",
    ("ordinary", "monitor"),
    ids=("interconnection", "monitor-interconnection"),
)
def test_connection_adders_reject_bad_endpoints_and_cross_type_duplicate_names(operation: str) -> None:
    root = _registered()
    design_id = get_handle(root)
    add = api.addDesignInterconnection if operation == "ordinary" else api.addDesignMonitorInterconnection
    args = ("collision", "u0", "bus0", "u1", "bus1")
    add(design_id, *args)
    before = tuple(root.interconnections.interconnection_or_monitor_interconnection)

    with pytest.raises(TgiError) as duplicate:
        (api.addDesignMonitorInterconnection if operation == "ordinary" else api.addDesignInterconnection)(
            design_id, *args
        )
    assert duplicate.value.fault_code == TgiFaultCode.ALREADY_EXISTS
    assert tuple(root.interconnections.interconnection_or_monitor_interconnection) == before

    bad_args = ("valid_name", "u0", "", "u1", "bus1")
    with pytest.raises(TgiError) as invalid:
        add(design_id, *bad_args)
    assert invalid.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert tuple(root.interconnections.interconnection_or_monitor_interconnection) == before


@pytest.mark.parametrize(
    ("remove", "wrong_add", "target_kind"),
    [
        (api.removeDesignInterconnection, api.addDesignMonitorInterconnection, "ordinary"),
        (api.removeDesignMonitorConnection, api.addDesignInterconnection, "monitor"),
    ],
    ids=("remove-interconnection", "remove-monitor-interconnection"),
)
def test_connection_removers_invalidate_only_target_and_prune_empty_holder(
    remove: Callable[[str], bool],
    wrong_add: Callable[[str, str, str, str, str, str], str],
    target_kind: str,
) -> None:
    root = _registered()
    design_id = get_handle(root)
    create = api.addDesignInterconnection if target_kind == "ordinary" else api.addDesignMonitorInterconnection
    target_id = create(design_id, "target", "u0", "bus0", "u1", "bus1")
    sibling_id = wrong_add(design_id, "sibling", "u2", "bus2", "u3", "bus3")
    target = resolve_handle(target_id)
    sibling = resolve_handle(sibling_id)
    if target_kind == "ordinary":
        descendant_ids = api.getInterconnectionActiveInterfaceIDs(target_id)
    else:
        descendant_ids = api.getMonitorInterconnectionMonitorInterfaceIDs(target_id)
        monitored_id = api.getMonitorInterconnectionMonitoredActiveInterfaceID(target_id)
        descendant_ids.append(monitored_id)

    assert remove(target_id) is True
    assert resolve_handle(target_id) is None
    assert all(resolve_handle(descendant_id) is None for descendant_id in descendant_ids)
    assert resolve_handle(sibling_id) is sibling
    assert root.interconnections.interconnection_or_monitor_interconnection == [sibling]
    _schema_round_trip(root)
    remove_sibling = api.removeDesignMonitorConnection if target_kind == "ordinary" else api.removeDesignInterconnection
    assert remove_sibling(sibling_id) is True
    assert root.interconnections is None
    assert resolve_handle(get_handle(root)) is root
    with pytest.raises(TgiError) as stale:
        remove(target_id)
    assert stale.value.fault_code == TgiFaultCode.INVALID_ID
    assert target is not sibling


def test_connection_removers_reject_wrong_or_orphan_handles() -> None:
    ordinary = Interconnection(name="ordinary")
    monitor = MonitorInterconnection(
        name="monitor", monitored_active_interface=MonitorInterfaceType(component_instance_ref="u0", bus_ref="bus0")
    )
    ordinary_id, monitor_id = get_handle(ordinary), get_handle(monitor)
    root = _registered()
    attached_ordinary = api.addDesignInterconnection(get_handle(root), "attached", "u0", "bus0", "u1", "bus1")
    attached_monitor = api.addDesignMonitorInterconnection(
        get_handle(root), "attached_monitor", "u0", "bus0", "u1", "bus1"
    )

    for operation, wrong_id in (
        (api.removeDesignInterconnection, monitor_id),
        (api.removeDesignMonitorConnection, ordinary_id),
        (api.removeDesignInterconnection, get_handle(root)),
        (api.removeDesignMonitorConnection, get_handle(root)),
        (api.removeDesignInterconnection, attached_monitor),
        (api.removeDesignMonitorConnection, attached_ordinary),
    ):
        with pytest.raises(TgiError) as error:
            operation(wrong_id)
        assert error.value.fault_code == TgiFaultCode.INVALID_ID

    assert api.getDesignInterconnectionIDs(get_handle(root)) == [attached_ordinary]
    assert api.getDesignMonitorInterconnectionIDs(get_handle(root)) == [attached_monitor]


def test_connection_getters_and_adders_validate_design_collection_shape() -> None:
    root = _registered()
    design_id = get_handle(root)
    root.interconnections = object()

    with pytest.raises(TgiError) as getter_error:
        api.getDesignInterconnectionIDs(design_id)
    assert getter_error.value.fault_code == TgiFaultCode.INVALID_ID
    with pytest.raises(TgiError) as adder_error:
        api.addDesignInterconnection(design_id, "bad", "u0", "bus0", "u1", "bus1")
    assert adder_error.value.fault_code == TgiFaultCode.INVALID_ID

    malformed_child_root = _registered(name="malformed_child")
    malformed_child_root.interconnections = Interconnections(interconnection_or_monitor_interconnection=[object()])
    with pytest.raises(TgiError) as child_error:
        api.getDesignMonitorInterconnectionIDs(get_handle(malformed_child_root))
    assert child_error.value.fault_code == TgiFaultCode.INVALID_ID


def test_get_design_id_uses_nested_scoped_current_and_top_context_and_restores_after_errors() -> None:
    current = _registered(name="current")
    top = _registered(name="top")
    nested = _registered(name="nested")

    assert api.getDesignID(False) is None
    assert api.getDesignID(True) is None
    with generator_context(get_handle(current), get_handle(top)):
        assert api.getDesignID(False) == get_handle(current)
        assert api.getDesignID(True) == get_handle(top)
        assert Context().run(api.getDesignID, False) is None
        with pytest.raises(RuntimeError), generator_context(get_handle(nested)):
            assert api.getDesignID(False) == get_handle(nested)
            assert api.getDesignID(True) == get_handle(nested)
            raise RuntimeError("restore outer context")
        assert api.getDesignID(False) == get_handle(current)
        assert api.getDesignID(True) == get_handle(top)
    assert api.getDesignID(False) is None
    assert api.getDesignID(True) is None


@pytest.mark.parametrize("bad_top", [1, None, "true"], ids=("integer", "none", "string"))
def test_get_design_id_rejects_non_boolean_selector(bad_top: object) -> None:
    with pytest.raises(TgiError) as error:
        api.getDesignID(bad_top)
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT


def test_generator_context_rejects_stale_wrong_and_orphan_handles_without_changing_outer_context(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    current = _registered(name="current")
    standalone_choice_id = get_handle(Choices.Choice(name="other", enumeration=[Choices.Choice.Enumeration(value="0")]))
    with generator_context(get_handle(current)):
        for bad_handle in ("unknown-handle", standalone_choice_id):
            with pytest.raises(TgiError) as error, generator_context(bad_handle):
                pytest.fail("invalid handle unexpectedly established generator context")
            assert error.value.fault_code == TgiFaultCode.INVALID_ID
            assert api.getDesignID(False) == get_handle(current)

        other = _registered(name="other")
        other_id = get_handle(other)
        actual_resolve = context_api.resolve_handle
        with generator_context(other_id):
            monkeypatch.setattr(
                context_api,
                "resolve_handle",
                lambda handle: None if handle == other_id else actual_resolve(handle),
            )
            with pytest.raises(TgiError) as stale:
                api.getDesignID(False)
            assert stale.value.fault_code == TgiFaultCode.INVALID_ID
        monkeypatch.setattr(context_api, "resolve_handle", actual_resolve)
        assert api.getDesignID(False) == get_handle(current)


@pytest.mark.parametrize(
    ("name", "expression"),
    [("bad name", "1"), ("9mode", "1"), ("mode", "1 +"), ("mode", "1\x00"), ("mode", "bad\x00value")],
    ids=("invalid-name", "numeric-name", "malformed-expression", "illegal-xml-numeric", "illegal-xml-symbolic"),
)
def test_choice_name_and_expression_failures_leave_holder_absent(name: str, expression: str) -> None:
    root = _registered()
    with pytest.raises(TgiError) as failure:
        api.addDesignChoice(get_handle(root), name, [expression])
    assert failure.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert root.choices is None


def test_choice_tuple_mutation_preserves_existing_metadata_and_rejects_normalized_duplicate() -> None:
    existing = Choices.Choice(
        name="mode", id="preserved_choice", enumeration=[Choices.Choice.Enumeration(value="0", help="preserved help")]
    )
    root = _register(_design(choices=Choices(choice=(existing,))))
    design_id = get_handle(root)
    with pytest.raises(TgiError) as duplicate:
        api.addDesignChoice(design_id, " mode\n", ["1"])
    assert duplicate.value.fault_code == TgiFaultCode.ALREADY_EXISTS
    assert root.choices.choice == (existing,)
    assert existing.id == "preserved_choice"
    assert existing.enumeration[0].help == "preserved help"
    added_id = api.addDesignChoice(design_id, "size", ["WIDTH + 1"])
    assert isinstance(root.choices.choice, list)
    assert root.choices.choice[0] is existing
    assert api.getDesignChoiceIDs(design_id) == [get_handle(existing), added_id]
    enumeration_id = get_handle(existing.enumeration[0])
    assert api.removeDesignChoice(get_handle(existing))
    assert resolve_handle(enumeration_id) is None
    assert api.getDesignChoiceIDs(design_id) == [added_id]
    _schema_round_trip(root)

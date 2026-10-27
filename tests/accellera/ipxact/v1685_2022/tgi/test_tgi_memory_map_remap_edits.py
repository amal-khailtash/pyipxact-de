"""Memory remap mode, definition-reference, and subspace base mutations."""

import inspect

import pytest
from lxml import etree

from amal.eda.accellera.ipxact.v1685_2022 import tgi as api
from amal.eda.accellera.ipxact.v1685_2022.tgi.component import _register_graph
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
    AlternateRegisters,
    BusInterface,
    BusInterfaces,
    BusInterfaceType,
    Component,
    ComponentType,
    ConfigurableLibraryRefType,
    ExternalTypeDefinitions,
    MemoryMaps,
    MemoryMapType,
    MemoryRemap,
    MemoryRemapType,
    ModeRef,
    SignedLongintExpression,
    SubspaceMap,
)

SCHEMA = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))
OPERATIONS = {
    "addMemoryRemapModeRef": ["memoryRemapID", "modeRef", "priority"],
    "removeMemoryRemapModeRef": ["modeRefID"],
    "setMemoryRemapRemapDefinitionRef": ["memoryRemapID", "value", "typeDefinitions"],
    "setSubSpaceMapBaseAddress": ["subSpaceMapID", "baseAddress"],
}


@pytest.fixture(autouse=True)
def isolate_registry():
    registry.clear()
    yield
    registry.clear()


def component(remaps, names=("active", "sleep")):
    owner = Component(
        vendor="test",
        library="memory",
        name="remap_edits",
        version="1",
        memory_maps=MemoryMaps(memory_map=[MemoryMapType(name="map", choice=list(remaps))]),
        bus_interfaces=BusInterfaces(
            bus_interface=[
                BusInterface(
                    name="bus",
                    bus_type=ConfigurableLibraryRefType(vendor="test", library="bus", name="bus", version="1"),
                    choice=BusInterfaceType.Initiator(),
                )
            ]
        ),
        modes=ComponentType.Modes(mode=[ComponentType.Modes.Mode(name=name) for name in names]),
        type_definitions=ComponentType.TypeDefinitions(
            external_type_definitions=[
                ExternalTypeDefinitions(
                    name="definitions",
                    type_definitions_ref=ConfigurableLibraryRefType(
                        vendor="test", library="types", name="definitions", version="1"
                    ),
                )
            ]
        ),
    )
    _register_graph(owner)
    return owner


def subspace(source="-4", *, base_address=None, **kwargs):
    return SubspaceMap(
        name="sub",
        base_address=base_address if base_address is not None else SignedLongintExpression(value=source),
        initiator_ref="bus",
        **kwargs,
    )


def test_exports_signatures_and_invalid_owner_handles():
    from amal.eda.accellera.ipxact.v1685_2022.tgi import memory_map

    for name, parameters in OPERATIONS.items():
        operation = getattr(api, name)
        assert name in memory_map.__all__
        assert list(inspect.signature(operation).parameters) == parameters
        invalid_values = (None, [], {}, "missing", get_handle(ModeRef(value="foreign", priority=0)))
        for invalid in invalid_values:
            args = (
                [invalid, "value", "definitions"]
                if len(parameters) == 3
                else [invalid, "value"]
                if len(parameters) == 2
                else [invalid]
            )
            with pytest.raises(TgiError) as error:
                operation(*args)
            assert error.value.fault_code == TgiFaultCode.INVALID_ID


def test_add_mode_ref_normalizes_names_checks_signed_long_priority_and_preserves_tuple():
    first = ModeRef(value="active", priority=0)
    original = (first,)
    remap = MemoryRemap(name="remap", mode_ref=original)
    remap_id = get_handle(remap)

    mode_id = api.addMemoryRemapModeRef(remap_id, "  sleep  ", (1 << 63) - 1)
    mode = resolve_handle(mode_id)
    assert isinstance(mode, ModeRef)
    assert (mode.value, mode.priority) == ("sleep", (1 << 63) - 1)
    assert remap.mode_ref == [first, mode]
    assert remap.mode_ref is not original
    assert api.getMemoryRemapModeRefIDs(remap_id) == [get_handle(first), mode_id]
    info = get_parent_info(mode_id)
    assert resolve_handle(info.parent_handle) is remap and info.path == ("mode_ref",) and info.container == "list"


@pytest.mark.parametrize("priority", [-1, True, 1.0, "1", 1 << 63])
def test_add_mode_ref_rejects_bad_priorities_atomically(priority):
    first = ModeRef(value="active", priority=0)
    original = (first,)
    remap = MemoryRemap(name="remap", mode_ref=original)
    with pytest.raises(TgiError) as error:
        api.addMemoryRemapModeRef(get_handle(remap), "sleep", priority)
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert remap.mode_ref is original


@pytest.mark.parametrize("name", ["", "bad name", [], 17])
def test_add_mode_ref_rejects_bad_names_atomically(name):
    original = ()
    remap = MemoryRemap(name="remap", mode_ref=original)
    with pytest.raises(TgiError) as error:
        api.addMemoryRemapModeRef(get_handle(remap), name, 0)
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert remap.mode_ref is original


def test_add_mode_ref_enforces_schema_priority_and_mode_name_scopes():
    first = ModeRef(value="active", priority=0)
    remap = MemoryRemap(name="first", mode_ref=[first])
    sibling = MemoryRemap(name="second", mode_ref=[ModeRef(value="sleep", priority=0)])
    owner = component([remap, sibling])

    with pytest.raises(TgiError) as error:
        api.addMemoryRemapModeRef(get_handle(remap), "  sleep  ", 1)
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert remap.mode_ref == [first]

    for name, priority in (("other", 0), ("active", 1)):
        with pytest.raises(TgiError) as error:
            api.addMemoryRemapModeRef(get_handle(remap), name, priority)
        assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
        assert remap.mode_ref == [first]

    assert api.addMemoryRemapModeRef(get_handle(remap), "other", 1)
    assert owner.memory_maps.memory_map[0].choice == [remap, sibling]


def test_add_mode_ref_rejects_malformed_stored_collection_without_normalizing_it():
    for original in (
        None,
        {},
        (object(),),
        (ModeRef(value="bad name", priority=0),),
        (ModeRef(value="sleep", priority=0), ModeRef(value="sleep", priority=1)),
        (ModeRef(value="sleep", priority=0), ModeRef(value="active", priority=0)),
    ):
        remap = MemoryRemap(name="remap", mode_ref=original)
        with pytest.raises(TgiError) as error:
            api.addMemoryRemapModeRef(get_handle(remap), "sleep", 1)
        assert error.value.fault_code == TgiFaultCode.INVALID_ID
        assert remap.mode_ref is original


def test_remove_mode_ref_requires_actual_memory_remap_ownership_and_invalidates_handle():
    reference = ModeRef(value="active", priority=0, id="xml-mode-id")
    sibling_reference = ModeRef(value="sleep", priority=1, id="sibling-xml-id")
    remap = MemoryRemap(name="remap", mode_ref=(reference, sibling_reference))
    parsed_owner = XmlDocument.parser().from_string(XmlDocument.serializer().render(component([remap])), Component)
    registry.register(parsed_owner, ("test", "memory", "parsed", "1"))
    parsed_remap = parsed_owner.memory_maps.memory_map[0].choice[0]
    parsed_remap.mode_ref = tuple(parsed_remap.mode_ref)
    parsed_reference, parsed_sibling = parsed_remap.mode_ref
    mode_id, sibling_id = get_handle(parsed_reference), get_handle(parsed_sibling)

    assert isinstance(parsed_remap.mode_ref, tuple)
    assert api.removeMemoryRemapModeRef(mode_id) is True
    assert parsed_remap.mode_ref == [parsed_sibling]
    assert isinstance(parsed_remap.mode_ref, list)
    assert resolve_handle(mode_id) is None
    assert resolve_handle(sibling_id) is parsed_sibling
    with pytest.raises(TgiError) as error:
        api.removeMemoryRemapModeRef(mode_id)
    assert error.value.fault_code == TgiFaultCode.INVALID_ID

    foreign = ModeRef(value="foreign", priority=0)
    alternate = AlternateRegisters.AlternateRegister(name="alternate", mode_ref=[foreign])
    _register_graph(alternate)
    foreign_id = get_handle(foreign)
    with pytest.raises(TgiError) as error:
        api.removeMemoryRemapModeRef(foreign_id)
    assert error.value.fault_code == TgiFaultCode.INVALID_ID

    detached = ModeRef(value="detached", priority=0)
    with pytest.raises(TgiError) as error:
        api.removeMemoryRemapModeRef(get_handle(detached))
    assert error.value.fault_code == TgiFaultCode.INVALID_ID


def test_definition_setter_updates_wrapper_or_invalidates_inline_subtree_only():
    child = subspace()
    mode_ref = ModeRef(value="active", priority=0, id="mode-xml-id")
    remap = MemoryRemap(name="remap", choice=(child,), mode_ref=(mode_ref,), id="remap-xml-id")
    component([remap])
    remap_id, child_id, base_id, mode_id = map(get_handle, (remap, child, child.base_address, mode_ref))

    assert api.setMemoryRemapRemapDefinitionRef(remap_id, "  def  ", "  defs  ") is True
    (reference,) = remap.choice
    reference_id = get_handle(reference)
    assert isinstance(reference, MemoryRemapType.RemapDefinitionRef)
    assert (reference.value, reference.type_definitions) == ("def", "defs")
    assert remap.id == "remap-xml-id" and remap.mode_ref == (mode_ref,)
    assert resolve_handle(child_id) is None and resolve_handle(base_id) is None
    assert resolve_handle(mode_id) is mode_ref

    assert api.setMemoryRemapRemapDefinitionRef(remap_id, " next ", " imported ") is True
    assert remap.choice[0] is reference
    assert get_handle(remap.choice[0]) == reference_id
    assert reference.value == "next" and reference.type_definitions == "imported"


@pytest.mark.parametrize(
    "bad",
    [
        pytest.param((object(),), id="foreign-child"),
        pytest.param(
            (MemoryRemapType.RemapDefinitionRef(value="bad", type_definitions="defs"), subspace()),
            id="conflicting-reference",
        ),
    ],
)
def test_invalid_remap_choices_fail_before_definition_mutation(bad):
    remap = MemoryRemap(name="remap", choice=bad, mode_ref=[ModeRef(value="active", priority=0)])
    original = remap.choice
    with pytest.raises(TgiError):
        api.setMemoryRemapRemapDefinitionRef(get_handle(remap), "def", "defs")
    assert remap.choice is original


def test_definition_setter_rejects_bad_names_without_mutation():
    ref = MemoryRemapType.RemapDefinitionRef(value="old", type_definitions="defs")
    remap = MemoryRemap(name="remap", choice=[ref], mode_ref=[ModeRef(value="active", priority=0)])
    original = (ref.value, ref.type_definitions)
    for value, definitions in (("bad name", "defs"), ("new", "bad name"), ("", "defs")):
        with pytest.raises(TgiError) as error:
            api.setMemoryRemapRemapDefinitionRef(get_handle(remap), value, definitions)
        assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
        assert (ref.value, ref.type_definitions) == original


@pytest.mark.parametrize(
    "source,expected,bounds",
    [
        (str(-(1 << 63)), -(1 << 63), (None, None)),
        (str((1 << 63) - 1), (1 << 63) - 1, (None, None)),
        ("PARAM", None, (-(1 << 31), (1 << 31) - 1)),
        ("-(2 + 3)", -5, (-(1 << 31), (1 << 31) - 1)),
    ],
)
def test_subspace_setter_preserves_signed_wrapper_bounds_attributes_and_source(source, expected, bounds):
    node = SignedLongintExpression(value="0", minimum=bounds[0], maximum=bounds[1])
    node.other_attributes = {"{urn:test}tag": "kept"}
    sub = subspace(base_address=node)
    node_id = get_handle(node)

    assert api.setSubSpaceMapBaseAddress(get_handle(sub), source) is True
    assert node.value == source
    assert (node.minimum, node.maximum) == bounds
    assert node.other_attributes == {"{urn:test}tag": "kept"}
    assert get_handle(sub.base_address) == node_id
    if expected is not None:
        assert api.getSubspaceMapBaseAddress(get_handle(sub)) == expected
    else:
        assert api.getSubspaceMapBaseAddressExpression(get_handle(sub)) == "PARAM"


@pytest.mark.parametrize("source", ["", "1.5", "1 / 0", str(-(1 << 63) - 1), str(1 << 63)])
def test_subspace_setter_rejects_invalid_expression_before_mutation(source):
    sub = subspace("-4")
    node = sub.base_address
    node_id = get_handle(node)
    with pytest.raises(TgiError) as error:
        api.setSubSpaceMapBaseAddress(get_handle(sub), source)
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert node.value == "-4" and get_handle(sub.base_address) == node_id


def test_subspace_setter_obeys_declared_bounds_and_rejects_missing_or_wrong_wrapper():
    sub = subspace("-4")
    sub.base_address.minimum, sub.base_address.maximum = -5, -3
    assert api.setSubSpaceMapBaseAddress(get_handle(sub), "-5") is True
    with pytest.raises(TgiError) as error:
        api.setSubSpaceMapBaseAddress(get_handle(sub), "-6")
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert sub.base_address.value == "-5"

    for invalid in (None, ModeRef(value="wrong", priority=0)):
        sub.base_address = invalid
        with pytest.raises(TgiError) as error:
            api.setSubSpaceMapBaseAddress(get_handle(sub), "1")
        assert error.value.fault_code == TgiFaultCode.INVALID_ID


def test_inline_and_referenced_remaps_and_signed_subspace_round_trip_validate():
    child = subspace("-4")
    remap = MemoryRemap(
        name="inline",
        mode_ref=[ModeRef(value="active", priority=0)],
        choice=[child],
    )
    inline_owner = component([remap])
    assert api.setSubSpaceMapBaseAddress(get_handle(child), str(-(1 << 63))) is True
    inline_xml = XmlDocument.serializer().render(inline_owner)
    assert SCHEMA.validate(etree.fromstring(inline_xml.encode())), SCHEMA.error_log
    parsed_inline = XmlDocument.parser().from_string(inline_xml, Component)
    parsed_subspace = parsed_inline.memory_maps.memory_map[0].choice[0].choice[0]
    assert parsed_subspace.base_address.value == str(-(1 << 63))
    assert api.getSubspaceMapBaseAddress(get_handle(parsed_subspace)) == -(1 << 63)

    assert api.setMemoryRemapRemapDefinitionRef(get_handle(remap), "definition", "definitions") is True
    reference_xml = XmlDocument.serializer().render(inline_owner)
    assert SCHEMA.validate(etree.fromstring(reference_xml.encode())), SCHEMA.error_log
    parsed_reference = XmlDocument.parser().from_string(reference_xml, Component)
    parsed_remap = parsed_reference.memory_maps.memory_map[0].choice[0]
    assert isinstance(parsed_remap.choice[0], MemoryRemapType.RemapDefinitionRef)
    assert (parsed_remap.choice[0].value, parsed_remap.choice[0].type_definitions) == (
        "definition",
        "definitions",
    )
    assert [item.value for item in parsed_remap.mode_ref] == ["active"]

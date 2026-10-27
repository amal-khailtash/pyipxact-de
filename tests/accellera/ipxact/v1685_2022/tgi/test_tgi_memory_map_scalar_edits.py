"""Memory map shared and definition-reference mutations."""

import inspect

import pytest
from lxml import etree
from xsdata.formats.dataclass.models.generics import AnyElement

from amal.eda.accellera.ipxact.v1685_2022 import tgi as api
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
    AddressBlock,
    AddressUnitBits,
    Bank,
    BankAlignmentType,
    BaseAddress,
    Component,
    ComponentType,
    ConfigurableLibraryRefType,
    DisplayName,
    ExternalTypeDefinitions,
    LocalMemoryMapType,
    MemoryMapDefinitions,
    MemoryMaps,
    MemoryMapType,
    MemoryRemap,
    ModeRef,
    SharedType,
    SignedLongintExpression,
    SubspaceMap,
    TypeDefinitions,
    UnsignedPositiveIntExpression,
    UnsignedPositiveLongintExpression,
    VendorExtensions,
)


def _map_component(memory_map: MemoryMapType, external_name: str | None = None) -> Component:
    type_definitions = None
    if external_name is not None:
        type_definitions = ComponentType.TypeDefinitions(
            external_type_definitions=[
                ExternalTypeDefinitions(
                    name=external_name,
                    type_definitions_ref=ConfigurableLibraryRefType(
                        vendor="test", library="types", name="definitions", version="1.0"
                    ),
                )
            ]
        )
    return Component(
        vendor="test",
        library="scalar-edits",
        name="component",
        version="1.0",
        type_definitions=type_definitions,
        memory_maps=MemoryMaps(memory_map=[memory_map]),
    )


def _schema() -> etree.XMLSchema:
    return etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))


def _assert_component_round_trip(component: Component) -> Component:
    xml = XmlDocument.serializer().render(component)
    schema = _schema()
    assert schema.validate(etree.fromstring(xml.encode())), str(schema.error_log)
    return XmlDocument.parser().from_string(xml, Component)


def _block(name: str) -> AddressBlock:
    return AddressBlock(
        name=name,
        base_address=BaseAddress(value="0"),
        choice=(UnsignedPositiveLongintExpression(value="256"), UnsignedPositiveIntExpression(value="32")),
    )


def test_exact_signatures_exports_and_invalid_memory_map_handles():
    operations = (
        (api.removeMemoryMapShared, ("memoryMapID",)),
        (api.setMemoryMapMemoryMapDefinitionRef, ("memoryMapID", "value", "typeDefinitions")),
        (api.setMemoryMapShared, ("memoryMapID", "shared")),
    )
    for operation, parameters in operations:
        assert tuple(inspect.signature(operation).parameters) == parameters
        assert operation.__name__ in api.__all__
        for invalid in (
            None,
            [],
            {},
            "missing",
            get_handle(AddressUnitBits(value="8")),
            get_handle(LocalMemoryMapType(name="local")),
        ):
            with pytest.raises(TgiError) as error:
                operation(invalid, "definition", "defs") if operation is api.setMemoryMapMemoryMapDefinitionRef else (
                    operation(invalid, "yes") if operation is api.setMemoryMapShared else operation(invalid)
                )
            assert error.value.fault_code == TgiFaultCode.INVALID_ID


def test_shared_default_removal_and_tuple_mutations_preserve_owned_handles():
    block = _block("main")
    unit = AddressUnitBits(value="16")
    owner = MemoryMapType(name="map", choice=(block, unit))
    owner_id = get_handle(owner)
    block_id, unit_id = get_handle(block), get_handle(unit)
    assert api.getMemoryMapAddressUnitBitsID(owner_id) == unit_id
    assert api.getMemoryMapShared(owner_id) == "undefined"
    assert api.removeMemoryMapShared(owner_id) is False
    assert owner.choice == (block, unit)

    assert api.setMemoryMapShared(owner_id, "yes") is True
    assert owner.choice == [block, unit, SharedType.YES]
    assert api.getMemoryMapShared(owner_id) == "yes"
    assert resolve_handle(block_id) is block and resolve_handle(unit_id) is unit
    assert get_parent_info(unit_id).path == ("choice",)

    shared_id = get_handle(SharedType.YES)
    assert api.removeMemoryMapShared(owner_id) is True
    assert owner.choice == [block, unit]
    assert api.getMemoryMapShared(owner_id) == "undefined"
    assert api.removeMemoryMapShared(owner_id) is False
    assert resolve_handle(shared_id) is SharedType.YES

    round_tripped = _assert_component_round_trip(_map_component(owner))
    parsed_choice = round_tripped.memory_maps.memory_map[0].choice
    assert [type(item) for item in parsed_choice] == [AddressBlock, AddressUnitBits]
    assert parsed_choice[0].name == "main" and parsed_choice[1].value == "16"


@pytest.mark.parametrize("value", ["yes", "no", "undefined"])
def test_set_shared_accepts_only_schema_values_and_round_trips(value):
    owner = MemoryMapType(name="map", choice=())
    owner_id = get_handle(owner)
    assert api.setMemoryMapShared(owner_id, value) is True
    assert owner.choice == [SharedType(value)]
    assert api.getMemoryMapShared(owner_id) == value
    parsed = _assert_component_round_trip(_map_component(owner))
    assert parsed.memory_maps.memory_map[0].choice == [SharedType(value)]


@pytest.mark.parametrize("value", [None, 1, True, SharedType.YES, "", "YES", "false"])
def test_set_shared_rejects_non_enum_strings_without_mutation(value):
    owner = MemoryMapType(name="map", choice=())
    original = owner.choice
    with pytest.raises(TgiError) as error:
        api.setMemoryMapShared(get_handle(owner), value)
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert owner.choice is original


def test_shared_reference_branch_rules_and_primitive_handle_lifetime():
    reference = MemoryMapType.MemoryMapDefinitionRef(value="definition", type_definitions="defs")
    owner = MemoryMapType(name="referenced", choice=(reference,))
    original = owner.choice
    assert api.removeMemoryMapShared(get_handle(owner)) is False
    assert owner.choice is original
    with pytest.raises(TgiError) as error:
        api.setMemoryMapShared(get_handle(owner), "yes")
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert owner.choice is original


@pytest.mark.parametrize(
    "choice",
    [
        None,
        {},
        pytest.param((object(),), id="foreign-child"),
        (SharedType.YES, SharedType.NO),
        (MemoryMapType.MemoryMapDefinitionRef(value="def", type_definitions="defs"), _block("inline")),
    ],
)
def test_scalar_mutations_reject_malformed_or_conflicting_choices_atomically(choice):
    owner = MemoryMapType(name="map", choice=choice)
    original = owner.choice
    operations = (
        lambda: api.removeMemoryMapShared(get_handle(owner)),
        lambda: api.setMemoryMapShared(get_handle(owner), "yes"),
        lambda: api.setMemoryMapMemoryMapDefinitionRef(get_handle(owner), "definition", "defs"),
    )
    for operation in operations:
        with pytest.raises(TgiError) as error:
            operation()
        assert error.value.fault_code == TgiFaultCode.INVALID_ID
        assert owner.choice is original


@pytest.mark.parametrize(
    "value,type_definitions",
    [(None, "defs"), ("", "defs"), ("2bad", "defs"), ("definition", None), ("definition", "bad name")],
)
def test_definition_setter_validates_both_names_before_mutating_inline_content(value, type_definitions):
    block = _block("inline")
    owner = MemoryMapType(name="map", choice=(block, AddressUnitBits(value="8"), SharedType.NO))
    original = owner.choice
    block_id = get_handle(block)
    with pytest.raises(TgiError) as error:
        api.setMemoryMapMemoryMapDefinitionRef(get_handle(owner), value, type_definitions)
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert owner.choice is original
    assert resolve_handle(block_id) is block


def test_definition_setter_normalizes_literal_names_without_requiring_a_target():
    owner = MemoryMapType(name="map", choice=())
    owner_id = get_handle(owner)
    assert api.setMemoryMapMemoryMapDefinitionRef(owner_id, "  mapDefinition  ", "  localTypes  ") is True
    reference = owner.choice[0]
    assert isinstance(reference, MemoryMapType.MemoryMapDefinitionRef)
    assert (reference.value, reference.type_definitions) == ("mapDefinition", "localTypes")
    assert api.getMemoryMapMemoryMapDefinitionRefByName(owner_id) == "mapDefinition"
    parsed = _assert_component_round_trip(_map_component(owner, "localTypes"))
    parsed_ref = parsed.memory_maps.memory_map[0].choice[0]
    assert (parsed_ref.value, parsed_ref.type_definitions) == ("mapDefinition", "localTypes")


def test_definition_setter_updates_existing_wrapper_and_preserves_tuple_and_wrapper_handle():
    reference = MemoryMapType.MemoryMapDefinitionRef(value="old", type_definitions="oldTypes")
    owner = MemoryMapType(name="map", choice=(reference,))
    owner_id = get_handle(owner)
    original = owner.choice
    reference_id = api.getMemoryMapMemoryMapDefinitionRefID(owner_id)
    assert api.setMemoryMapMemoryMapDefinitionRef(owner_id, "  newDefinition  ", "  newTypes  ") is True
    assert owner.choice is original and owner.choice == (reference,)
    assert reference_id == get_handle(reference)
    assert (reference.value, reference.type_definitions) == ("newDefinition", "newTypes")
    assert get_parent_info(reference_id).path == ("choice",)


def test_definition_replacement_forgets_inline_descendants_and_preserves_map_metadata():
    remap_child = _block("remapped")
    remap = MemoryRemap(name="remap", mode_ref=[ModeRef(value="mode", priority=0)], choice=[remap_child])
    block = _block("direct")
    unit = AddressUnitBits(value="32")
    subspace = SubspaceMap(name="sub", base_address=SignedLongintExpression(value="0"), initiator_ref="bus")
    shared_handle = get_handle(SharedType.NO)
    extension = VendorExtensions(any_element=[AnyElement(qname="{urn:test}extension", text="metadata")])
    display_name = DisplayName(value="Visible map")
    owner = MemoryMapType(
        name="map",
        display_name=display_name,
        choice=(block, remap, subspace, unit, SharedType.NO),
        vendor_extensions=extension,
        id="map-id",
    )
    # Keep a nested block below a separate direct block so its handle is invalidated through the same graph walk.
    bank_child = _block("banked-child")
    bank = Bank(
        name="bank", base_address=BaseAddress(value="0"), bank_alignment=BankAlignmentType.SERIAL, choice=[bank_child]
    )
    owner.choice = (block, bank, remap, subspace, unit, SharedType.NO)
    removed = [
        block,
        block.base_address,
        bank,
        bank_child,
        bank_child.base_address,
        remap,
        remap.mode_ref[0],
        remap_child,
        remap_child.base_address,
        subspace,
        subspace.base_address,
        unit,
    ]
    removed_handles = [get_handle(item) for item in removed]
    assert api.setMemoryMapMemoryMapDefinitionRef(get_handle(owner), "definition", "defs") is True
    assert len(owner.choice) == 1 and isinstance(owner.choice[0], MemoryMapType.MemoryMapDefinitionRef)
    assert all(resolve_handle(handle) is None for handle in removed_handles)
    assert resolve_handle(shared_handle) is SharedType.NO
    assert owner.name == "map" and owner.id == "map-id"
    assert owner.display_name is display_name and owner.vendor_extensions is extension
    parsed = _assert_component_round_trip(_map_component(owner, "defs"))
    assert parsed.memory_maps.memory_map[0].choice[0].value == "definition"


def test_set_definition_reference_does_not_change_registered_definition_target():
    registry.clear()
    try:
        definition = MemoryMapDefinitions.MemoryMapDefinition(name="original")
        target = TypeDefinitions(
            vendor="test",
            library="types",
            name="definitions",
            version="1.0",
            memory_map_definitions=MemoryMapDefinitions(memory_map_definition=[definition]),
        )
        reference = MemoryMapType.MemoryMapDefinitionRef(value="original", type_definitions="localTypes")
        owner = MemoryMapType(name="map", choice=(reference,))
        component = _map_component(owner, "localTypes")
        registry.register(component, ("test", "scalar-edits", "component", "1.0"))
        registry.register(target, ("test", "types", "definitions", "1.0"))
        assert api.getMemoryMapMemoryMapDefinitionRefByID(get_handle(owner)) == get_handle(definition)
        assert api.setMemoryMapMemoryMapDefinitionRef(get_handle(owner), "changed", "otherTypes") is True
        assert definition.name == "original"
        assert (reference.value, reference.type_definitions) == ("changed", "otherTypes")
    finally:
        registry.clear()

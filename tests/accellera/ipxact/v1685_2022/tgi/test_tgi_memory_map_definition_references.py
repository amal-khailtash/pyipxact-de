"""Address-block and memory-map definition reference layers and document scope."""

from inspect import signature

import pytest
from lxml import etree

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
    AddressBlockDefinitions,
    AddressBlockType,
    BankedBlockType,
    BaseAddress,
    Component,
    ComponentType,
    ConfigurableLibraryRefType,
    ExternalTypeDefinitions,
    LocalMemoryMapType,
    MemoryMapDefinitions,
    MemoryMaps,
    MemoryMapType,
    TypeDefinitions,
    UnsignedPositiveIntExpression,
    UnsignedPositiveLongintExpression,
)

OWNER = ("test", "components", "definitionrefs", "1")
TARGET = ("test", "types", "definitionrefs", "1")
FAMILIES = ["AddressBlock", "MemoryMap"]


@pytest.fixture(autouse=True)
def isolate_registry():
    registry.clear()
    yield
    registry.clear()


def operations(kind):
    prefix = "get" + kind + kind + "DefinitionRef"
    return [getattr(api, prefix + suffix) for suffix in ("ByExternalTypeDefID", "ByID", "ByName", "ID")]


def context(kind, *, register_target=True):
    external = ExternalTypeDefinitions(
        name="imported",
        type_definitions_ref=ConfigurableLibraryRefType(
            vendor=TARGET[0], library=TARGET[1], name=TARGET[2], version=TARGET[3]
        ),
    )
    if kind == "AddressBlock":
        ref = AddressBlockType.AddressBlockDefinitionRef(value="definition", type_definitions="imported")
        source = AddressBlock(name="block", base_address=BaseAddress(value="0"), choice=(ref,))
        map = MemoryMapType(name="map", choice=[source])
        definition = AddressBlockDefinitions.AddressBlockDefinition(
            name="definition",
            range=UnsignedPositiveLongintExpression(value="256"),
            width=UnsignedPositiveIntExpression(value="32"),
        )
        holder = AddressBlockDefinitions(address_block_definition=[definition])
        attr = "address_block_definitions"
    else:
        ref = MemoryMapType.MemoryMapDefinitionRef(value="definition", type_definitions="imported")
        source = map = MemoryMapType(name="map", choice=(ref,))
        definition = MemoryMapDefinitions.MemoryMapDefinition(name="definition")
        holder = MemoryMapDefinitions(memory_map_definition=[definition])
        attr = "memory_map_definitions"
    owner = Component(
        vendor=OWNER[0],
        library=OWNER[1],
        name=OWNER[2],
        version=OWNER[3],
        type_definitions=ComponentType.TypeDefinitions(external_type_definitions=[external]),
        memory_maps=MemoryMaps(memory_map=[map]),
    )
    target = TypeDefinitions(vendor=TARGET[0], library=TARGET[1], name=TARGET[2], version=TARGET[3], **{attr: holder})
    registry.register(owner, OWNER)
    if register_target:
        registry.register(target, TARGET)
    return owner, source, ref, external, target, definition


@pytest.mark.parametrize("kind", FAMILIES)
def test_all_four_layers_return_distinct_objects_and_preserve_source_tuple_ownership(kind):
    owner, source, ref, external, target, definition = context(kind)
    external_op, target_op, name_op, wrapper_op = operations(kind)
    original = source.choice
    ref.value, ref.type_definitions = "  definition  ", "  imported  "
    assert external_op(get_handle(source)) == get_handle(external)
    assert target_op(get_handle(source)) == get_handle(definition)
    assert name_op(get_handle(source)) == "definition"
    assert wrapper_op(get_handle(source)) == get_handle(ref)
    assert ref.value == "  definition  " and ref.type_definitions == "  imported  "
    assert source.choice is original
    info = get_parent_info(get_handle(ref))
    assert resolve_handle(info.parent_handle) is source and info.path == ("choice",) and info.container == "list"
    assert resolve_handle(get_parent_info(get_handle(external)).parent_handle) is owner.type_definitions
    assert resolve_handle(get_parent_info(get_handle(definition)).parent_handle) is (
        target.address_block_definitions if kind == "AddressBlock" else target.memory_map_definitions
    )


@pytest.mark.parametrize("kind", FAMILIES)
def test_source_wrapper_and_local_declaration_work_without_loaded_target_library(kind):
    _, source, ref, external, _, _ = context(kind, register_target=False)
    external_op, target_op, name_op, wrapper_op = operations(kind)
    assert name_op(get_handle(source)) == "definition"
    assert wrapper_op(get_handle(source)) == get_handle(ref)
    assert external_op(get_handle(source)) == get_handle(external)
    with pytest.raises(TgiError) as error:
        target_op(get_handle(source))
    assert error.value.fault_code == TgiFaultCode.NOT_FOUND
    ref.type_definitions = "unavailable"
    assert name_op(get_handle(source)) == "definition"
    assert wrapper_op(get_handle(source)) == get_handle(ref)
    with pytest.raises(TgiError) as error:
        external_op(get_handle(source))
    assert error.value.fault_code == TgiFaultCode.NOT_FOUND


@pytest.mark.parametrize("kind", FAMILIES)
def test_parsed_component_references_validate_and_resolve_with_registered_library(kind):
    owner, _, _, _, target, definition = context(kind)
    xml = XmlDocument.serializer().render(owner)
    schema = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))
    assert schema.validate(etree.fromstring(xml.encode()))
    parsed = XmlDocument.parser().from_string(xml, Component)
    registry.clear()
    registry.register(parsed, OWNER)
    registry.register(target, TARGET)
    source = parsed.memory_maps.memory_map[0]
    if kind == "AddressBlock":
        source = source.choice[0]
    external_op, target_op, name_op, wrapper_op = operations(kind)
    assert name_op(get_handle(source)) == "definition"
    assert target_op(get_handle(source)) == get_handle(definition)
    assert external_op(get_handle(source)) == get_handle(parsed.type_definitions.external_type_definitions[0])
    assert wrapper_op(get_handle(source)) == get_handle(source.choice[0])


@pytest.mark.parametrize("kind", FAMILIES)
def test_optional_absence_does_not_require_external_resolution(kind):
    source = (
        AddressBlock(
            name="inline",
            base_address=BaseAddress(value="0"),
            choice=(UnsignedPositiveLongintExpression(value="256"), UnsignedPositiveIntExpression(value="32")),
        )
        if kind == "AddressBlock"
        else MemoryMapType(name="inline", choice=())
    )
    original = source.choice
    for op in operations(kind):
        assert op(get_handle(source)) is None
        assert source.choice is original
    if kind == "AddressBlock":
        banked = BankedBlockType(
            name="nested",
            range=UnsignedPositiveLongintExpression(value="256"),
            width=UnsignedPositiveIntExpression(value="32"),
        )
        for op in operations(kind):
            assert op(get_handle(banked)) is None


@pytest.mark.parametrize("kind", FAMILIES)
def test_declaration_and_definition_scope_do_not_include_other_registered_documents(kind):
    owner, source, ref, external, target, definition = context(kind)
    decoy_vlnv = ("test", "types", "decoy", "1")
    decoy = TypeDefinitions(vendor=decoy_vlnv[0], library=decoy_vlnv[1], name=decoy_vlnv[2], version=decoy_vlnv[3])
    if kind == "AddressBlock":
        decoy.address_block_definitions = AddressBlockDefinitions(
            address_block_definition=[
                AddressBlockDefinitions.AddressBlockDefinition(
                    name="definition",
                    range=UnsignedPositiveLongintExpression(value="4"),
                    width=UnsignedPositiveIntExpression(value="8"),
                )
            ]
        )
    else:
        decoy.memory_map_definitions = MemoryMapDefinitions(
            memory_map_definition=[MemoryMapDefinitions.MemoryMapDefinition(name="definition")]
        )
    registry.register(decoy, decoy_vlnv)
    target_op = operations(kind)[1]
    assert target_op(get_handle(source)) == get_handle(definition)
    ref.value = "missing"
    with pytest.raises(TgiError) as error:
        target_op(get_handle(source))
    assert error.value.fault_code == TgiFaultCode.NOT_FOUND
    ref.value = "definition"
    owner.type_definitions.external_type_definitions.append(
        ExternalTypeDefinitions(name="imported", type_definitions_ref=external.type_definitions_ref)
    )
    with pytest.raises(TgiError) as error:
        operations(kind)[0](get_handle(source))
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT


@pytest.mark.parametrize("kind", FAMILIES)
def test_duplicate_target_definition_is_ambiguous(kind):
    _, source, _, _, target, definition = context(kind)
    if kind == "AddressBlock":
        target.address_block_definitions.address_block_definition.append(
            AddressBlockDefinitions.AddressBlockDefinition(
                name="definition",
                range=UnsignedPositiveLongintExpression(value="4"),
                width=UnsignedPositiveIntExpression(value="8"),
            )
        )
    else:
        target.memory_map_definitions.memory_map_definition.append(
            MemoryMapDefinitions.MemoryMapDefinition(name="definition")
        )
    with pytest.raises(TgiError) as error:
        operations(kind)[1](get_handle(source))
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT


@pytest.mark.parametrize("kind", FAMILIES)
@pytest.mark.parametrize("field,value", [("value", "bad name"), ("type_definitions", ""), ("value", 5)])
def test_malformed_stored_name_data_faults_for_all_getters(kind, field, value):
    _, source, ref, _, _, _ = context(kind)
    setattr(ref, field, value)
    for op in operations(kind):
        with pytest.raises(TgiError) as error:
            op(get_handle(source))
        assert error.value.fault_code == TgiFaultCode.INVALID_ID
        assert getattr(ref, field) == value


@pytest.mark.parametrize("kind", FAMILIES)
def test_conflicting_foreign_or_invalid_choice_is_rejected_before_target_lookup(kind):
    _, source, ref, _, _, _ = context(kind)
    for values in (None, {}, (object(),), (ref, ref), (ref, UnsignedPositiveIntExpression(value="32"))):
        source.choice = values
        for op in operations(kind):
            with pytest.raises(TgiError) as error:
                op(get_handle(source))
            assert error.value.fault_code == TgiFaultCode.INVALID_ID
            assert source.choice is values


@pytest.mark.parametrize("kind", FAMILIES)
def test_exact_signatures_and_strict_handle_types(kind):
    for op in operations(kind):
        assert list(signature(op).parameters) == (["addressBlockID"] if kind == "AddressBlock" else ["memoryMapID"])
        for invalid in (None, [], {}, "missing", get_handle(LocalMemoryMapType(name="wrong"))):
            with pytest.raises(TgiError) as error:
                op(invalid)
            assert error.value.fault_code == TgiFaultCode.INVALID_ID

"""Exact IEEE 1685-2022 builders for inline memoryRemap content."""

from inspect import signature

import pytest
from lxml import etree
from xsdata.formats.dataclass.models.generics import AnyElement

from amal.eda.accellera.ipxact.v1685_2022 import tgi as api
from amal.eda.accellera.ipxact.v1685_2022.tgi import memory_map as memory_map_api
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
    AddressBlock,
    AddressUnitBits,
    Bank,
    BankAlignmentType,
    BankedBlockType,
    BaseAddress,
    BusInterface,
    BusInterfaces,
    BusInterfaceType,
    Component,
    ComponentType,
    ConfigurableLibraryRefType,
    LocalMemoryMapType,
    MemoryMaps,
    MemoryMapType,
    MemoryRemap,
    MemoryRemapType,
    ModeRef,
    SignedLongintExpression,
    SubspaceMap,
    UnsignedPositiveIntExpression,
    UnsignedPositiveLongintExpression,
    VendorExtensions,
)

UINT64_MAX = (1 << 64) - 1
UINT32_MAX = (1 << 32) - 1
SCHEMA = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))
OPERATIONS = {
    "addMemoryRemapAddressBlock": ["memoryRemapID", "name", "baseAddress", "range", "width"],
    "addMemoryRemapBank": ["memoryRemapID", "name", "baseAddress", "bankAlignment"],
    "addMemoryRemapSubspaceMap": ["memoryRemapID", "name", "initiatorRef", "baseAddress"],
}


@pytest.fixture(autouse=True)
def isolate_registry():
    registry.clear()
    yield
    registry.clear()


def assert_fault(operation, fault, *args):
    with pytest.raises(TgiError) as error:
        operation(*args)
    assert error.value.fault_code == fault


def component_with_remap(remap, *, memory_map=None):
    owner = Component(
        vendor="test",
        library="memory",
        name="remap_builders",
        version="1",
        memory_maps=MemoryMaps(memory_map=[memory_map or MemoryMapType(name="map", choice=[remap])]),
        bus_interfaces=BusInterfaces(
            bus_interface=[
                BusInterface(
                    name="target_bus",
                    bus_type=ConfigurableLibraryRefType(vendor="test", library="bus", name="bus", version="1"),
                    choice=BusInterfaceType.Initiator(),
                )
            ]
        ),
        modes=ComponentType.Modes(mode=[ComponentType.Modes.Mode(name="active")]),
    )
    _register_graph(owner)
    return owner


def test_exact_exports_signatures_and_owner_scopes():
    for name, parameters in OPERATIONS.items():
        operation = getattr(api, name)
        assert name in memory_map_api.__all__
        assert name in api.__all__
        assert list(signature(operation).parameters) == parameters

    remap = MemoryRemap(name="window", mode_ref=[ModeRef(value="active", priority=0)])
    memory_map = MemoryMapType(name="map")
    local_map = LocalMemoryMapType(name="local")
    definition_type = MemoryRemapType.RemapDefinitionRef(value="external", type_definitions="types")
    foreign = ModeRef(value="active", priority=0)
    for owner in (remap, memory_map):
        api.addMemoryRemapBank(get_handle(owner), "bank", "0", "serial")
    for operation, args in (
        (api.addMemoryRemapAddressBlock, (get_handle(memory_map), "block", "0", "1", "1")),
        (api.addMemoryRemapAddressBlock, (get_handle(local_map), "block", "0", "1", "1")),
        (api.addMemoryRemapSubspaceMap, (get_handle(memory_map), "sub", "bus", "0")),
        (api.addMemoryRemapBank, (get_handle(local_map), "bank", "0", "serial")),
        (api.addMemoryRemapBank, (get_handle(definition_type), "bank", "0", "serial")),
        (api.addMemoryRemapSubspaceMap, (get_handle(foreign), "sub", "bus", "0")),
        (api.addMemoryRemapBank, ("stale", "bank", "0", "serial")),
    ):
        assert_fault(operation, TgiFaultCode.INVALID_ID, *args)


def test_address_block_and_subspace_builders_validate_values_and_register_graph():
    remap = MemoryRemap(name="window", mode_ref=[ModeRef(value="active", priority=0)])
    remap.choice = ()
    remap_id = get_handle(remap)
    block_id = api.addMemoryRemapAddressBlock(remap_id, "  data  ", str(UINT64_MAX), str(UINT64_MAX), str(UINT32_MAX))
    block = resolve_handle(block_id)
    assert isinstance(block, AddressBlock)
    assert block.name == "data" and block.base_address.value == str(UINT64_MAX)
    assert [type(item) for item in block.choice] == [UnsignedPositiveLongintExpression, UnsignedPositiveIntExpression]
    assert [item.value for item in block.choice] == [str(UINT64_MAX), str(UINT32_MAX)]
    assert get_parent_info(block_id).parent_handle == remap_id
    assert get_parent_info(get_handle(block.base_address)).parent_handle == block_id
    assert get_parent_info(get_handle(block.choice[0])).parent_handle == block_id

    subspace_ids = [
        api.addMemoryRemapSubspaceMap(remap_id, "low", "unknown_but_valid_name", "-9223372036854775808"),
        api.addMemoryRemapSubspaceMap(remap_id, "high", "target_bus", "9223372036854775807"),
        api.addMemoryRemapSubspaceMap(remap_id, "later", "target_bus", "OFFSET_PARAM"),
    ]
    for handle, source in zip(
        subspace_ids,
        ("-9223372036854775808", "9223372036854775807", "OFFSET_PARAM"),
        strict=True,
    ):
        item = resolve_handle(handle)
        assert isinstance(item, SubspaceMap)
        assert item.base_address.value == source and isinstance(item.base_address, SignedLongintExpression)
        assert get_parent_info(handle).parent_handle == remap_id
        assert get_parent_info(get_handle(item.base_address)).parent_handle == handle
    assert api.getMemoryRemapAddressBlockIDs(remap_id) == [block_id]
    assert api.getMemoryRemapSubspaceMapIDs(remap_id) == subspace_ids
    assert api.getMemoryRemapElementIDs(remap_id) == [block_id, *subspace_ids]


@pytest.mark.parametrize(
    ("base", "address_range", "width"),
    [
        ("-1", "1", "1"),
        (str(UINT64_MAX + 1), "1", "1"),
        ("0", "0", "1"),
        ("0", str(UINT64_MAX + 1), "1"),
        ("0", "1", "0"),
        ("0", "1", str(UINT32_MAX + 1)),
        ("0", "1.5", "1"),
        ("0", "1", "bad +"),
    ],
)
def test_address_block_invalid_expressions_leave_tuple_unmodified(base, address_range, width):
    remap = MemoryRemap(name="window", mode_ref=[ModeRef(value="active", priority=0)])
    remap.choice = ()
    original = remap.choice
    assert_fault(
        api.addMemoryRemapAddressBlock,
        TgiFaultCode.INVALID_ARGUMENT,
        get_handle(remap),
        "block",
        base,
        address_range,
        width,
    )
    assert remap.choice is original


@pytest.mark.parametrize("source", ["", "9223372036854775808", "-9223372036854775809", "1.5", "1 +", None])
def test_subspace_invalid_expressions_and_names_do_not_mutate(source):
    remap = MemoryRemap(name="window", mode_ref=[ModeRef(value="active", priority=0)])
    remap.choice = ()
    original = remap.choice
    assert_fault(
        api.addMemoryRemapSubspaceMap,
        TgiFaultCode.INVALID_ARGUMENT,
        get_handle(remap),
        "subspace",
        "target_bus",
        source,
    )
    assert remap.choice is original
    assert_fault(
        api.addMemoryRemapSubspaceMap,
        TgiFaultCode.INVALID_ARGUMENT,
        get_handle(remap),
        "subspace",
        "bad initiator name",
        "0",
    )
    assert remap.choice is original


def test_remap_choice_validation_and_normalized_names_are_atomic():
    reference = MemoryRemapType.RemapDefinitionRef(value="external", type_definitions="types")
    referenced = MemoryRemap(name="referenced", mode_ref=[ModeRef(value="active", priority=0)], choice=(reference,))
    original = referenced.choice
    for operation, args in (
        (api.addMemoryRemapAddressBlock, ("block", "0", "1", "1")),
        (api.addMemoryRemapBank, ("bank", "0", "serial")),
        (api.addMemoryRemapSubspaceMap, ("sub", "target_bus", "0")),
    ):
        assert_fault(operation, TgiFaultCode.INVALID_ARGUMENT, get_handle(referenced), *args)
    assert referenced.choice is original

    map_reference = MemoryMapType.MemoryMapDefinitionRef(value="external", type_definitions="types")
    referenced_map = MemoryMapType(name="map", choice=(map_reference,))
    original_map_choice = referenced_map.choice
    assert_fault(
        api.addMemoryRemapBank,
        TgiFaultCode.INVALID_ARGUMENT,
        get_handle(referenced_map),
        "bank",
        "0",
        "serial",
    )
    assert referenced_map.choice is original_map_choice

    first = AddressBlock(name="same", base_address=BaseAddress(value="0"))
    second = Bank(
        name=" same ",
        base_address=BaseAddress(value="0"),
        bank_alignment=BankAlignmentType.SERIAL,
        choice=[],
    )
    malformed = MemoryRemap(name="malformed", mode_ref=[ModeRef(value="active", priority=0)], choice=(first, second))
    original = malformed.choice
    assert_fault(
        api.addMemoryRemapSubspaceMap,
        TgiFaultCode.INVALID_ID,
        get_handle(malformed),
        "subspace",
        "target_bus",
        "0",
    )
    assert malformed.choice is original

    malformed.choice = (AddressUnitBits(value="8"),)
    original = malformed.choice
    assert_fault(
        api.addMemoryRemapBank,
        TgiFaultCode.INVALID_ID,
        get_handle(malformed),
        "new",
        "0",
        "serial",
    )
    assert malformed.choice is original

    existing = AddressBlock(name="duplicate", base_address=BaseAddress(value="0"))
    remap = MemoryRemap(name="inline", mode_ref=[ModeRef(value="active", priority=0)], choice=[existing])
    original_list = remap.choice
    assert_fault(
        api.addMemoryRemapBank,
        TgiFaultCode.INVALID_ARGUMENT,
        get_handle(remap),
        " duplicate ",
        "0",
        "serial",
    )
    assert remap.choice is original_list


def test_bank_signature_order_staged_addition_and_map_owner_schema_order():
    remap = MemoryRemap(name="window", mode_ref=[ModeRef(value="active", priority=0)])
    remap.choice = ()
    remap_id = get_handle(remap)
    bank_id = api.addMemoryRemapBank(remap_id, "  bank  ", "0", "parallel")
    bank = resolve_handle(bank_id)
    assert isinstance(bank, Bank)
    assert bank.name == "bank" and bank.base_address.value == "0"
    assert bank.bank_alignment is BankAlignmentType.PARALLEL and bank.choice == []
    assert remap.choice == [bank] and get_parent_info(bank_id).parent_handle == remap_id

    nested = api.addBankAddressBlock(bank_id, "rows", "64", "32")
    seed = resolve_handle(nested)
    assert isinstance(seed, BankedBlockType)
    assert bank.choice == [seed] and get_parent_info(nested).parent_handle == bank_id
    maximum_bank_id = api.addMemoryRemapBank(remap_id, "maximum_base", str(UINT64_MAX), "serial")
    maximum_bank = resolve_handle(maximum_bank_id)
    assert isinstance(maximum_bank, Bank) and maximum_bank.base_address.value == str(UINT64_MAX)

    memory_map = MemoryMapType(name="map", choice=[AddressUnitBits(value="8")])
    map_id = get_handle(memory_map)
    map_unit = memory_map.choice[0]
    map_bank_id = api.addMemoryRemapBank(map_id, "map_bank", "0", "serial")
    map_bank = resolve_handle(map_bank_id)
    assert isinstance(map_bank, Bank) and map_bank.choice == []
    assert memory_map.choice == [map_bank, map_unit]
    assert get_parent_info(map_bank_id).parent_handle == map_id

    duplicate_map = MemoryMapType(
        name="duplicate_map",
        choice=(AddressBlock(name="present", base_address=BaseAddress(value="0")),),
    )
    original_map_choice = duplicate_map.choice
    assert_fault(
        api.addMemoryRemapBank,
        TgiFaultCode.INVALID_ARGUMENT,
        get_handle(duplicate_map),
        " present ",
        "0",
        "serial",
    )
    assert duplicate_map.choice is original_map_choice

    invalid_target = MemoryRemap(name="bad", mode_ref=[ModeRef(value="active", priority=0)], choice=[])
    for args in (
        (get_handle(invalid_target), "new", "-1", "serial"),
        (get_handle(remap), "bad", str(UINT64_MAX + 1), "serial"),
        (get_handle(remap), "bad", "0", "SERIAL"),
        (get_handle(remap), "bad name", "0", "serial"),
    ):
        target = resolve_handle(args[0])
        before = target.choice
        assert_fault(api.addMemoryRemapBank, TgiFaultCode.INVALID_ARGUMENT, *args)
        assert target.choice is before


def test_remap_children_round_trip_and_keep_mode_vendor_and_sibling_state():
    extension = VendorExtensions(any_element=[AnyElement(qname="{urn:test}metadata", text="kept")])
    mode = ModeRef(value="active", priority=7)
    old_block = AddressBlock(
        name="prior",
        base_address=BaseAddress(value="0"),
        choice=[UnsignedPositiveLongintExpression(value="16"), UnsignedPositiveIntExpression(value="32")],
    )
    remap = MemoryRemap(name="window", mode_ref=(mode,), choice=(old_block,), vendor_extensions=extension)
    root = component_with_remap(remap)
    remap_id = get_handle(remap)
    mode_ids = api.getMemoryRemapModeRefIDs(remap_id)
    old_block_id = get_handle(old_block)
    old_choice = remap.choice

    api.addMemoryRemapAddressBlock(remap_id, "new_block", "0", "64", "32")
    bank_id = api.addMemoryRemapBank(remap_id, "bank", "256", "serial")
    api.addBankAddressBlock(bank_id, "banked", "8", "16")
    api.addMemoryRemapSubspaceMap(remap_id, "subspace", "target_bus", "-8")

    assert remap.name == "window" and get_handle(remap) == remap_id
    assert remap.mode_ref == (mode,) and api.getMemoryRemapModeRefIDs(remap_id) == mode_ids
    assert remap.vendor_extensions is extension
    assert remap.choice[0] is old_block and get_handle(remap.choice[0]) == old_block_id
    assert old_choice[0] is old_block
    assert get_parent_info(get_handle(remap.choice[1])).parent_handle == remap_id

    xml = XmlDocument.serializer().render(root)
    xml_root = etree.fromstring(xml.encode())
    assert SCHEMA.validate(xml_root), SCHEMA.error_log
    parsed = XmlDocument.parser().from_string(xml, Component)
    parsed_remap = parsed.memory_maps.memory_map[0].choice[0]
    assert isinstance(parsed_remap, MemoryRemap)
    assert [type(item) for item in parsed_remap.choice] == [AddressBlock, AddressBlock, Bank, SubspaceMap]
    assert parsed_remap.choice[2].choice[0].name == "banked"
    assert parsed_remap.mode_ref[0].value == "active" and parsed_remap.mode_ref[0].priority == 7
    assert parsed_remap.name == "window"
    assert SCHEMA.validate(etree.fromstring(XmlDocument.serializer().render(parsed).encode())), SCHEMA.error_log

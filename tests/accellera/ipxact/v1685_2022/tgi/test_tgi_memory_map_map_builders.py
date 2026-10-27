"""Exact IEEE 1685-2022 memory-map child builders."""

from inspect import signature

import pytest
from lxml import etree

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
    AddressSpaces,
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
    LocalAddressBankType,
    LocalMemoryMapType,
    MemoryMaps,
    MemoryMapType,
    MemoryRemap,
    ModeRef,
    SharedType,
    SignedLongintExpression,
    SubspaceMap,
    UnsignedPositiveIntExpression,
    UnsignedPositiveLongintExpression,
)

UINT64_MAX = (1 << 64) - 1
UINT32_MAX = (1 << 32) - 1
LONG_MAX = (1 << 63) - 1
SCHEMA = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))
OPERATIONS = {
    "addLocalMemoryMapBank": [
        "localMemoryMapID",
        "name",
        "bankAlignment",
        "baseAddress",
        "addressBlockName",
        "addressBlockRange",
        "addressBlockWidth",
    ],
    "addMemoryMapAddressBlock": ["memoryMapID", "name", "baseAddress", "range", "width"],
    "addMemoryMapBank": [
        "memoryMapID",
        "name",
        "bankAlignment",
        "baseAddress",
        "addressBlockName",
        "addressBlockRange",
        "addressBlockWidth",
    ],
    "addMemoryMapMemoryRemap": ["memoryMapID", "name", "modeRef", "priority"],
    "addMemoryMapSubspaceMap": ["memoryMapID", "name", "initiatorRef", "baseAddress"],
}


@pytest.fixture(autouse=True)
def isolate_registry():
    registry.clear()
    yield
    registry.clear()


def map_model(choice=()):
    return MemoryMapType(name="map", choice=choice)


def banked_block(name="seed", address_range="16", width="32"):
    return BankedBlockType(
        name=name,
        range=UnsignedPositiveLongintExpression(value=address_range),
        width=UnsignedPositiveIntExpression(value=width),
    )


def component_with_maps(memory_map, local_map=None):
    address_spaces = None
    if local_map is not None:
        address_spaces = AddressSpaces(
            address_space=[
                AddressSpaces.AddressSpace(
                    name="local_space",
                    range=UnsignedPositiveLongintExpression(value="16"),
                    width=UnsignedPositiveIntExpression(value="32"),
                    local_memory_map=local_map,
                )
            ]
        )
    result = Component(
        vendor="test",
        library="memory",
        name="builder_roundtrip",
        version="1",
        memory_maps=MemoryMaps(memory_map=[memory_map]),
        address_spaces=address_spaces,
        bus_interfaces=BusInterfaces(
            bus_interface=[
                BusInterface(
                    name="bus",
                    bus_type=ConfigurableLibraryRefType(vendor="test", library="bus", name="bus", version="1"),
                    choice=BusInterfaceType.Initiator(),
                )
            ]
        ),
        modes=ComponentType.Modes(mode=[ComponentType.Modes.Mode(name="active")]),
    )
    _register_graph(result)
    return result


def assert_fault(operation, fault, *args):
    with pytest.raises(TgiError) as error:
        operation(*args)
    assert error.value.fault_code == fault


def test_exact_exports_signatures_and_wrong_handle_scopes():
    for name, parameters in OPERATIONS.items():
        operation = getattr(api, name)
        assert name in memory_map_api.__all__
        assert list(signature(operation).parameters) == parameters
        assert name in api.__all__

    for name in ("removeMemoryMapAddressBlock", "removeMemoryMapBank"):
        assert name in memory_map_api.__all__ and name in api.__all__

    mm = map_model()
    local = LocalMemoryMapType(name="local")
    foreign = ModeRef(value="active", priority=0)
    assert_fault(api.addLocalMemoryMapBank, TgiFaultCode.INVALID_ID, get_handle(mm), "b", "serial", "0", "x", "1", "1")
    assert_fault(api.addMemoryMapBank, TgiFaultCode.INVALID_ID, get_handle(local), "b", "serial", "0", "x", "1", "1")
    assert_fault(api.addMemoryMapAddressBlock, TgiFaultCode.INVALID_ID, get_handle(foreign), "b", "0", "1", "1")
    registry.clear()
    assert_fault(api.addMemoryMapAddressBlock, TgiFaultCode.INVALID_ID, "stale", "b", "0", "1", "1")


def test_concrete_address_block_and_nonlocal_bank_builders_seed_owned_children():
    old_bank = Bank(
        name="old_bank",
        bank_alignment=BankAlignmentType.SERIAL,
        base_address=BaseAddress(value="0"),
        choice=[banked_block("nested")],
    )
    old_subspace = SubspaceMap(
        name="old_subspace",
        base_address=SignedLongintExpression(value="0"),
        initiator_ref="initiator",
    )
    old_block = AddressBlock(name="old_block", base_address=BaseAddress(value="0"))
    old_unit = AddressUnitBits(value="8")
    old_shared = SharedType(value="yes")
    memory_map = map_model((old_bank, old_subspace, old_block, old_unit, old_shared))
    memory_map.choice = (old_bank, old_subspace, old_block, old_unit, old_shared)
    map_id = get_handle(memory_map)
    old_ids = tuple(get_handle(item) for item in memory_map.choice)

    block_id = api.addMemoryMapAddressBlock(map_id, "  data_block ", str(UINT64_MAX), str(UINT64_MAX), str(UINT32_MAX))
    block = resolve_handle(block_id)
    assert isinstance(block, AddressBlock)
    assert block.name == "data_block" and block.base_address.value == str(UINT64_MAX)
    assert [type(item) for item in block.choice] == [UnsignedPositiveLongintExpression, UnsignedPositiveIntExpression]
    assert [item.value for item in block.choice] == [str(UINT64_MAX), str(UINT32_MAX)]
    assert memory_map.choice == [old_bank, old_subspace, old_block, block, old_unit, old_shared]
    assert all(
        resolve_handle(handle) is item
        for handle, item in zip(old_ids, (old_bank, old_subspace, old_block, old_unit, old_shared), strict=True)
    )
    assert get_parent_info(block_id).parent_handle == map_id
    assert get_parent_info(get_handle(block.base_address)).parent_handle == block_id
    assert get_parent_info(get_handle(block.choice[0])).parent_handle == block_id

    bank_id = api.addMemoryMapBank(map_id, "bank", "parallel", "BASE", "rows", "COUNT + 1", "WIDTH")
    bank = resolve_handle(bank_id)
    assert isinstance(bank, Bank)
    assert bank.bank_alignment is BankAlignmentType.PARALLEL and bank.base_address.value == "BASE"
    assert len(bank.choice) == 1 and isinstance(bank.choice[0], BankedBlockType)
    assert (bank.choice[0].name, bank.choice[0].range.value, bank.choice[0].width.value) == (
        "rows",
        "COUNT + 1",
        "WIDTH",
    )
    assert memory_map.choice == [old_bank, old_subspace, old_block, block, bank, old_unit, old_shared]
    assert get_parent_info(bank_id).path == ("choice",)
    assert get_parent_info(get_handle(bank.choice[0])).parent_handle == bank_id


def test_local_bank_uses_local_type_and_unified_local_names():
    old_block = AddressBlock(name="before", base_address=BaseAddress(value="0"))
    local_map = LocalMemoryMapType(name="local", address_block_or_bank=(old_block,))
    local_id = get_handle(local_map)

    bank_id = api.addLocalMemoryMapBank(local_id, "local_bank", "serial", "0", "inside", "1", "8")
    bank = resolve_handle(bank_id)
    assert isinstance(bank, LocalAddressBankType)
    assert bank.bank_alignment is BankAlignmentType.SERIAL and bank.base_address.value == "0"
    assert bank.address_block_or_bank[0].name == "inside"
    assert local_map.address_block_or_bank == [old_block, bank]
    assert get_parent_info(bank_id).parent_handle == local_id
    assert get_parent_info(get_handle(bank.address_block_or_bank[0])).parent_handle == bank_id

    original = tuple(local_map.address_block_or_bank)
    local_map.address_block_or_bank = original
    assert_fault(
        api.addLocalMemoryMapBank,
        TgiFaultCode.INVALID_ARGUMENT,
        local_id,
        " before ",
        "serial",
        "0",
        "seed",
        "1",
        "1",
    )
    assert local_map.address_block_or_bank is original


def test_subspace_map_signed_extrema_deferred_values_and_invalid_constants():
    memory_map = map_model()
    map_id = get_handle(memory_map)
    lower = api.addMemoryMapSubspaceMap(map_id, "low", "  initiator  ", "-9223372036854775808")
    upper = api.addMemoryMapSubspaceMap(map_id, "high", "initiator", "9223372036854775807")
    deferred = api.addMemoryMapSubspaceMap(map_id, "later", "initiator", "OFFSET_PARAM")
    for handle, source in ((lower, "-9223372036854775808"), (upper, "9223372036854775807"), (deferred, "OFFSET_PARAM")):
        item = resolve_handle(handle)
        assert isinstance(item, SubspaceMap) and item.base_address.value == source
        assert isinstance(item.base_address, SignedLongintExpression)
        assert get_parent_info(handle).parent_handle == map_id

    before = memory_map.choice
    for source in ("", "9223372036854775808", "-9223372036854775809", "1.5", "1 +", None):
        assert_fault(
            api.addMemoryMapSubspaceMap,
            TgiFaultCode.INVALID_ARGUMENT,
            map_id,
            "bad",
            "initiator",
            source,
        )
        assert memory_map.choice is before


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
    memory_map = map_model()
    memory_map.choice = ()
    original = memory_map.choice
    assert_fault(
        api.addMemoryMapAddressBlock,
        TgiFaultCode.INVALID_ARGUMENT,
        get_handle(memory_map),
        "block",
        base,
        address_range,
        width,
    )
    assert memory_map.choice is original


def test_bank_builder_rejects_invalid_alignment_sizes_and_duplicate_normalized_names_atomically():
    memory_map = map_model()
    memory_map.choice = (AddressBlock(name="existing", base_address=BaseAddress(value="0")),)
    original = memory_map.choice
    args = (get_handle(memory_map), "bank", "serial", "0", "seed", "1", "1")
    for changed in (
        (args[0], "bank", "SERIAL", "0", "seed", "1", "1"),
        (args[0], "bank", "parallel", "-1", "seed", "1", "1"),
        (args[0], "bank", "serial", "0", "seed", "0", "1"),
        (args[0], "bank", "serial", "0", "seed", "1", str(UINT32_MAX + 1)),
        (args[0], " existing ", "serial", "0", "seed", "1", "1"),
    ):
        assert_fault(api.addMemoryMapBank, TgiFaultCode.INVALID_ARGUMENT, *changed)
        assert memory_map.choice is original


@pytest.mark.parametrize("priority", [None, True, -1, LONG_MAX + 1, 1.5, "3"])
def test_memory_remap_requires_xs_long_priority_and_preserves_tuple(priority):
    memory_map = map_model()
    memory_map.choice = ()
    original = memory_map.choice
    assert_fault(
        api.addMemoryMapMemoryRemap,
        TgiFaultCode.INVALID_ARGUMENT,
        get_handle(memory_map),
        "remap",
        "active",
        priority,
    )
    assert memory_map.choice is original


def test_memory_remap_requires_unique_global_mode_name_and_accepts_xml_large_sibling_priority():
    existing = MemoryRemap(name="existing", mode_ref=[ModeRef(value="active", priority=1 << 80)])
    memory_map = map_model((existing,))
    memory_map.choice = (existing,)
    map_id = get_handle(memory_map)

    remap_id = api.addMemoryMapMemoryRemap(map_id, "next", " sleep ", LONG_MAX)
    remap = resolve_handle(remap_id)
    assert isinstance(remap, MemoryRemap)
    assert remap.name == "next" and len(remap.mode_ref) == 1
    assert (remap.mode_ref[0].value, remap.mode_ref[0].priority) == ("sleep", LONG_MAX)
    assert memory_map.choice == [existing, remap]
    assert get_parent_info(remap_id).parent_handle == map_id
    assert get_parent_info(get_handle(remap.mode_ref[0])).parent_handle == remap_id

    original = memory_map.choice
    assert_fault(
        api.addMemoryMapMemoryRemap,
        TgiFaultCode.INVALID_ARGUMENT,
        map_id,
        "other",
        " active ",
        2,
    )
    assert memory_map.choice is original


def test_builder_rejects_referenced_and_malformed_branches_invalid_order_and_existing_key_collisions():
    ref = MemoryMapType.MemoryMapDefinitionRef(value="external", type_definitions="types")
    referenced = map_model((ref,))
    referenced.choice = (ref,)
    original = referenced.choice
    assert_fault(
        api.addMemoryMapAddressBlock,
        TgiFaultCode.INVALID_ARGUMENT,
        get_handle(referenced),
        "new",
        "0",
        "1",
        "1",
    )
    assert referenced.choice is original

    malformed = map_model((ref, AddressBlock(name="stale", base_address=BaseAddress(value="0"))))
    malformed.choice = tuple(malformed.choice)
    malformed_original = malformed.choice
    assert_fault(
        api.addMemoryMapAddressBlock,
        TgiFaultCode.INVALID_ID,
        get_handle(malformed),
        "new",
        "0",
        "1",
        "1",
    )
    assert malformed.choice is malformed_original

    out_of_order = map_model(
        (AddressUnitBits(value="8"), AddressBlock(name="old", base_address=BaseAddress(value="0")))
    )
    out_of_order.choice = tuple(out_of_order.choice)
    old_choice = out_of_order.choice
    assert_fault(
        api.addMemoryMapAddressBlock,
        TgiFaultCode.INVALID_ID,
        get_handle(out_of_order),
        "new",
        "0",
        "1",
        "1",
    )
    assert out_of_order.choice is old_choice

    duplicate = map_model(
        (
            AddressBlock(name="same", base_address=BaseAddress(value="0")),
            SubspaceMap(
                name=" same ",
                base_address=SignedLongintExpression(value="0"),
                initiator_ref="initiator",
            ),
        )
    )
    assert_fault(
        api.addMemoryMapAddressBlock,
        TgiFaultCode.INVALID_ID,
        get_handle(duplicate),
        "new",
        "0",
        "1",
        "1",
    )


def test_all_nonlocal_children_and_local_bank_validate_and_round_trip():
    memory_map = map_model()
    map_id = get_handle(memory_map)
    api.addMemoryMapAddressBlock(map_id, "plain", "0", "256", "32")
    api.addMemoryMapBank(map_id, "bank", "parallel", "0", "banked", "64", "32")
    api.addMemoryMapSubspaceMap(map_id, "subspace", "bus", "-2")
    api.addMemoryMapMemoryRemap(map_id, "remap", "active", 1 << 40)
    memory_map.choice.append(AddressUnitBits(value="8"))
    memory_map.choice.append(SharedType(value="yes"))

    local_map = LocalMemoryMapType(name="local")
    api.addLocalMemoryMapBank(get_handle(local_map), "local_bank", "serial", "0", "local_block", "32", "16")
    owner = component_with_maps(memory_map, local_map)
    xml = XmlDocument.serializer().render(owner)
    root = etree.fromstring(xml.encode())
    assert SCHEMA.validate(root), SCHEMA.error_log
    parsed = XmlDocument.parser().from_string(xml, Component)
    parsed_map = parsed.memory_maps.memory_map[0]
    assert [type(item) for item in parsed_map.choice] == [
        AddressBlock,
        Bank,
        SubspaceMap,
        MemoryRemap,
        AddressUnitBits,
        SharedType,
    ]
    parsed_bank = parsed_map.choice[1]
    assert isinstance(parsed_bank, Bank) and isinstance(parsed_bank.choice[0], BankedBlockType)
    assert parsed_map.choice[3].mode_ref[0].priority == 1 << 40
    parsed_local_bank = parsed.address_spaces.address_space[0].local_memory_map.address_block_or_bank[0]
    assert isinstance(parsed_local_bank, LocalAddressBankType)
    assert isinstance(parsed_local_bank.address_block_or_bank[0], BankedBlockType)

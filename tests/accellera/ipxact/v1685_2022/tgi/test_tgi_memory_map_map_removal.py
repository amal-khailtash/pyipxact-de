"""Direct memoryMap and localMemoryMap child removal contracts."""

from inspect import signature

import pytest
from lxml import etree
from xsdata.formats.dataclass.models.generics import AnyElement

from amal.eda.accellera.ipxact.v1685_2022 import tgi as api
from amal.eda.accellera.ipxact.v1685_2022.tgi import memory_map as memory_map_api
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import (
    TgiError,
    TgiFaultCode,
    get_handle,
    register_parent,
    registry,
    resolve_handle,
)
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import (
    AccessPolicies,
    AccessType,
    AddressBlock,
    AddressSpaces,
    AddressUnitBits,
    Bank,
    BankAlignmentType,
    BankedBlockType,
    BankedSubspaceType,
    BaseAddress,
    BusInterface,
    BusInterfaces,
    BusInterfaceType,
    Component,
    ComponentType,
    ConfigurableLibraryRefType,
    DisplayName,
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
    VendorExtensions,
)

SCHEMA = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))


@pytest.fixture(autouse=True)
def isolate_registry():
    registry.clear()
    yield
    registry.clear()


def block(name: str) -> AddressBlock:
    return AddressBlock(
        name=name,
        base_address=BaseAddress(value="0"),
        choice=(
            UnsignedPositiveLongintExpression(value="32"),
            UnsignedPositiveIntExpression(value="32"),
        ),
    )


def subspace(name: str) -> SubspaceMap:
    return SubspaceMap(name=name, base_address=SignedLongintExpression(value="-4"), initiator_ref="bus")


def component_with_map(memory_map: MemoryMapType) -> Component:
    return Component(
        vendor="test",
        library="memory",
        name="map_removal",
        version="1",
        memory_maps=MemoryMaps(memory_map=[memory_map]),
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


def register_root(root: Component) -> None:
    registry.register(root, ("test", "memory", root.name, "1"))


def assert_invalid_id(operation, handle: str) -> None:
    with pytest.raises(TgiError) as error:
        operation(handle)
    assert error.value.fault_code == TgiFaultCode.INVALID_ID


def assert_schema_valid(root: Component) -> None:
    xml = XmlDocument.serializer().render(root)
    parsed_xml = etree.fromstring(xml.encode())
    assert SCHEMA.validate(parsed_xml), SCHEMA.error_log
    reparsed = XmlDocument.parser().from_string(xml, Component)
    assert XmlDocument.serializer().render(reparsed)


def test_exact_exports_signatures_and_invalid_handles() -> None:
    expected = {
        "removeMemoryMapAddressBlock": ["addressBlockID"],
        "removeMemoryMapBank": ["bankOrLocalBankID"],
        "removeMemoryMapMemoryRemap": ["memoryRemapID"],
        "removeMemoryMapSubspaceMap": ["subSpaceMapID"],
    }
    for name, parameters in expected.items():
        operation = getattr(api, name)
        assert name in memory_map_api.__all__ and name in api.__all__
        assert list(signature(operation).parameters) == parameters
        for invalid in ("unknown-map-child", None, [], {}, 7):
            assert_invalid_id(operation, invalid)


def test_parsed_registered_root_removals_invalidate_subtrees_and_preserve_siblings() -> None:
    removed_block = block("remove-block")
    kept_block = block("keep-block")
    policy = AccessPolicies.AccessPolicy(access=AccessType.READ_WRITE)
    policies = AccessPolicies(access_policy=[policy])
    bank_block = BankedBlockType(
        name="bank-block",
        range=UnsignedPositiveLongintExpression(value="8"),
        width=UnsignedPositiveIntExpression(value="32"),
    )
    bank_extension = VendorExtensions(any_element=[AnyElement(qname="{urn:test}bank", text="metadata")])
    bank = Bank(
        name="remove-bank",
        base_address=BaseAddress(value="0"),
        bank_alignment=BankAlignmentType.SERIAL,
        choice=(bank_block, policies),
        vendor_extensions=bank_extension,
    )
    remap_child = subspace("remap-subspace")
    remap = MemoryRemap(
        name="remove-remap",
        mode_ref=(ModeRef(value="active", priority=0),),
        choice=(remap_child,),
    )
    direct_subspace = subspace("direct-subspace")
    shared = SharedType.NO
    memory_map_extension = VendorExtensions(any_element=[AnyElement(qname="{urn:test}map", text="metadata")])
    memory_map = MemoryMapType(
        name="map",
        display_name=DisplayName(value="keep map metadata"),
        choice=(removed_block, kept_block, bank, direct_subspace, remap, AddressUnitBits(value="8"), shared),
        vendor_extensions=memory_map_extension,
    )
    root = component_with_map(memory_map)
    source = XmlDocument.serializer().render(root)
    assert SCHEMA.validate(etree.fromstring(source.encode())), SCHEMA.error_log
    root = XmlDocument.parser().from_string(source, Component)
    register_root(root)
    memory_map = root.memory_maps.memory_map[0]
    removed_block = memory_map.choice[0]
    kept_block = memory_map.choice[1]
    bank = memory_map.choice[2]
    direct_subspace = memory_map.choice[3]
    remap = memory_map.choice[4]

    block_id, base_id = get_handle(removed_block), get_handle(removed_block.base_address)
    kept_id = get_handle(kept_block)
    bank_id = get_handle(bank)
    bank_block_id = get_handle(bank.choice[0])
    policy_id = get_handle(bank.choice[1].access_policy[0])
    bank_extension_id = get_handle(bank.vendor_extensions)
    remap_id = get_handle(remap)
    mode_ref_id = get_handle(remap.mode_ref[0])
    remap_subspace = remap.choice[0]
    remap_subspace_id = get_handle(remap_subspace)
    remap_base_id = get_handle(remap_subspace.base_address)
    direct_subspace_id = get_handle(direct_subspace)
    direct_base_id = get_handle(direct_subspace.base_address)
    unit_id, map_extension_id = get_handle(memory_map.choice[5]), get_handle(memory_map.vendor_extensions)

    # get_handle and root registration do not prime object-parent links.
    assert api.removeMemoryMapAddressBlock(block_id) is True
    assert resolve_handle(block_id) is None and resolve_handle(base_id) is None
    assert_schema_valid(root)
    assert api.removeMemoryMapBank(bank_id) is True
    assert all(resolve_handle(handle) is None for handle in (bank_id, bank_block_id, policy_id, bank_extension_id))
    assert_schema_valid(root)
    assert api.removeMemoryMapMemoryRemap(remap_id) is True
    assert all(resolve_handle(handle) is None for handle in (remap_id, mode_ref_id, remap_subspace_id, remap_base_id))
    assert_schema_valid(root)
    assert api.removeMemoryMapSubspaceMap(direct_subspace_id) is True
    assert resolve_handle(direct_subspace_id) is None and resolve_handle(direct_base_id) is None
    assert_schema_valid(root)

    assert memory_map.choice[0] is kept_block
    assert memory_map.choice[1] is resolve_handle(unit_id)
    assert memory_map.choice[2] is shared
    assert resolve_handle(kept_id) is kept_block
    assert resolve_handle(unit_id) is memory_map.choice[1]
    assert memory_map.display_name.value == "keep map metadata"
    assert resolve_handle(map_extension_id) is memory_map.vendor_extensions
    assert memory_map.choice[-1] is SharedType.NO
    for operation, removed_id in (
        (api.removeMemoryMapAddressBlock, block_id),
        (api.removeMemoryMapBank, bank_id),
        (api.removeMemoryMapMemoryRemap, remap_id),
        (api.removeMemoryMapSubspaceMap, direct_subspace_id),
    ):
        assert_invalid_id(operation, removed_id)


def test_local_map_removes_concrete_block_and_local_bank_with_direct_links() -> None:
    bank_child = BankedBlockType(
        name="banked-block",
        range=UnsignedPositiveLongintExpression(value="8"),
        width=UnsignedPositiveIntExpression(value="32"),
    )
    local_bank_extension = VendorExtensions(any_element=[AnyElement(qname="{urn:test}bank", text="metadata")])
    local_bank = LocalAddressBankType(
        name="local-bank",
        base_address=BaseAddress(value="0"),
        bank_alignment=BankAlignmentType.SERIAL,
        address_block_or_bank=(bank_child,),
        vendor_extensions=local_bank_extension,
    )
    address_block = block("local-block")
    local_map_extension = VendorExtensions(any_element=[AnyElement(qname="{urn:test}map", text="metadata")])
    local_map = LocalMemoryMapType(
        name="local-map",
        address_block_or_bank=(address_block, local_bank),
        vendor_extensions=local_map_extension,
    )
    address_space = AddressSpaces.AddressSpace(
        name="space",
        range=UnsignedPositiveLongintExpression(value="256"),
        width=UnsignedPositiveIntExpression(value="32"),
        address_unit_bits=AddressUnitBits(value="8"),
        local_memory_map=local_map,
    )
    root = Component(
        vendor="test",
        library="memory",
        name="local_map_removal",
        version="1",
        address_spaces=AddressSpaces(address_space=[address_space]),
    )
    local_block_id, local_bank_id = get_handle(address_block), get_handle(local_bank)
    local_bank_child_id = get_handle(bank_child)
    local_bank_extension_id = get_handle(local_bank_extension)
    register_parent(address_block, local_map, ("address_block_or_bank",), "list")
    register_parent(local_bank, local_map, ("address_block_or_bank",), "list")

    assert api.removeMemoryMapAddressBlock(local_block_id) is True
    assert local_map.address_block_or_bank == [local_bank]
    assert resolve_handle(local_block_id) is None
    assert_schema_valid(root)
    assert api.removeMemoryMapBank(local_bank_id) is True
    assert local_map.address_block_or_bank == []
    assert all(
        resolve_handle(handle) is None for handle in (local_bank_id, local_bank_child_id, local_bank_extension_id)
    )
    assert_schema_valid(root)
    assert resolve_handle(get_handle(local_map)) is local_map
    assert resolve_handle(get_handle(local_map_extension)) is local_map_extension


def test_parsed_registered_local_map_removal_needs_no_getter_or_graph_priming() -> None:
    local_map = LocalMemoryMapType(
        name="local-map",
        address_block_or_bank=(
            block("local-block"),
            LocalAddressBankType(
                name="local-bank",
                base_address=BaseAddress(value="0"),
                bank_alignment=BankAlignmentType.SERIAL,
                address_block_or_bank=(
                    BankedBlockType(
                        name="nested-block",
                        range=UnsignedPositiveLongintExpression(value="8"),
                        width=UnsignedPositiveIntExpression(value="32"),
                    ),
                ),
            ),
        ),
    )
    root = Component(
        vendor="test",
        library="memory",
        name="parsed_local_map_removal",
        version="1",
        address_spaces=AddressSpaces(
            address_space=[
                AddressSpaces.AddressSpace(
                    name="space",
                    range=UnsignedPositiveLongintExpression(value="256"),
                    width=UnsignedPositiveIntExpression(value="32"),
                    address_unit_bits=AddressUnitBits(value="8"),
                    local_memory_map=local_map,
                )
            ]
        ),
    )
    xml = XmlDocument.serializer().render(root)
    assert SCHEMA.validate(etree.fromstring(xml.encode())), SCHEMA.error_log
    root = XmlDocument.parser().from_string(xml, Component)
    register_root(root)
    local_map = root.address_spaces.address_space[0].local_memory_map
    block_id, bank_id = get_handle(local_map.address_block_or_bank[0]), get_handle(local_map.address_block_or_bank[1])

    assert api.removeMemoryMapAddressBlock(block_id) is True
    assert_schema_valid(root)
    assert api.removeMemoryMapBank(bank_id) is True
    assert local_map.address_block_or_bank == []
    assert_schema_valid(root)


def test_constructed_memory_map_children_need_only_direct_parent_registration() -> None:
    for child in (block("created-block"),):
        owner = MemoryMapType(name="created-map", choice=(child,))
        register_parent(child, owner, ("choice",), "list")
        assert api.removeMemoryMapAddressBlock(get_handle(child)) is True
        assert owner.choice == []

    bank = Bank(name="created-bank", base_address=BaseAddress(value="0"), bank_alignment=BankAlignmentType.SERIAL)
    owner = MemoryMapType(name="created-map", choice=(bank,))
    register_parent(bank, owner, ("choice",), "list")
    assert api.removeMemoryMapBank(get_handle(bank)) is True
    assert owner.choice == []

    remap = MemoryRemap(name="created-remap", mode_ref=(ModeRef(value="active", priority=0),))
    owner = MemoryMapType(name="created-map", choice=(remap,))
    register_parent(remap, owner, ("choice",), "list")
    assert api.removeMemoryMapMemoryRemap(get_handle(remap)) is True
    assert owner.choice == []

    subspace_map = subspace("created-subspace")
    owner = MemoryMapType(name="created-map", choice=(subspace_map,))
    register_parent(subspace_map, owner, ("choice",), "list")
    assert api.removeMemoryMapSubspaceMap(get_handle(subspace_map)) is True
    assert owner.choice == []


def test_map_removers_reject_foreign_stale_duplicate_and_malformed_ownership_atomically() -> None:
    block_child = block("child")
    map_owner = MemoryMapType(name="map", choice=[block_child])
    foreign_remap = MemoryRemap(
        name="foreign-remap", mode_ref=(ModeRef(value="active", priority=0),), choice=(block_child,)
    )
    child_id = get_handle(block_child)
    register_parent(block_child, foreign_remap, ("choice",), "list")
    original = map_owner.choice
    assert_invalid_id(api.removeMemoryMapAddressBlock, child_id)
    assert map_owner.choice is original and original == [block_child]

    register_parent(block_child, map_owner, ("address_block",), "list")
    assert_invalid_id(api.removeMemoryMapAddressBlock, child_id)
    assert map_owner.choice is original and original == [block_child]

    register_parent(block_child, map_owner, ("choice",), "list")
    map_owner.choice = (block_child, block_child)
    malformed = map_owner.choice
    assert_invalid_id(api.removeMemoryMapAddressBlock, child_id)
    assert map_owner.choice is malformed

    map_owner.choice = (block_child, object())
    malformed = map_owner.choice
    register_parent(block_child, map_owner, ("choice",), "list")
    assert_invalid_id(api.removeMemoryMapAddressBlock, child_id)
    assert map_owner.choice is malformed

    absent_child = block("absent")
    absent_owner = MemoryMapType(name="absent-owner", choice=[])
    register_parent(absent_child, absent_owner, ("choice",), "list")
    assert_invalid_id(api.removeMemoryMapAddressBlock, get_handle(absent_child))
    assert absent_owner.choice == []

    remap_child = subspace("nested-subspace")
    nested_remap = MemoryRemap(
        name="nested",
        mode_ref=(ModeRef(value="active", priority=0),),
        choice=(remap_child,),
    )
    register_parent(remap_child, nested_remap, ("choice",), "list")
    assert_invalid_id(api.removeMemoryMapSubspaceMap, get_handle(remap_child))
    assert nested_remap.choice == (remap_child,)

    banked_subspace = BankedSubspaceType(name="nested-banked-subspace", initiator_ref="bus")
    containing_bank = Bank(
        name="containing-bank",
        base_address=BaseAddress(value="0"),
        bank_alignment=BankAlignmentType.SERIAL,
        choice=(banked_subspace,),
    )
    register_parent(banked_subspace, containing_bank, ("choice",), "list")
    assert_invalid_id(api.removeMemoryMapSubspaceMap, get_handle(banked_subspace))
    assert containing_bank.choice == (banked_subspace,)

    remap_bank = Bank(name="remap-bank", base_address=BaseAddress(value="0"), bank_alignment=BankAlignmentType.SERIAL)
    nested_remap.choice = [remap_bank]
    register_parent(remap_bank, nested_remap, ("choice",), "list")
    assert_invalid_id(api.removeMemoryMapBank, get_handle(remap_bank))
    assert nested_remap.choice == [remap_bank]

    raw_bad = LocalMemoryMapType(name="bad-local", address_block_or_bank=[block_child, object()])
    local_child = block("local-child")
    raw_bad.address_block_or_bank = [local_child, object()]
    register_parent(local_child, raw_bad, ("address_block_or_bank",), "list")
    malformed_local = raw_bad.address_block_or_bank
    assert_invalid_id(api.removeMemoryMapAddressBlock, get_handle(local_child))
    assert raw_bad.address_block_or_bank is malformed_local

    raw_wrong_bank = LocalMemoryMapType(
        name="wrong-bank",
        address_block_or_bank=[
            Bank(
                name="ordinary-bank",
                base_address=BaseAddress(value="0"),
                bank_alignment=BankAlignmentType.SERIAL,
            )
        ],
    )
    wrong_bank = raw_wrong_bank.address_block_or_bank[0]
    register_parent(wrong_bank, raw_wrong_bank, ("address_block_or_bank",), "list")
    malformed_wrong_bank = raw_wrong_bank.address_block_or_bank
    assert_invalid_id(api.removeMemoryMapBank, get_handle(wrong_bank))
    assert raw_wrong_bank.address_block_or_bank is malformed_wrong_bank

    assert_invalid_id(api.removeMemoryMapBank, get_handle(map_owner))
    assert_invalid_id(api.removeMemoryMapMemoryRemap, get_handle(foreign_remap))

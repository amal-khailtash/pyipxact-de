"""Address-block register and registerFile child operations (IEEE 1685-2022 F.7.58)."""

from inspect import signature

import pytest
from lxml import etree

from amal.eda.accellera.ipxact.v1685_2022 import tgi as api
from amal.eda.accellera.ipxact.v1685_2022.tgi import memory_map
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import (
    TgiError,
    TgiFaultCode,
    get_handle,
    get_parent_info,
    register_parent,
    registry,
    resolve_handle,
)
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import (
    AddressBlock,
    AddressBlockType,
    AddressUnitBits,
    AlternateRegisters,
    Bank,
    BankAlignmentType,
    BankedBlockType,
    BaseAddress,
    Component,
    FieldType,
    MemoryMaps,
    MemoryMapType,
    RegisterFile,
    UnsignedLongintExpression,
    UnsignedPositiveIntExpression,
    UnsignedPositiveLongintExpression,
)

SCHEMA = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))


@pytest.fixture(autouse=True)
def isolate_registry():
    registry.clear()
    yield
    registry.clear()


def block(model=AddressBlock):
    if model is BankedBlockType:
        return model(
            name="banked_block",
            range=UnsignedPositiveLongintExpression(value="16"),
            width=UnsignedPositiveIntExpression(value="32"),
        )
    return model(
        name="address_block",
        base_address=BaseAddress(value="0"),
        choice=[UnsignedPositiveLongintExpression(value="16"), UnsignedPositiveIntExpression(value="32")],
    )


def register_root(root: Component) -> None:
    registry.register(root, ("test", "memory", root.name, "1"))


def root_with_block(address_block, name="address_block_children"):
    return Component(
        vendor="test",
        library="memory",
        name=name,
        version="1",
        memory_maps=MemoryMaps(
            memory_map=[MemoryMapType(name="map", choice=[address_block, AddressUnitBits(value="8")])]
        ),
    )


def assert_fault(operation, fault: str, *args) -> None:
    with pytest.raises(TgiError) as error:
        operation(*args)
    assert error.value.fault_code == fault


def test_public_signatures_match_annex_f_and_invalid_handles_fail():
    expected = {
        "addAddressBlockRegister": [
            "addressBlockID",
            "name",
            "addressOffset",
            "size",
            "fieldName",
            "fieldOffset",
            "fieldWidth",
        ],
        "addAddressBlockRegisterFile": ["addressBlockID", "name", "addressOffset", "range"],
        "removeAddressBlockRegister": ["registerID"],
        "removeAddressBlockRegisterFile": ["registerFileID"],
    }
    for name, parameters in expected.items():
        operation = getattr(api, name)
        assert name in memory_map.__all__
        assert list(signature(operation).parameters) == parameters
    assert_fault(api.removeAddressBlockRegister, TgiFaultCode.INVALID_ID, "not-a-handle")
    assert_fault(api.removeAddressBlockRegisterFile, TgiFaultCode.INVALID_ID, "not-a-handle")


def test_add_address_block_children_seed_inline_data_and_round_trip_schema():
    owner = block()
    owner.choice = tuple(owner.choice)
    original_range, original_width = owner.choice
    owner_id = get_handle(owner)

    register_id = api.addAddressBlockRegister(owner_id, "control", "16", "32", "ready", "0", "1")
    register = resolve_handle(register_id)
    assert isinstance(register, AddressBlockType.Register)
    assert register.name == "control" and register.address_offset.value == "16"
    assert register.choice[0].value == "32"
    assert register.choice[1].name == "ready"
    assert isinstance(register.choice[1], FieldType)
    assert get_parent_info(register_id).path == ("choice",)
    assert owner.choice[:2] == [original_range, original_width]
    assert owner.choice[0] is original_range and owner.choice[1] is original_width

    register_file_id = api.addAddressBlockRegisterFile(owner_id, "cluster", "128", "64")
    register_file = resolve_handle(register_file_id)
    assert isinstance(register_file, RegisterFile)
    assert register_file.name == "cluster" and register_file.address_offset.value == "128"
    assert register_file.choice[0].value == "64"

    root = root_with_block(owner)
    xml = XmlDocument.serializer().render(root)
    assert SCHEMA.validate(etree.fromstring(xml.encode())), SCHEMA.error_log
    parsed = XmlDocument.parser().from_string(xml, Component)
    parsed_block = parsed.memory_maps.memory_map[0].choice[0]
    parsed_names = [
        item.name for item in parsed_block.choice if isinstance(item, (AddressBlockType.Register, RegisterFile))
    ]
    assert parsed_names == [
        "control",
        "cluster",
    ]
    round_trip = XmlDocument.serializer().render(parsed)
    assert SCHEMA.validate(etree.fromstring(round_trip.encode())), SCHEMA.error_log


def test_banked_block_uses_its_distinct_register_data_storage():
    owner = block(BankedBlockType)
    owner.register_or_register_file = tuple()
    owner_id = get_handle(owner)
    register_id = api.addAddressBlockRegister(owner_id, "status", "4", "16", "valid", "0", "1")
    register_file_id = api.addAddressBlockRegisterFile(owner_id, "nested", "16", "64")
    assert isinstance(resolve_handle(register_id), BankedBlockType.Register)
    assert isinstance(resolve_handle(register_file_id), RegisterFile)
    assert len(owner.register_or_register_file) == 2
    assert [item.name for item in owner.register_or_register_file] == ["status", "nested"]
    assert get_parent_info(register_id).path == ("register_or_register_file",)

    bank = Bank(
        name="bank",
        bank_alignment=BankAlignmentType.SERIAL,
        base_address=BaseAddress(value="0"),
        choice=[owner],
    )
    root = Component(
        vendor="test",
        library="memory",
        name="banked_address_block_children",
        version="1",
        memory_maps=MemoryMaps(memory_map=[MemoryMapType(name="map", choice=[bank, AddressUnitBits(value="8")])]),
    )
    xml = XmlDocument.serializer().render(root)
    assert SCHEMA.validate(etree.fromstring(xml.encode())), SCHEMA.error_log
    parsed = XmlDocument.parser().from_string(xml, Component)
    parsed_block = parsed.memory_maps.memory_map[0].choice[0].choice[0]
    assert isinstance(parsed_block, BankedBlockType)
    assert [item.name for item in parsed_block.register_or_register_file] == ["status", "nested"]


def test_unsigned_expression_width_boundaries_match_schema_types():
    owner = block()
    owner_id = get_handle(owner)
    max_u64 = (1 << 64) - 1
    max_u32 = (1 << 32) - 1

    register_id = api.addAddressBlockRegister(
        owner_id,
        "max_register",
        str(max_u64),
        str(max_u32),
        "max_field",
        "0",
        str(max_u32),
    )
    register_file_id = api.addAddressBlockRegisterFile(owner_id, "max_file", str(max_u64), str(max_u64))
    assert resolve_handle(register_id).address_offset.value == str(max_u64)
    assert resolve_handle(register_file_id).choice[0].value == str(max_u64)

    for args in (
        ("over_offset", str(max_u64 + 1), "8", "field", "0", "1"),
        ("over_size", "0", str(max_u32 + 1), "field", "0", "1"),
        ("over_field_offset", "0", "8", "field", str(max_u32 + 1), "1"),
        ("over_field_width", "0", "8", "field", "0", str(max_u32 + 1)),
    ):
        assert_fault(api.addAddressBlockRegister, TgiFaultCode.INVALID_ARGUMENT, owner_id, *args)
    assert_fault(
        api.addAddressBlockRegisterFile,
        TgiFaultCode.INVALID_ARGUMENT,
        owner_id,
        "over_file_offset",
        str(max_u64 + 1),
        "8",
    )
    assert_fault(
        api.addAddressBlockRegisterFile,
        TgiFaultCode.INVALID_ARGUMENT,
        owner_id,
        "over_file_range",
        "0",
        str(max_u64 + 1),
    )


def test_builders_reject_bad_arguments_duplicate_and_alternate_names_without_mutation():
    owner = block()
    existing = AddressBlockType.Register(
        name="base",
        address_offset=UnsignedLongintExpression(value="0"),
        choice=[UnsignedPositiveIntExpression(value="8")],
        alternate_registers=AlternateRegisters(alternate_register=[AlternateRegisters.AlternateRegister(name="other")]),
    )
    owner.choice = tuple((*owner.choice, existing))
    original = owner.choice
    owner_id = get_handle(owner)
    assert_fault(
        api.addAddressBlockRegister,
        TgiFaultCode.INVALID_ARGUMENT,
        owner_id,
        "other",
        "0",
        "8",
        "f",
        "0",
        "1",
    )
    assert_fault(
        api.addAddressBlockRegisterFile,
        TgiFaultCode.INVALID_ARGUMENT,
        owner_id,
        "base",
        "0",
        "16",
    )
    for args in (
        ("bad name", "0", "8", "f", "0", "1"),
        ("bad-offset", "-1", "8", "f", "0", "1"),
        ("bad-size", "0", "0", "f", "0", "1"),
        ("bad-field", "0", "8", "f", "0", "9"),
    ):
        assert_fault(api.addAddressBlockRegister, TgiFaultCode.INVALID_ARGUMENT, owner_id, *args)
        assert owner.choice is original
    assert_fault(api.addAddressBlockRegisterFile, TgiFaultCode.INVALID_ARGUMENT, owner_id, "bad", "0", "0")
    assert owner.choice is original


def test_reference_address_block_branch_is_never_edited():
    owner = block()
    reference = AddressBlockType.AddressBlockDefinitionRef(value="external", type_definitions="types")
    owner.choice = (reference,)
    original = owner.choice
    owner_id = get_handle(owner)
    assert_fault(
        api.addAddressBlockRegister,
        TgiFaultCode.INVALID_ARGUMENT,
        owner_id,
        "reg",
        "0",
        "8",
        "field",
        "0",
        "1",
    )
    assert_fault(api.addAddressBlockRegisterFile, TgiFaultCode.INVALID_ARGUMENT, owner_id, "file", "0", "8")
    assert owner.choice is original and owner.choice[0] is reference


def test_removal_invalidates_register_and_register_file_subtrees_but_preserves_siblings():
    owner = block()
    owner_id = get_handle(owner)
    first_id = api.addAddressBlockRegister(owner_id, "first", "0", "8", "field", "0", "1")
    second_id = api.addAddressBlockRegister(owner_id, "second", "8", "8", "field", "0", "1")
    file_id = api.addAddressBlockRegisterFile(owner_id, "file", "16", "16")
    first = resolve_handle(first_id)
    field_id = get_handle(first.choice[1])
    size_id = get_handle(first.choice[0])
    offset_id = get_handle(first.address_offset)
    second = resolve_handle(second_id)
    second_field_id = get_handle(second.choice[1])
    file_child_id = get_handle(resolve_handle(file_id).choice[0])

    owner.choice = tuple(owner.choice)
    assert api.removeAddressBlockRegister(first_id) is True
    assert isinstance(owner.choice, list)
    assert [item.name for item in owner.choice if isinstance(item, (AddressBlockType.Register, RegisterFile))] == [
        "second",
        "file",
    ]
    assert all(resolve_handle(handle) is None for handle in (first_id, field_id, size_id, offset_id))
    assert resolve_handle(second_id) is second and resolve_handle(second_field_id) is not None
    assert api.removeAddressBlockRegisterFile(file_id) is True
    assert resolve_handle(file_id) is None and resolve_handle(file_child_id) is None
    assert second in owner.choice
    assert_fault(api.removeAddressBlockRegister, TgiFaultCode.INVALID_ID, first_id)
    assert_fault(api.removeAddressBlockRegisterFile, TgiFaultCode.INVALID_ID, file_id)


def test_removers_recover_registered_roots_and_direct_owner_links_and_reject_forged_membership():
    owner = block()
    register = AddressBlockType.Register(
        name="rooted",
        address_offset=UnsignedLongintExpression(value="0"),
        choice=[UnsignedPositiveIntExpression(value="8")],
    )
    register_file = RegisterFile(
        name="linked",
        address_offset=UnsignedLongintExpression(value="8"),
        choice=[UnsignedPositiveLongintExpression(value="8")],
    )
    owner.choice.extend((register, register_file))
    root = root_with_block(owner)
    register_root(root)
    assert get_parent_info(get_handle(register)) is None
    assert api.removeAddressBlockRegister(get_handle(register)) is True

    detached_block = block()
    linked_register = AddressBlockType.Register(
        name="linked",
        address_offset=UnsignedLongintExpression(value="0"),
        choice=[UnsignedPositiveIntExpression(value="8")],
    )
    detached_block.choice.append(linked_register)
    register_parent(linked_register, detached_block, ("choice",), "list")
    assert api.removeAddressBlockRegister(get_handle(linked_register)) is True

    rooted_block = block()
    forged_register = AddressBlockType.Register(
        name="forged",
        address_offset=UnsignedLongintExpression(value="0"),
        choice=[UnsignedPositiveIntExpression(value="8")],
    )
    rooted_block.choice.append(forged_register)
    root = root_with_block(rooted_block, "forged_children")
    register_root(root)
    false_parent = block()
    false_parent.choice.append(forged_register)
    register_parent(forged_register, false_parent, ("choice",), "list")
    assert_fault(api.removeAddressBlockRegister, TgiFaultCode.INVALID_ID, get_handle(forged_register))
    assert forged_register in false_parent.choice and forged_register in rooted_block.choice


def test_removers_reject_wrong_nested_owner_duplicate_membership_and_foreign_types():
    owner = block()
    register_id = api.addAddressBlockRegister(get_handle(owner), "direct", "0", "8", "field", "0", "1")
    register = resolve_handle(register_id)
    nested = RegisterFile(
        name="nested",
        address_offset=UnsignedLongintExpression(value="0"),
        choice=[UnsignedPositiveLongintExpression(value="8"), register],
    )
    owner.choice.append(nested)
    register_parent(register, nested, ("choice",), "list")
    assert_fault(api.removeAddressBlockRegister, TgiFaultCode.INVALID_ID, register_id)
    assert register in owner.choice and register in nested.choice

    owner2 = block()
    duplicate = AddressBlockType.Register(
        name="duplicate",
        address_offset=UnsignedLongintExpression(value="0"),
        choice=[UnsignedPositiveIntExpression(value="8")],
    )
    owner2.choice.extend((duplicate, duplicate))
    register_parent(duplicate, owner2, ("choice",), "list")
    assert_fault(api.removeAddressBlockRegister, TgiFaultCode.INVALID_ID, get_handle(duplicate))
    assert owner2.choice.count(duplicate) == 2

    foreign_file = RegisterFile(name="foreign", address_offset=UnsignedLongintExpression(value="0"), choice=[])
    assert_fault(api.removeAddressBlockRegisterFile, TgiFaultCode.INVALID_ID, get_handle(foreign_file))

    first_owner, second_owner = block(), block()
    shared_register = AddressBlockType.Register(
        name="shared",
        address_offset=UnsignedLongintExpression(value="0"),
        choice=[UnsignedPositiveIntExpression(value="8")],
    )
    first_owner.choice.append(shared_register)
    second_owner.choice.append(shared_register)
    root = Component(
        vendor="test",
        library="memory",
        name="duplicate_edge",
        version="1",
        memory_maps=MemoryMaps(
            memory_map=[
                MemoryMapType(
                    name="map",
                    choice=[first_owner, second_owner, AddressUnitBits(value="8")],
                )
            ]
        ),
    )
    register_root(root)
    register_parent(shared_register, first_owner, ("choice",), "list")
    assert_fault(api.removeAddressBlockRegister, TgiFaultCode.INVALID_ID, get_handle(shared_register))
    assert shared_register in first_owner.choice and shared_register in second_owner.choice

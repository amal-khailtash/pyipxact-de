"""Memory-map AliasOf extended reference edits."""

import inspect

import pytest
from lxml import etree

from amal.eda.accellera.ipxact.v1685_2022 import tgi as api
from amal.eda.accellera.ipxact.v1685_2022.tgi import memory_map
from amal.eda.accellera.ipxact.v1685_2022.tgi.component import _register_graph
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
    AddressBlock,
    AddressBlockRef,
    AddressBlockType,
    AddressUnitBits,
    BankRef,
    BaseAddress,
    Component,
    FieldRef,
    FieldType,
    Index,
    Indices,
    MemoryMaps,
    MemoryMapType,
    MemoryRemapRef,
    UnsignedIntExpression,
    UnsignedLongintExpression,
    UnsignedPositiveIntExpression,
    UnsignedPositiveLongintExpression,
    UsageType,
)

SCHEMA = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))

OPERATIONS = {
    "addAliasOfBankRef": ["aliasOfID", "bankRef"],
    "removeAliasOfAddressBlockRef": ["aliasOfID"],
    "removeAliasOfAddressSpaceRef": ["aliasOfID"],
    "removeAliasOfBankRef": ["bankrefID"],
    "removeAliasOfMemoryMapRef": ["aliasOfID"],
    "setAliasOfAddressBlockRef": ["aliasOfID", "addressBlockRef"],
    "setAliasOfAddressSpaceRef": ["aliasOfID", "addressSpaceRef"],
    "setAliasOfMemoryMapRef": ["aliasOfID", "memoryMapRef"],
    "setAliasOfMemoryRemapRef": ["aliasOfID", "memoryRemapRef"],
}


@pytest.fixture(autouse=True)
def isolate_registry():
    registry.clear()
    yield
    registry.clear()


def alias(**kwargs):
    return FieldType.AliasOf(field_ref=FieldRef(field_ref="field"), **kwargs)


def test_exports_signatures_and_strict_owner_handles():
    for name, parameters in OPERATIONS.items():
        operation = getattr(api, name)
        assert name in memory_map.__all__
        assert list(inspect.signature(operation).parameters) == parameters
        for invalid in (None, [], {}, "missing", get_handle(FieldRef(field_ref="foreign"))):
            args = [invalid, "target"] if len(parameters) == 2 else [invalid]
            with pytest.raises(TgiError) as error:
                operation(*args)
            assert error.value.fault_code == TgiFaultCode.INVALID_ID


def test_bank_ref_append_and_remove_preserve_order_and_invalidate_owned_handle():
    first = BankRef(bank_ref="existing", id="bank-id")
    owner = alias(bank_ref=(first,))
    first_id = get_handle(first)
    owner_id = get_handle(owner)

    second_id = api.addAliasOfBankRef(owner_id, " \tδBank\n")
    second = resolve_handle(second_id)
    assert isinstance(second, BankRef)
    assert second.bank_ref == "δBank"
    assert owner.bank_ref == [first, second]
    assert first.id == "bank-id"
    assert api.getAliasOfBankRefIDs(owner_id) == [first_id, second_id]
    assert api.removeAliasOfBankRef(second_id) is True
    assert owner.bank_ref == [first]
    assert resolve_handle(second_id) is None
    assert api.getAliasOfBankRefIDs(owner_id) == [first_id]
    with pytest.raises(TgiError) as error:
        api.removeAliasOfBankRef(second_id)
    assert error.value.fault_code == TgiFaultCode.INVALID_ID


def test_bank_ref_removal_rejects_detached_and_foreign_family_handles():
    owner = alias()
    bank_id = api.addAliasOfBankRef(get_handle(owner), "bank")
    assert api.removeAliasOfBankRef(bank_id) is True
    for reference in (BankRef(bank_ref="detached"), FieldRef(field_ref="wrong-type")):
        with pytest.raises(TgiError) as error:
            api.removeAliasOfBankRef(get_handle(reference))
        assert error.value.fault_code == TgiFaultCode.INVALID_ID

    foreign = Component(vendor="acme", library="test", name="foreign", version="1")
    foreign_bank = BankRef(bank_ref="foreign")
    foreign_bank_id = get_handle(foreign_bank)
    register_parent(foreign_bank, foreign, ("memory_maps", "memory_map"), "list")
    with pytest.raises(TgiError) as error:
        api.removeAliasOfBankRef(foreign_bank_id)
    assert error.value.fault_code == TgiFaultCode.INVALID_ID


def test_parsed_bank_ref_removal_discovers_tuple_backed_ownership_from_registered_root():
    source = _component_with_alias()
    source_alias = source.memory_maps.memory_map[0].choice[0].choice[3].choice[1].choice[0]
    source_alias.bank_ref = (BankRef(bank_ref="old", id="xml-bank-id"),)
    parsed = XmlDocument.parser().from_string(XmlDocument.serializer().render(source), Component)
    parsed_alias = parsed.memory_maps.memory_map[0].choice[0].choice[3].choice[1].choice[0]
    parsed_alias.bank_ref = tuple(parsed_alias.bank_ref)
    registry.register(parsed, ("acme", "test", "alias_edits", "1"))
    reference = parsed_alias.bank_ref[0]
    reference_id = get_handle(reference)

    assert isinstance(parsed_alias.bank_ref, tuple)
    assert api.removeAliasOfBankRef(reference_id) is True
    assert parsed_alias.bank_ref == []
    assert isinstance(parsed_alias.bank_ref, list)
    assert resolve_handle(reference_id) is None


def test_address_block_setter_preserves_wrapper_indices_and_removal_invalidates_descendants():
    index = Index(value="INDEX")
    indices = Indices(index=[index])
    reference = AddressBlockRef(address_block_ref="old", indices=indices)
    owner = alias(address_block_ref=reference)
    owner_id = get_handle(owner)
    reference_id, indices_id, index_id = get_handle(reference), get_handle(indices), get_handle(index)

    assert api.setAliasOfAddressBlockRef(owner_id, " \tδBlock\n") is True
    assert reference.address_block_ref == "δBlock"
    assert owner.address_block_ref is reference
    assert api.getAliasOfAddressBlockRefID(owner_id) == reference_id
    assert resolve_handle(indices_id) is indices and resolve_handle(index_id) is index

    assert api.removeAliasOfAddressBlockRef(owner_id) is True
    assert owner.address_block_ref is None
    assert all(resolve_handle(handle) is None for handle in (reference_id, indices_id, index_id))
    assert api.removeAliasOfAddressBlockRef(owner_id) is False


def test_choice_setters_preserve_same_branch_wrappers_and_switching_invalidates_dependents():
    address = FieldType.AliasOf.AddressSpaceRef(address_space_ref="space")
    owner = alias(address_space_ref_or_memory_map_ref_or_memory_remap_ref=(address,))
    bank = BankRef(bank_ref="bank")
    block = AddressBlockRef(address_block_ref="block")
    owner.bank_ref = (bank,)
    owner.address_block_ref = block
    bank_id, block_id = get_handle(bank), get_handle(block)
    owner_id = get_handle(owner)
    original_choice = owner.address_space_ref_or_memory_map_ref_or_memory_remap_ref

    assert api.setAliasOfAddressSpaceRef(owner_id, " \tnewSpace\n") is True
    assert owner.address_space_ref_or_memory_map_ref_or_memory_remap_ref[0] is address
    assert address.address_space_ref == "newSpace"
    assert owner.address_space_ref_or_memory_map_ref_or_memory_remap_ref is not original_choice

    address_id = get_handle(address)
    assert api.setAliasOfMemoryMapRef(owner_id, "map") is True
    (memory_map_ref,) = owner.address_space_ref_or_memory_map_ref_or_memory_remap_ref
    map_id = get_handle(memory_map_ref)
    assert resolve_handle(address_id) is None
    assert api.setAliasOfMemoryRemapRef(owner_id, "remap") is True
    remap = owner.address_space_ref_or_memory_map_ref_or_memory_remap_ref[1]
    remap_id = get_handle(remap)
    assert owner.address_space_ref_or_memory_map_ref_or_memory_remap_ref[0] is memory_map_ref
    assert api.setAliasOfMemoryRemapRef(owner_id, "updatedRemap") is True
    assert owner.address_space_ref_or_memory_map_ref_or_memory_remap_ref[1] is remap
    assert remap.memory_remap_ref == "updatedRemap"
    assert api.setAliasOfMemoryMapRef(owner_id, "newMap") is True
    assert owner.address_space_ref_or_memory_map_ref_or_memory_remap_ref[0] is memory_map_ref
    assert owner.address_space_ref_or_memory_map_ref_or_memory_remap_ref[1] is remap
    assert memory_map_ref.memory_map_ref == "newMap"
    assert resolve_handle(map_id) is memory_map_ref and resolve_handle(remap_id) is remap
    assert api.setAliasOfAddressSpaceRef(owner_id, "replacementSpace") is True
    (address_space_ref,) = owner.address_space_ref_or_memory_map_ref_or_memory_remap_ref
    assert address_space_ref.address_space_ref == "replacementSpace"
    assert resolve_handle(map_id) is None and resolve_handle(remap_id) is None
    assert resolve_handle(bank_id) is bank and resolve_handle(block_id) is block
    assert owner.field_ref.field_ref == "field"

    empty_alias_id = get_handle(alias())
    with pytest.raises(TgiError) as error:
        api.setAliasOfMemoryRemapRef(empty_alias_id, "remap")
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT


def test_invalid_names_and_malformed_choices_leave_models_unchanged():
    block = AddressBlockRef(address_block_ref="old")
    owner = alias(
        address_block_ref=block,
        address_space_ref_or_memory_map_ref_or_memory_remap_ref=(
            FieldType.AliasOf.MemoryMapRef(memory_map_ref="old-map"),
        ),
        bank_ref=(),
    )
    owner_id = get_handle(owner)
    original_choice = owner.address_space_ref_or_memory_map_ref_or_memory_remap_ref
    original_banks = owner.bank_ref

    for operation in (
        lambda: api.addAliasOfBankRef(owner_id, "not a Name"),
        lambda: api.setAliasOfAddressBlockRef(owner_id, "not a Name"),
        lambda: api.setAliasOfAddressSpaceRef(owner_id, "not a Name"),
        lambda: api.setAliasOfMemoryMapRef(owner_id, "not a Name"),
        lambda: api.setAliasOfMemoryRemapRef(owner_id, "not a Name"),
    ):
        with pytest.raises(TgiError) as error:
            operation()
        assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert block.address_block_ref == "old"
    assert owner.address_space_ref_or_memory_map_ref_or_memory_remap_ref is original_choice
    assert owner.bank_ref is original_banks

    malformed = (MemoryRemapRef(memory_remap_ref="orphan"),)
    owner.address_space_ref_or_memory_map_ref_or_memory_remap_ref = malformed
    with pytest.raises(TgiError) as error:
        api.setAliasOfMemoryMapRef(owner_id, "map")
    assert error.value.fault_code == TgiFaultCode.INVALID_ID
    assert owner.address_space_ref_or_memory_map_ref_or_memory_remap_ref is malformed


def test_wrong_address_block_wrapper_is_rejected_without_setter_or_removal_mutation():
    wrong_wrapper = FieldRef(field_ref="wrong")
    owner = alias(address_block_ref=wrong_wrapper)
    owner_id = get_handle(owner)

    with pytest.raises(TgiError) as set_error:
        api.setAliasOfAddressBlockRef(owner_id, "replacement")
    assert set_error.value.fault_code == TgiFaultCode.INVALID_ID
    with pytest.raises(TgiError) as remove_error:
        api.removeAliasOfAddressBlockRef(owner_id)
    assert remove_error.value.fault_code == TgiFaultCode.INVALID_ID
    assert owner.address_block_ref is wrong_wrapper
    assert owner.field_ref.field_ref == "field"


def test_choice_removals_are_idempotent_and_map_removal_invalidates_remap_only():
    owner = alias()
    owner_id = get_handle(owner)
    original = (FieldType.AliasOf.AddressSpaceRef(address_space_ref="space"),)
    owner.address_space_ref_or_memory_map_ref_or_memory_remap_ref = original
    assert api.removeAliasOfMemoryMapRef(owner_id) is False
    assert owner.address_space_ref_or_memory_map_ref_or_memory_remap_ref is original
    assert api.removeAliasOfAddressSpaceRef(owner_id) is True
    assert owner.address_space_ref_or_memory_map_ref_or_memory_remap_ref == []
    assert api.removeAliasOfAddressSpaceRef(owner_id) is False

    memory_map_ref = FieldType.AliasOf.MemoryMapRef(memory_map_ref="map")
    remap = MemoryRemapRef(memory_remap_ref="remap")
    bank = BankRef(bank_ref="bank")
    block = AddressBlockRef(address_block_ref="block")
    owner.bank_ref = (bank,)
    owner.address_block_ref = block
    owner.address_space_ref_or_memory_map_ref_or_memory_remap_ref = (memory_map_ref, remap)
    map_id, remap_id = get_handle(memory_map_ref), get_handle(remap)
    bank_id, block_id = get_handle(bank), get_handle(block)
    original_choice = owner.address_space_ref_or_memory_map_ref_or_memory_remap_ref

    assert api.removeAliasOfMemoryMapRef(owner_id) is True
    assert owner.address_space_ref_or_memory_map_ref_or_memory_remap_ref == []
    assert owner.address_space_ref_or_memory_map_ref_or_memory_remap_ref is not original_choice
    assert resolve_handle(map_id) is None and resolve_handle(remap_id) is None
    assert resolve_handle(bank_id) is bank and resolve_handle(block_id) is block
    assert owner.field_ref.field_ref == "field"
    assert api.removeAliasOfMemoryMapRef(owner_id) is False


def _component_with_alias() -> Component:
    field = FieldType(
        name="field",
        bit_offset=UnsignedIntExpression(value="0"),
        choice=[alias()],
    )
    register = AddressBlockType.Register(
        name="control",
        address_offset=UnsignedLongintExpression(value="0"),
        choice=[UnsignedPositiveIntExpression(value="8"), field],
    )
    block = AddressBlock(
        name="registers",
        base_address=BaseAddress(value="0"),
        choice=[
            UnsignedPositiveLongintExpression(value="16"),
            UnsignedPositiveIntExpression(value="8"),
            UsageType.REGISTER,
            register,
        ],
    )
    return Component(
        vendor="acme",
        library="test",
        name="alias_edits",
        version="1",
        memory_maps=MemoryMaps(memory_map=[MemoryMapType(name="map", choice=[block, AddressUnitBits(value="8")])]),
    )


def test_parsed_component_alias_edits_validate_and_round_trip():
    source = _component_with_alias()
    parsed = XmlDocument.parser().from_string(XmlDocument.serializer().render(source), Component)
    _register_graph(parsed)
    field = parsed.memory_maps.memory_map[0].choice[0].choice[3].choice[1]
    alias_id = get_handle(field.choice[0])

    bank_id = api.addAliasOfBankRef(alias_id, "bank")
    assert api.setAliasOfAddressBlockRef(alias_id, "block")
    assert api.setAliasOfMemoryMapRef(alias_id, "map")
    assert api.setAliasOfMemoryRemapRef(alias_id, "window")
    assert resolve_handle(bank_id).bank_ref == "bank"

    xml = XmlDocument.serializer().render(parsed)
    tree = etree.fromstring(xml.encode())
    SCHEMA.assertValid(tree)
    loaded = XmlDocument.parser().from_string(xml, Component)
    assert XmlDocument.serializer().render(loaded) == xml

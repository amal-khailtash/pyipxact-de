"""Bank-scoped child removal contracts from IEEE 1685-2022 F.7.58.32-F.7.58.35."""

from inspect import signature

import pytest
from lxml import etree

from amal.eda.accellera.ipxact.v1685_2022 import tgi as api
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
    AddressBankDefinitionType,
    AddressBankType,
    AddressBlock,
    AddressSpaces,
    AddressUnitBits,
    Bank,
    BankAlignmentType,
    BankDefinitions,
    BankedBankType,
    BankedBlockType,
    BankedDefinitionBankType,
    BankedSubspaceType,
    BaseAddress,
    Component,
    LocalAddressBankType,
    LocalBankedBankType,
    LocalMemoryMapType,
    MemoryMaps,
    MemoryMapType,
    ModeRef,
    UnsignedPositiveIntExpression,
    UnsignedPositiveLongintExpression,
    VendorExtensions,
    Volatile,
)

SCHEMA = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))
ALIGNMENT = BankAlignmentType.SERIAL


@pytest.fixture(autouse=True)
def isolate_registry():
    registry.clear()
    yield
    registry.clear()


def block(name: str = "block") -> BankedBlockType:
    return BankedBlockType(
        name=name,
        range=UnsignedPositiveLongintExpression(value="16"),
        width=UnsignedPositiveIntExpression(value="32"),
    )


def root_with_bank(bank: Bank) -> Component:
    return Component(
        vendor="test",
        library="memory",
        name="bank_removal",
        version="1",
        memory_maps=MemoryMaps(memory_map=[MemoryMapType(name="map", choice=[bank, AddressUnitBits(value="8")])]),
    )


def register_root(root: Component) -> None:
    registry.register(root, ("test", "memory", root.name, "1"))


def assert_invalid_id(operation, handle: str) -> None:
    with pytest.raises(TgiError) as error:
        operation(handle)
    assert error.value.fault_code == TgiFaultCode.INVALID_ID


def test_exports_signatures_and_exact_handle_contracts() -> None:
    expected = {
        "removeBankAccessPolicy": ["accessPolicyID"],
        "removeBankAddressBlock": ["addressBlockID"],
        "removeBankBank": ["bankOrLocalBankID"],
        "removeBankSubspaceMap": ["subspaceMapID"],
    }
    from amal.eda.accellera.ipxact.v1685_2022.tgi import memory_map

    for name, parameters in expected.items():
        operation = getattr(api, name)
        assert name in memory_map.__all__
        assert list(signature(operation).parameters) == parameters
        assert_invalid_id(operation, "not-a-handle")


def test_bank_children_remove_from_registered_parsed_root_and_invalidate_subtrees() -> None:
    block_a, block_b = block("first"), block("last")
    nested_only = AddressBankType.Bank(
        name="nested",
        bank_alignment=ALIGNMENT,
        choice=(),
        vendor_extensions=VendorExtensions(),
    )
    subspace = BankedSubspaceType(name="sub", initiator_ref="bus")
    volatility = Volatile(value=False)
    bank = Bank(
        name="outer",
        bank_alignment=ALIGNMENT,
        base_address=BaseAddress(value="0"),
        choice=(block_a, nested_only, subspace, block_b, volatility),
    )
    root = root_with_bank(bank)
    register_root(root)

    nested_id = get_handle(nested_only)
    extension_id = get_handle(nested_only.vendor_extensions)
    assert api.removeBankBank(nested_id) is True
    assert bank.choice == [block_a, subspace, block_b, volatility]
    assert resolve_handle(nested_id) is None and resolve_handle(extension_id) is None

    block_id = get_handle(block_a)
    range_id = get_handle(block_a.range)
    assert api.removeBankAddressBlock(block_id) is True
    assert bank.choice[0] is subspace and bank.choice[1] is block_b
    assert resolve_handle(block_id) is None and resolve_handle(range_id) is None

    subspace_id = get_handle(subspace)
    assert api.removeBankSubspaceMap(subspace_id) is True
    assert bank.choice[0] is block_b and isinstance(bank.choice[-1], Volatile)
    assert resolve_handle(subspace_id) is None
    assert resolve_handle(get_handle(block_b)) is block_b
    assert_invalid_id(api.removeBankSubspaceMap, subspace_id)


def test_nested_local_bank_removers_accept_real_local_parent_but_not_top_level_local_bank() -> None:
    nested = LocalBankedBankType(
        name="nested-local",
        bank_alignment=ALIGNMENT,
        address_block_or_bank=(block("nested-block"),),
    )
    local = LocalAddressBankType(
        name="local",
        bank_alignment=ALIGNMENT,
        base_address=BaseAddress(value="0"),
        address_block_or_bank=(nested, block("sibling")),
    )
    root = Component(
        vendor="test",
        library="memory",
        name="local_bank_removal",
        version="1",
        address_spaces=AddressSpaces(
            address_space=[
                AddressSpaces.AddressSpace(
                    name="space",
                    range=UnsignedPositiveLongintExpression(value="256"),
                    width=UnsignedPositiveIntExpression(value="32"),
                    address_unit_bits=AddressUnitBits(value="8"),
                    local_memory_map=LocalMemoryMapType(name="local-map", address_block_or_bank=[local]),
                )
            ]
        ),
    )
    register_root(root)

    nested_id = get_handle(nested)
    nested_block_id = get_handle(nested.address_block_or_bank[0])
    assert api.removeBankBank(nested_id) is True
    assert resolve_handle(nested_id) is None and resolve_handle(nested_block_id) is None
    assert local.address_block_or_bank == [block("sibling")]
    assert_invalid_id(api.removeBankBank, get_handle(local))


def test_direct_parent_links_cover_constructed_bank_families_without_registry_roots() -> None:
    for model in (AddressBankType, BankedBankType, AddressBankDefinitionType, BankedDefinitionBankType):
        kwargs = (
            {"base_address": BaseAddress(value="0")} if model in (AddressBankType, AddressBankDefinitionType) else {}
        )
        address_block = block(f"{model.__name__}-block")
        owner = model(name="owner", bank_alignment=ALIGNMENT, choice=(address_block,), **kwargs)
        register_parent(address_block, owner, ("choice",), "list")
        assert api.removeBankAddressBlock(get_handle(address_block)) is True
        assert owner.choice == []

        policy = AccessPolicies.AccessPolicy(access=AccessType.READ_WRITE)
        holder = AccessPolicies(access_policy=(policy,))
        owner = model(name="policy-owner", bank_alignment=ALIGNMENT, choice=(holder,), **kwargs)
        register_parent(holder, owner, ("choice",), "list")
        register_parent(policy, holder, ("access_policy",), "list")
        assert api.removeBankAccessPolicy(get_handle(policy)) is True
        assert owner.choice == []

        nested = (
            model.Bank(name="nested", bank_alignment=ALIGNMENT, choice=())
            if model in (AddressBankType, AddressBankDefinitionType)
            else model.Bank()
        )
        owner = model(name="bank-owner", bank_alignment=ALIGNMENT, choice=(nested,), **kwargs)
        register_parent(nested, owner, ("choice",), "list")
        assert api.removeBankBank(get_handle(nested)) is True
        assert owner.choice == []

    for model in (AddressBankType, BankedBankType):
        kwargs = {"base_address": BaseAddress(value="0")} if model is AddressBankType else {}
        subspace = BankedSubspaceType(name="sub", initiator_ref="bus")
        owner = model(name="subspace-owner", bank_alignment=ALIGNMENT, choice=(subspace,), **kwargs)
        register_parent(subspace, owner, ("choice",), "list")
        assert api.removeBankSubspaceMap(get_handle(subspace)) is True
        assert owner.choice == []

    nested_definition_bank = BankDefinitions.BankDefinition.Bank(
        name="nested-definition-bank",
        bank_alignment=ALIGNMENT,
        choice=(block("definition-block"),),
    )
    definition_block = nested_definition_bank.choice[0]
    register_parent(definition_block, nested_definition_bank, ("choice",), "list")
    assert api.removeBankAddressBlock(get_handle(definition_block)) is True
    assert nested_definition_bank.choice == []

    top_level_definition = BankDefinitions.BankDefinition(
        name="definition",
        address_block_or_bank=(BankDefinitions.BankDefinition.Bank(name="nested", bank_alignment=ALIGNMENT),),
    )
    nested_child = top_level_definition.address_block_or_bank[0]
    register_parent(nested_child, top_level_definition, ("address_block_or_bank",), "list")
    assert_invalid_id(api.removeBankBank, get_handle(nested_child))


def test_policy_removal_keeps_other_policies_then_prunes_final_holder() -> None:
    first_mode = ModeRef(value="read", priority=0)
    second_mode = ModeRef(value="write", priority=1)
    first = AccessPolicies.AccessPolicy(mode_ref=(first_mode,), access=AccessType.READ_ONLY)
    second = AccessPolicies.AccessPolicy(mode_ref=(second_mode,), access=AccessType.WRITE_ONLY)
    policies = AccessPolicies(access_policy=(first, second))
    block_child = block()
    bank = Bank(
        name="outer",
        bank_alignment=ALIGNMENT,
        base_address=BaseAddress(value="0"),
        choice=(block_child, policies),
    )
    root = root_with_bank(bank)
    register_root(root)
    first_id, first_mode_id = get_handle(first), get_handle(first_mode)
    second_id, second_mode_id = get_handle(second), get_handle(second_mode)
    holder_id, block_id = get_handle(policies), get_handle(block_child)

    assert api.removeBankAccessPolicy(first_id) is True
    assert policies.access_policy == [second]
    assert resolve_handle(first_id) is None and resolve_handle(first_mode_id) is None
    assert resolve_handle(second_id) is second and resolve_handle(second_mode_id) is second_mode
    assert resolve_handle(holder_id) is policies and resolve_handle(block_id) is block_child

    assert api.removeBankAccessPolicy(second_id) is True
    assert bank.choice == [block_child]
    assert resolve_handle(second_id) is None and resolve_handle(second_mode_id) is None
    assert resolve_handle(holder_id) is None and resolve_handle(block_id) is block_child
    assert_invalid_id(api.removeBankAccessPolicy, second_id)


def test_removers_reject_foreign_forged_duplicate_and_malformed_membership_atomically() -> None:
    child = block()
    bank = Bank(
        name="outer",
        bank_alignment=ALIGNMENT,
        base_address=BaseAddress(value="0"),
        choice=[child, block("sibling")],
    )
    root = root_with_bank(bank)
    register_root(root)
    child_id = get_handle(child)
    foreign = Bank(
        name="foreign",
        bank_alignment=ALIGNMENT,
        base_address=BaseAddress(value="0"),
        choice=(),
    )
    register_parent(child, foreign, ("choice",), "list")
    before = tuple(bank.choice)
    assert_invalid_id(api.removeBankAddressBlock, child_id)
    assert tuple(bank.choice) == before

    register_parent(child, bank, ("choice",), "list")
    bank.choice = (child, child, bank.choice[-1])
    malformed = bank.choice
    assert_invalid_id(api.removeBankAddressBlock, child_id)
    assert bank.choice is malformed

    bank.choice = (child, block("sibling"))
    assert_invalid_id(api.removeBankAddressBlock, get_handle(block("detached")))
    assert bank.choice[0] is child

    top_level_bank_id = get_handle(bank)
    assert_invalid_id(api.removeBankBank, top_level_bank_id)


def test_address_block_and_policy_from_nonbank_owner_are_rejected() -> None:
    access_policies = AccessPolicies(access_policy=(AccessPolicies.AccessPolicy(access=AccessType.READ_WRITE),))
    block_owner = AddressBlock(
        name="ordinary",
        base_address=BaseAddress(value="0"),
        choice=(
            UnsignedPositiveLongintExpression(value="16"),
            UnsignedPositiveIntExpression(value="32"),
            access_policies,
        ),
    )
    root = Component(
        vendor="test",
        library="memory",
        name="foreign_holder",
        version="1",
        memory_maps=MemoryMaps(memory_map=[MemoryMapType(name="map", choice=[block_owner])]),
    )
    register_root(root)
    policy_id = get_handle(access_policies.access_policy[0])
    assert_invalid_id(api.removeBankAccessPolicy, policy_id)

    ordinary_address_block_id = get_handle(block_owner)
    assert_invalid_id(api.removeBankAddressBlock, ordinary_address_block_id)


def test_schema_valid_removal_round_trips_parsed_bank_children() -> None:
    bank = Bank(
        name="outer",
        bank_alignment=ALIGNMENT,
        base_address=BaseAddress(value="0"),
        choice=(block("remove-me"), block("keep-me")),
    )
    root = root_with_bank(bank)
    source_xml = XmlDocument.serializer().render(root)
    assert SCHEMA.validate(etree.fromstring(source_xml.encode())), SCHEMA.error_log
    parsed = XmlDocument.parser().from_string(source_xml, Component)
    parsed_bank = parsed.memory_maps.memory_map[0].choice[0]
    register_root(parsed)

    assert api.removeBankAddressBlock(get_handle(parsed_bank.choice[0])) is True
    result_xml = XmlDocument.serializer().render(parsed)
    assert SCHEMA.validate(etree.fromstring(result_xml.encode())), SCHEMA.error_log
    loaded = XmlDocument.parser().from_string(result_xml, Component)
    loaded_bank = loaded.memory_maps.memory_map[0].choice[0]
    assert [child.name for child in loaded_bank.choice] == ["keep-me"]

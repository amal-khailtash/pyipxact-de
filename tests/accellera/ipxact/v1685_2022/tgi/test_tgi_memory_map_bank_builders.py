"""Seeded child builders for the IEEE 1685-2022 bank TGI."""

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
    AccessPolicies,
    AccessType,
    AddressBankDefinitionType,
    AddressBankType,
    Bank,
    BankAlignmentType,
    BankedBankType,
    BankedBlockType,
    BankedDefinitionBankType,
    BankedSubspaceType,
    BaseAddress,
    BusInterface,
    BusInterfaces,
    BusInterfaceType,
    Component,
    ConfigurableLibraryRefType,
    LocalBankedBankType,
    MemoryMaps,
    MemoryMapType,
    Parameters,
    UnsignedPositiveIntExpression,
    UnsignedPositiveLongintExpression,
    UsageType,
    Volatile,
)

ALIGNMENT = BankAlignmentType.SERIAL
UINT64_MAX = (1 << 64) - 1
UINT32_MAX = (1 << 32) - 1


@pytest.fixture(autouse=True)
def isolate_registry():
    registry.clear()
    yield
    registry.clear()


def address_block(name="seed"):
    return BankedBlockType(
        name=name,
        range=UnsignedPositiveLongintExpression(value="16"),
        width=UnsignedPositiveIntExpression(value="32"),
    )


def bank(model=AddressBankType, *, choice=()):
    kwargs = (
        {"base_address": BaseAddress(value="0")}
        if issubclass(model, (AddressBankType, AddressBankDefinitionType))
        else {}
    )
    return model(name="bank", bank_alignment=ALIGNMENT, choice=choice, **kwargs)


def assert_fault(operation, fault, *args):
    with pytest.raises(TgiError) as error:
        operation(*args)
    assert error.value.fault_code == fault


def test_exact_builder_and_remover_exports_and_signatures():
    expected = {
        "addBankAccessPolicy": ["bankID", "access"],
        "addBankAddressBlock": ["bankID", "name", "range", "width"],
        "addBankBank": [
            "bankID",
            "name",
            "bankAlignment",
            "addressBlockName",
            "addressBlockRange",
            "addressBlockWidth",
        ],
        "addBankSubspaceMap": ["bankID", "initiatorRef"],
        "removeBankAccessPolicy": ["accessPolicyID"],
        "removeBankAddressBlock": ["addressBlockID"],
        "removeBankBank": ["bankOrLocalBankID"],
        "removeBankSubspaceMap": ["subspaceMapID"],
    }
    for name, parameters in expected.items():
        operation = getattr(api, name)
        assert list(signature(operation).parameters) == parameters
        assert name in api.__all__


@pytest.mark.parametrize("access", [item.value for item in AccessType])
def test_access_policy_builder_reuses_holder_and_registers_policy(access):
    old_policy = AccessPolicies.AccessPolicy(access=AccessType.READ_ONLY)
    holder = AccessPolicies(access_policy=(old_policy,))
    owner = bank(choice=(address_block(), UsageType.MEMORY, Volatile(value=False), holder, Parameters()))
    owner.choice = tuple(owner.choice)
    owner_id, holder_id, old_policy_id = get_handle(owner), get_handle(holder), get_handle(old_policy)

    policy_id = api.addBankAccessPolicy(owner_id, access)
    policy = resolve_handle(policy_id)
    assert isinstance(policy, AccessPolicies.AccessPolicy) and policy.access is AccessType(access)
    assert holder.access_policy == [old_policy, policy]
    assert resolve_handle(holder_id) is holder and resolve_handle(old_policy_id) is old_policy
    assert owner.choice[0].name == "seed" and owner.choice[1] is UsageType.MEMORY
    assert owner.choice[2].value is False and owner.choice[3] is holder and isinstance(owner.choice[4], Parameters)
    assert get_parent_info(policy_id).parent_handle == holder_id
    assert get_parent_info(holder_id).parent_handle == owner_id


def test_access_policy_holder_insertion_order_tuple_path_and_bad_holder_are_atomic():
    owner = bank(choice=(address_block(), Volatile(value=False), Parameters()))
    owner.choice = tuple(owner.choice)
    original_ids = [get_handle(item) for item in owner.choice]
    owner_id = get_handle(owner)
    policy_id = api.addBankAccessPolicy(owner_id, "writeOnce")
    assert [type(item) for item in owner.choice] == [
        BankedBlockType,
        Volatile,
        AccessPolicies,
        Parameters,
    ]
    holder = owner.choice[2]
    assert holder.access_policy[0].access is AccessType.WRITE_ONCE
    assert get_parent_info(get_handle(holder)).path == ("choice",)
    assert get_parent_info(policy_id).path == ("access_policy",)
    assert all(resolve_handle(handle) is not None for handle in original_ids)

    invalid_accesses = (None, 4, "READ_ONLY", "execute")
    for access in invalid_accesses:
        before = owner.choice
        assert_fault(api.addBankAccessPolicy, TgiFaultCode.INVALID_ARGUMENT, owner_id, access)
        assert owner.choice is before

    malformed = bank(choice=(AccessPolicies(access_policy=()), address_block()))
    original = malformed.choice
    assert_fault(api.addBankAccessPolicy, TgiFaultCode.INVALID_ID, get_handle(malformed), "read-only")
    assert malformed.choice is original and malformed.choice[0].access_policy == ()


@pytest.mark.parametrize(
    "model", [AddressBankType, BankedBankType, AddressBankDefinitionType, BankedDefinitionBankType]
)
def test_address_block_builder_handles_all_nonlocal_bank_models_and_tuple_choices(model):
    existing = address_block("existing")
    owner = bank(model, choice=(existing, UsageType.REGISTER, Parameters()))
    owner.choice = tuple(owner.choice)
    owner_id, existing_id = get_handle(owner), get_handle(existing)
    result_id = api.addBankAddressBlock(owner_id, "  fresh  ", str(UINT64_MAX), str(UINT32_MAX))
    child = resolve_handle(result_id)
    assert isinstance(child, BankedBlockType)
    assert (child.name, child.range.value, child.width.value) == ("fresh", str(UINT64_MAX), str(UINT32_MAX))
    assert owner.choice == [existing, child, UsageType.REGISTER, owner.choice[-1]]
    assert resolve_handle(existing_id) is existing
    assert get_parent_info(result_id).parent_handle == owner_id
    assert get_parent_info(get_handle(child.range)).parent_handle == result_id


def test_builder_insertion_preserves_metadata_order_and_existing_sibling_ids():
    block = address_block("prior")
    nested = AddressBankType.Bank(name="nested", bank_alignment=ALIGNMENT, choice=[address_block("inner")])
    subspace = BankedSubspaceType(initiator_ref="master")
    owner = bank(choice=(block, nested, subspace, UsageType.RESERVED, Volatile(value=True), Parameters()))
    owner.choice = tuple(owner.choice)
    sibling_ids = tuple(get_handle(child) for child in owner.choice)
    sibling_objects = tuple(owner.choice)

    added_id = api.addBankAddressBlock(get_handle(owner), "added", "COUNT + 1", "ROW_WIDTH")
    added = resolve_handle(added_id)
    assert owner.choice == [block, nested, subspace, added, *sibling_objects[3:]]
    assert added.range.value == "COUNT + 1" and added.width.value == "ROW_WIDTH"
    assert all(resolve_handle(handle) is child for handle, child in zip(sibling_ids, sibling_objects, strict=True))
    assert isinstance(owner.choice[-1], Parameters)


def test_seeded_nested_bank_for_rich_types_and_generated_deep_type_limit():
    for model, nested_model in (
        (AddressBankType, AddressBankType.Bank),
        (AddressBankDefinitionType, AddressBankDefinitionType.Bank),
    ):
        owner = bank(model, choice=(address_block("root_block"),))
        child_id = api.addBankBank(get_handle(owner), "nested", "parallel", "seed_block", "BLOCKS + 1", "32")
        child = resolve_handle(child_id)
        assert isinstance(child, nested_model)
        assert child.name == "nested" and child.bank_alignment is BankAlignmentType.PARALLEL
        assert len(child.choice) == 1 and isinstance(child.choice[0], BankedBlockType)
        assert child.choice[0].name == "seed_block" and child.choice[0].range.value == "BLOCKS + 1"
        assert get_parent_info(child_id).parent_handle == get_handle(owner)

    for model in (BankedBankType, BankedDefinitionBankType):
        owner = bank(model, choice=(address_block(),))
        original = owner.choice
        assert_fault(
            api.addBankBank,
            TgiFaultCode.INVALID_ID,
            get_handle(owner),
            "nested",
            "serial",
            "seed",
            "1",
            "1",
        )
        assert owner.choice is original

    for unsupported in (BankedBankType.Bank(), BankedDefinitionBankType.Bank()):
        assert_fault(
            api.addBankAddressBlock,
            TgiFaultCode.INVALID_ID,
            get_handle(unsupported),
            "child",
            "1",
            "1",
        )


def test_rich_inherited_nested_bank_handles_support_editable_content():
    for nested_type in (AddressBankType.Bank, AddressBankDefinitionType.Bank):
        owner = nested_type(name="nested", bank_alignment=ALIGNMENT, choice=[address_block("first")])
        owner_id = get_handle(owner)
        block_id = api.addBankAddressBlock(owner_id, "second", "4", "8")
        policy_id = api.addBankAccessPolicy(owner_id, "no-access")
        assert resolve_handle(block_id).name == "second"
        assert resolve_handle(policy_id).access is AccessType.NO_ACCESS
        assert owner.choice[0].name == "first" and owner.choice[1].name == "second"

    definition_nested = AddressBankDefinitionType.Bank(name="definition_nested", bank_alignment=ALIGNMENT)
    assert_fault(
        api.addBankSubspaceMap,
        TgiFaultCode.INVALID_ARGUMENT,
        get_handle(definition_nested),
        "initiator",
    )


@pytest.mark.parametrize("model", [AddressBankType, BankedBankType])
def test_subspace_map_builder_uses_only_initiator_ref_without_invented_name(model):
    owner = bank(model, choice=(address_block(),))
    subspace_id = api.addBankSubspaceMap(get_handle(owner), "  initiator  ")
    subspace = resolve_handle(subspace_id)
    assert isinstance(subspace, BankedSubspaceType)
    assert subspace.initiator_ref == "initiator" and subspace.name is None
    assert get_parent_info(subspace_id).parent_handle == get_handle(owner)


def test_subspace_map_rejected_for_definition_banks_and_references_without_target_resolution():
    for model in (AddressBankDefinitionType, BankedDefinitionBankType):
        owner = bank(model, choice=(address_block(),))
        before = owner.choice
        assert_fault(
            api.addBankSubspaceMap,
            TgiFaultCode.INVALID_ARGUMENT,
            get_handle(owner),
            "initiator",
        )
        assert owner.choice is before

    reference = AddressBankType.BankDefinitionRef(value="missing", type_definitions="missing_types")
    owner = bank(AddressBankType, choice=(reference,))
    original = owner.choice
    assert_fault(
        api.addBankAddressBlock,
        TgiFaultCode.INVALID_ARGUMENT,
        get_handle(owner),
        "new",
        "1",
        "1",
    )
    assert_fault(api.addBankAccessPolicy, TgiFaultCode.INVALID_ARGUMENT, get_handle(owner), "read-only")
    assert owner.choice is original and owner.choice[0] is reference


def test_invalid_parent_scope_malformed_choices_names_and_collisions_are_atomic():
    invalid_handles = (None, 5, "missing", get_handle(BaseAddress(value="0")))
    for operation, args in (
        (api.addBankAccessPolicy, ("read-only",)),
        (api.addBankAddressBlock, ("new", "1", "1")),
        (api.addBankBank, ("new", "serial", "seed", "1", "1")),
        (api.addBankSubspaceMap, ("initiator",)),
    ):
        for invalid in invalid_handles:
            assert_fault(operation, TgiFaultCode.INVALID_ID, invalid, *args)

    local = LocalBankedBankType(name="local", bank_alignment=ALIGNMENT, address_block_or_bank=[address_block()])
    assert_fault(api.addBankAddressBlock, TgiFaultCode.INVALID_ID, get_handle(local), "new", "1", "1")

    owner = bank(choice=(address_block("same"),))
    for call in (
        (api.addBankAddressBlock, (get_handle(owner), " same ", "1", "1")),
        (api.addBankBank, (get_handle(owner), "same", "serial", "seed", "1", "1")),
    ):
        original = owner.choice
        assert_fault(call[0], TgiFaultCode.INVALID_ARGUMENT, *call[1])
        assert owner.choice is original

    malformed = bank(choice=(address_block("bad name"),))
    original = malformed.choice
    assert_fault(api.addBankAddressBlock, TgiFaultCode.INVALID_ID, get_handle(malformed), "new", "1", "1")
    assert malformed.choice is original

    malformed_choice = bank(choice=(address_block(), object()))
    original = malformed_choice.choice
    assert_fault(api.addBankSubspaceMap, TgiFaultCode.INVALID_ID, get_handle(malformed_choice), "initiator")
    assert malformed_choice.choice is original

    malformed_order = bank(choice=(UsageType.MEMORY, address_block()))
    original = malformed_order.choice
    assert_fault(api.addBankAddressBlock, TgiFaultCode.INVALID_ID, get_handle(malformed_order), "new", "1", "1")
    assert malformed_order.choice is original


@pytest.mark.parametrize(
    "operation,args",
    [
        (api.addBankAddressBlock, ("bad name", "1", "1")),
        (api.addBankAddressBlock, ("block", "0", "1")),
        (api.addBankAddressBlock, ("block", str(UINT64_MAX + 1), "1")),
        (api.addBankAddressBlock, ("block", "1", "0")),
        (api.addBankAddressBlock, ("block", "1", str(UINT32_MAX + 1))),
        (api.addBankBank, ("nested", "SERIAL", "seed", "1", "1")),
        (api.addBankBank, ("nested", "serial", "bad name", "1", "1")),
        (api.addBankBank, ("nested", "serial", "seed", "-1", "1")),
        (api.addBankBank, ("nested", "serial", "seed", "1", "0")),
        (api.addBankSubspaceMap, ("bad initiator",)),
    ],
)
def test_invalid_builder_arguments_do_not_mutate_parent(operation, args):
    owner = bank(choice=(address_block(), UsageType.MEMORY, Parameters()))
    original = owner.choice
    assert_fault(operation, TgiFaultCode.INVALID_ARGUMENT, get_handle(owner), *args)
    assert owner.choice is original


def test_schema_valid_builder_round_trip_with_ordered_bank_children():
    owner = bank(Bank, choice=(address_block("first"),))
    root = Component(
        vendor="test",
        library="component",
        name="bank_builders",
        version="1",
        memory_maps=MemoryMaps(memory_map=[MemoryMapType(name="map", choice=[owner])]),
        bus_interfaces=BusInterfaces(
            bus_interface=[
                BusInterface(
                    name="target_interface",
                    bus_type=ConfigurableLibraryRefType(vendor="test", library="bus", name="bus", version="1"),
                    choice=BusInterfaceType.Initiator(),
                )
            ]
        ),
    )
    owner_id = get_handle(owner)
    api.addBankAccessPolicy(owner_id, "read-writeOnce")
    api.addBankAddressBlock(owner_id, "second", "64", "32")
    api.addBankBank(owner_id, "nested", "serial", "seed", "8", "16")
    subspace_id = api.addBankSubspaceMap(owner_id, "target_interface")
    subspace = resolve_handle(subspace_id)
    assert isinstance(subspace, BankedSubspaceType) and subspace.name is None
    # The schema's bankedMMKey requires this optional name even though the TGI signature omits it.
    assert api.setName(subspace_id, "mapped_space") is True

    schema = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))
    xml = XmlDocument.serializer().render(root)
    assert schema.validate(etree.fromstring(xml.encode())), schema.error_log
    parsed = XmlDocument.parser().from_string(xml, Component)
    parsed_bank = parsed.memory_maps.memory_map[0].choice[0]
    assert isinstance(parsed_bank.choice[0], BankedBlockType)
    assert isinstance(parsed_bank.choice[1], BankedBlockType)
    assert isinstance(parsed_bank.choice[2], AddressBankType.Bank)
    assert isinstance(parsed_bank.choice[3], BankedSubspaceType)
    assert isinstance(parsed_bank.choice[4], AccessPolicies)
    assert parsed_bank.choice[2].name == "nested"
    assert parsed_bank.choice[2].choice[0].name == "seed"
    assert parsed_bank.choice[3].initiator_ref == "target_interface"
    assert parsed_bank.choice[4].access_policy[0].access is AccessType.READ_WRITE_ONCE
    round_trip = XmlDocument.serializer().render(parsed)
    assert schema.validate(etree.fromstring(round_trip.encode())), schema.error_log

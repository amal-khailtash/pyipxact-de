"""Instance-local metadata, base-address and definition edits for banks."""

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
    AddressBankDefinitionType,
    AddressBankType,
    AddressSpaces,
    AddressUnitBits,
    Bank,
    BankAlignmentType,
    BankDefinitions,
    BankedBankType,
    BankedBlockType,
    BankedDefinitionBankType,
    BaseAddress,
    Component,
    ComponentType,
    ConfigurableLibraryRefType,
    ExternalTypeDefinitions,
    LocalAddressBankType,
    LocalBankedBankType,
    LocalMemoryMapType,
    MemoryMaps,
    MemoryMapType,
    Parameter,
    Parameters,
    TypeDefinitions,
    UnsignedPositiveIntExpression,
    UnsignedPositiveLongintExpression,
    UsageType,
    Value,
    Volatile,
)

ALIGNMENT = BankAlignmentType.SERIAL
UINT64_MAX = (1 << 64) - 1


@pytest.fixture(autouse=True)
def isolate_registry():
    registry.clear()
    yield
    registry.clear()


def block(name="block"):
    return BankedBlockType(
        name=name,
        range=UnsignedPositiveLongintExpression(value="16"),
        width=UnsignedPositiveIntExpression(value="32"),
    )


def bank(model=Bank, *, choice=(), base="0"):
    kwargs = (
        {"base_address": BaseAddress(value=base)} if model in (Bank, AddressBankType, AddressBankDefinitionType) else {}
    )
    return model(name="bank", bank_alignment=ALIGNMENT, choice=choice, **kwargs)


def component_with_local_bank(inline_bank):
    local_bank = LocalAddressBankType(
        name="local_bank",
        bank_alignment=ALIGNMENT,
        base_address=BaseAddress(value="4"),
        address_block_or_bank=[block("local_block")],
    )
    address_space = AddressSpaces.AddressSpace(
        name="space",
        range=UnsignedPositiveLongintExpression(value="256"),
        width=UnsignedPositiveIntExpression(value="32"),
        address_unit_bits=AddressUnitBits(value="8"),
        local_memory_map=LocalMemoryMapType(name="local_map", address_block_or_bank=[local_bank]),
    )
    return Component(
        vendor="test",
        library="component",
        name="banks",
        version="1",
        address_spaces=AddressSpaces(address_space=[address_space]),
        memory_maps=MemoryMaps(memory_map=[MemoryMapType(name="map", choice=[inline_bank])]),
    ), local_bank


def test_exact_exports_signatures_and_invalid_handle_scopes():
    expected = {
        "removeBankUsage": ["bankID"],
        "removeBankVolatility": ["bankID"],
        "setBankBankDefinitionRef": ["bankID", "value", "typeDefinitions"],
        "setBankBaseAddress": ["bankID", "baseAddress"],
        "setBankUsage": ["bankID", "usage"],
        "setBankVolatility": ["bankOrLocalBankID", "_volatile"],
    }
    for name, parameters in expected.items():
        operation = getattr(api, name)
        assert list(signature(operation).parameters) == parameters
        assert name in api.__all__
    invalid = (None, 7, "missing", get_handle(BaseAddress(value="0")))
    for operation in (api.removeBankUsage, api.removeBankVolatility):
        local = LocalAddressBankType(name="local", bank_alignment=ALIGNMENT, base_address=BaseAddress(value="0"))
        for handle in (*invalid, get_handle(local)):
            with pytest.raises(TgiError) as error:
                operation(handle)
            assert error.value.fault_code == TgiFaultCode.INVALID_ID
    definition = BankDefinitions.BankDefinition(name="definition")
    with pytest.raises(TgiError) as error:
        api.setBankUsage(get_handle(definition), "memory")
    assert error.value.fault_code == TgiFaultCode.INVALID_ID
    for handle in (
        get_handle(BankedBankType.Bank()),
        get_handle(BankedDefinitionBankType.Bank()),
    ):
        with pytest.raises(TgiError) as error:
            api.setBankUsage(handle, "memory")
        assert error.value.fault_code == TgiFaultCode.INVALID_ID


def test_inline_metadata_insert_order_repeat_update_removal_and_wrapper_identity():
    child = block()
    access_policies, parameters = AccessPolicies(), Parameters()
    owner = bank(choice=(child, access_policies, parameters))
    owner.choice = tuple(owner.choice)
    child_id = get_handle(child)
    assert api.removeBankUsage(get_handle(owner)) is False
    assert api.removeBankVolatility(get_handle(owner)) is False
    assert api.setBankUsage(get_handle(owner), "reserved") is True
    assert owner.choice[0] is child and owner.choice[1] is UsageType.RESERVED
    assert owner.choice[2] is access_policies and owner.choice[3] is parameters
    assert resolve_handle(child_id) is child
    assert api.setBankVolatility(get_handle(owner), False) is True
    volatile = owner.choice[2]
    assert isinstance(volatile, Volatile) and volatile.value is False
    assert owner.choice[0] is child and owner.choice[1] is UsageType.RESERVED
    assert owner.choice[3] is access_policies and owner.choice[4] is parameters

    volatile_bank = bank(choice=(child,))
    handle = get_handle(volatile_bank)
    assert api.setBankVolatility(handle, True) is True
    volatile = next(item for item in volatile_bank.choice if isinstance(item, Volatile))
    volatile_id = get_handle(volatile)
    assert volatile_bank.choice.index(child) < volatile_bank.choice.index(volatile)
    original_choice = volatile_bank.choice
    assert api.setBankVolatility(handle, False) is True
    assert volatile_bank.choice is original_choice
    assert volatile.value is False and resolve_handle(volatile_id) is volatile
    assert get_parent_info(volatile_id).parent_handle == handle
    assert api.setBankUsage(handle, "memory") is True
    assert volatile_bank.choice[0] is child
    assert volatile_bank.choice[1] is UsageType.MEMORY
    assert volatile_bank.choice[2] is volatile
    assert api.setBankUsage(handle, "memory") is True
    assert api.removeBankUsage(handle) is True
    assert api.removeBankUsage(handle) is False
    assert api.removeBankVolatility(handle) is True
    assert resolve_handle(volatile_id) is None
    assert api.removeBankVolatility(handle) is False


def test_tuple_backed_volatile_removal_preserves_siblings_and_invalidates_wrapper():
    child = block()
    volatile = Volatile(value=True)
    owner = bank(choice=(child, UsageType.MEMORY, volatile))
    owner.choice = tuple(owner.choice)
    handle, volatile_id = get_handle(owner), get_handle(volatile)
    assert api.removeBankVolatility(handle) is True
    assert owner.choice == [child, UsageType.MEMORY]
    assert resolve_handle(volatile_id) is None
    assert resolve_handle(get_handle(child)) is child


def test_existing_tuple_volatile_update_preserves_source_and_registers_ownership():
    child, wrapper = block(), Volatile(value=False)
    owner = bank(choice=(child, wrapper))
    owner.choice = tuple(owner.choice)
    original, handle, wrapper_id = owner.choice, get_handle(owner), get_handle(wrapper)
    assert api.setBankVolatility(handle, True) is True
    assert owner.choice is original and wrapper.value is True
    assert resolve_handle(wrapper_id) is wrapper
    assert get_parent_info(wrapper_id).parent_handle == handle

    local_wrapper = Volatile(value=False)
    local = LocalBankedBankType(
        name="local",
        bank_alignment=ALIGNMENT,
        address_block_or_bank=[block("local_block")],
        volatile=local_wrapper,
    )
    local_id, local_wrapper_id = get_handle(local), get_handle(local_wrapper)
    assert api.setBankVolatility(local_id, True) is True
    assert local.volatile is local_wrapper and local_wrapper.value is True
    assert resolve_handle(local_wrapper_id) is local_wrapper
    assert get_parent_info(local_wrapper_id).parent_handle == local_id


@pytest.mark.parametrize(
    "model", [AddressBankType, BankedBankType, AddressBankDefinitionType, BankedDefinitionBankType]
)
def test_each_nonlocal_bank_model_supports_metadata_and_literal_definition_reference(model):
    owner = bank(model, choice=(block(),))
    handle = get_handle(owner)
    assert api.setBankUsage(handle, "memory") is True
    assert api.setBankVolatility(handle, False) is True
    assert owner.choice[1] is UsageType.MEMORY
    wrapper = owner.choice[2]
    wrapper_id = get_handle(wrapper)
    assert api.setBankVolatility(handle, True) is True
    assert wrapper.value is True and resolve_handle(wrapper_id) is wrapper
    assert api.setBankBankDefinitionRef(handle, "definition", "external") is True
    reference = owner.choice[0]
    assert isinstance(reference, model.BankDefinitionRef)
    assert (reference.value, reference.type_definitions) == ("definition", "external")
    assert resolve_handle(wrapper_id) is None


@pytest.mark.parametrize("model", [LocalAddressBankType, LocalBankedBankType])
def test_both_local_bank_models_accept_instance_metadata(model):
    kwargs = {"base_address": BaseAddress(value="0")} if model is LocalAddressBankType else {}
    owner = model(name="local", bank_alignment=ALIGNMENT, address_block_or_bank=[block()], **kwargs)
    handle = get_handle(owner)
    assert api.setBankUsage(handle, "reserved") is True
    assert api.setBankVolatility(handle, False) is True
    assert owner.usage is UsageType.RESERVED and owner.volatile.value is False
    wrapper, wrapper_id = owner.volatile, get_handle(owner.volatile)
    assert api.setBankVolatility(handle, True) is True
    assert owner.volatile is wrapper and wrapper.value is True and resolve_handle(wrapper_id) is wrapper


def test_local_metadata_fields_and_nested_supported_bank_children():
    local = LocalAddressBankType(
        name="local",
        bank_alignment=ALIGNMENT,
        base_address=BaseAddress(value="0"),
        address_block_or_bank=[block()],
    )
    handle = get_handle(local)
    assert api.setBankUsage(handle, "register") is True
    assert local.usage is UsageType.REGISTER
    assert api.setBankVolatility(handle, False) is True
    wrapper = local.volatile
    wrapper_id = get_handle(wrapper)
    assert wrapper.value is False and get_parent_info(wrapper_id).parent_handle == handle
    assert api.setBankVolatility(handle, True) is True
    assert local.volatile is wrapper and resolve_handle(wrapper_id) is wrapper
    for operation in (api.removeBankUsage, api.removeBankVolatility):
        with pytest.raises(TgiError) as error:
            operation(handle)
        assert error.value.fault_code == TgiFaultCode.INVALID_ID

    nested = AddressBankType.Bank(
        name="nested",
        bank_alignment=ALIGNMENT,
        choice=[block("nested_block")],
    )
    assert api.setBankUsage(get_handle(nested), "memory") is True
    assert nested.choice[0].name == "nested_block"
    assert nested.choice[1] is UsageType.MEMORY
    definition_nested = BankDefinitions.BankDefinition.Bank(
        name="definition_nested",
        bank_alignment=ALIGNMENT,
        choice=[block("definition_block")],
    )
    assert api.setBankVolatility(get_handle(definition_nested), True) is True
    assert isinstance(definition_nested.choice[-1], Volatile)


def test_referenced_bank_metadata_is_instance_local_and_never_edits_target():
    reference = AddressBankType.BankDefinitionRef(value="definition", type_definitions="imported")
    owner = bank(choice=(reference,))
    definition = BankDefinitions.BankDefinition(
        name="definition",
        address_block_or_bank=(block(),),
        usage=UsageType.RESERVED,
        volatile=Volatile(value=False),
    )
    original = (definition.usage, definition.volatile, definition.address_block_or_bank)
    handle = get_handle(owner)
    assert api.removeBankUsage(handle) is False
    assert api.removeBankVolatility(handle) is False
    for operation, args in (
        (api.setBankUsage, ("memory",)),
        (api.setBankVolatility, (True,)),
    ):
        with pytest.raises(TgiError) as error:
            operation(handle, *args)
        assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert (definition.usage, definition.volatile, definition.address_block_or_bank) == original
    assert owner.choice == (reference,)


def test_base_address_updates_preserve_wrapper_and_validate_evaluated_domain():
    for model in (Bank, AddressBankDefinitionType):
        owner = bank(model, choice=(block(),))
        node = owner.base_address
        node.other_attributes = {"{urn:test}tag": "preserved"}
        node_id = get_handle(node)
        choice = owner.choice
        for source in ("0", str(UINT64_MAX), " BASE + 4 "):
            assert api.setBankBaseAddress(get_handle(owner), source) is True
            assert node.value == source and resolve_handle(node_id) is node
            assert owner.choice is choice
        for source in ("-1", str(UINT64_MAX + 1), "1.5", "1 / 0"):
            with pytest.raises(TgiError) as error:
                api.setBankBaseAddress(get_handle(owner), source)
            assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
            assert node.value == " BASE + 4 "
        node.minimum, node.maximum = 5, 8
        for source in ("4", "9"):
            with pytest.raises(TgiError):
                api.setBankBaseAddress(get_handle(owner), source)
            assert node.value == " BASE + 4 "
    for unsupported in (
        BankedBankType(name="nested", bank_alignment=ALIGNMENT, choice=[block()]),
        BankedBankType.Bank(),
    ):
        with pytest.raises(TgiError) as error:
            api.setBankBaseAddress(get_handle(unsupported), "8")
        assert error.value.fault_code == TgiFaultCode.INVALID_ID


def test_base_setter_rejects_missing_wrong_and_local_bank_addresses():
    for owner in (
        AddressBankType(name="missing", bank_alignment=ALIGNMENT, base_address=None, choice=[block()]),
        AddressBankType(name="wrong", bank_alignment=ALIGNMENT, base_address=object(), choice=[block()]),
        LocalAddressBankType(
            name="local",
            bank_alignment=ALIGNMENT,
            base_address=BaseAddress(value="0"),
            address_block_or_bank=[block()],
        ),
        LocalBankedBankType(name="nested_local", bank_alignment=ALIGNMENT),
    ):
        with pytest.raises(TgiError) as error:
            api.setBankBaseAddress(get_handle(owner), "4")
        assert error.value.fault_code == TgiFaultCode.INVALID_ID


def test_definition_reference_preserves_existing_wrapper_and_replaces_inline_tree():
    parameter_value = Value(value="1")
    parameter = Parameter(name="parameter", value=parameter_value)
    parameters = Parameters(parameter=[parameter])
    volatility = Volatile(value=False)
    owner = bank(choice=(block(), UsageType.RESERVED, volatility, parameters))
    subtree = AddressBankType.Bank(name="subtree", bank_alignment=ALIGNMENT, choice=[block("deep")])
    owner.choice = (owner.choice[0], subtree, UsageType.RESERVED, volatility, parameters)
    old_nodes = (owner.choice[0], subtree, subtree.choice[0], volatility, parameters, parameter, parameter_value)
    old_ids = [get_handle(item) for item in old_nodes]
    base, name = owner.base_address, owner.name
    owner.id = "instance-id"
    choice = owner.choice
    with pytest.raises(TgiError) as error:
        api.setBankBankDefinitionRef(get_handle(owner), "not a name!", "external")
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert owner.choice is choice and all(resolve_handle(handle) is not None for handle in old_ids)

    assert api.setBankBankDefinitionRef(get_handle(owner), "  new_definition  ", " imported ") is True
    reference = owner.choice[0]
    reference_id = get_handle(reference)
    assert reference.value == "new_definition" and reference.type_definitions == "imported"
    assert all(resolve_handle(handle) is None for handle in old_ids)
    assert owner.base_address is base and owner.name == name and owner.id == "instance-id"
    owner.choice = tuple(owner.choice)
    original_choice = owner.choice
    assert api.setBankBankDefinitionRef(get_handle(owner), " updated ", " imported ") is True
    assert owner.choice is original_choice and resolve_handle(reference_id) is reference
    assert (reference.value, reference.type_definitions) == ("updated", "imported")


def test_invalid_arguments_malformed_choices_and_duplicate_scalars_are_atomic():
    owner = bank(choice=(block(),))
    original = owner.choice
    for usage in ("Memory", "read", "", 1):
        with pytest.raises(TgiError) as error:
            api.setBankUsage(get_handle(owner), usage)
        assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
        assert owner.choice is original
    for value in (1, "true", None):
        with pytest.raises(TgiError) as error:
            api.setBankVolatility(get_handle(owner), value)
        assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
        assert owner.choice is original
    for source in (None, 0):
        with pytest.raises(TgiError):
            api.setBankBaseAddress(get_handle(owner), source)
        assert owner.base_address.value == "0"

    duplicate = bank(choice=(UsageType.MEMORY, UsageType.REGISTER))
    before = duplicate.choice
    with pytest.raises(TgiError) as error:
        api.setBankUsage(get_handle(duplicate), "reserved")
    assert error.value.fault_code == TgiFaultCode.INVALID_ID
    assert duplicate.choice is before
    conflict = bank(choice=(AddressBankType.BankDefinitionRef(value="ref", type_definitions="external"), block()))
    before = conflict.choice
    with pytest.raises(TgiError) as error:
        api.setBankBankDefinitionRef(get_handle(conflict), "new", "external")
    assert error.value.fault_code == TgiFaultCode.INVALID_ID
    assert conflict.choice is before

    inline = bank(choice=(block(),))
    before = inline.choice
    for value, external in (("bad name", "external"), ("definition", "bad name"), ("definition", None)):
        with pytest.raises(TgiError) as error:
            api.setBankBankDefinitionRef(get_handle(inline), value, external)
        assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
        assert inline.choice is before


def test_schema_valid_bank_metadata_and_reference_round_trip_with_local_bank():
    owner = bank(choice=(block(),))
    root, local_bank = component_with_local_bank(owner)
    assert api.setBankUsage(get_handle(owner), "memory") is True
    assert api.setBankVolatility(get_handle(owner), False) is True
    assert api.setBankUsage(get_handle(local_bank), "reserved") is True
    assert api.setBankVolatility(get_handle(local_bank), True) is True
    external = ExternalTypeDefinitions(
        name="imported",
        type_definitions_ref=ConfigurableLibraryRefType(vendor="test", library="types", name="banks", version="1"),
    )
    root.type_definitions = ComponentType.TypeDefinitions(external_type_definitions=[external])
    schema = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))
    inline_xml = XmlDocument.serializer().render(root)
    assert schema.validate(etree.fromstring(inline_xml.encode())), schema.error_log
    parsed_inline = XmlDocument.parser().from_string(inline_xml, Component)
    parsed_inline_bank = parsed_inline.memory_maps.memory_map[0].choice[0]
    parsed_inline_local = parsed_inline.address_spaces.address_space[0].local_memory_map.address_block_or_bank[0]
    assert api.getBankUsage(get_handle(parsed_inline_bank)) == "memory"
    assert api.getBankVolatility(get_handle(parsed_inline_bank)) is False
    assert api.getBankUsage(get_handle(parsed_inline_local)) == "reserved"
    assert api.getBankVolatility(get_handle(parsed_inline_local)) is True
    assert schema.validate(etree.fromstring(XmlDocument.serializer().render(parsed_inline).encode())), schema.error_log

    assert api.setBankBankDefinitionRef(get_handle(owner), "definition", "imported") is True
    referenced_xml = XmlDocument.serializer().render(root)
    assert schema.validate(etree.fromstring(referenced_xml.encode())), schema.error_log
    parsed = XmlDocument.parser().from_string(referenced_xml, Component)
    parsed_map_bank = parsed.memory_maps.memory_map[0].choice[0]
    parsed_local = parsed.address_spaces.address_space[0].local_memory_map.address_block_or_bank[0]
    assert parsed_map_bank.choice[0].value == "definition"
    assert len(parsed_map_bank.choice) == 1
    assert api.getBankUsage(get_handle(parsed_local)) == "reserved"
    assert api.getBankVolatility(get_handle(parsed_local)) is True
    assert schema.validate(etree.fromstring(XmlDocument.serializer().render(parsed).encode())), schema.error_log


def test_schema_valid_referenced_target_remains_unchanged_after_instance_edits():
    identity = ("test", "types", "banks", "1")
    external = ExternalTypeDefinitions(
        name="imported",
        type_definitions_ref=ConfigurableLibraryRefType(
            vendor=identity[0], library=identity[1], name=identity[2], version=identity[3]
        ),
    )
    target_bank = BankDefinitions.BankDefinition(
        name="definition",
        address_block_or_bank=(block(),),
        usage=UsageType.RESERVED,
        volatile=Volatile(value=False),
    )
    target = TypeDefinitions(
        vendor=identity[0],
        library=identity[1],
        name=identity[2],
        version=identity[3],
        bank_definitions=BankDefinitions(bank_definition=[target_bank]),
    )
    reference = AddressBankType.BankDefinitionRef(value="definition", type_definitions="imported")
    owner = bank(choice=(reference,))
    root, _local_bank = component_with_local_bank(owner)
    root.type_definitions = ComponentType.TypeDefinitions(external_type_definitions=[external])
    registry.register(root, ("test", "component", "banks", "1"))
    registry.register(target, identity)
    before = (target_bank.usage, target_bank.volatile.value, target_bank.address_block_or_bank)
    assert api.getBankUsage(get_handle(owner)) == "reserved"
    assert api.getBankVolatility(get_handle(owner)) is False
    assert api.setBankBaseAddress(get_handle(owner), "32") is True
    assert api.setBankBankDefinitionRef(get_handle(owner), " definition ", " imported ") is True
    assert api.getBankUsage(get_handle(owner)) == "reserved"
    assert api.getBankVolatility(get_handle(owner)) is False
    assert (target_bank.usage, target_bank.volatile.value, target_bank.address_block_or_bank) == before
    xml = XmlDocument.serializer().render(root)
    schema = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))
    assert schema.validate(etree.fromstring(xml.encode())), schema.error_log

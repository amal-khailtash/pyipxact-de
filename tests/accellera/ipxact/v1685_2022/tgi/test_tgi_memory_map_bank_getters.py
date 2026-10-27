"""Bank structure, local address and definition metadata contracts."""

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
    AddressBankDefinitionType,
    AddressBankType,
    Bank,
    BankAlignmentType,
    BankDefinitions,
    BankedBankType,
    BankedBlockType,
    BankedDefinitionBankType,
    BankedSubspaceType,
    BaseAddress,
    Component,
    ComponentType,
    ConfigurableLibraryRefType,
    ExternalTypeDefinitions,
    LocalAddressBankType,
    LocalBankedBankType,
    MemoryMaps,
    MemoryMapType,
    TypeDefinitions,
    UnsignedPositiveIntExpression,
    UnsignedPositiveLongintExpression,
    UsageType,
    Volatile,
)

ALIGNMENT = BankAlignmentType.SERIAL
OPERATIONS = {
    "getBankAddressBlockIDs": "bankID",
    "getBankBankIDs": "bankID",
    "getBankBaseAddress": "bankOrLocalBankID",
    "getBankBaseAddressExpression": "bankOrLocalBankID",
    "getBankBaseAddressID": "bankID",
    "getBankBlockAndSubspaceElementIDs": "bankOrLocalBankID",
    "getBankSubspaceMapIDs": "bankID",
    "getBankUsage": "bankOrLocalBankID",
    "getBankVolatility": "bankOrLocalBankID",
}


@pytest.fixture(autouse=True)
def isolate_registry():
    registry.clear()
    yield
    registry.clear()


@pytest.mark.parametrize("model", [Bank, AddressBankType, AddressBankDefinitionType, LocalAddressBankType])
@pytest.mark.parametrize("source,value", [("0", 0), ("'h20 + 2", 34), (str((1 << 64) - 1), (1 << 64) - 1)])
def test_base_value_source_wrapper_and_owner(model, source, value):
    node = BaseAddress(value=source)
    bank = model(name="bank", bank_alignment=ALIGNMENT, base_address=node)
    handle = get_handle(bank)
    assert api.getBankBaseAddress(handle) == value
    assert api.getBankBaseAddressExpression(handle) == source
    if model is LocalAddressBankType:
        with pytest.raises(TgiError):
            api.getBankBaseAddressID(handle)
    else:
        assert resolve_handle(api.getBankBaseAddressID(handle)) is node
    info = get_parent_info(get_handle(node))
    assert resolve_handle(info.parent_handle) is bank and info.path == ("base_address",)
    assert node.value == source


@pytest.mark.parametrize("source", ["-1", str(1 << 64), "PARAM", "1 / 0", "1.5"])
def test_invalid_bank_base_values(source):
    bank = Bank(name="bank", bank_alignment=ALIGNMENT, base_address=BaseAddress(value=source))
    with pytest.raises(TgiError):
        api.getBankBaseAddress(get_handle(bank))
    assert api.getBankBaseAddressExpression(get_handle(bank)) == source


@pytest.mark.parametrize("node", [None, pytest.param(object(), id="foreign"), BaseAddress(value=5)])
def test_missing_foreign_or_invalid_base(node):
    bank = Bank(name="bank", bank_alignment=ALIGNMENT, base_address=node)
    with pytest.raises(TgiError):
        api.getBankBaseAddress(get_handle(bank))


@pytest.mark.parametrize("model", [BankedBankType, AddressBankType.Bank, BankedDefinitionBankType, LocalBankedBankType])
def test_nested_banks_have_no_base(model):
    bank = model(name="nested", bank_alignment=ALIGNMENT)
    for op in (api.getBankBaseAddress, api.getBankBaseAddressExpression, api.getBankBaseAddressID):
        with pytest.raises(TgiError) as error:
            op(get_handle(bank))
        assert error.value.fault_code == TgiFaultCode.INVALID_ID


@pytest.mark.parametrize(
    "model", [AddressBankType, BankedBankType, AddressBankDefinitionType, BankedDefinitionBankType]
)
def test_direct_choice_collections_preserve_order_and_descendant_ownership(model):
    block = BankedBlockType(
        name="block",
        range=UnsignedPositiveLongintExpression(value="16"),
        width=UnsignedPositiveIntExpression(value="32"),
    )
    child = (
        model.Bank(name="nested", bank_alignment=ALIGNMENT)
        if model in (AddressBankType, AddressBankDefinitionType)
        else model.Bank()
    )
    # Some generated deep nested bank classes contain only vendorExtensions.
    values = [block, child]
    subspace = BankedSubspaceType(initiator_ref="master")
    if model in (AddressBankType, BankedBankType):
        values.insert(1, subspace)
    kwargs = {"base_address": BaseAddress(value="0")} if model in (AddressBankType, AddressBankDefinitionType) else {}
    bank = model(name="bank", bank_alignment=ALIGNMENT, choice=tuple(values), **kwargs)
    original = bank.choice
    handle = get_handle(bank)
    assert api.getBankBlockAndSubspaceElementIDs(handle) == [get_handle(item) for item in values]
    assert api.getBankAddressBlockIDs(handle) == [get_handle(block)]
    assert api.getBankBankIDs(handle) == [get_handle(child)]
    assert api.getBankSubspaceMapIDs(handle) == ([get_handle(subspace)] if subspace in values else [])
    assert bank.choice is original
    for item in values:
        info = get_parent_info(get_handle(item))
        assert resolve_handle(info.parent_handle) is bank and info.path == ("choice",)
        assert api.getMemoryMapElementType(get_handle(item)) in ("bank", "addressBlock", "subSpaceMap")


@pytest.mark.parametrize("model", [LocalAddressBankType, LocalBankedBankType])
def test_local_bank_children_and_optional_metadata(model):
    child = LocalBankedBankType(name="child", bank_alignment=ALIGNMENT)
    block = BankedBlockType(
        name="block",
        range=UnsignedPositiveLongintExpression(value="16"),
        width=UnsignedPositiveIntExpression(value="32"),
    )
    kwargs = {"base_address": BaseAddress(value="0")} if model is LocalAddressBankType else {}
    bank = model(name="bank", bank_alignment=ALIGNMENT, address_block_or_bank=(child, block), **kwargs)
    handle = get_handle(bank)
    assert api.getBankBlockAndSubspaceElementIDs(handle) == [get_handle(child), get_handle(block)]
    assert api.getBankUsage(handle) is None and api.getBankVolatility(handle) is None
    bank.usage, bank.volatile = UsageType.MEMORY, Volatile(value=False)
    assert api.getBankUsage(handle) == "memory" and api.getBankVolatility(handle) is False
    assert api.getMemoryMapElementType(get_handle(child)) == "bank"
    for op in (api.getBankAddressBlockIDs, api.getBankBankIDs, api.getBankSubspaceMapIDs):
        with pytest.raises(TgiError):
            op(handle)


def test_bank_metadata_is_optional_strict_and_does_not_reown_enum():
    bank = Bank(name="bank", bank_alignment=ALIGNMENT, base_address=BaseAddress(value="0"), choice=())
    handle = get_handle(bank)
    assert api.getBankUsage(handle) is None and api.getBankVolatility(handle) is None
    for usage in UsageType:
        bank.choice = (usage, Volatile(value=True))
        assert api.getBankUsage(handle) == usage.value and api.getBankVolatility(handle) is True
        assert get_parent_info(get_handle(usage)) is None
    bank.choice = (Volatile(value="false"),)
    with pytest.raises(TgiError):
        api.getBankVolatility(handle)


@pytest.mark.parametrize(
    "values", [None, {}, pytest.param((object(),), id="foreign"), (UsageType.MEMORY, UsageType.REGISTER)]
)
def test_invalid_bank_choices_do_not_modify_storage(values):
    bank = Bank(name="bank", bank_alignment=ALIGNMENT, base_address=BaseAddress(value="0"), choice=values)
    for op in (api.getBankAddressBlockIDs, api.getBankUsage, api.getBankVolatility):
        with pytest.raises(TgiError):
            op(get_handle(bank))
        assert bank.choice is values


def reference_context():
    identity = ("test", "types", "banks", "1")
    external = ExternalTypeDefinitions(
        name="imported",
        type_definitions_ref=ConfigurableLibraryRefType(
            vendor=identity[0], library=identity[1], name=identity[2], version=identity[3]
        ),
    )
    ref = AddressBankType.BankDefinitionRef(value="definition", type_definitions="imported")
    bank = Bank(name="bank", bank_alignment=ALIGNMENT, base_address=BaseAddress(value="16"), choice=(ref,))
    owner = Component(
        vendor="test",
        library="components",
        name="banks",
        version="1",
        type_definitions=ComponentType.TypeDefinitions(external_type_definitions=[external]),
        memory_maps=MemoryMaps(memory_map=[MemoryMapType(name="map", choice=[bank])]),
    )
    child = BankDefinitions.BankDefinition.Bank(name="nested", bank_alignment=ALIGNMENT)
    block = BankedBlockType(
        name="block",
        range=UnsignedPositiveLongintExpression(value="16"),
        width=UnsignedPositiveIntExpression(value="32"),
    )
    definition = BankDefinitions.BankDefinition(
        name="definition",
        address_block_or_bank=(child, block),
        usage=UsageType.RESERVED,
        volatile=Volatile(value=False),
    )
    target = TypeDefinitions(
        vendor=identity[0],
        library=identity[1],
        name=identity[2],
        version=identity[3],
        bank_definitions=BankDefinitions(bank_definition=[definition]),
    )
    registry.register(owner, ("test", "components", "banks", "1"))
    registry.register(target, identity)
    return bank, ref, definition, child, block, owner


def test_referenced_bank_children_metadata_and_local_base_are_distinct():
    bank, ref, definition, child, block, _owner = reference_context()
    handle = get_handle(bank)
    assert api.getBankBankIDs(handle) == [get_handle(child)]
    assert api.getBankAddressBlockIDs(handle) == [get_handle(block)]
    assert api.getBankBlockAndSubspaceElementIDs(handle) == [get_handle(child), get_handle(block)]
    assert api.getBankSubspaceMapIDs(handle) == []
    assert api.getBankUsage(handle) == "reserved" and api.getBankVolatility(handle) is False
    assert api.getBankBaseAddress(handle) == 16
    assert resolve_handle(get_parent_info(get_handle(child)).parent_handle) is definition
    assert bank.choice == (ref,) and definition.address_block_or_bank == (child, block)
    with pytest.raises(TgiError):
        api.getBankUsage(get_handle(definition))
    ref.value = "missing"
    with pytest.raises(TgiError):
        api.getBankAddressBlockIDs(handle)
    ref.value = "bad name"
    with pytest.raises(TgiError):
        api.getBankUsage(handle)
    bank.choice = (ref, block)
    with pytest.raises(TgiError):
        api.getBankBankIDs(handle)


@pytest.mark.parametrize("name,parameter", list(OPERATIONS.items()))
def test_exact_signatures_and_invalid_handles(name, parameter):
    op = getattr(api, name)
    assert list(signature(op).parameters) == [parameter]
    for handle in (None, 42, "missing", get_handle(BaseAddress(value="0"))):
        with pytest.raises(TgiError) as error:
            op(handle)
        assert error.value.fault_code == TgiFaultCode.INVALID_ID


def test_bank_reference_component_validates_and_round_trips():
    bank, _ref, _definition, _child, _block, owner = reference_context()
    xml = XmlDocument.serializer().render(owner)
    schema = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))
    assert schema.validate(etree.fromstring(xml.encode())), schema.error_log
    parsed = XmlDocument.parser().from_string(xml, Component)
    registry.unregister(("test", "components", "banks", "1"))
    registry.register(parsed, ("test", "components", "banks", "1"))
    parsed_bank = parsed.memory_maps.memory_map[0].choice[0]
    assert api.getBankBaseAddress(get_handle(parsed_bank)) == 16
    assert len(api.getBankAddressBlockIDs(get_handle(parsed_bank))) == 1
    assert api.getBankUsage(get_handle(parsed_bank)) == "reserved"
    assert schema.validate(etree.fromstring(XmlDocument.serializer().render(parsed).encode()))


def test_bank_base_declared_bounds_and_descendant_ownership():
    node = BaseAddress(value="4", minimum=5, maximum=10)
    bank = Bank(name="bank", bank_alignment=ALIGNMENT, base_address=node)
    with pytest.raises(TgiError):
        api.getBankBaseAddress(get_handle(bank))
    node.value = "11"
    with pytest.raises(TgiError):
        api.getBankBaseAddress(get_handle(bank))
    node.value = "5"
    assert api.getBankBaseAddress(get_handle(bank)) == 5
    block = BankedBlockType(
        name="block",
        range=UnsignedPositiveLongintExpression(value="16"),
        width=UnsignedPositiveIntExpression(value="32"),
    )
    bank.choice = (block,)
    api.getBankAddressBlockIDs(get_handle(bank))
    assert resolve_handle(get_parent_info(get_handle(block.width)).parent_handle) is block

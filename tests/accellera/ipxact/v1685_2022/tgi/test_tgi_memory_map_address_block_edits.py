"""Address-block instance metadata and optional-node removal contracts."""

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
    AddressBlockRef,
    AddressBlockType,
    Array,
    Bank,
    BankAlignmentType,
    BankedBlockType,
    BaseAddress,
    Component,
    Dim,
    Index,
    Indices,
    MemoryMaps,
    MemoryMapType,
    RegisterRef,
    Stride,
    UnsignedPositiveIntExpression,
    UnsignedPositiveLongintExpression,
    UsageType,
    Volatile,
)


@pytest.fixture(autouse=True)
def isolate_registry():
    registry.clear()
    yield
    registry.clear()


def block(model=AddressBlock):
    range = UnsignedPositiveLongintExpression(value="16")
    width = UnsignedPositiveIntExpression(value="8")
    if model is BankedBlockType:
        return model(name="block", range=range, width=width)
    return model(name="block", base_address=BaseAddress(value="0"), choice=(range, width))


@pytest.mark.parametrize("model", [AddressBlock, AddressBlockType, BankedBlockType])
def test_usage_and_volatility_creation_identity_removal_and_defaults(model):
    owner = block(model)
    handle = get_handle(owner)
    assert api.removeAddressBlockUsage(handle) is False
    assert api.removeAddressBlockVolatility(handle) is False
    for usage in UsageType:
        assert api.setAddressBlockUsage(handle, usage.value) is True
        assert api.getAddressBlockUsage(handle) == usage.value
        assert get_parent_info(get_handle(usage)) is None
    assert api.setAddressBlockVolatility(handle, True) is True
    volatile = (
        owner.volatile
        if model is BankedBlockType
        else next(item for item in owner.choice if isinstance(item, Volatile))
    )
    volatile_id = get_handle(volatile)
    if model is not BankedBlockType:
        owner.choice = tuple(owner.choice)
        original = owner.choice
    assert api.setAddressBlockVolatility(handle, False) is True
    assert resolve_handle(volatile_id) is volatile and volatile.value is False
    if model is not BankedBlockType:
        assert owner.choice is original
    info = get_parent_info(volatile_id)
    assert resolve_handle(info.parent_handle) is owner
    assert api.removeAddressBlockVolatility(handle) is True
    assert resolve_handle(volatile_id) is None
    assert api.getAddressBlockVolatility(handle) is None
    assert api.removeAddressBlockUsage(handle) is True
    assert api.getAddressBlockUsage(handle) == "reserved"
    assert api.removeAddressBlockUsage(handle) is False
    assert api.removeAddressBlockVolatility(handle) is False


@pytest.mark.parametrize("model", [AddressBlock, AddressBlockType])
def test_identifier_name_normalization_tuple_idempotence_and_removal(model):
    owner = block(model)
    handle = get_handle(owner)
    assert api.removeAddressBlockTypeIdentifier(handle) is False
    assert api.setAddressBlockTypeIdentifier(handle, " \tδ_block\n") is True
    assert api.getAddressBlockTypeIdentifier(handle) == "δ_block"
    assert isinstance(owner.choice[0], str)
    owner.choice = tuple(owner.choice)
    original = owner.choice
    assert api.setAddressBlockTypeIdentifier(handle, "δ_block") is True
    assert owner.choice is original
    assert api.setAddressBlockTypeIdentifier(handle, "new_name") is True
    assert api.getAddressBlockTypeIdentifier(handle) == "new_name"
    assert api.removeAddressBlockTypeIdentifier(handle) is True
    assert api.getAddressBlockTypeIdentifier(handle) is None
    assert api.removeAddressBlockTypeIdentifier(handle) is False


def test_banked_blocks_have_no_identifier_or_array():
    owner = block(BankedBlockType)
    assert api.removeAddressBlockTypeIdentifier(get_handle(owner)) is False
    assert api.removeAddressBlockArray(get_handle(owner)) is False
    with pytest.raises(TgiError) as error:
        api.setAddressBlockTypeIdentifier(get_handle(owner), "name")
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT


def test_array_removal_invalidates_owned_descendants_without_changing_other_nodes():
    owner = block()
    dim = Dim(value="2")
    stride = Stride(value="16")
    owner.array = Array(dim=(dim,), stride=stride)
    handles = [get_handle(item) for item in (owner.array, dim, stride)]
    original = owner.choice
    assert api.removeAddressBlockArray(get_handle(owner)) is True
    assert owner.array is None and owner.choice is original
    assert all(resolve_handle(handle) is None for handle in handles)
    assert api.removeAddressBlockArray(get_handle(owner)) is False


def test_index_removal_preserves_order_and_metadata_and_prunes_empty_holder():
    first, last = Index(value="PARAM"), Index(value="2 + 1")
    holder = Indices(index=(first, last))
    reference = AddressBlockRef(address_block_ref="block", indices=holder)
    api.getAddressBlockRefIndexIDs(get_handle(reference))
    first_id, last_id, holder_id = map(get_handle, (first, last, holder))
    assert api.removeAddressBlockRefIndex(first_id) is True
    assert resolve_handle(first_id) is None and holder.index == [last]
    assert last.value == "2 + 1" and reference.indices is holder
    assert api.removeAddressBlockRefIndex(last_id) is True
    assert reference.indices is None and resolve_handle(last_id) is None and resolve_handle(holder_id) is None
    with pytest.raises(TgiError) as error:
        api.removeAddressBlockRefIndex(last_id)
    assert error.value.fault_code == TgiFaultCode.INVALID_ID


def test_foreign_or_detached_indices_are_rejected():
    detached = Index(value="0")
    reference = RegisterRef(register_ref="register", indices=Indices(index=[Index(value="0")]))
    foreign_id = api.getRegisterRefIndexIDs(get_handle(reference))[0]
    for handle in (foreign_id, get_handle(detached), get_handle(Indices(index=[]))):
        with pytest.raises(TgiError) as error:
            api.removeAddressBlockRefIndex(handle)
        assert error.value.fault_code == TgiFaultCode.INVALID_ID
    assert len(reference.indices.index) == 1


def test_reference_branch_metadata_edits_do_not_resolve_or_mutate_definition():
    owner = block()
    reference = AddressBlockType.AddressBlockDefinitionRef(value="unloaded", type_definitions="missing")
    owner.choice = (reference,)
    owner.array = Array(dim=[Dim(value="2")])
    handle = get_handle(owner)
    for op in (api.removeAddressBlockTypeIdentifier, api.removeAddressBlockUsage, api.removeAddressBlockVolatility):
        assert op(handle) is False and owner.choice == (reference,)
    for op, value in (
        (api.setAddressBlockTypeIdentifier, "type"),
        (api.setAddressBlockUsage, "memory"),
        (api.setAddressBlockVolatility, False),
    ):
        with pytest.raises(TgiError) as error:
            op(handle, value)
        assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT and owner.choice == (reference,)
    assert api.removeAddressBlockArray(handle) is True
    assert owner.choice == (reference,)


@pytest.mark.parametrize(
    "operation,value",
    [
        (api.setAddressBlockTypeIdentifier, "bad name"),
        (api.setAddressBlockTypeIdentifier, 3),
        (api.setAddressBlockUsage, "invalid"),
        (api.setAddressBlockUsage, False),
        (api.setAddressBlockVolatility, 1),
        (api.setAddressBlockVolatility, "false"),
    ],
)
def test_invalid_arguments_leave_source_tuple_unchanged(operation, value):
    owner = block()
    original = owner.choice
    with pytest.raises(TgiError) as error:
        operation(get_handle(owner), value)
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert owner.choice is original


@pytest.mark.parametrize(
    "values",
    [
        None,
        {},
        pytest.param((object(),), id="foreign"),
        (UsageType.MEMORY, UsageType.RESERVED),
        (Volatile(value="false"),),
    ],
)
def test_malformed_choices_are_not_mutated(values):
    owner = block()
    owner.choice = values
    for op in (api.removeAddressBlockUsage, api.removeAddressBlockVolatility):
        # Foreign stored volatility is checked when removing volatility.
        if (
            isinstance(values, tuple)
            and len(values) == 1
            and isinstance(values[0], Volatile)
            and op is api.removeAddressBlockUsage
        ):
            continue
        with pytest.raises(TgiError):
            op(get_handle(owner))
        assert owner.choice is values


@pytest.mark.parametrize("model", [AddressBlock, BankedBlockType])
def test_edited_metadata_order_validates_and_round_trips(model):
    owner = block(model)
    handle = get_handle(owner)
    # Insert in reverse schema order to verify setters choose the proper positions.
    api.setAddressBlockVolatility(handle, True)
    api.setAddressBlockUsage(handle, "memory")
    if model is AddressBlock:
        api.setAddressBlockTypeIdentifier(handle, "type")
    container = (
        owner
        if model is AddressBlock
        else Bank(
            name="bank", bank_alignment=BankAlignmentType.SERIAL, base_address=BaseAddress(value="0"), choice=[owner]
        )
    )
    root = Component(
        vendor="test",
        library="component",
        name="edits",
        version="1",
        memory_maps=MemoryMaps(memory_map=[MemoryMapType(name="map", choice=[container])]),
    )
    xml = XmlDocument.serializer().render(root)
    schema = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))
    assert schema.validate(etree.fromstring(xml.encode())), schema.error_log
    parsed = XmlDocument.parser().from_string(xml, Component)
    registry.register(parsed, ("test", "component", "edits", "1"))
    parsed_block = parsed.memory_maps.memory_map[0].choice[0]
    if model is BankedBlockType:
        parsed_block = parsed_block.choice[0]
    assert api.getAddressBlockTypeIdentifier(get_handle(parsed_block)) == ("type" if model is AddressBlock else None)
    assert api.getAddressBlockUsage(get_handle(parsed_block)) == "memory"
    volatile = (
        parsed_block.volatile
        if model is BankedBlockType
        else next(item for item in parsed_block.choice if isinstance(item, Volatile))
    )
    handle = get_handle(volatile)
    assert api.removeAddressBlockVolatility(get_handle(parsed_block)) is True
    assert resolve_handle(handle) is None
    assert schema.validate(etree.fromstring(XmlDocument.serializer().render(parsed).encode()))


@pytest.mark.parametrize(
    "operation,parameters,args",
    [
        (api.removeAddressBlockArray, ["addressBlockID"], []),
        (api.removeAddressBlockRefIndex, ["indexID"], []),
        (api.removeAddressBlockTypeIdentifier, ["addressBlockID"], []),
        (api.removeAddressBlockUsage, ["addressBlockID"], []),
        (api.removeAddressBlockVolatility, ["addressBlockID"], []),
        (api.setAddressBlockTypeIdentifier, ["addressBlockID", "typeIdentifier"], ["name"]),
        (api.setAddressBlockUsage, ["addressBlockID", "usage"], ["memory"]),
        (api.setAddressBlockVolatility, ["addressBlockID", "_volatile"], [False]),
    ],
)
def test_exact_signatures_and_invalid_handles(operation, parameters, args):
    assert list(signature(operation).parameters) == parameters
    for handle in (None, 7, "missing", get_handle(BaseAddress(value="0"))):
        with pytest.raises(TgiError) as error:
            operation(handle, *args)
        assert error.value.fault_code == TgiFaultCode.INVALID_ID


def test_duplicate_indices_and_foreign_arrays_fault_without_mutation():
    index = Index(value="0")
    holder = Indices(index=(index, index))
    reference = AddressBlockRef(address_block_ref="block", indices=holder)
    api.getAddressBlockRefIndexIDs(get_handle(reference))
    original = holder.index
    with pytest.raises(TgiError):
        api.removeAddressBlockRefIndex(get_handle(index))
    assert holder.index is original and reference.indices is holder
    owner = block()
    owner.array = Indices(index=[])
    with pytest.raises(TgiError):
        api.removeAddressBlockArray(get_handle(owner))
    assert isinstance(owner.array, Indices)

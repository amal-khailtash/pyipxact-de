"""Memory map/remap collections and schema-aware shared defaults."""

import inspect

import pytest

from amal.eda.accellera.ipxact.v1685_2022 import tgi as api
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import (
    TgiError,
    TgiFaultCode,
    get_handle,
    get_parent_info,
    resolve_handle,
)
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import (
    AddressBlock,
    AddressUnitBits,
    Bank,
    BankAlignmentType,
    BaseAddress,
    LocalMemoryMapType,
    MemoryMapType,
    MemoryRemap,
    MemoryRemapType,
    ModeRef,
    SharedType,
    SignedLongintExpression,
    SubspaceMap,
)

OPERATIONS = [
    (api.getMemoryMapMemoryRemapIDs, "memoryMapID"),
    (api.getMemoryMapRemapIDs, "memoryMapOrLocalMemoryMapID"),
    (api.getMemoryMapShared, "memoryMapOrLocalMemoryMapID"),
    (api.getMemoryMapSubspaceMapIDs, "memoryMapID"),
    (api.getMemoryRemapAddressBlockIDs, "memoryRemapID"),
    (api.getMemoryRemapBankIDs, "memoryRemapID"),
    (api.getMemoryRemapElementIDs, "memoryRemapID"),
    (api.getMemoryRemapSubspaceMapIDs, "memoryRemapID"),
]


def block(name):
    return AddressBlock(name=name, base_address=BaseAddress(value="0"))


def bank():
    return Bank(name="bank", base_address=BaseAddress(value="0"), bank_alignment=BankAlignmentType.SERIAL)


def subspace(name):
    return SubspaceMap(name=name, base_address=SignedLongintExpression(value="-4"), initiator_ref="bus")


def test_memory_map_collections_preserve_order_tuple_metadata_and_owned_descendants():
    first, second = MemoryRemap(name="first", mode_ref=[ModeRef(value="mode", priority=0)]), MemoryRemap(name="second")
    direct = subspace("direct")
    first.choice = [subspace("nested")]
    original = (bank(), direct, block("block"), first, second, AddressUnitBits(value="8"), SharedType.NO)
    owner = MemoryMapType(name="map", choice=original, id="map-id")
    handle = get_handle(owner)
    assert api.getMemoryMapMemoryRemapIDs(handle) == [get_handle(first), get_handle(second)]
    assert api.getMemoryMapRemapIDs(handle) == [get_handle(first), get_handle(second)]
    assert api.getMemoryMapSubspaceMapIDs(handle) == [get_handle(direct)]
    assert owner.choice is original and owner.id == "map-id"
    for child in (first, second, direct):
        info = get_parent_info(get_handle(child))
        assert resolve_handle(info.parent_handle) is owner and info.path == ("choice",) and info.container == "list"
    mode = first.mode_ref[0]
    assert resolve_handle(get_parent_info(get_handle(mode)).parent_handle) is first
    parsed = XmlDocument.parser().from_string(XmlDocument.serializer().render(owner), MemoryMapType)
    remaps = [resolve_handle(handle) for handle in api.getMemoryMapMemoryRemapIDs(get_handle(parsed))]
    assert [item.name for item in remaps] == ["first", "second"]
    assert [resolve_handle(handle).name for handle in api.getMemoryMapSubspaceMapIDs(get_handle(parsed))] == ["direct"]


@pytest.mark.parametrize("owner_type", [MemoryRemapType, MemoryRemap])
def test_remap_mixed_children_filter_by_type_and_preserve_immediate_ownership(owner_type):
    first, second = block("first"), block("second")
    b, sub = bank(), subspace("sub")
    b.choice = [Bank.BankDefinitionRef(value="unrelated", type_definitions="defs")]
    original = (sub, first, b, second)
    owner = owner_type(name="remap", choice=original, mode_ref=(ModeRef(value="mode", priority=1),), id="remap-id")
    handle = get_handle(owner)
    assert api.getMemoryRemapElementIDs(handle) == [get_handle(item) for item in original]
    assert api.getMemoryRemapAddressBlockIDs(handle) == [get_handle(first), get_handle(second)]
    assert api.getMemoryRemapBankIDs(handle) == [get_handle(b)]
    assert api.getMemoryRemapSubspaceMapIDs(handle) == [get_handle(sub)]
    assert owner.choice is original and owner.id == "remap-id" and isinstance(owner.mode_ref, tuple)
    for child in original:
        info = get_parent_info(get_handle(child))
        assert resolve_handle(info.parent_handle) is owner and info.path == ("choice",) and info.container == "list"
    assert resolve_handle(get_parent_info(get_handle(first.base_address)).parent_handle) is first


@pytest.mark.parametrize("shared", list(SharedType))
def test_shared_values_and_absent_default_do_not_materialize_or_reown_scalar(shared):
    owner = MemoryMapType(name="map", choice=(shared,))
    original = owner.choice
    assert api.getMemoryMapShared(get_handle(owner)) == shared.value
    assert owner.choice is original
    owner.choice = ()
    assert api.getMemoryMapShared(get_handle(owner)) == "undefined"
    assert owner.choice == ()
    owner.choice = (MemoryMapType.MemoryMapDefinitionRef(value="definition", type_definitions="defs"),)
    assert api.getMemoryMapShared(get_handle(owner)) is None
    assert api.getMemoryMapRemapIDs(get_handle(owner)) == []
    assert api.getMemoryMapMemoryRemapIDs(get_handle(owner)) == []
    assert api.getMemoryMapSubspaceMapIDs(get_handle(owner)) == []


def test_local_map_has_no_remap_or_shared_property_and_rejects_schema_foreign_children():
    local = LocalMemoryMapType(name="local", address_block_or_bank=(block("local-block"),))
    original = local.address_block_or_bank
    assert api.getMemoryMapRemapIDs(get_handle(local)) == []
    assert api.getMemoryMapShared(get_handle(local)) is None
    assert local.address_block_or_bank is original
    for op in (api.getMemoryMapMemoryRemapIDs, api.getMemoryMapSubspaceMapIDs):
        with pytest.raises(TgiError) as error:
            op(get_handle(local))
        assert error.value.fault_code == TgiFaultCode.INVALID_ID
    malformed = (MemoryRemap(name="foreign"),)
    local.address_block_or_bank = malformed
    for op in (api.getMemoryMapRemapIDs, api.getMemoryMapShared):
        with pytest.raises(TgiError) as error:
            op(get_handle(local))
        assert error.value.fault_code == TgiFaultCode.INVALID_ID
        assert local.address_block_or_bank is malformed


@pytest.mark.parametrize("operation,parameter", OPERATIONS)
def test_signatures_and_invalid_owner_handles(operation, parameter):
    assert list(inspect.signature(operation).parameters) == [parameter]
    for invalid in (None, [], {}, "missing", get_handle(AddressUnitBits(value="8"))):
        with pytest.raises(TgiError) as error:
            operation(**{parameter: invalid})
        assert error.value.fault_code == TgiFaultCode.INVALID_ID
    foreign = MemoryMapType(name="map") if parameter == "memoryRemapID" else MemoryRemap(name="remap")
    with pytest.raises(TgiError) as error:
        operation(get_handle(foreign))
    assert error.value.fault_code == TgiFaultCode.INVALID_ID


@pytest.mark.parametrize(
    "values", [None, {}, pytest.param((object(),), id="foreign-object"), (SharedType.YES, SharedType.NO), ("yes",)]
)
def test_map_getters_reject_malformed_choice_before_modification(values):
    owner = MemoryMapType(name="map", choice=values)
    for op in (
        api.getMemoryMapMemoryRemapIDs,
        api.getMemoryMapRemapIDs,
        api.getMemoryMapShared,
        api.getMemoryMapSubspaceMapIDs,
    ):
        with pytest.raises(TgiError) as error:
            op(get_handle(owner))
        assert error.value.fault_code == TgiFaultCode.INVALID_ID
        assert owner.choice is values


@pytest.mark.parametrize(
    "values",
    [
        None,
        {},
        pytest.param((object(),), id="foreign-object"),
        (MemoryRemap(name="foreign"),),
        (MemoryRemapType.RemapDefinitionRef(value="def", type_definitions="defs"), block("bad")),
    ],
)
def test_remap_getters_reject_invalid_or_conflicting_choices(values):
    owner = MemoryRemap(name="remap", choice=values)
    for op in (
        api.getMemoryRemapElementIDs,
        api.getMemoryRemapAddressBlockIDs,
        api.getMemoryRemapBankIDs,
        api.getMemoryRemapSubspaceMapIDs,
    ):
        with pytest.raises(TgiError) as error:
            op(get_handle(owner))
        assert error.value.fault_code == TgiFaultCode.INVALID_ID
        assert owner.choice is values


def test_remap_empty_and_definition_branch_return_only_stored_inline_children():
    owner = MemoryRemap(name="empty", choice=())
    for values in ((), (MemoryRemapType.RemapDefinitionRef(value="definition", type_definitions="defs"),)):
        owner.choice = values
        for op in (
            api.getMemoryRemapElementIDs,
            api.getMemoryRemapAddressBlockIDs,
            api.getMemoryRemapBankIDs,
            api.getMemoryRemapSubspaceMapIDs,
        ):
            assert op(get_handle(owner)) == []
            assert owner.choice is values

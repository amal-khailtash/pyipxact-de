"""Memory map core traversal, local-map units and exact Annex signatures."""

import inspect

import pytest

from amal.eda.accellera.ipxact.v1685_2022 import tgi as api
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import (
    TgiError,
    TgiFaultCode,
    get_handle,
    get_parent_info,
    register_parent,
    resolve_handle,
)
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import (
    AddressBlock,
    AddressSpaces,
    AddressUnitBits,
    Bank,
    BankAlignmentType,
    BankedBankType,
    BankedBlockType,
    BankedSubspaceType,
    BaseAddress,
    LocalAddressBankType,
    LocalMemoryMapType,
    MemoryMapType,
    MemoryRemap,
    SharedType,
    SignedLongintExpression,
    SubspaceMap,
    UnsignedPositiveIntExpression,
    UnsignedPositiveLongintExpression,
)


def block(name="block"):
    return AddressBlock(name=name, base_address=BaseAddress(value="0"))


def bank(model=Bank):
    return model(name="bank", base_address=BaseAddress(value="0"), bank_alignment=BankAlignmentType.SERIAL)


def address_space(local, unit):
    return AddressSpaces.AddressSpace(
        name="space",
        range=UnsignedPositiveLongintExpression(value="256"),
        width=UnsignedPositiveIntExpression(value="32"),
        local_memory_map=local,
        address_unit_bits=unit,
    )


def test_ordered_mixed_choice_filters_remaps_scalars_and_restores_parsed_ownership():
    nested = block("nested")
    remap = MemoryRemap(name="remap", choice=[nested])
    b = bank()
    first, second = block("first"), block("second")
    subspace = SubspaceMap(name="subspace", base_address=SignedLongintExpression(value="0"), initiator_ref="bus")
    unit = AddressUnitBits(value="8", other_attributes={"{urn:test}tag": "metadata"})
    original = (b, first, subspace, second, remap, unit, SharedType.UNDEFINED)
    owner = MemoryMapType(name="map", choice=original)
    assert api.getMemoryMapElementIDs(get_handle(owner)) == [get_handle(item) for item in original[:4]]
    assert owner.choice is original
    assert api.getMemoryMapAddressBlockIDs(get_handle(owner)) == [get_handle(first), get_handle(second)]
    assert api.getMemoryMapBankIDs(get_handle(owner)) == [get_handle(b)]
    assert get_handle(nested) not in api.getMemoryMapElementIDs(get_handle(owner))
    parsed = XmlDocument.parser().from_string(XmlDocument.serializer().render(owner), MemoryMapType)
    ids = api.getMemoryMapElementIDs(get_handle(parsed))
    assert [api.getMemoryMapElementType(handle) for handle in ids] == [
        "bank",
        "addressBlock",
        "subSpaceMap",
        "addressBlock",
    ]
    for handle in ids:
        info = get_parent_info(handle)
        assert resolve_handle(info.parent_handle) is parsed and info.path == ("choice",) and info.container == "list"


def test_local_map_uses_actual_mixed_container_and_parent_address_units():
    local = LocalMemoryMapType(name="local", address_block_or_bank=(bank(LocalAddressBankType), block()))
    unit = AddressUnitBits(value="(2 + 2) * 4", other_attributes={"{urn:test}tag": "source-id"})
    owner = address_space(local, unit)
    register_parent(local, owner, ("local_memory_map",), "single")
    original = local.address_block_or_bank
    ids = api.getMemoryMapElementIDs(get_handle(local))
    assert [api.getMemoryMapElementType(handle) for handle in ids] == ["bank", "addressBlock"]
    assert local.address_block_or_bank is original
    assert api.getMemoryMapAddressUnitBits(get_handle(local)) == 16
    assert api.getMemoryMapAddressUnitBitsExpression(get_handle(local)) == "(2 + 2) * 4"
    assert unit.other_attributes == {"{urn:test}tag": "source-id"}
    assert resolve_handle(get_parent_info(get_handle(unit)).parent_handle) is owner
    owner.address_unit_bits = None
    assert api.getMemoryMapAddressUnitBits(get_handle(local)) == 8
    assert api.getMemoryMapAddressUnitBitsExpression(get_handle(local)) is None
    detached = LocalMemoryMapType(name="detached")
    for op in (api.getMemoryMapAddressUnitBits, api.getMemoryMapAddressUnitBitsExpression):
        with pytest.raises(TgiError) as error:
            op(get_handle(detached))
        assert error.value.fault_code == TgiFaultCode.INVALID_ID


@pytest.mark.parametrize("source,value", [("8", 8), ("'h10", 16), ("2 ** 5", 32), (str((1 << 63) - 1), (1 << 63) - 1)])
def test_unit_getters_evaluate_source_and_preserve_wrapper_and_metadata(source, value):
    unit = AddressUnitBits(
        value=source, other_attributes={"{urn:test}tag": "unit-id"}, minimum=1, maximum=(1 << 63) - 1
    )
    owner = MemoryMapType(name="map", choice=(unit,))
    handle = get_handle(owner)
    unit_id = get_handle(unit)
    assert api.getMemoryMapAddressUnitBits(handle) == value
    assert api.getMemoryMapAddressUnitBitsExpression(handle) == source
    assert api.getMemoryMapAddressUnitBitsID(handle) == unit_id
    assert unit.value == source and unit.other_attributes == {"{urn:test}tag": "unit-id"} and owner.choice == (unit,)
    info = get_parent_info(unit_id)
    assert resolve_handle(info.parent_handle) is owner and info.path == ("choice",)


@pytest.mark.parametrize("source", ["PARAM", "1 / 0", "0", "-1", str(1 << 63)])
def test_numeric_faults_leave_raw_source_available(source):
    unit = AddressUnitBits(value=source)
    owner = MemoryMapType(name="map", choice=(unit,))
    with pytest.raises(TgiError) as error:
        api.getMemoryMapAddressUnitBits(get_handle(owner))
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert api.getMemoryMapAddressUnitBitsExpression(get_handle(owner)) == source
    assert api.getMemoryMapAddressUnitBitsID(get_handle(owner)) == get_handle(unit)


def test_absent_inline_defaults_do_not_materialize_nodes_and_definition_branch_is_not_defaulted():
    owner = MemoryMapType(name="empty", choice=())
    handle = get_handle(owner)
    assert api.getMemoryMapAddressUnitBits(handle) == 8
    assert api.getMemoryMapAddressUnitBitsExpression(handle) is None
    assert api.getMemoryMapAddressUnitBitsID(handle) is None
    assert api.getMemoryMapElementIDs(handle) == [] and owner.choice == ()
    owner.choice = (MemoryMapType.MemoryMapDefinitionRef(value="definition", type_definitions="external"),)
    assert api.getMemoryMapAddressUnitBits(handle) is None
    assert api.getMemoryMapElementIDs(handle) == []


@pytest.mark.parametrize(
    "values",
    [
        None,
        {},
        pytest.param((object(),), id="foreign-object"),
        (AddressUnitBits(value="8"), AddressUnitBits(value="16")),
        (MemoryMapType.MemoryMapDefinitionRef(value="def", type_definitions="ext"), block()),
    ],
)
def test_invalid_choices_rejected_before_traversal(values):
    owner = MemoryMapType(name="map", choice=values)
    for operation in (
        api.getMemoryMapElementIDs,
        api.getMemoryMapAddressBlockIDs,
        api.getMemoryMapBankIDs,
        api.getMemoryMapAddressUnitBits,
        api.getMemoryMapAddressUnitBitsExpression,
        api.getMemoryMapAddressUnitBitsID,
    ):
        with pytest.raises(TgiError) as error:
            operation(get_handle(owner))
        assert error.value.fault_code == TgiFaultCode.INVALID_ID
        assert owner.choice is values


def test_exact_signatures_and_strict_handle_types():
    operations = [
        (api.getMemoryMapAddressBlockIDs, "memoryMapID"),
        (api.getMemoryMapAddressUnitBits, "memoryMapOrLocalMemoryMapID"),
        (api.getMemoryMapAddressUnitBitsExpression, "memoryMapOrLocalMemoryMapID"),
        (api.getMemoryMapAddressUnitBitsID, "memoryMapID"),
        (api.getMemoryMapBankIDs, "memoryMapID"),
        (api.getMemoryMapElementIDs, "memoryMapOrLocalMemoryMapID"),
        (api.getMemoryMapElementType, "memoryMapElementID"),
    ]
    for operation, parameter in operations:
        assert list(inspect.signature(operation).parameters) == [parameter]
        for invalid in (None, [], {}, "missing", get_handle(AddressUnitBits(value="8"))):
            with pytest.raises(TgiError) as error:
                operation(**{parameter: invalid})
            assert error.value.fault_code == TgiFaultCode.INVALID_ID
    local = LocalMemoryMapType(name="local")
    for operation in (api.getMemoryMapAddressBlockIDs, api.getMemoryMapBankIDs, api.getMemoryMapAddressUnitBitsID):
        with pytest.raises(TgiError):
            operation(get_handle(local))
    with pytest.raises(TgiError):
        api.getMemoryMapElementType(get_handle(MemoryRemap(name="remap")))


def test_element_type_recognizes_banked_models():
    models = [
        (
            BankedBlockType(
                name="block",
                range=UnsignedPositiveLongintExpression(value="4"),
                width=UnsignedPositiveIntExpression(value="8"),
            ),
            "addressBlock",
        ),
        (BankedBankType(name="bank", bank_alignment=BankAlignmentType.SERIAL), "bank"),
        (BankedSubspaceType(initiator_ref="bus"), "subSpaceMap"),
    ]
    for model, expected in models:
        assert api.getMemoryMapElementType(get_handle(model)) == expected

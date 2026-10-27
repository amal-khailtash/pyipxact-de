"""Alias memory-path source wrappers and qualified remap target contracts."""

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
    BankRef,
    BaseAddress,
    Component,
    ComponentType,
    FieldRef,
    FieldType,
    Index,
    Indices,
    MemoryMaps,
    MemoryMapType,
    MemoryRemap,
    MemoryRemapRef,
    ModeRef,
    RegisterRef,
    UnsignedIntExpression,
    UnsignedLongintExpression,
    UnsignedPositiveIntExpression,
    UnsignedPositiveLongintExpression,
)

OPERATIONS = [
    "getAliasOfAddressBlockRefByName",
    "getAliasOfAddressBlockRefID",
    "getAliasOfBankRefByNames",
    "getAliasOfBankRefIDs",
    "getAliasOfMemoryMapRefByName",
    "getAliasOfMemoryMapRefID",
    "getAliasOfMemoryRemapRefByID",
    "getAliasOfMemoryRemapRefByName",
    "getAliasOfMemoryRemapRefID",
]


@pytest.fixture(autouse=True)
def isolate_registry():
    registry.clear()
    yield
    registry.clear()


def alias():
    return FieldType.AliasOf(field_ref=FieldRef(field_ref="target"))


@pytest.mark.parametrize("operation", OPERATIONS)
def test_signatures_strict_handles_and_optional_absence(operation):
    op = getattr(api, operation)
    assert list(signature(op).parameters) == ["aliasOfID"]
    owner = alias()
    assert op(get_handle(owner)) == ([] if operation in OPERATIONS[2:4] else None)
    for invalid in (None, {}, 7, "missing", get_handle(FieldRef(field_ref="foreign"))):
        with pytest.raises(TgiError) as error:
            op(invalid)
        assert error.value.fault_code == TgiFaultCode.INVALID_ID


@pytest.mark.parametrize("kind", ["AddressBlock", "MemoryMap", "MemoryRemap"])
def test_names_and_wrappers_preserve_sources_tuples_indices_and_ownership(kind):
    owner = alias()
    indices = Indices(index=(Index(value="PARAM"),))
    block = AddressBlockRef(address_block_ref=" \tδ_block\n", indices=indices)
    map = FieldType.AliasOf.MemoryMapRef(memory_map_ref=" \tδ_map\n")
    remap = MemoryRemapRef(memory_remap_ref=" \tδ_remap\n")
    owner.address_block_ref = block
    owner.address_space_ref_or_memory_map_ref_or_memory_remap_ref = (map, remap)
    original = owner.address_space_ref_or_memory_map_ref_or_memory_remap_ref
    reference = {"AddressBlock": block, "MemoryMap": map, "MemoryRemap": remap}[kind]
    getter = getattr(api, "getAliasOf" + kind + "RefByName")
    ids = getattr(api, "getAliasOf" + kind + "RefID")
    source = getattr(
        reference,
        {"AddressBlock": "address_block_ref", "MemoryMap": "memory_map_ref", "MemoryRemap": "memory_remap_ref"}[kind],
    )
    assert getter(get_handle(owner)) == source.strip()
    assert ids(get_handle(owner)) == get_handle(reference)
    info = get_parent_info(get_handle(reference))
    assert resolve_handle(info.parent_handle) is owner
    assert owner.address_space_ref_or_memory_map_ref_or_memory_remap_ref is original
    assert (
        getattr(
            reference,
            {"AddressBlock": "address_block_ref", "MemoryMap": "memory_map_ref", "MemoryRemap": "memory_remap_ref"}[
                kind
            ],
        )
        == source
    )
    assert resolve_handle(get_parent_info(get_handle(indices.index[0])).parent_handle) is indices
    assert indices.index[0].value == "PARAM"


def test_ordered_bank_sources_and_owned_wrappers():
    owner = alias()
    refs = (BankRef(bank_ref=" outer ", id="outer_id"), BankRef(bank_ref="δ_inner"))
    owner.bank_ref = refs
    assert api.getAliasOfBankRefByNames(get_handle(owner)) == ["outer", "δ_inner"]
    assert api.getAliasOfBankRefIDs(get_handle(owner)) == [get_handle(ref) for ref in refs]
    assert owner.bank_ref is refs and refs[0].bank_ref == " outer " and refs[0].id == "outer_id"
    for ref in refs:
        info = get_parent_info(get_handle(ref))
        assert resolve_handle(info.parent_handle) is owner and info.path == ("bank_ref",) and info.container == "list"


@pytest.mark.parametrize(
    "values",
    [None, {}, pytest.param((object(),), id="foreign"), (BankRef(bank_ref="bad name"),), (BankRef(bank_ref=5),)],
)
def test_invalid_bank_lists_fault_without_replacing_storage(values):
    owner = alias()
    owner.bank_ref = values
    for op in (api.getAliasOfBankRefByNames, api.getAliasOfBankRefIDs):
        with pytest.raises(TgiError):
            op(get_handle(owner))
        assert owner.bank_ref is values


@pytest.mark.parametrize(
    "values",
    [
        None,
        {},
        pytest.param((object(),), id="foreign"),
        (MemoryRemapRef(memory_remap_ref="remap"),),
        (MemoryRemapRef(memory_remap_ref="remap"), FieldType.AliasOf.MemoryMapRef(memory_map_ref="map")),
        (
            FieldType.AliasOf.AddressSpaceRef(address_space_ref="space"),
            FieldType.AliasOf.MemoryMapRef(memory_map_ref="map"),
        ),
        (FieldType.AliasOf.MemoryMapRef(memory_map_ref="map"), FieldType.AliasOf.MemoryMapRef(memory_map_ref="map")),
    ],
)
def test_invalid_exclusive_choices_fault_without_mutation(values):
    owner = alias()
    owner.address_space_ref_or_memory_map_ref_or_memory_remap_ref = values
    for name in OPERATIONS[4:]:
        with pytest.raises(TgiError):
            getattr(api, name)(get_handle(owner))
        assert owner.address_space_ref_or_memory_map_ref_or_memory_remap_ref is values


@pytest.mark.parametrize("kind", ["AddressBlock", "MemoryMap", "MemoryRemap"])
def test_malformed_source_names_and_foreign_direct_models(kind):
    owner = alias()
    owner.address_block_ref = AddressBlockRef(address_block_ref="bad name")
    owner.address_space_ref_or_memory_map_ref_or_memory_remap_ref = (
        FieldType.AliasOf.MemoryMapRef(memory_map_ref="bad name"),
        MemoryRemapRef(memory_remap_ref="bad name"),
    )
    for suffix in ("ByName", "ID"):
        with pytest.raises(TgiError):
            getattr(api, "getAliasOf" + kind + "Ref" + suffix)(get_handle(owner))
    owner.address_block_ref = RegisterRef(register_ref="foreign")
    with pytest.raises(TgiError):
        api.getAliasOfAddressBlockRefID(get_handle(owner))


def context():
    owner = alias()
    owner.address_space_ref_or_memory_map_ref_or_memory_remap_ref = (
        FieldType.AliasOf.MemoryMapRef(memory_map_ref="target_map"),
        MemoryRemapRef(memory_remap_ref="selected"),
    )
    # Deeper qualifiers refer to a field path, not ancestors of the remap itself.
    owner.bank_ref = (BankRef(bank_ref="deep_bank"),)
    owner.address_block_ref = AddressBlockRef(address_block_ref="deep_block")
    owner.register_ref = RegisterRef(register_ref="deep_register")
    field = FieldType(name="source", bit_offset=UnsignedIntExpression(value="0"), choice=[owner])
    register = AddressBlockType.Register(
        name="source_reg",
        address_offset=UnsignedLongintExpression(value="0"),
        choice=[UnsignedPositiveIntExpression(value="8"), field],
    )
    block = AddressBlock(
        name="source_block",
        base_address=BaseAddress(value="0"),
        choice=[UnsignedPositiveLongintExpression(value="16"), UnsignedPositiveIntExpression(value="8"), register],
    )
    remap = MemoryRemap(name="selected", mode_ref=[ModeRef(value="active", priority=0)])
    target_map = MemoryMapType(name="target_map", choice=[remap])
    source_map = MemoryMapType(
        name="source_map", choice=[block, MemoryRemap(name="selected", mode_ref=[ModeRef(value="active", priority=1)])]
    )
    root = Component(
        vendor="test",
        library="component",
        name="alias",
        version="1",
        modes=ComponentType.Modes(mode=[ComponentType.Modes.Mode(name="active")]),
        memory_maps=MemoryMaps(memory_map=[source_map, target_map]),
    )
    registry.register(root, ("test", "component", "alias", "1"))
    return root, owner, remap, target_map


def test_remap_target_is_distinct_from_wrapper_and_uses_only_ancestor_qualifiers():
    _root, owner, remap, _map = context()
    wrapper = owner.address_space_ref_or_memory_map_ref_or_memory_remap_ref[1]
    assert api.getAliasOfMemoryRemapRefID(get_handle(owner)) == get_handle(wrapper)
    assert api.getAliasOfMemoryRemapRefByID(get_handle(owner)) == get_handle(remap)
    assert resolve_handle(get_parent_info(get_handle(remap)).parent_handle) is _map
    owner.address_space_ref_or_memory_map_ref_or_memory_remap_ref[0].memory_map_ref = " target_map "
    wrapper.memory_remap_ref = " selected "
    remap.name = " selected "
    assert api.getAliasOfMemoryRemapRefByID(get_handle(owner)) == get_handle(remap)


def test_missing_ambiguous_and_detached_targets_leave_source_access_available():
    _root, owner, remap, map = context()
    wrapper = owner.address_space_ref_or_memory_map_ref_or_memory_remap_ref[1]
    wrapper.memory_remap_ref = "missing"
    with pytest.raises(TgiError) as error:
        api.getAliasOfMemoryRemapRefByID(get_handle(owner))
    assert error.value.fault_code == TgiFaultCode.NOT_FOUND
    assert api.getAliasOfMemoryRemapRefByName(get_handle(owner)) == "missing"
    assert api.getAliasOfMemoryRemapRefID(get_handle(owner)) == get_handle(wrapper)
    wrapper.memory_remap_ref = "selected"
    map.choice.append(MemoryRemap(name="selected", mode_ref=[ModeRef(value="active", priority=2)]))
    with pytest.raises(TgiError) as error:
        api.getAliasOfMemoryRemapRefByID(get_handle(owner))
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    detached = alias()
    detached.address_space_ref_or_memory_map_ref_or_memory_remap_ref = (
        FieldType.AliasOf.MemoryMapRef(memory_map_ref="target_map"),
        MemoryRemapRef(memory_remap_ref="selected"),
    )
    with pytest.raises(TgiError) as error:
        api.getAliasOfMemoryRemapRefByID(get_handle(detached))
    assert error.value.fault_code == TgiFaultCode.NOT_FOUND


def test_alias_schema_round_trip_and_parsed_target_scope():
    root, _owner, _remap, _map = context()
    xml = XmlDocument.serializer().render(root)
    schema = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))
    assert schema.validate(etree.fromstring(xml.encode())), schema.error_log
    parsed = XmlDocument.parser().from_string(xml, Component)
    registry.clear()
    registry.register(parsed, ("test", "component", "alias", "1"))
    source_map, target_map = parsed.memory_maps.memory_map
    alias_node = source_map.choice[0].choice[2].choice[1].choice[0]
    assert api.getAliasOfMemoryRemapRefByID(get_handle(alias_node)) == get_handle(target_map.choice[0])
    assert api.getAliasOfBankRefByNames(get_handle(alias_node)) == ["deep_bank"]
    assert schema.validate(etree.fromstring(XmlDocument.serializer().render(parsed).encode()))


@pytest.mark.parametrize(
    "choice",
    [
        (FieldType.AliasOf.AddressSpaceRef(address_space_ref="space"),),
        (FieldType.AliasOf.MemoryMapRef(memory_map_ref="map"),),
    ],
)
def test_valid_choices_without_remap_do_not_invent_source_or_target(choice):
    owner = alias()
    owner.address_space_ref_or_memory_map_ref_or_memory_remap_ref = choice
    for op in (api.getAliasOfMemoryRemapRefByID, api.getAliasOfMemoryRemapRefByName, api.getAliasOfMemoryRemapRefID):
        assert op(get_handle(owner)) is None
    expected = "map" if isinstance(choice[0], FieldType.AliasOf.MemoryMapRef) else None
    assert api.getAliasOfMemoryMapRefByName(get_handle(owner)) == expected
    assert owner.address_space_ref_or_memory_map_ref_or_memory_remap_ref is choice

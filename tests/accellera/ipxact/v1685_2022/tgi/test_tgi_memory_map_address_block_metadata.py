"""Address-block child handles, defaults and referenced definition metadata."""

from inspect import signature

import pytest

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
    AddressBlock,
    AddressBlockDefinitions,
    AddressBlockRef,
    AddressBlockType,
    Array,
    BankedBlockType,
    BaseAddress,
    Component,
    ComponentType,
    ConfigurableLibraryRefType,
    Dim,
    ExternalTypeDefinitions,
    Index,
    Indices,
    MemoryMaps,
    MemoryMapType,
    ModeRef,
    RegisterFile,
    TypeDefinitions,
    UnsignedLongintExpression,
    UnsignedPositiveIntExpression,
    UnsignedPositiveLongintExpression,
    UsageType,
    Volatile,
)

BLOCK_MODELS = [AddressBlock, AddressBlockType, BankedBlockType]
GETTERS = [
    "getAddressBlockAccessPolicyIDs",
    "getAddressBlockArrayID",
    "getAddressBlockRegisterFileIDs",
    "getAddressBlockRegisterIDs",
    "getAddressBlockTypeIdentifier",
    "getAddressBlockUsage",
    "getAddressBlockVolatility",
]


@pytest.fixture(autouse=True)
def isolated_registry():
    registry.clear()
    yield
    registry.clear()


def register(model, name):
    return model(name=name, address_offset=UnsignedLongintExpression(value="0"), choice=[])


def content(model=AddressBlock):
    r, w = UnsignedPositiveLongintExpression(value="256"), UnsignedPositiveIntExpression(value="32")
    if model is BankedBlockType:
        return model(name="block", range=r, width=w)
    return model(name="block", base_address=BaseAddress(value="0"), choice=(r, w))


def populate(owner, *, regs=(), files=(), usage=None, volatile=None, policies=None, identifier=None):
    if isinstance(owner, AddressBlockType):
        values = list(owner.choice)
        values += [identifier] if identifier is not None else []
        values += ([usage] if usage is not None else []) + ([volatile] if volatile is not None else [])
        values += ([policies] if policies is not None else []) + list(files) + list(regs)
        owner.choice = tuple(values)
    else:
        owner.register_or_register_file = tuple([*files, *regs])
        owner.usage, owner.volatile, owner.access_policies = usage, volatile, policies
        if isinstance(owner, AddressBlockDefinitions.AddressBlockDefinition):
            owner.type_identifier = identifier


@pytest.mark.parametrize("model", BLOCK_MODELS)
def test_direct_register_and_file_ids_preserve_order_and_do_not_list_nested_registers(model):
    owner = content(model)
    reg_type = BankedBlockType.Register if model is BankedBlockType else AddressBlockType.Register
    first, second = register(reg_type, "first"), register(reg_type, "second")
    nested = register(RegisterFile.Register, "nested")
    file = RegisterFile(name="file", address_offset=UnsignedLongintExpression(value="4"), choice=(nested,))
    populate(owner, regs=(first, second), files=(file,))
    original = owner.choice if model is not BankedBlockType else owner.register_or_register_file
    assert api.getAddressBlockRegisterIDs(get_handle(owner)) == [get_handle(first), get_handle(second)]
    assert api.getAddressBlockRegisterFileIDs(get_handle(owner)) == [get_handle(file)]
    assert get_handle(nested) not in api.getAddressBlockRegisterIDs(get_handle(owner))
    assert (owner.choice if model is not BankedBlockType else owner.register_or_register_file) is original
    info = get_parent_info(get_handle(first))
    assert resolve_handle(info.parent_handle) is owner
    assert info.path == (("register_or_register_file",) if model is BankedBlockType else ("choice",))
    assert resolve_handle(get_parent_info(get_handle(nested)).parent_handle) is file


@pytest.mark.parametrize("model", BLOCK_MODELS)
def test_access_policy_ids_refer_to_policies_and_preserve_wrapper_and_descendants(model):
    owner = content(model)
    first = AccessPolicies.AccessPolicy(id="first", mode_ref=(ModeRef(value="active", priority=0),))
    second = AccessPolicies.AccessPolicy(id="second")
    holder = AccessPolicies(access_policy=(first, second))
    populate(owner, policies=holder)
    assert api.getAddressBlockAccessPolicyIDs(get_handle(owner)) == [get_handle(first), get_handle(second)]
    assert holder.access_policy == (first, second) and first.id == "first"
    assert resolve_handle(get_parent_info(get_handle(first)).parent_handle) is holder
    assert resolve_handle(get_parent_info(get_handle(holder)).parent_handle) is owner
    assert resolve_handle(get_parent_info(get_handle(first.mode_ref[0])).parent_handle) is first


@pytest.mark.parametrize("model", BLOCK_MODELS)
def test_usage_default_from_direct_and_nested_registers_and_explicit_values(model):
    owner = content(model)
    assert api.getAddressBlockUsage(get_handle(owner)) == "reserved"
    empty = RegisterFile(name="empty", address_offset=UnsignedLongintExpression(value="0"))
    populate(owner, files=(empty,))
    assert api.getAddressBlockUsage(get_handle(owner)) == "reserved"
    empty.choice = (register(RegisterFile.Register, "nested"),)
    assert api.getAddressBlockUsage(get_handle(owner)) == "register"
    for usage in UsageType:
        owner = content(model)
        populate(owner, usage=usage)
        before = get_parent_info(get_handle(usage))
        assert api.getAddressBlockUsage(get_handle(owner)) == usage.value
        assert get_parent_info(get_handle(usage)) == before


@pytest.mark.parametrize("model", BLOCK_MODELS)
def test_volatility_absence_and_explicit_false_true_preserve_handle(model):
    owner = content(model)
    assert api.getAddressBlockVolatility(get_handle(owner)) is None
    for value in (False, True):
        owner = content(model)
        node = Volatile(value=value)
        populate(owner, volatile=node)
        handle = get_handle(node)
        assert api.getAddressBlockVolatility(get_handle(owner)) is value
        assert resolve_handle(handle) is node
        node.value = "false"
        with pytest.raises(TgiError) as error:
            api.getAddressBlockVolatility(get_handle(owner))
        assert error.value.fault_code == TgiFaultCode.INVALID_ID


def test_identifier_normalization_duplicate_and_banked_absence():
    owner = content()
    assert api.getAddressBlockTypeIdentifier(get_handle(owner)) is None
    populate(owner, identifier="  blockType  ")
    original = owner.choice
    assert api.getAddressBlockTypeIdentifier(get_handle(owner)) == "blockType"
    assert owner.choice is original and "  blockType  " in original
    owner.choice += ("duplicate",)
    with pytest.raises(TgiError) as error:
        api.getAddressBlockTypeIdentifier(get_handle(owner))
    assert error.value.fault_code == TgiFaultCode.INVALID_ID
    owner = content()
    populate(owner, identifier="bad name")
    with pytest.raises(TgiError):
        api.getAddressBlockTypeIdentifier(get_handle(owner))
    assert api.getAddressBlockTypeIdentifier(get_handle(content(BankedBlockType))) is None


def test_local_array_ownership_and_optional_absence():
    owner = content()
    assert api.getAddressBlockArrayID(get_handle(owner)) is None
    array = Array(dim=(Dim(value="2"),))
    owner.array = array
    assert api.getAddressBlockArrayID(get_handle(owner)) == get_handle(array)
    assert resolve_handle(get_parent_info(get_handle(array)).parent_handle) is owner
    assert resolve_handle(get_parent_info(get_handle(array.dim[0])).parent_handle) is array
    assert api.getAddressBlockArrayID(get_handle(content(BankedBlockType))) is None
    owner.array = Indices(index=[])
    with pytest.raises(TgiError):
        api.getAddressBlockArrayID(get_handle(owner))


def test_ref_index_ids_preserve_raw_sources_order_tuple_and_parsed_ownership():
    first, second = Index(value="PARAM"), Index(value="3")
    indices = Indices(index=(first, second))
    ref = AddressBlockRef(address_block_ref="block", indices=indices)
    assert api.getAddressBlockRefIndexIDs(get_handle(ref)) == [get_handle(first), get_handle(second)]
    assert indices.index == (first, second) and first.value == "PARAM"
    assert resolve_handle(get_parent_info(get_handle(indices)).parent_handle) is ref
    assert resolve_handle(get_parent_info(get_handle(first)).parent_handle) is indices
    parsed = XmlDocument.parser().from_string(XmlDocument.serializer().render(ref), AddressBlockRef)
    assert [resolve_handle(handle).value for handle in api.getAddressBlockRefIndexIDs(get_handle(parsed))] == [
        "PARAM",
        "3",
    ]
    ref.indices = None
    assert api.getAddressBlockRefIndexIDs(get_handle(ref)) == []
    ref.indices = Indices(index=(ModeRef(value="bad", priority=0),))
    with pytest.raises(TgiError) as error:
        api.getAddressBlockRefIndexIDs(get_handle(ref))
    assert error.value.fault_code == TgiFaultCode.INVALID_ID


def test_referenced_definition_children_metadata_and_usage_defaults():
    target_vlnv, owner_vlnv = ("test", "types", "metadata", "1"), ("test", "components", "metadata", "1")
    definition = AddressBlockDefinitions.AddressBlockDefinition(
        name="definition",
        range=UnsignedPositiveLongintExpression(value="256"),
        width=UnsignedPositiveIntExpression(value="32"),
    )
    reg = register(AddressBlockDefinitions.AddressBlockDefinition.Register, "defined")
    policy = AccessPolicies.AccessPolicy(id="defined-policy")
    populate(definition, regs=(reg,), policies=AccessPolicies(access_policy=(policy,)), identifier="typeName")
    target = TypeDefinitions(
        vendor=target_vlnv[0],
        library=target_vlnv[1],
        name=target_vlnv[2],
        version=target_vlnv[3],
        address_block_definitions=AddressBlockDefinitions(address_block_definition=[definition]),
    )
    ref = AddressBlockType.AddressBlockDefinitionRef(value="definition", type_definitions="imported")
    owner_block = AddressBlock(
        name="block", base_address=BaseAddress(value="0"), choice=(ref,), array=Array(dim=[Dim(value="2")])
    )
    declaration = ExternalTypeDefinitions(
        name="imported",
        type_definitions_ref=ConfigurableLibraryRefType(
            vendor=target_vlnv[0], library=target_vlnv[1], name=target_vlnv[2], version=target_vlnv[3]
        ),
    )
    owner = Component(
        vendor=owner_vlnv[0],
        library=owner_vlnv[1],
        name=owner_vlnv[2],
        version=owner_vlnv[3],
        type_definitions=ComponentType.TypeDefinitions(external_type_definitions=[declaration]),
        memory_maps=MemoryMaps(memory_map=[MemoryMapType(name="map", choice=[owner_block])]),
    )
    registry.register(owner, owner_vlnv)
    registry.register(target, target_vlnv)
    handle = get_handle(owner_block)
    assert api.getAddressBlockRegisterIDs(handle) == [get_handle(reg)]
    assert api.getAddressBlockRegisterFileIDs(handle) == []
    assert api.getAddressBlockAccessPolicyIDs(handle) == [get_handle(policy)]
    assert api.getAddressBlockTypeIdentifier(handle) == "typeName"
    assert api.getAddressBlockUsage(handle) == "register"
    assert api.getAddressBlockVolatility(handle) is None
    definition.volatile = Volatile(value=False)
    assert api.getAddressBlockVolatility(handle) is False
    assert api.getAddressBlockArrayID(handle) == get_handle(owner_block.array)
    assert resolve_handle(get_parent_info(get_handle(reg)).parent_handle) is definition
    assert owner_block.choice == (ref,)


@pytest.mark.parametrize("model", BLOCK_MODELS)
def test_absent_collections_and_invalid_members(model):
    owner = content(model)
    assert api.getAddressBlockAccessPolicyIDs(get_handle(owner)) == []
    assert api.getAddressBlockRegisterIDs(get_handle(owner)) == []
    assert api.getAddressBlockRegisterFileIDs(get_handle(owner)) == []
    holder = AccessPolicies(access_policy=(object(),))
    populate(owner, policies=holder)
    with pytest.raises(TgiError) as error:
        api.getAddressBlockAccessPolicyIDs(get_handle(owner))
    assert error.value.fault_code == TgiFaultCode.INVALID_ID
    if model is BankedBlockType:
        owner.register_or_register_file = (AddressBlockRef(address_block_ref="wrong"),)
        with pytest.raises(TgiError):
            api.getAddressBlockRegisterIDs(get_handle(owner))


def test_exact_signatures_and_strict_invalid_handles():
    for name in [*GETTERS, "getAddressBlockRefIndexIDs"]:
        op = getattr(api, name)
        expected = "addressBlockRefID" if name == "getAddressBlockRefIndexIDs" else "addressBlockID"
        assert list(signature(op).parameters) == [expected]
        for invalid in (None, [], {}, "missing", get_handle(ModeRef(value="wrong", priority=0))):
            with pytest.raises(TgiError) as error:
                op(invalid)
            assert error.value.fault_code == TgiFaultCode.INVALID_ID

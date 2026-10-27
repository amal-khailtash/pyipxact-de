"""IEEE 1685-2022 memory-map broadcast and register-field edits."""

import inspect
from collections.abc import Iterator

import pytest
from lxml import etree

from amal.eda.accellera.ipxact.v1685_2022.tgi import memory_map as api
from amal.eda.accellera.ipxact.v1685_2022.tgi.component import _register_graph
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import (
    TgiError,
    TgiFaultCode,
    get_handle,
    get_parent_info,
    register_parent,
    registry,
    resolve_handle,
)
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import (
    Access,
    AccessType,
    AddressBlock,
    AddressBlockDefinitions,
    AddressBlockType,
    AddressSpaces,
    AddressUnitBits,
    AlternateRegisters,
    BankedBlockType,
    BaseAddress,
    BitStride,
    Component,
    Dim,
    FieldDefinitions,
    FieldRef,
    FieldType,
    MemoryMaps,
    MemoryMapType,
    RegisterFile,
    RegisterFileDefinitions,
    UnsignedIntExpression,
    UnsignedLongintExpression,
    UnsignedPositiveIntExpression,
    UnsignedPositiveLongintExpression,
    UsageType,
)

_SCHEMA = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))
_U32_MAX = (1 << 32) - 1
_U64_MAX = (1 << 64) - 1


@pytest.fixture(autouse=True)
def clean_registry() -> Iterator[None]:
    registry.clear()
    yield
    registry.clear()


def _broadcast_models():
    return (
        FieldType.FieldAccessPolicies.FieldAccessPolicy.Broadcasts.BroadcastTo,
        FieldDefinitions.FieldDefinition.FieldAccessPolicies.FieldAccessPolicy.Broadcasts.BroadcastTo,
    )


def _broadcast_field(broadcast_type, choice=None):
    broadcast = broadcast_type(
        address_space_ref_or_memory_map_ref_or_memory_remap_ref=list(choice or ()),
        field_ref=FieldRef(field_ref="status"),
    )
    if broadcast_type is _broadcast_models()[0]:
        policy = FieldType.FieldAccessPolicies.FieldAccessPolicy(
            choice=[Access(value=AccessType.READ_WRITE)],
            broadcasts=FieldType.FieldAccessPolicies.FieldAccessPolicy.Broadcasts(broadcast_to=[broadcast]),
        )
        policies = FieldType.FieldAccessPolicies(field_access_policy=[policy])
        field = FieldType(
            name="status",
            bit_offset=UnsignedIntExpression(value="0"),
            choice=[UnsignedPositiveIntExpression(value="8"), policies],
        )
    else:
        policy = FieldDefinitions.FieldDefinition.FieldAccessPolicies.FieldAccessPolicy(
            choice=[Access(value=AccessType.READ_WRITE)],
            broadcasts=FieldDefinitions.FieldDefinition.FieldAccessPolicies.FieldAccessPolicy.Broadcasts(
                broadcast_to=[broadcast]
            ),
        )
        field = FieldDefinitions.FieldDefinition(
            name="status",
            bit_width=UnsignedPositiveIntExpression(value="8"),
            field_access_policies=FieldDefinitions.FieldDefinition.FieldAccessPolicies(field_access_policy=[policy]),
        )
    return field, broadcast


def _inline_register(field, *, size="32"):
    register = AddressBlockType.Register(
        name="control",
        address_offset=UnsignedLongintExpression(value="0"),
        choice=[UnsignedPositiveIntExpression(value=size), field],
    )
    _register_graph(register)
    return register


def _component(field, *, size="32"):
    register = AddressBlockType.Register(
        name="control",
        address_offset=UnsignedLongintExpression(value="0"),
        choice=[UnsignedPositiveIntExpression(value=size), field],
    )
    block = AddressBlock(
        name="registers",
        base_address=BaseAddress(value="0"),
        choice=[
            UnsignedPositiveLongintExpression(value="256"),
            UnsignedPositiveIntExpression(value="32"),
            UsageType.REGISTER,
            register,
        ],
    )
    return Component(
        vendor="test",
        library="library",
        name="fieldBroadcastEdits",
        version="1",
        address_spaces=AddressSpaces(
            address_space=[
                AddressSpaces.AddressSpace(
                    name="cpu_space",
                    range=UnsignedPositiveLongintExpression(value="256"),
                    width=UnsignedPositiveIntExpression(value="32"),
                    address_unit_bits=AddressUnitBits(value="8"),
                )
            ]
        ),
        memory_maps=MemoryMaps(
            memory_map=[MemoryMapType(name="peripheral", choice=[block, AddressUnitBits(value="8")])]
        ),
    )


@pytest.mark.parametrize(
    "name,parameters",
    [
        ("setBroadcastToAddressSpaceRef", ["broadcastToID", "addressSpaceRef"]),
        ("setRegisterFieldArray", ["registerFieldID", "value"]),
        ("setRegisterFieldBitOffset", ["registerFieldID", "bitOffset"]),
    ],
)
def test_signatures_are_the_annex_f_contract(name, parameters):
    assert list(inspect.signature(getattr(api, name)).parameters) == parameters


@pytest.mark.parametrize("broadcast_type", _broadcast_models())
def test_broadcast_address_space_setter_replaces_map_and_remap_branch(broadcast_type):
    _field, broadcast = _broadcast_field(
        broadcast_type,
        [broadcast_type.MemoryMapRef(memory_map_ref="map"), api.MemoryRemapRef(memory_remap_ref="remap")],
    )
    if broadcast_type is _broadcast_models()[0]:
        _inline_register(_field)
        broadcast_id = get_handle(broadcast)
    else:
        root = FieldDefinitions(field_definition=[_field])
        registry.register(root, ("test", "types", "fields", "1"))
        broadcast_id = get_handle(broadcast)
    _register_graph(_field)
    old_choice = broadcast.address_space_ref_or_memory_map_ref_or_memory_remap_ref
    old_children = tuple(old_choice)
    old_ids = [get_handle(child) for child in old_children]

    assert api.setBroadcastToAddressSpaceRef(broadcast_id, "  cpu_space  ") is True
    selected = broadcast.address_space_ref_or_memory_map_ref_or_memory_remap_ref
    assert len(selected) == 1
    assert type(selected[0]) is broadcast_type.AddressSpaceRef
    assert selected[0].address_space_ref == "cpu_space"
    assert all(resolve_handle(handle) is None for handle in old_ids)
    with pytest.raises(TgiError) as error:
        api.setBroadcastToAddressSpaceRef(broadcast_id, "bad name")
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert broadcast.address_space_ref_or_memory_map_ref_or_memory_remap_ref is selected
    assert api.setBroadcastToAddressSpaceRef(broadcast_id, "next_space") is True
    assert broadcast.address_space_ref_or_memory_map_ref_or_memory_remap_ref[0] is selected[0]
    assert selected[0].address_space_ref == "next_space"


def test_broadcast_setter_round_trips_and_rejects_unowned_or_competing_models():
    broadcast_type = _broadcast_models()[0]
    field, broadcast = _broadcast_field(
        broadcast_type,
        [broadcast_type.MemoryMapRef(memory_map_ref="peripheral")],
    )
    root = _component(field)
    xml = XmlDocument.serializer().render(root)
    _SCHEMA.assertValid(etree.fromstring(xml.encode()))
    loaded = XmlDocument.parser().from_string(xml, Component)
    registry.register(loaded, (loaded.vendor, loaded.library, loaded.name, loaded.version))
    parsed_field = loaded.memory_maps.memory_map[0].choice[0].choice[3].choice[1]
    parsed_broadcast = parsed_field.choice[1].field_access_policy[0].broadcasts.broadcast_to[0]
    broadcast_id = get_handle(parsed_broadcast)
    assert get_parent_info(broadcast_id) is None

    assert api.setBroadcastToAddressSpaceRef(broadcast_id, "cpu_space") is True
    output = XmlDocument.serializer().render(loaded)
    _SCHEMA.assertValid(etree.fromstring(output.encode()))
    reparsed = XmlDocument.parser().from_string(output, Component)
    path = reparsed.memory_maps.memory_map[0].choice[0].choice[3].choice[1]
    child = path.choice[1].field_access_policy[0].broadcasts.broadcast_to[0]
    assert child.address_space_ref_or_memory_map_ref_or_memory_remap_ref[0].address_space_ref == "cpu_space"

    orphan = broadcast_type(field_ref=FieldRef(field_ref="status"))
    for bad in (None, [], {}, 1, get_handle(orphan)):
        with pytest.raises(TgiError) as error:
            api.setBroadcastToAddressSpaceRef(bad, "space")
        assert error.value.fault_code == TgiFaultCode.INVALID_ID

    competing = FieldType.FieldAccessPolicies.FieldAccessPolicy.Broadcasts.BroadcastTo(
        field_ref=FieldRef(field_ref="status")
    )
    first, _ = _broadcast_field(broadcast_type)
    second, _ = _broadcast_field(broadcast_type)
    first_holder = first.choice[-1] if isinstance(first, FieldType) else first.field_access_policies
    second_holder = second.choice[-1] if isinstance(second, FieldType) else second.field_access_policies
    first_policy = first_holder.field_access_policy[0]
    second_policy = second_holder.field_access_policy[0]
    first_policy.broadcasts.broadcast_to = [competing]
    second_policy.broadcasts.broadcast_to = [competing]
    _register_graph(first)
    _register_graph(second)
    registry.register(first, ("test", "fields", "first", "1"))
    registry.register(second, ("test", "fields", "second", "1"))
    with pytest.raises(TgiError) as error:
        api.setBroadcastToAddressSpaceRef(get_handle(competing), "space")
    assert error.value.fault_code == TgiFaultCode.INVALID_ID


@pytest.mark.parametrize(
    "register_type",
    [
        AddressBlockType.Register,
        BankedBlockType.Register,
        RegisterFile.Register,
        RegisterFileDefinitions.RegisterFileDefinition.Register,
        AddressBlockDefinitions.AddressBlockDefinition.Register,
    ],
)
def test_field_array_setter_supports_schema_register_owners_and_preserves_existing_dimensions(register_type):
    stride = BitStride(value="6")
    dims = (Dim(value="2", index_var="row"), Dim(value="3", index_var="column"))
    array = FieldType.Array(dim=dims, bit_stride=stride)
    field = FieldType(name="matrix", bit_offset=UnsignedIntExpression(value="0"), array=array)
    register = register_type(
        name="control",
        address_offset=UnsignedLongintExpression(value="0"),
        choice=[UnsignedPositiveIntExpression(value="32"), field],
    )
    _register_graph(register)
    field_id = get_handle(field)
    array_id, first_id, second_id, stride_id = map(get_handle, (array, *dims, stride))

    assert api.setRegisterFieldArray(field_id, "  rows + 1 ") is True
    assert field.array is array and get_handle(field.array) == array_id
    assert field.array.dim[0] is dims[0] and dims[0].value == "  rows + 1 "
    assert dims[0].index_var == "row"
    assert field.array.dim[1] is dims[1] and dims[1].value == "3"
    assert field.array.bit_stride is stride
    assert [get_handle(child) for child in field.array.dim] == [first_id, second_id]
    assert get_handle(field.array.bit_stride) == stride_id


def test_field_array_creation_u64_bounds_wrong_handles_and_xml_round_trip():
    field = FieldType(
        name="items",
        bit_offset=UnsignedIntExpression(value="0"),
        choice=[UnsignedPositiveIntExpression(value="8")],
    )
    register = _inline_register(field, size="8")
    field_id = get_handle(field)
    assert api.setRegisterFieldArray(field_id, str(_U64_MAX)) is True
    array = field.array
    assert type(array) is FieldType.Array
    assert len(array.dim) == 1 and type(array.dim[0]) is Dim
    dim = array.dim[0]
    array_id, dim_id = get_handle(array), get_handle(dim)
    assert dim.value == str(_U64_MAX)
    assert get_parent_info(array_id).parent_handle == field_id
    assert get_parent_info(dim_id).parent_handle == array_id
    for source in ("0", str(_U64_MAX + 1), "-1", "", None, [], {}):
        with pytest.raises(TgiError) as error:
            api.setRegisterFieldArray(field_id, source)
        assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
        assert field.array is array and dim.value == str(_U64_MAX)

    root = _component(field, size="8")
    xml = XmlDocument.serializer().render(root)
    _SCHEMA.assertValid(etree.fromstring(xml.encode()))
    loaded = XmlDocument.parser().from_string(xml, Component)
    loaded_field = loaded.memory_maps.memory_map[0].choice[0].choice[3].choice[1]
    assert loaded_field.array.dim[0].value == str(_U64_MAX)
    assert loaded_field.array.dim[0].index_var is None

    _ = register
    for bad in (None, [], {}, 1, get_handle([])):
        with pytest.raises(TgiError) as error:
            api.setRegisterFieldArray(bad, "2")
        assert error.value.fault_code == TgiFaultCode.INVALID_ID


def test_rootless_direct_parent_link_recovers_unprimed_field_and_array_children():
    stride = BitStride(value="2")
    array = FieldType.Array(dim=(Dim(value="2", index_var="i"),), bit_stride=stride)
    field = FieldType(
        name="items",
        bit_offset=UnsignedIntExpression(value="0", minimum=0, maximum=31),
        array=array,
        choice=[UnsignedPositiveIntExpression(value="4")],
    )
    register = AddressBlockType.Register(
        name="control",
        address_offset=UnsignedLongintExpression(value="0"),
        choice=[UnsignedPositiveIntExpression(value="8"), field],
    )
    register_parent(field, register, ("choice",), "list")
    field_id = get_handle(field)
    offset_id = get_handle(field.bit_offset)
    array_id = get_handle(array)
    dim_id = get_handle(array.dim[0])
    stride_id = get_handle(stride)

    assert api.setRegisterFieldArray(field_id, "3") is True
    assert array.dim[0].value == "3" and array.dim[0].index_var == "i"
    assert get_handle(array) == array_id and get_handle(array.dim[0]) == dim_id
    assert get_handle(array.bit_stride) == stride_id
    assert get_parent_info(array_id).parent_handle == field_id
    assert get_parent_info(dim_id).parent_handle == array_id
    assert get_parent_info(stride_id).parent_handle == array_id
    assert api.setRegisterFieldBitOffset(field_id, "4") is True
    assert field.bit_offset.value == "4"
    assert get_parent_info(offset_id).parent_handle == field_id


def test_field_bit_offset_preserves_expression_wrapper_and_checks_known_containment():
    offset = UnsignedIntExpression(value="0", minimum=0, maximum=31)
    field = FieldType(
        name="lower",
        bit_offset=offset,
        choice=[UnsignedPositiveIntExpression(value="4")],
    )
    register = _inline_register(field, size="8")
    field_id, offset_id = get_handle(field), get_handle(offset)
    assert api.setRegisterFieldBitOffset(field_id, "4") is True
    assert field.bit_offset is offset and get_handle(field.bit_offset) == offset_id
    assert offset.value == "4" and offset.minimum == 0 and offset.maximum == 31
    before = offset.value
    with pytest.raises(TgiError) as error:
        api.setRegisterFieldBitOffset(field_id, "5")
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert offset.value == before

    assert api.setRegisterFieldBitOffset(field_id, "offset_parameter") is True
    assert offset.value == "offset_parameter"
    for source in ("-1", str(_U32_MAX + 1), "", "unknown +"):
        with pytest.raises(TgiError) as error:
            api.setRegisterFieldBitOffset(field_id, source)
        assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
        assert offset.value == "offset_parameter"
    assert get_parent_info(offset_id).parent_handle == field_id
    _ = register

    root = _component(field, size="8")
    xml = XmlDocument.serializer().render(root)
    _SCHEMA.assertValid(etree.fromstring(xml.encode()))
    loaded = XmlDocument.parser().from_string(xml, Component)
    loaded_field = loaded.memory_maps.memory_map[0].choice[0].choice[3].choice[1]
    assert loaded_field.bit_offset.value == "offset_parameter"


def test_field_offset_skips_reference_branches_and_rejects_forged_or_duplicate_owners():
    referenced = FieldType.FieldDefinitionRef(value="shared", type_definitions="types")
    field = FieldType(
        name="external",
        bit_offset=UnsignedIntExpression(value="0"),
        choice=[referenced],
    )
    register = _inline_register(field, size="4")
    field_id = get_handle(field)
    assert api.setRegisterFieldBitOffset(field_id, "4") is True
    assert field.choice == [referenced]

    alias = FieldType.AliasOf(field_ref=FieldRef(field_ref="target"))
    alias_field = FieldType(
        name="aliased",
        bit_offset=UnsignedIntExpression(value="0"),
        choice=[alias],
    )
    _inline_register(alias_field, size="4")
    assert api.setRegisterFieldBitOffset(get_handle(alias_field), "4") is True
    assert alias_field.choice == [alias]

    duplicate_field = FieldType(
        name="duplicate",
        bit_offset=UnsignedIntExpression(value="0"),
        choice=[UnsignedPositiveIntExpression(value="1")],
    )
    malformed_register = AddressBlockType.Register(
        name="bad",
        address_offset=UnsignedLongintExpression(value="0"),
        choice=[UnsignedPositiveIntExpression(value="8"), duplicate_field, duplicate_field],
    )
    _register_graph(malformed_register)
    with pytest.raises(TgiError) as error:
        api.setRegisterFieldBitOffset(get_handle(duplicate_field), "1")
    assert error.value.fault_code == TgiFaultCode.INVALID_ID

    foreign = AddressBlockType.Register(
        name="foreign",
        address_offset=UnsignedLongintExpression(value="0"),
        choice=[UnsignedPositiveIntExpression(value="8")],
    )
    register_parent(field, foreign, ("choice",), "list")
    with pytest.raises(TgiError) as error:
        api.setRegisterFieldBitOffset(field_id, "2")
    assert error.value.fault_code == TgiFaultCode.INVALID_ID
    _ = register


def test_field_array_containment_checks_the_first_field_instance():
    field = FieldType(
        name="arrayElement",
        bit_offset=UnsignedIntExpression(value="0"),
        array=FieldType.Array(dim=[Dim(value="4")], bit_stride=BitStride(value="4")),
        choice=[UnsignedPositiveIntExpression(value="4")],
    )
    _inline_register(field, size="8")
    field_id = get_handle(field)
    assert api.setRegisterFieldBitOffset(field_id, "4") is True
    with pytest.raises(TgiError) as error:
        api.setRegisterFieldBitOffset(field_id, "5")
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert field.bit_offset.value == "4"


def test_alternate_register_field_offset_uses_the_owning_register_size():
    field = FieldType(
        name="alternateField",
        bit_offset=UnsignedIntExpression(value="0"),
        choice=[UnsignedPositiveIntExpression(value="4")],
    )
    alternate = AlternateRegisters.AlternateRegister(
        name="alternate",
        field_value=[field],
    )
    register = AddressBlockType.Register(
        name="control",
        address_offset=UnsignedLongintExpression(value="0"),
        choice=[UnsignedPositiveIntExpression(value="8")],
        alternate_registers=AlternateRegisters(alternate_register=[alternate]),
    )
    _register_graph(register)
    assert api.setRegisterFieldBitOffset(get_handle(field), "4") is True
    with pytest.raises(TgiError) as error:
        api.setRegisterFieldBitOffset(get_handle(field), "5")
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT

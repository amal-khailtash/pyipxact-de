"""Register and registerFile array operations from IEEE 1685-2022 F.7.58."""

from inspect import signature

import pytest
from lxml import etree

from amal.eda.accellera.ipxact.v1685_2022.tgi import memory_map as api
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
    AddressBlock,
    AddressBlockDefinitions,
    AddressBlockType,
    AddressUnitBits,
    Array,
    BankedBlockType,
    BaseAddress,
    Component,
    Dim,
    FieldType,
    MemoryMaps,
    MemoryMapType,
    RegisterFile,
    RegisterFileDefinitions,
    Stride,
    UnsignedIntExpression,
    UnsignedLongintExpression,
    UnsignedPositiveIntExpression,
    UnsignedPositiveLongintExpression,
)

_SCHEMA = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))
_REGISTER_TYPES = (
    AddressBlockType.Register,
    BankedBlockType.Register,
    RegisterFile.Register,
    AddressBlockDefinitions.AddressBlockDefinition.Register,
    RegisterFileDefinitions.RegisterFileDefinition.Register,
)


@pytest.fixture(autouse=True)
def isolate_registry():
    registry.clear()
    yield
    registry.clear()


def _register(register_type=AddressBlockType.Register, *, array=None, name="r"):
    return register_type(
        name=name,
        address_offset=UnsignedLongintExpression(value="0"),
        array=array,
        choice=[
            UnsignedPositiveIntExpression(value="32"),
            FieldType(
                name="data",
                bit_offset=UnsignedIntExpression(value="0"),
                choice=[UnsignedPositiveIntExpression(value="1")],
            ),
        ],
    )


def _register_file(*, array=None, choice=None, name="rf"):
    return RegisterFile(
        name=name,
        address_offset=UnsignedLongintExpression(value="0"),
        array=array,
        choice=choice if choice is not None else [UnsignedPositiveLongintExpression(value="64")],
    )


def _owner_with_child(child, owner_kind: str):
    if owner_kind == "address_block":
        owner = AddressBlock(
            name="block",
            base_address=BaseAddress(value="0"),
            choice=[UnsignedPositiveLongintExpression(value="256"), UnsignedPositiveIntExpression(value="32"), child],
        )
        return owner, "choice"
    if owner_kind == "banked_block":
        owner = BankedBlockType(
            name="banked",
            range=UnsignedPositiveLongintExpression(value="256"),
            width=UnsignedPositiveIntExpression(value="32"),
            register_or_register_file=[child],
        )
        return owner, "register_or_register_file"
    if owner_kind == "register_file":
        owner = _register_file(choice=[UnsignedPositiveLongintExpression(value="64"), child], name="parent-rf")
        return owner, "choice"
    if owner_kind == "address_block_definition":
        owner = AddressBlockDefinitions.AddressBlockDefinition(
            name="block_definition",
            range=UnsignedPositiveLongintExpression(value="256"),
            width=UnsignedPositiveIntExpression(value="32"),
            register_or_register_file=[child],
        )
        return owner, "register_or_register_file"
    if owner_kind == "register_file_definition":
        owner = RegisterFileDefinitions.RegisterFileDefinition(
            name="rf_definition",
            range=UnsignedPositiveLongintExpression(value="64"),
            register_or_register_file=[child],
        )
        return owner, "register_or_register_file"
    raise AssertionError(owner_kind)


def _root_with_register_file(register_file: RegisterFile) -> Component:
    block = AddressBlock(
        name="block",
        base_address=BaseAddress(value="0"),
        choice=[
            UnsignedPositiveLongintExpression(value="256"),
            UnsignedPositiveIntExpression(value="32"),
            register_file,
        ],
    )
    return Component(
        vendor="test",
        library="memory",
        name="register_array_test",
        version="1",
        memory_maps=MemoryMaps(memory_map=[MemoryMapType(name="map", choice=[block, AddressUnitBits(value="8")])]),
    )


def _register_root(root: Component) -> None:
    registry.register(root, ("test", "memory", root.name, "1"))


def _assert_schema_valid(root: Component) -> str:
    xml = XmlDocument.serializer().render(root)
    assert _SCHEMA.validate(etree.fromstring(xml.encode())), _SCHEMA.error_log
    return xml


def test_exports_signatures_and_invalid_handles_match_annex_contracts():
    expected = {
        "removeRegisterArray": ["registerID"],
        "removeRegisterFileArray": ["registerFileID"],
        "setRegisterArray": ["registerID", "dimValue"],
        "setRegisterFileArray": ["registerFileID", "dimValue"],
    }
    for name, parameters in expected.items():
        operation = getattr(api, name)
        assert name in api.__all__
        assert list(signature(operation).parameters) == parameters
        args = ("invalid-handle", "2") if name.startswith("set") else ("invalid-handle",)
        with pytest.raises(TgiError) as error:
            operation(*args)
        assert error.value.fault_code == TgiFaultCode.INVALID_ID


@pytest.mark.parametrize("register_type", _REGISTER_TYPES)
def test_set_register_array_accepts_each_generated_register_element_scope(register_type):
    target = _register(register_type)
    owner_kind = {
        AddressBlockType.Register: "address_block",
        BankedBlockType.Register: "banked_block",
        RegisterFile.Register: "register_file",
        AddressBlockDefinitions.AddressBlockDefinition.Register: "address_block_definition",
        RegisterFileDefinitions.RegisterFileDefinition.Register: "register_file_definition",
    }[register_type]
    owner, path = _owner_with_child(target, owner_kind)
    target_id = get_handle(target)
    register_parent(target, owner, (path,), "list")

    assert api.setRegisterArray(target_id, "DEPTH + 1") is True
    assert target.array.dim[0].value == "DEPTH + 1"
    assert get_parent_info(target_id).parent_handle == get_handle(owner)


@pytest.mark.parametrize(
    "owner_kind",
    ("address_block", "banked_block", "register_file", "address_block_definition", "register_file_definition"),
)
def test_set_register_file_array_accepts_each_generated_register_file_scope(owner_kind):
    target = _register_file(name="target")
    owner, path = _owner_with_child(target, owner_kind)
    target_id = get_handle(target)
    register_parent(target, owner, (path,), "list")

    assert api.setRegisterFileArray(target_id, "WORDS") is True
    assert target.array.dim[0].value == "WORDS"
    assert get_parent_info(target_id).parent_handle == get_handle(owner)


def test_setters_preserve_existing_dimensions_metadata_stride_and_schema_round_trip():
    first_register_dim = Dim(value="4", id="register_dim", index_var="word")
    second_register_dim = Dim(value="2", id="register_second_dim", index_var="lane")
    register_stride = Stride(value="8", id="register_stride")
    first_file_dim = Dim(value="3", id="file_dim", index_var="instance")
    file_stride = Stride(value="32", id="file_stride")
    register = _register(
        RegisterFile.Register,
        array=Array(dim=[first_register_dim, second_register_dim], stride=register_stride),
        name="data",
    )
    register_file = _register_file(
        array=Array(dim=[first_file_dim], stride=file_stride),
        choice=[UnsignedPositiveLongintExpression(value="64"), register],
    )
    root = _root_with_register_file(register_file)
    _register_root(root)
    register_id, register_file_id = get_handle(register), get_handle(register_file)
    register_array_id, file_array_id = get_handle(register.array), get_handle(register_file.array)

    assert api.setRegisterArray(register_id, "5") is True
    assert api.setRegisterFileArray(register_file_id, "7") is True
    assert register.array.dim[0] is first_register_dim
    assert register.array.dim[0].value == "5"
    assert register.array.dim[0].id == "register_dim" and register.array.dim[0].index_var == "word"
    assert register.array.dim[1] is second_register_dim
    assert register.array.dim[1].value == "2" and register.array.dim[1].index_var == "lane"
    assert register.array.stride is register_stride and register_stride.value == "8"
    assert register_file.array.dim[0] is first_file_dim
    assert register_file.array.dim[0].id == "file_dim" and register_file.array.dim[0].index_var == "instance"
    assert register_file.array.stride is file_stride and file_stride.value == "32"
    assert get_handle(register.array) == register_array_id
    assert get_handle(register_file.array) == file_array_id

    xml = _assert_schema_valid(root)
    parsed = XmlDocument.parser().from_string(xml, Component)
    parsed_file = parsed.memory_maps.memory_map[0].choice[0].choice[2]
    assert [dimension.value for dimension in parsed_file.array.dim] == ["7"]
    assert parsed_file.array.dim[0].index_var == "instance"
    assert parsed_file.array.stride.value == "32"
    parsed_register = parsed_file.choice[1]
    assert [dimension.value for dimension in parsed_register.array.dim] == ["5", "2"]
    assert [dimension.index_var for dimension in parsed_register.array.dim] == ["word", "lane"]
    assert parsed_register.array.stride.value == "8"
    _assert_schema_valid(parsed)


@pytest.mark.parametrize(
    "setter,argument",
    ((api.setRegisterArray, "registerID"), (api.setRegisterFileArray, "registerFileID")),
)
def test_dimension_validation_is_positive_u64_and_invalid_inputs_are_atomic(setter, argument):
    if argument == "registerID":
        target = _register(array=Array(dim=[Dim(value="4", id="d", index_var="i")]))
        owner, path = _owner_with_child(target, "address_block")
    else:
        target = _register_file(array=Array(dim=[Dim(value="4", id="d", index_var="i")]))
        owner, path = _owner_with_child(target, "address_block")
    target_id = get_handle(target)
    register_parent(target, owner, (path,), "list")
    before = (target.array, target.array.dim[0], target.array.dim[0].value, target.array.dim[0].id)

    assert setter(target_id, str((1 << 64) - 1)) is True
    before_bad = (target.array, target.array.dim[0], target.array.dim[0].value, target.array.dim[0].id)
    for invalid in ("", "0", "-1", str(1 << 64), "1 +", None, 2):
        with pytest.raises(TgiError) as error:
            setter(target_id, invalid)
        assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
        assert (target.array, target.array.dim[0], target.array.dim[0].value, target.array.dim[0].id) == before_bad
    assert before[0] is target.array and before[1] is target.array.dim[0] and before[3] == "d"


def test_set_register_file_array_creates_owned_dim_and_preserves_existing_file_metadata():
    register_file = _register_file()
    owner, path = _owner_with_child(register_file, "address_block")
    register_file_id = get_handle(register_file)
    register_parent(register_file, owner, (path,), "list")

    assert api.setRegisterFileArray(register_file_id, "2 * COUNT") is True
    array = register_file.array
    assert isinstance(array, Array)
    assert array.dim[0].value == "2 * COUNT"
    assert get_parent_info(get_handle(array)).parent_handle == register_file_id
    assert get_parent_info(get_handle(array.dim[0])).path == ("dim",)


def test_remove_array_returns_false_when_absent_and_invalidates_the_complete_subtree():
    size = UnsignedPositiveIntExpression(value="32")
    field = _register().choice[1]
    register = _register(
        array=Array(dim=[Dim(value="4", id="first"), Dim(value="2", id="second")], stride=Stride(value="8"))
    )
    register.choice = [size, field]
    register_file = _register_file(array=Array(dim=[Dim(value="3")], stride=Stride(value="16")))
    owner, path = _owner_with_child(register, "address_block")
    register_parent(register, owner, (path,), "list")
    file_owner, file_path = _owner_with_child(register_file, "address_block")
    register_parent(register_file, file_owner, (file_path,), "list")

    register_array = register.array
    register_file_array = register_file.array
    subtree_ids = [
        get_handle(register_array),
        *(get_handle(dimension) for dimension in register_array.dim),
        get_handle(register_array.stride),
        get_handle(register_file_array),
        *(get_handle(dimension) for dimension in register_file_array.dim),
        get_handle(register_file_array.stride),
    ]

    assert api.removeRegisterArray(get_handle(register)) is True
    assert api.removeRegisterFileArray(get_handle(register_file)) is True
    assert register.array is None and register_file.array is None
    assert register.choice[0] is size and register.choice[1] is field
    assert all(resolve_handle(handle) is None for handle in subtree_ids)
    assert api.removeRegisterArray(get_handle(register)) is False
    assert api.removeRegisterFileArray(get_handle(register_file)) is False


def test_array_mutations_reject_unowned_forged_duplicate_and_conflicting_targets():
    target = _register()
    target_id = get_handle(target)
    with pytest.raises(TgiError) as unowned:
        api.setRegisterArray(target_id, "2")
    assert unowned.value.fault_code == TgiFaultCode.INVALID_ID

    first_owner, path = _owner_with_child(target, "address_block")
    second_owner, _ = _owner_with_child(target, "address_block")
    root = _root_with_register_file(_register_file())
    root.memory_maps.memory_map[0].choice[0].choice.append(target)
    root.memory_maps.memory_map[0].choice[0].choice.extend(second_owner.choice)
    _register_root(root)
    with pytest.raises(TgiError) as duplicate:
        api.setRegisterArray(target_id, "2")
    assert duplicate.value.fault_code == TgiFaultCode.INVALID_ID
    assert target.array is None

    isolated = _register()
    isolated_owner, isolated_path = _owner_with_child(isolated, "address_block")
    isolated_id = get_handle(isolated)
    register_parent(isolated, isolated_owner, ("array",), "single")
    with pytest.raises(TgiError) as forged:
        api.removeRegisterArray(isolated_id)
    assert forged.value.fault_code == TgiFaultCode.INVALID_ID
    assert isolated.array is None


def test_register_file_parent_reference_or_malformed_choice_cannot_claim_inline_child():
    register = _register(RegisterFile.Register)
    parent = _register_file(
        choice=[
            UnsignedPositiveLongintExpression(value="64"),
            RegisterFile.RegisterFileDefinitionRef(value="definition", type_definitions="local"),
            register,
        ],
    )
    register_id = get_handle(register)
    register_parent(register, parent, ("choice",), "list")
    with pytest.raises(TgiError):
        api.setRegisterArray(register_id, "2")
    assert register.array is None

    malformed = _register(RegisterFile.Register)
    malformed_parent = _register_file(choice=[UnsignedPositiveLongintExpression(value="64"), object(), malformed])
    malformed_id = get_handle(malformed)
    register_parent(malformed, malformed_parent, ("choice",), "list")
    with pytest.raises(TgiError):
        api.setRegisterArray(malformed_id, "2")
    assert malformed.array is None

"""Register-file Annex contracts, atomic mutations and scoped reference resolution."""

import inspect

import pytest

from amal.eda.accellera.ipxact.v1685_2022 import tgi
from amal.eda.accellera.ipxact.v1685_2022.tgi import register_file as api
from amal.eda.accellera.ipxact.v1685_2022.tgi.component import _register_graph
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import TgiError, get_handle, registry, resolve_handle
from org.accellera.ipxact.v1685_2022 import (
    AddressBlockRef,
    Component,
    ComponentType,
    ConfigurableLibraryRefType,
    ExternalTypeDefinitions,
    FieldRef,
    FieldType,
    RegisterFile,
    RegisterFileDefinitions,
    RegisterFileRef,
    TypeDefinitions,
    UnsignedLongintExpression,
    UnsignedPositiveLongintExpression,
)

_BASE = [
    (name, "aliasOfID" if i < 2 else "addressBlockRefID" if i == 10 else "registerFileID")
    for i, name in enumerate(
        [
            "getAliasOfRegisterFileRefByNames",
            "getAliasOfRegisterFileRefIDs",
            "getRegisterFileAccessHandleIDs",
            "getRegisterFileAccessPolicyIDs",
            "getRegisterFileAddressOffset",
            "getRegisterFileAddressOffsetExpression",
            "getRegisterFileArrayID",
            "getRegisterFileRange",
            "getRegisterFileRangeExpression",
            "getRegisterFileRangeID",
            "getRegisterFileRefIndexIDs",
            "getRegisterFileRegisterFileDefinitionRefByExternalTypeDefID",
            "getRegisterFileRegisterFileDefinitionRefByID",
            "getRegisterFileRegisterFileDefinitionRefByName",
            "getRegisterFileRegisterFileDefinitionRefID",
            "getRegisterFileRegisterFileIDs",
            "getRegisterFileRegisterIDs",
            "getRegisterFileTypeIdentifier",
        ]
    )
]
_EXTENDED = [
    ("addAliasOfRegisterFileRef", "aliasOfID,registerFileRef"),
    ("addRegisterFileDefinitionRegisterFile", "registerFileDefinitionID,name,addressOffset,range"),
    ("addRegisterFileRefIndex", "registerFileRefID,value"),
    ("addRegisterFileRegister", "registerFileID,name,offset,size,fieldName,fieldOffset,fieldWidth"),
    ("removeAliasOfRegisterFileRef", "registerFileRefID"),
    ("removeRegisterFileAccessHandle", "accessHandleID"),
    ("removeRegisterFileRefIndex", "indexID"),
    ("removeRegisterFileRegister", "registerID"),
    ("removeRegisterFileRegisterFile", "registerFileID"),
    ("removeRegisterFileTypeIdentifier", "registerFileID"),
    ("setRegisterFileAddressOffset", "registerFileID,expression"),
    ("setRegisterFileRange", "registerFileID,expression"),
    ("setRegisterFileRegisterFileDefinitionRef", "registerFileID,value,typeDefinitions"),
    ("setRegisterFileTypeIdentifier", "registerFileID,typeIdentifier"),
]


@pytest.fixture(autouse=True)
def clean_registry():
    registry.clear()
    yield
    registry.clear()


def _file():
    return RegisterFile(
        name="file",
        address_offset=UnsignedLongintExpression(value="0"),
        choice=[UnsignedPositiveLongintExpression(value="64")],
    )


@pytest.mark.parametrize(
    "name,args,section",
    [
        *[(name, args, f"F.7.75.{i}") for i, (name, args) in enumerate(_BASE, 1)],
        *[(name, args, f"F.7.76.{i}") for i, (name, args) in enumerate(_EXTENDED, 1)],
    ],
)
def test_exact_annex_signatures_exports_and_static_docs(name, args, section):
    function = getattr(api, name)
    assert list(inspect.signature(function).parameters) == args.split(",")
    assert name in api.__all__ and getattr(tgi, name) is function
    assert "Args:" in function.__doc__ and "Returns:" in function.__doc__
    assert f"Section: {section}." in function.__doc__


@pytest.mark.parametrize("name,args", _BASE)
def test_base_getters_reject_invalid_types(name, args):
    with pytest.raises(TgiError):
        getattr(api, name)(get_handle(object()))


@pytest.mark.parametrize("value", ["-1", str(1 << 64), "", "1'bx", "1 +", None, True, 42])
@pytest.mark.parametrize("setter", [api.setRegisterFileAddressOffset, api.setRegisterFileRange])
def test_invalid_expressions_reject_atomically(value, setter):
    file = _file()
    old_offset, old_range = file.address_offset, file.choice[0]
    with pytest.raises(TgiError):
        setter(get_handle(file), value)
    assert file.address_offset is old_offset and file.choice == [old_range]
    assert old_offset.value == "0" and old_range.value == "64"


def test_required_positive_range_bounds_and_wrapper_metadata():
    file = _file()
    node = file.choice[0]
    node.minimum, node.maximum = 2, 128
    node.other_attributes = {"{urn:test}marker": "preserved"}
    with pytest.raises(TgiError):
        api.setRegisterFileRange(get_handle(file), "0")
    with pytest.raises(TgiError):
        api.setRegisterFileRange(get_handle(file), "129")
    api.setRegisterFileRange(get_handle(file), "64 + 1")
    assert api.getRegisterFileRange(get_handle(file)) == 65
    assert file.choice[0] is node and node.other_attributes
    api.setRegisterFileAddressOffset(get_handle(file), str((1 << 64) - 1))
    assert api.getRegisterFileAddressOffset(get_handle(file)) == (1 << 64) - 1


def test_factories_validate_width_and_duplicates_before_mutating():
    file = _file()
    handle = get_handle(file)
    for size, offset, width in [("0", "0", "1"), ("32", "32", "1"), ("32", "0", "0")]:
        with pytest.raises(TgiError):
            api.addRegisterFileRegister(handle, "reg", "0", size, "field", offset, width)
        assert len(file.choice) == 1
    child = api.addRegisterFileRegister(handle, "reg", "0", "32", "field", "0", "32")
    with pytest.raises(TgiError):
        api.addRegisterFileRegister(handle, "reg", "0", "32", "field", "0", "1")
    assert api.getRegisterFileRegisterIDs(handle) == [child]


def test_type_identifier_and_reference_branch_atomicity():
    file = _file()
    handle = get_handle(file)
    assert api.removeRegisterFileTypeIdentifier(handle) is False
    api.setRegisterFileTypeIdentifier(handle, " fileType ")
    assert api.getRegisterFileTypeIdentifier(handle) == "fileType"
    assert api.removeRegisterFileTypeIdentifier(handle)
    range_id = api.getRegisterFileRangeID(handle)
    with pytest.raises(TgiError):
        api.setRegisterFileRegisterFileDefinitionRef(handle, "invalid name", "types")
    assert resolve_handle(range_id) is file.choice[0]
    api.setRegisterFileRegisterFileDefinitionRef(handle, "definition", "types")
    assert resolve_handle(range_id) is None
    for action in [
        lambda: api.setRegisterFileTypeIdentifier(handle, "type"),
        lambda: api.addRegisterFileRegister(handle, "reg", "0", "32", "field", "0", "1"),
    ]:
        with pytest.raises(TgiError):
            action()
    assert api.getRegisterFileRegisterFileDefinitionRefByName(handle) == "definition"


def test_repeated_alias_segments_and_index_holder_pruning():
    alias = FieldType.AliasOf(field_ref=FieldRef(field_ref="data"))
    handle = get_handle(alias)
    refs = [api.addAliasOfRegisterFileRef(handle, "segment") for _ in range(2)]
    assert api.getAliasOfRegisterFileRefByNames(handle) == ["segment", "segment"]
    index = api.addRegisterFileRefIndex(refs[0], "3")
    assert api.removeRegisterFileRefIndex(index)
    assert resolve_handle(refs[0]).indices is None
    assert api.getRegisterFileRefIndexIDs(get_handle(AddressBlockRef(address_block_ref="block"))) == []
    with pytest.raises(TgiError):
        api.removeAliasOfRegisterFileRef(get_handle(RegisterFileRef(register_file_ref="orphan")))


def test_definition_targets_are_scoped_to_external_declaration_and_loaded_document():
    file = _file()
    api.setRegisterFileRegisterFileDefinitionRef(get_handle(file), "definition", "types")
    declaration = ExternalTypeDefinitions(
        name="types",
        type_definitions_ref=ConfigurableLibraryRefType(vendor="v", library="l", name="external", version="1"),
    )
    # TypeDefinitions may itself own external declarations and inline file definitions.
    owner_definition = RegisterFileDefinitions.RegisterFileDefinition(
        name="owner", range=UnsignedPositiveLongintExpression(value="128"), register_or_register_file=[file]
    )
    root = TypeDefinitions(
        vendor="v",
        library="l",
        name="root",
        version="1",
        external_type_definitions=[declaration],
        register_file_definitions=RegisterFileDefinitions(register_file_definition=[owner_definition]),
    )
    registry.register(root, ("v", "l", "root", "1"))
    _register_graph(root)
    assert api.getRegisterFileRegisterFileDefinitionRefByExternalTypeDefID(get_handle(file)) == get_handle(declaration)
    assert api.getRegisterFileRegisterFileDefinitionRefByID(get_handle(file)) is None
    target_definition = RegisterFileDefinitions.RegisterFileDefinition(
        name="definition", range=UnsignedPositiveLongintExpression(value="64")
    )
    target = TypeDefinitions(
        vendor="v",
        library="l",
        name="external",
        version="1",
        register_file_definitions=RegisterFileDefinitions(register_file_definition=[target_definition]),
    )
    registry.register(target, ("v", "l", "external", "1"))
    assert api.getRegisterFileRegisterFileDefinitionRefByID(get_handle(file)) == get_handle(target_definition)
    target.register_file_definitions.register_file_definition.append(
        RegisterFileDefinitions.RegisterFileDefinition(
            name="definition", range=UnsignedPositiveLongintExpression(value="32")
        )
    )
    with pytest.raises(TgiError):
        api.getRegisterFileRegisterFileDefinitionRefByID(get_handle(file))
    registry.clear()
    registry.register(root, ("v", "l", "root", "1"))
    registry.register(
        Component(
            vendor="v", library="l", name="external", version="1", type_definitions=ComponentType.TypeDefinitions()
        ),
        ("v", "l", "external", "1"),
    )
    _register_graph(root)
    with pytest.raises(TgiError):
        api.getRegisterFileRegisterFileDefinitionRefByID(get_handle(file))


def test_tuple_children_and_parsed_ownership_removal_invalidate_descendants():
    child = _file()
    definition = RegisterFileDefinitions.RegisterFileDefinition(
        name="definition", range=UnsignedPositiveLongintExpression(value="128"), register_or_register_file=(child,)
    )
    root = TypeDefinitions(
        vendor="v",
        library="l",
        name="types",
        version="1",
        register_file_definitions=RegisterFileDefinitions(register_file_definition=[definition]),
    )
    registry.register(root, ("v", "l", "types", "1"))
    child_id, range_id = get_handle(child), get_handle(child.choice[0])
    assert api.removeRegisterFileRegisterFile(child_id)
    assert definition.register_or_register_file == []
    assert resolve_handle(child_id) is None and resolve_handle(range_id) is None


def test_register_and_register_file_share_name_uniqueness_scope():
    nested = _file()
    nested.name = "taken"
    parent = _file()
    parent.choice.append(nested)
    with pytest.raises(TgiError):
        api.addRegisterFileRegister(get_handle(parent), "taken", "0", "32", "field", "0", "1")
    definition = RegisterFileDefinitions.RegisterFileDefinition(
        name="definition", range=UnsignedPositiveLongintExpression(value="128"), register_or_register_file=[nested]
    )
    with pytest.raises(TgiError):
        api.addRegisterFileDefinitionRegisterFile(get_handle(definition), "taken", "0", "32")
    assert definition.register_or_register_file == [nested]


def test_definition_reference_update_preserves_existing_node_identity():
    file = _file()
    handle = get_handle(file)
    api.setRegisterFileRegisterFileDefinitionRef(handle, "first", "types")
    node_id = api.getRegisterFileRegisterFileDefinitionRefID(handle)
    node = resolve_handle(node_id)
    api.setRegisterFileRegisterFileDefinitionRef(handle, "second", "otherTypes")
    assert api.getRegisterFileRegisterFileDefinitionRefID(handle) == node_id
    assert file.choice[0] is node and node.value == "second" and node.type_definitions == "otherTypes"


@pytest.mark.parametrize(
    "remove",
    [
        api.removeAliasOfRegisterFileRef,
        api.removeRegisterFileAccessHandle,
        api.removeRegisterFileRefIndex,
        api.removeRegisterFileRegister,
        api.removeRegisterFileRegisterFile,
    ],
)
def test_removals_reject_unrelated_handles(remove):
    with pytest.raises(TgiError):
        remove(get_handle(FieldType.AliasOf(field_ref=FieldRef(field_ref="data"))))


def test_factories_preserve_unresolved_sources_and_allow_same_field_in_distinct_registers():
    file = _file()
    handle = get_handle(file)
    first = api.addRegisterFileRegister(handle, "first", "OFFSET", "SIZE", "data", "BIT_OFFSET", "WIDTH")
    second = api.addRegisterFileRegister(handle, "second", "4", "32", "data", "0", "32")
    assert api.getRegisterFileRegisterIDs(handle) == [first, second]
    assert resolve_handle(first).address_offset.value == "OFFSET"
    alias = FieldType.AliasOf(field_ref=FieldRef(field_ref="data"))
    ref = api.addAliasOfRegisterFileRef(get_handle(alias), "segment")
    index = api.addRegisterFileRefIndex(ref, "INDEX")
    assert resolve_handle(index).value == "INDEX"
    definition = RegisterFileDefinitions.RegisterFileDefinition(
        name="definition", range=UnsignedPositiveLongintExpression(value="128")
    )
    nested = api.addRegisterFileDefinitionRegisterFile(get_handle(definition), "nested", "BASE", "RANGE")
    assert resolve_handle(nested).choice[0].value == "RANGE"


def test_index_removal_requires_register_file_reference_ownership():
    from org.accellera.ipxact.v1685_2022 import Index, Indices

    ref = AddressBlockRef(address_block_ref="block", indices=Indices(index=[Index(value="0")]))
    index = api.getRegisterFileRefIndexIDs(get_handle(ref))[0]
    with pytest.raises(TgiError):
        api.removeRegisterFileRefIndex(index)
    assert len(ref.indices.index) == 1


@pytest.mark.parametrize("source", ["0", "-1", str(1 << 64)])
def test_numeric_range_getter_rejects_invalid_intrinsic_domain(source):
    file = _file()
    file.choice[0].value = source
    with pytest.raises(TgiError):
        api.getRegisterFileRange(get_handle(file))


@pytest.mark.parametrize("source", ["-1", str(1 << 64)])
def test_numeric_offset_getter_rejects_invalid_intrinsic_domain(source):
    file = _file()
    file.address_offset.value = source
    with pytest.raises(TgiError):
        api.getRegisterFileAddressOffset(get_handle(file))


def test_tuple_alias_path_addition_and_removal():
    alias = FieldType.AliasOf(field_ref=FieldRef(field_ref="data"), register_file_ref=())
    ref = api.addAliasOfRegisterFileRef(get_handle(alias), "segment")
    assert api.getAliasOfRegisterFileRefIDs(get_handle(alias)) == [ref]
    alias.register_file_ref = tuple(alias.register_file_ref)
    assert api.removeAliasOfRegisterFileRef(ref)
    assert alias.register_file_ref == []

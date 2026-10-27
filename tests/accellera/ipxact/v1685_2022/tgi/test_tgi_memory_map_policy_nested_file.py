"""IEEE 1685-2022 memory-map policy and nested register-file mutations."""

from inspect import signature
from types import SimpleNamespace

import pytest

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
    AccessPolicies,
    AddressBlock,
    AddressBlockDefinitions,
    AddressBlockType,
    Bank,
    BankAlignmentType,
    BankedBlockType,
    BaseAddress,
    Component,
    MemoryMaps,
    MemoryMapType,
    ModeRef,
    RegisterFile,
    RegisterFileDefinitions,
    UnsignedLongintExpression,
    UnsignedPositiveIntExpression,
    UnsignedPositiveLongintExpression,
)

_LONG_MAX = (1 << 63) - 1
_U64_MAX = (1 << 64) - 1


@pytest.fixture(autouse=True)
def clean_registry():
    registry.clear()
    yield
    registry.clear()


def _register_file(name: str = "rf", *, choice=None) -> RegisterFile:
    return RegisterFile(
        name=name,
        address_offset=UnsignedLongintExpression(value="0"),
        choice=choice if choice is not None else [UnsignedPositiveLongintExpression(value="64")],
    )


def _document(
    policy: AccessPolicies.AccessPolicy | None = None,
    register_file: RegisterFile | None = None,
    component_name: str = "component",
) -> Component:
    policy = policy or AccessPolicies.AccessPolicy(mode_ref=[])
    register_file = register_file or _register_file(choice=[UnsignedPositiveLongintExpression(value="64")])
    if not any(isinstance(item, AccessPolicies) for item in register_file.choice):
        register_file.choice = [*register_file.choice, AccessPolicies(access_policy=[policy])]
    access_block = AddressBlock(
        name="block",
        base_address=BaseAddress(value="0"),
        choice=[
            UnsignedPositiveLongintExpression(value="256"),
            UnsignedPositiveIntExpression(value="32"),
            register_file,
        ],
    )
    root = Component(
        vendor="vendor",
        library="library",
        name=component_name,
        version="1.0",
        memory_maps=MemoryMaps(memory_map=[MemoryMapType(name="map", choice=[access_block])]),
    )
    registry.register(root, ("vendor", "library", component_name, "1.0"))
    return root


def _policy(root: Component) -> AccessPolicies.AccessPolicy:
    file = root.memory_maps.memory_map[0].choice[0].choice[2]
    holder = next(item for item in file.choice if isinstance(item, AccessPolicies))
    return holder.access_policy[0]


@pytest.mark.parametrize(
    "function,parameters,section",
    [
        (api.addAccessPolicyModeRef, "accessPolicyID,modeRef,priority", "F.7.58.1"),
        (api.removeAccessPolicyModeRef, "accessPolicyID,modeRef", "F.7.58.20"),
        (api.addRegisterFileRegisterFile, "registerFileID,name,addressOffset,range", "F.7.58.19"),
    ],
)
def test_extended_exports_signatures_and_annex_docs(function, parameters, section):
    assert list(signature(function).parameters) == parameters.split(",")
    assert function.__name__ in api.__all__
    assert "Args:" in function.__doc__ and "Returns:" in function.__doc__
    assert f"Section: {section}." in function.__doc__


def test_add_access_policy_mode_ref_validates_tgi_long_and_existing_schema_priorities():
    old = ModeRef(value="old_mode", priority=_LONG_MAX + 1, id="old-id")
    root = _document(AccessPolicies.AccessPolicy(mode_ref=[old]))
    policy = _policy(root)
    policy_id = get_handle(policy)
    assert get_parent_info(policy_id) is None

    created_id = api.addAccessPolicyModeRef(policy_id, "  selected\n", _LONG_MAX)
    created = resolve_handle(created_id)
    assert created is policy.mode_ref[1]
    assert created.value == "selected" and created.priority == _LONG_MAX
    assert old.priority == _LONG_MAX + 1 and old.id == "old-id"

    for value, priority in (("selected", 4), ("another", _LONG_MAX + 1), ("another", -1), ("bad name", 3)):
        before = tuple(policy.mode_ref)
        with pytest.raises(TgiError) as error:
            api.addAccessPolicyModeRef(policy_id, value, priority)
        assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
        assert tuple(policy.mode_ref) == before

    with pytest.raises(TgiError) as error:
        api.addAccessPolicyModeRef(policy_id, "another", True)
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT


def test_remove_access_policy_mode_ref_matches_source_name_and_invalidates_only_removed_node():
    first = ModeRef(value="mode_a", priority=0, id="first")
    second = ModeRef(value="mode_b", priority=1, id="second")
    policy = AccessPolicies.AccessPolicy(mode_ref=(first, second))
    _document(policy)
    policy_id = get_handle(policy)
    first_id, second_id = get_handle(first), get_handle(second)
    old_mode_refs = policy.mode_ref

    assert api.removeAccessPolicyModeRef(policy_id, " mode_a ") is True
    assert isinstance(policy.mode_ref, list) and policy.mode_ref == [second]
    assert resolve_handle(first_id) is None
    assert resolve_handle(second_id) is second and second.id == "second" and second.priority == 1
    assert api.removeAccessPolicyModeRef(policy_id, "mode_a") is False
    assert api.removeAccessPolicyModeRef(policy_id, "mode_b") is True
    assert policy.mode_ref == [] and resolve_handle(second_id) is None
    assert old_mode_refs == (first, second)


@pytest.mark.parametrize("bad_handle", [None, 0, [], {}])
def test_access_policy_operations_reject_non_string_handles_with_invalid_id(bad_handle):
    for operation in (
        lambda: api.addAccessPolicyModeRef(bad_handle, "mode", 0),
        lambda: api.removeAccessPolicyModeRef(bad_handle, "mode"),
    ):
        with pytest.raises(TgiError) as error:
            operation()
        assert error.value.fault_code == TgiFaultCode.INVALID_ID


def test_access_policy_rejects_forged_rootless_holder_owner_and_duplicate_membership():
    policy = AccessPolicies.AccessPolicy(mode_ref=[])
    holder = AccessPolicies(access_policy=[policy])
    fake_owner = SimpleNamespace(access_policies=holder)
    policy_id = get_handle(policy)
    register_parent(policy, holder, ("access_policy",), "list")
    register_parent(holder, fake_owner, ("access_policies",), "single")
    with pytest.raises(TgiError) as error:
        api.addAccessPolicyModeRef(policy_id, "mode", 0)
    assert error.value.fault_code == TgiFaultCode.INVALID_ID

    duplicate_policy = AccessPolicies.AccessPolicy(mode_ref=[])
    root = _document(duplicate_policy)
    access_holder = next(
        item for item in root.memory_maps.memory_map[0].choice[0].choice[2].choice if isinstance(item, AccessPolicies)
    )
    access_holder.access_policy = (duplicate_policy, duplicate_policy)
    with pytest.raises(TgiError) as error:
        api.addAccessPolicyModeRef(get_handle(duplicate_policy), "mode", 0)
    assert error.value.fault_code == TgiFaultCode.INVALID_ID


def test_access_policy_accepts_direct_typed_parent_links_without_a_registered_root():
    policy = AccessPolicies.AccessPolicy(mode_ref=[])
    holder = AccessPolicies(access_policy=[policy])
    register_file = _register_file(choice=[UnsignedPositiveLongintExpression(value="16"), holder])
    register_parent(holder, register_file, ("choice",), "list")
    register_parent(policy, holder, ("access_policy",), "list")

    mode_id = api.addAccessPolicyModeRef(get_handle(policy), "direct_mode", 3)
    assert resolve_handle(mode_id).value == "direct_mode"
    assert register_file.choice[1] is holder and holder.access_policy[0] is policy

    nested = _register_file("nested_parent")
    outer = _register_file("outer", choice=[UnsignedPositiveLongintExpression(value="32"), nested])
    register_parent(nested, outer, ("choice",), "list")
    nested_id = api.addRegisterFileRegisterFile(get_handle(nested), "rootless_child", "4", "2")
    assert resolve_handle(nested_id).name == "rootless_child"


@pytest.mark.parametrize(
    "register_model",
    [
        AddressBlockDefinitions.AddressBlockDefinition.Register,
        RegisterFileDefinitions.RegisterFileDefinition.Register,
    ],
)
def test_access_policy_accepts_definition_register_choice_owners(register_model):
    policy = AccessPolicies.AccessPolicy(mode_ref=[])
    holder = AccessPolicies(access_policy=[policy])
    register = register_model(
        name="reg",
        address_offset=UnsignedLongintExpression(value="0"),
        choice=[UnsignedPositiveIntExpression(value="8"), holder],
    )
    register_parent(holder, register, ("choice",), "list")
    register_parent(policy, holder, ("access_policy",), "list")

    mode_id = api.addAccessPolicyModeRef(get_handle(policy), "definition_mode", 1)
    assert resolve_handle(mode_id).value == "definition_mode"


def test_access_policy_accepts_nonlocal_bank_policy_ownership():
    root = _document()
    policy = AccessPolicies.AccessPolicy(mode_ref=[])
    holder = AccessPolicies(access_policy=[policy])
    bank = Bank(
        name="bank",
        base_address=BaseAddress(value="0"),
        bank_alignment=BankAlignmentType.PARALLEL,
        choice=[holder],
    )
    root.memory_maps.memory_map[0].choice.append(bank)

    mode_id = api.addAccessPolicyModeRef(get_handle(policy), "bank_mode", 2)
    assert resolve_handle(mode_id).value == "bank_mode"


def test_add_nested_register_file_accepts_banked_block_storage_without_a_root():
    nested = _register_file("nested")
    block = BankedBlockType(
        name="banked",
        range=UnsignedPositiveLongintExpression(value="32"),
        width=UnsignedPositiveIntExpression(value="8"),
        register_or_register_file=[nested],
    )
    register_parent(nested, block, ("register_or_register_file",), "list")

    child_id = api.addRegisterFileRegisterFile(get_handle(nested), "child", "0", "1")
    assert resolve_handle(child_id).name == "child"


def test_add_nested_register_file_normalizes_only_edited_choice_and_round_trips_xml():
    root = _document()
    register_file = root.memory_maps.memory_map[0].choice[0].choice[2]
    old_range = register_file.choice[0]
    policy_holder = register_file.choice[1]
    register_file.choice = (old_range, policy_holder)
    choice_before = register_file.choice

    child_id = api.addRegisterFileRegisterFile(get_handle(register_file), "nested", str(_U64_MAX), "1")
    child = resolve_handle(child_id)
    assert isinstance(child, RegisterFile)
    assert child.name == "nested" and child.address_offset.value == str(_U64_MAX)
    assert child.choice[0].value == "1"
    assert register_file.choice is not choice_before
    assert tuple(register_file.choice[:2]) == choice_before
    assert register_file.choice[0] is old_range and register_file.choice[1] is policy_holder

    xml = XmlDocument.serializer().render(root)
    parsed = XmlDocument.deserialize(xml, Component)
    parsed_file = parsed.memory_maps.memory_map[0].choice[0].choice[2]
    parsed_nested = parsed_file.choice[-1]
    parsed_policy = next(item for item in parsed_file.choice if isinstance(item, AccessPolicies)).access_policy[0]
    assert isinstance(parsed_nested, RegisterFile)
    assert parsed_nested.name == "nested"
    assert parsed_nested.address_offset.value == str(_U64_MAX)
    assert api.addAccessPolicyModeRef(get_handle(_policy(root)), "round_trip_mode", 17)
    xml = XmlDocument.serializer().render(root)
    parsed = XmlDocument.deserialize(xml, Component)
    parsed_policy = _policy(parsed)
    assert parsed_policy.mode_ref[0].value == "round_trip_mode"
    assert parsed_policy.mode_ref[0].priority == 17


def test_add_nested_register_file_enforces_scope_branch_and_u64_bounds_atomically():
    root = _document()
    register_file = root.memory_maps.memory_map[0].choice[0].choice[2]
    register_file.choice = tuple(register_file.choice)
    before = register_file.choice
    register_file_id = get_handle(register_file)

    for name, offset, range_value in (
        ("nested", "-1", "1"),
        ("nested", str(_U64_MAX + 1), "1"),
        ("nested", "0", "0"),
        ("bad name", "0", "1"),
    ):
        with pytest.raises(TgiError):
            api.addRegisterFileRegisterFile(register_file_id, name, offset, range_value)
        assert register_file.choice is before

    api.addRegisterFileRegisterFile(register_file_id, "nested", "0", "1")
    after = register_file.choice
    with pytest.raises(TgiError) as error:
        api.addRegisterFileRegisterFile(register_file_id, "nested", "1", "2")
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert register_file.choice is after and len(register_file.choice) == 3

    register_file.choice.append(
        RegisterFile.Register(
            name="shared_name",
            address_offset=UnsignedLongintExpression(value="0"),
            choice=[UnsignedPositiveIntExpression(value="8")],
        )
    )
    before_shared = register_file.choice
    with pytest.raises(TgiError) as error:
        api.addRegisterFileRegisterFile(get_handle(register_file), "shared_name", "0", "1")
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert register_file.choice is before_shared

    reference_parent = _register_file(
        choice=[RegisterFile.RegisterFileDefinitionRef(value="external", type_definitions="defs")]
    )
    _document(register_file=reference_parent, component_name="reference_component")
    reference_before = reference_parent.choice
    with pytest.raises(TgiError) as error:
        api.addRegisterFileRegisterFile(get_handle(reference_parent), "nested", "0", "1")
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert reference_parent.choice is reference_before


def test_nested_register_file_rejects_definition_reference_on_parent_address_block():
    root = _document()
    block = root.memory_maps.memory_map[0].choice[0]
    register_file = block.choice[2]
    block.choice = (
        AddressBlockType.AddressBlockDefinitionRef(value="external", type_definitions="defs"),
        register_file,
    )
    original = register_file.choice
    with pytest.raises(TgiError) as error:
        api.addRegisterFileRegisterFile(get_handle(register_file), "nested", "0", "1")
    assert error.value.fault_code == TgiFaultCode.INVALID_ID
    assert register_file.choice is original


def test_nested_register_file_rejects_unowned_forged_and_duplicate_membership():
    detached = _register_file()
    with pytest.raises(TgiError) as error:
        api.addRegisterFileRegisterFile(get_handle(detached), "nested", "0", "1")
    assert error.value.fault_code == TgiFaultCode.INVALID_ID

    root = _document()
    parent = root.memory_maps.memory_map[0].choice[0].choice[2]
    child = _register_file("existing")
    parent.choice = [*parent.choice, child]
    root_id = get_handle(root)
    registry.register(root, ("vendor", "library", "component", "1.0"), replace=True)
    child_id = get_handle(child)

    false_parent = _register_file("false_parent", choice=[UnsignedPositiveLongintExpression(value="2"), child])
    register_parent(child, false_parent, ("choice",), "list")
    with pytest.raises(TgiError) as error:
        api.addRegisterFileRegisterFile(child_id, "nested", "0", "1")
    assert error.value.fault_code == TgiFaultCode.INVALID_ID
    assert resolve_handle(root_id) is root

    register_parent(child, parent, ("choice",), "list")
    parent.choice.append(child)
    with pytest.raises(TgiError) as error:
        api.addRegisterFileRegisterFile(child_id, "nested", "0", "1")
    assert error.value.fault_code == TgiFaultCode.INVALID_ID

"""Access-policy TGI reference, ownership, and XML contracts."""

from pathlib import Path

import pytest

from amal.eda.accellera.ipxact.v1685_2022.tgi import access_policy as api
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import (
    TgiError,
    TgiFaultCode,
    get_handle,
    registry,
    resolve_handle,
)
from amal.eda.ipxact_de.xml_document import XmlDocument
from amal.eda.ipxact_de.xml_validation import validate_ipxact_xml
from org.accellera.ipxact.v1685_2022 import (
    AddressBlock,
    BaseAddress,
    TypeDefinitions,
    UnsignedLongintExpression,
)
from org.accellera.ipxact.v1685_2022.access_policies import AccessPolicies
from org.accellera.ipxact.v1685_2022.address_block_type import AddressBlockType
from org.accellera.ipxact.v1685_2022.alternate_registers import AlternateRegisters
from org.accellera.ipxact.v1685_2022.bank import Bank
from org.accellera.ipxact.v1685_2022.mode_ref import ModeRef
from org.accellera.ipxact.v1685_2022.register_file import RegisterFile
from org.accellera.ipxact.v1685_2022.reset_type_links import ResetTypeLinks

SAMPLES = Path("tests/xml/ipxact/v1685_2022/accellera.org/Sample")
SAMPLE_TYPES = SAMPLES / "SampleTypeDefinitions/1.0/xml/SampleTypeDefinitions.xml"
POLICY_TYPES = SAMPLES / "FieldAccessPolicyDefinitions/1.0/xml/FieldAccessPolicyDefinitions.xml"


@pytest.fixture(autouse=True)
def clean_registry():
    registry.clear()
    yield
    registry.clear()


def _parse(path: Path):
    return XmlDocument.parser().from_string(path.read_text(), TypeDefinitions)


def _registered_documents():
    owner = _parse(SAMPLE_TYPES)
    target = _parse(POLICY_TYPES)
    registry.register(owner, ("accellera.org", "Sample", "SampleTypeDefinitions", "1.0"))
    registry.register(target, ("accellera.org", "Sample", "FieldAccessPolicyDefinitions", "1.0"))
    return owner, target


def _field_policy(owner, index=0):
    policy = owner.field_definitions.field_definition[index].field_access_policies.field_access_policy[0]
    return policy, get_handle(policy)


def test_external_definition_and_mode_references_resolve_in_registered_documents():
    owner, target = _registered_documents()
    ref_policy, ref_policy_id = _field_policy(owner)

    external_id = api.getFieldAccessPolicyFieldAccessPolicyDefinitionRefByExternalTypeDefID(ref_policy_id)
    assert external_id is not None
    assert resolve_handle(external_id).name == "fieldAccessTypes"
    definition_id = api.getFieldAccessPolicyFieldAccessPolicyDefinitionRefByID(ref_policy_id)
    assert definition_id is not None
    definition = resolve_handle(definition_id)
    assert definition.name == "RC"
    assert api.getFieldAccessPolicyDefinitionReadAction(definition_id) == "clear"
    access_policy = owner.register_definitions.register_definition[0].access_policies.access_policy[0]
    access_policy_id = get_handle(access_policy)
    mode_id = api.getAccessPolicyModeRefByID(access_policy_id, "Normal")
    assert mode_id is not None
    assert resolve_handle(mode_id).name == "Normal"
    assert api.getAccessPolicyModeRefByID(access_policy_id, "missing") is None

    ref_policy.mode_ref.append(ModeRef(value="Normal", priority=1))
    mode_ref_id = api.getFieldAccessPolicyModeRefIDs(ref_policy_id)[0]
    assert api.getFieldAccessPolicyModeRefByID(ref_policy_id, mode_ref_id) == mode_id
    with pytest.raises(TgiError) as error:
        api.getFieldAccessPolicyModeRefByID(ref_policy_id, "Normal")
    assert error.value.fault_code == TgiFaultCode.INVALID_ID

    # Resolving the definition is a non-owning cross-document reference; neither graph is changed.
    assert len(owner.field_definitions.field_definition[0].field_access_policies.field_access_policy) == 1
    assert len(target.field_access_policy_definitions.field_access_policy_definition) > 1


def test_invalid_policy_category_and_unrelated_reference_handles_are_rejected():
    owner, _target = _registered_documents()
    policy, policy_id = _field_policy(owner, 1)
    assert api.getFieldAccessPolicyAccess(policy_id) == "read-write"
    with pytest.raises(TgiError) as error:
        api.getFieldAccessPolicyAccess("not-a-policy-handle")
    assert error.value.fault_code == TgiFaultCode.INVALID_ID

    mode_ref_id = api.getFieldAccessPolicyModeRefIDs(policy_id)
    assert mode_ref_id == []
    restriction_id = api.addFieldAccessPolicyAccessRestriction(policy_id)
    with pytest.raises(TgiError) as error:
        api.getAccessRestrictionModeRefbyID(restriction_id, "Normal")
    assert error.value.fault_code == TgiFaultCode.INVALID_ID
    assert policy is resolve_handle(policy_id)


def test_choice_wrapper_identity_removal_and_round_trip_schema_validation(tmp_path):
    owner, _target = _registered_documents()
    inline, inline_id = _field_policy(owner, 1)
    assert api.getFieldAccessPolicyAccess(inline_id) == "read-write"
    # Updating a choice branch mutates its generated wrapper in place.
    access_wrapper_id = get_handle(inline.choice[0])
    api.setFieldAccessPolicyAccess(inline_id, "read-only")
    assert api.getFieldAccessPolicyAccess(inline_id) == "read-only"
    assert get_handle(inline.choice[0]) == access_wrapper_id

    old_modified_write_id = api.getFieldAccessPolicyModifiedWriteValueID(inline_id)
    assert old_modified_write_id is not None
    assert api.removeFieldAccessPolicyModifiedWriteValue(inline_id)
    assert resolve_handle(old_modified_write_id) is None
    assert api.getFieldAccessPolicyModifiedWriteValue(inline_id) is None

    serialized = XmlDocument.serializer().render(owner)
    round_tripped = XmlDocument.parser().from_string(serialized, TypeDefinitions)
    assert round_tripped.field_definitions.field_definition[1].field_access_policies.field_access_policy[0].choice
    path = tmp_path / "type-definitions.xml"
    path.write_text(serialized)
    result = validate_ipxact_xml(path, schema_root="submodules/accellera-schemas")
    assert result.ok, result.issues


def test_definition_ref_removal_invalidates_handle_and_sole_child_remove_works():
    owner, _target = _registered_documents()
    policy, policy_id = _field_policy(owner)
    container = owner.field_definitions.field_definition[0].field_access_policies
    container_id = get_handle(container)
    ref_id = api.getFieldAccessPolicyFieldAccessPolicyDefinitionRefID(policy_id)
    assert ref_id is not None
    assert api.removeFieldAccessPolicyFieldAccessPolicyDefinitionRef(policy_id)
    assert resolve_handle(ref_id) is None

    _second, second_id = _field_policy(owner, 1)
    second_container = owner.field_definitions.field_definition[1].field_access_policies
    second_container_id = get_handle(second_container)
    assert api.removeFieldAccessPoliciesFieldAccessPolicy(second_container_id)
    assert second_container.field_access_policy == []
    assert resolve_handle(second_id) is None

    first_added = api.addFieldAccessPoliciesFieldAccessPolicy(second_container_id)
    api.addFieldAccessPoliciesFieldAccessPolicy(second_container_id)
    with pytest.raises(TgiError) as error:
        api.removeFieldAccessPoliciesFieldAccessPolicy(second_container_id)
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert api.removeFieldAccessPoliciesFieldAccessPolicy(second_container_id, first_added)
    assert resolve_handle(first_added) is None
    assert policy is resolve_handle(policy_id)
    assert container_id == get_handle(container)


def test_remaining_access_policy_collections_and_inline_optional_values():
    owner, target = _registered_documents()
    register_definition = owner.register_definitions.register_definition[0]
    access_policy = register_definition.access_policies.access_policy[0]
    access_policy_id = get_handle(access_policy)
    assert api.getAccessPolicyAccess(access_policy_id) == "read-write"
    assert api.getAccessPolicyModeRefByNames(access_policy_id) == ["Normal"]
    access_mode_ref_id = api.getAccessPolicyModeRefIDs(access_policy_id)[0]
    api.setAccessPolicyAccess(access_policy_id, "read-only")
    assert api.getAccessPolicyAccess(access_policy_id) == "read-only"
    # This fixture's parsed TypeDefinitions register policy stores its access as a simple enum field.
    with pytest.raises(TgiError) as error:
        api.removeAccessRestrictionModeRef(access_mode_ref_id)
    assert error.value.fault_code == TgiFaultCode.INVALID_ID
    assert resolve_handle(access_mode_ref_id) is not None
    restriction_id = api.addFieldAccessPolicyAccessRestriction(_field_policy(owner, 1)[1])
    mode_ref_id = api.addAccessRestrictionModeRef(restriction_id, "Normal")
    assert mode_ref_id
    assert api.removeAccessPolicyAccess(access_policy_id)
    assert api.getAccessPolicyAccess(access_policy_id) is None

    _definition_ref_policy, definition_ref_policy_id = _field_policy(owner)
    assert api.getFieldAccessPolicyFieldAccessPolicyDefinitionRefByName(definition_ref_policy_id) == "RC"
    _inline_policy, inline_policy_id = _field_policy(owner, 1)
    field_access_policies_id = api.getRegisterFieldFieldAccessPoliciesID(
        get_handle(owner.field_definitions.field_definition[0])
    )
    assert field_access_policies_id == get_handle(owner.field_definitions.field_definition[0].field_access_policies)
    assert api.getFieldAccessPoliciesFieldAccessPolicyIDs(
        get_handle(owner.field_definitions.field_definition[1].field_access_policies)
    ) == [inline_policy_id]

    new_mode = api.addFieldAccessPolicyModeRef(inline_policy_id, "Normal")
    assert resolve_handle(new_mode).priority == 0
    assert api.getFieldAccessPolicyModeRefByName(inline_policy_id) == ["Normal"]
    api.setFieldAccessPolicyReserved(inline_policy_id, "1")
    reserved_id = api.getFieldAccessPolicyReservedID(inline_policy_id)
    assert reserved_id is not None
    assert api.getFieldAccessPolicyReserved(inline_policy_id) is True
    assert api.getFieldAccessPolicyReservedExpression(inline_policy_id) == "1"
    api.setFieldAccessPolicyTestable(inline_policy_id, True)
    testable_id = api.getFieldAccessPolicyTestableID(inline_policy_id)
    assert testable_id is not None
    assert api.getFieldAccessPolicyTestable(inline_policy_id) is True
    broadcast_id = api.addFieldAccessPolicyBroadcastTo(inline_policy_id, fieldRef="field0")
    assert api.getFieldAccesspolicyBroadcastToIDs(inline_policy_id) == [broadcast_id]
    assert api.removeFieldAccessPolicyBroadcastTo(broadcast_id)
    assert api.removeFieldAccessPolicyModeRef(new_mode)
    assert api.removeFieldAccessPolicyReserved(inline_policy_id)
    assert api.removeFieldAccessPolicyTestable(inline_policy_id)

    assert api.getTypeDefinitionsFieldAccessPolicyDefinitionIDs(
        get_handle(target)
    ) == api.getFieldAccessPolicyDefinitionIDs(get_handle(target.field_access_policy_definitions))
    assert api.getAccessRestrictionModeRefIDs(restriction_id) == [mode_ref_id]
    assert api.getAccessRestrictionModeRefbyNames(restriction_id) == ["Normal"]
    assert api.removeAccessRestrictionModeRef(mode_ref_id)
    assert resolve_handle(mode_ref_id) is None


def test_all_access_policy_owner_creators_and_external_reset_type_link():
    owner, _target = _registered_documents()
    base_address = BaseAddress(value="0")
    address_block = AddressBlock(name="block", base_address=base_address)
    address_policy = api.addAddressBlockAccessPolicy(get_handle(address_block))
    assert api.getAccessPolicyAccess(address_policy) is None
    assert api.removeAddressBlockAccessPolicyID(address_policy)
    assert resolve_handle(address_policy) is None

    alternate_register = AlternateRegisters.AlternateRegister(name="alt")
    alternate_policy = api.addAlternateRegisterAccessPolicy(get_handle(alternate_register))
    assert api.getAlternateRegisterAccessPolicyIDs(get_handle(alternate_register)) == [alternate_policy]
    assert api.removeAlternateRegisterAccessPolicy(alternate_policy)

    register = AddressBlockType.Register(name="reg", address_offset=UnsignedLongintExpression(value="0"))
    register_policy = api.addRegisterAccessPolicy(get_handle(register))
    assert api.getRegisterAccessPolicyIDs(get_handle(register)) == [register_policy]
    assert api.removeRegisterAccessPolicy(register_policy)

    register_file = RegisterFile(name="rf", address_offset=UnsignedLongintExpression(value="0"))
    register_file_policy = api.addRegisterFileAccessPolicy(get_handle(register_file))
    assert api.removeRegisterFileAccessPolicy(register_file_policy)

    field_definition = owner.field_definitions.field_definition[0]
    definition_policy = api.addFieldDefinitionFieldAccessPolicy(get_handle(field_definition))
    assert field_definition.field_access_policies.field_access_policy[-1] is resolve_handle(definition_policy)
    assert api.removeFieldDefinitionFieldAccessPolicy(definition_policy)
    assert resolve_handle(definition_policy) is None

    field_container = owner.field_definitions.field_definition[1].field_access_policies
    child = api.addFieldAccessPoliciesFieldAccessPolicy(get_handle(field_container))
    assert child in api.getFieldAccessPoliciesFieldAccessPolicyIDs(get_handle(field_container))
    assert api.removeFieldAccessPoliciesFieldAccessPolicy(get_handle(field_container), child)

    inline_policy_id = _field_policy(owner, 1)[1]
    assert api.setFieldAccessPolicyFieldAccessPolicyDefinitionRef(inline_policy_id, "RC", "fieldAccessTypes")
    assert api.getFieldAccessPolicyFieldAccessPolicyDefinitionRefByName(inline_policy_id) == "RC"
    assert api.removeFieldAccessPolicyFieldAccessPolicyDefinitionRef(inline_policy_id)

    external = owner.external_type_definitions[0]
    external_ref = ResetTypeLinks.ResetTypeLink.ExternalResetTypeReference(reset_type_ref="SOFT")
    internal_reset = ResetTypeLinks.ResetTypeLink.ResetTypeReference(reset_type_ref="SOFT")
    # Handles must be supplied for the exact generated reset reference categories.
    external_ref_id = get_handle(external_ref)
    internal_ref_id = get_handle(internal_reset)
    link_id = api.addExternalTypeDefinitionsResetTypeLink(get_handle(external), external_ref_id, internal_ref_id)
    assert resolve_handle(link_id).external_reset_type_reference.reset_type_ref == "SOFT"

    # Bank policy getters traverse the generated AccessPolicies choice wrapper.
    from org.accellera.ipxact.v1685_2022.bank_alignment_type import BankAlignmentType

    bank_policy = AccessPolicies(access_policy=[AccessPolicies.AccessPolicy()])
    bank = Bank(
        name="bank",
        base_address=base_address,
        bank_alignment=BankAlignmentType.PARALLEL,
        choice=[bank_policy],
    )
    ids = api.getBankAccessPoliciesIDs(get_handle(bank))
    assert ids == [get_handle(bank_policy.access_policy[0])]

"""Register field policy-holder integration and remaining reference getters."""

import inspect

import pytest
from lxml import etree

from amal.eda.accellera.ipxact.v1685_2022 import tgi as api
from amal.eda.accellera.ipxact.v1685_2022.tgi import register
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
    AddressBlockType,
    AddressUnitBits,
    AlternateRegisterRef,
    BaseAddress,
    Component,
    EnumeratedValues,
    FieldDefinitions,
    FieldRef,
    FieldType,
    Index,
    Indices,
    MemoryMaps,
    MemoryMapType,
    ModeRef,
    RegisterFile,
    UnsignedIntExpression,
    UnsignedLongintExpression,
    UnsignedPositiveIntExpression,
    UnsignedPositiveLongintExpression,
    UsageType,
)

SCHEMA = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))
BROADCASTS = [
    FieldType.FieldAccessPolicies.FieldAccessPolicy.Broadcasts.BroadcastTo,
    FieldDefinitions.FieldDefinition.FieldAccessPolicies.FieldAccessPolicy.Broadcasts.BroadcastTo,
]
HOLDERS = [FieldType.FieldAccessPolicies, FieldDefinitions.FieldDefinition.FieldAccessPolicies]


def field(branch=None):
    return FieldType(
        name="field",
        bit_offset=UnsignedIntExpression(value="0"),
        choice=(branch or UnsignedPositiveIntExpression(value="8"),),
    )


def component(source):
    register_node = AddressBlockType.Register(
        name="control",
        address_offset=UnsignedLongintExpression(value="0"),
        choice=[UnsignedPositiveIntExpression(value="8"), source],
    )
    block = AddressBlock(
        name="registers",
        base_address=BaseAddress(value="0"),
        choice=[
            UnsignedPositiveLongintExpression(value="16"),
            UnsignedPositiveIntExpression(value="8"),
            UsageType.REGISTER,
            register_node,
        ],
    )
    return Component(
        vendor="acme",
        library="test",
        name="policies",
        version="1",
        memory_maps=MemoryMaps(memory_map=[MemoryMapType(name="map", choice=[block, AddressUnitBits(value="8")])]),
    )


@pytest.mark.parametrize(
    "name,parameters",
    [
        ("setRegisterFieldFieldAccessPolicies", ["registerFieldID"]),
        ("removeRegisterFieldFieldAccessPolicices", ["registerFieldID"]),
        ("getAlternateRegisterRefAlternateRegisterRefByName", ["alternateRegisterRefID"]),
        ("getRegisterFileAddressOffsetID", ["registerFileID"]),
        ("getBroadcastToFieldRefByName", ["broadcastToID"]),
        ("getBroadcastToFieldRefID", ["broadcastToID"]),
    ],
)
def test_public_signatures_and_invalid_handles(name, parameters):
    operation = getattr(api, name)
    assert name in register.__all__ and list(inspect.signature(operation).parameters) == parameters
    for invalid in (None, [], {}, "missing", get_handle(UnsignedIntExpression(value="1"))):
        with pytest.raises(TgiError) as error:
            operation(invalid)
        assert error.value.fault_code == TgiFaultCode.INVALID_ID


@pytest.mark.parametrize(
    "branch", [UnsignedPositiveIntExpression(value="8"), FieldType.AliasOf(field_ref=FieldRef(field_ref="target"))]
)
def test_holder_creation_order_identity_policy_adder_and_owned_removal(branch):
    source = field(branch)
    enumerations = EnumeratedValues()
    source.choice = ("Type", branch, enumerations)
    field_id = get_handle(source)
    assert api.getRegisterFieldFieldAccessPoliciesID(field_id) is None
    assert api.setRegisterFieldFieldAccessPolicies(field_id) is True
    holder_id = api.getRegisterFieldFieldAccessPoliciesID(field_id)
    holder = resolve_handle(holder_id)
    assert isinstance(holder, FieldType.FieldAccessPolicies)
    assert source.choice == ["Type", branch, holder, enumerations]
    source.choice = tuple(source.choice)
    original = source.choice
    assert api.setRegisterFieldFieldAccessPolicies(field_id) is True
    assert source.choice is original and api.getRegisterFieldFieldAccessPoliciesID(field_id) == holder_id
    assert get_parent_info(holder_id).parent_handle == field_id
    holder.field_access_policy = ()
    policy_id = api.addFieldAccessPoliciesFieldAccessPolicy(holder_id)
    policy = resolve_handle(policy_id)
    assert isinstance(policy, FieldType.FieldAccessPolicies.FieldAccessPolicy)
    mode = ModeRef(value="normal", priority=0)
    policy.mode_ref = [mode]
    assert api.setFieldAccessPolicyAccess(policy_id, "read-write")
    # Getters establish all newly attached descendants before the holder is removed.
    assert api.getRegisterFieldFieldAccessPoliciesID(field_id) == holder_id
    mode_id = get_handle(mode)
    assert api.getFieldAccessPoliciesFieldAccessPolicyIDs(holder_id) == [policy_id]
    assert get_parent_info(policy_id).parent_handle == holder_id
    assert api.removeRegisterFieldFieldAccessPolicices(field_id) is True
    assert all(resolve_handle(handle) is None for handle in (holder_id, policy_id, mode_id))
    assert source.choice == ["Type", branch, enumerations]
    assert api.removeRegisterFieldFieldAccessPolicices(field_id) is False


@pytest.mark.parametrize("holder_type", HOLDERS)
def test_policy_adder_uses_owning_generated_type_and_tuple_normalization(holder_type):
    holder = holder_type(field_access_policy=())
    holder_id = get_handle(holder)
    child_id = api.addFieldAccessPoliciesFieldAccessPolicy(holder_id)
    expected = (
        FieldType.FieldAccessPolicies.FieldAccessPolicy
        if holder_type is FieldType.FieldAccessPolicies
        else FieldDefinitions.FieldDefinition.FieldAccessPolicies.FieldAccessPolicy
    )
    assert isinstance(resolve_handle(child_id), expected)
    assert holder.field_access_policy == [resolve_handle(child_id)]
    assert api.removeFieldAccessPoliciesFieldAccessPolicy(holder_id, child_id)
    assert resolve_handle(child_id) is None


def test_field_definition_accessor_compatibility():
    holder = FieldDefinitions.FieldDefinition.FieldAccessPolicies()
    definition = FieldDefinitions.FieldDefinition(
        name="definition", bit_width=UnsignedPositiveIntExpression(value="8"), field_access_policies=holder
    )
    assert api.getRegisterFieldFieldAccessPoliciesID(get_handle(definition)) == get_handle(holder)
    assert get_parent_info(get_handle(holder)).parent_handle == get_handle(definition)


@pytest.mark.parametrize(
    "malformed",
    [
        FieldType.FieldAccessPolicies(field_access_policy="bad"),
        FieldType.FieldAccessPolicies(
            field_access_policy=[FieldDefinitions.FieldDefinition.FieldAccessPolicies.FieldAccessPolicy()]
        ),
    ],
)
def test_malformed_policy_holder_does_not_mutate_field_or_adder(malformed):
    source = field()
    source.choice = (*source.choice, malformed)
    original = source.choice
    for operation in (
        api.getRegisterFieldFieldAccessPoliciesID,
        api.setRegisterFieldFieldAccessPolicies,
        api.removeRegisterFieldFieldAccessPolicices,
    ):
        with pytest.raises(TgiError) as error:
            operation(get_handle(source))
        assert error.value.fault_code == TgiFaultCode.INVALID_ID
        assert source.choice is original
    children = malformed.field_access_policy
    with pytest.raises(TgiError) as error:
        api.addFieldAccessPoliciesFieldAccessPolicy(get_handle(malformed))
    assert error.value.fault_code == TgiFaultCode.INVALID_ID
    assert malformed.field_access_policy is children


def test_definition_reference_rejects_holder_creation_and_duplicate_holders_fault():
    reference = FieldType.FieldDefinitionRef(value="definition", type_definitions="library")
    source = field(reference)
    original = source.choice
    assert api.getRegisterFieldFieldAccessPoliciesID(get_handle(source)) is None
    assert api.removeRegisterFieldFieldAccessPolicices(get_handle(source)) is False
    with pytest.raises(TgiError) as error:
        api.setRegisterFieldFieldAccessPolicies(get_handle(source))
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT and source.choice is original
    source = field()
    source.choice = (*source.choice, FieldType.FieldAccessPolicies(), FieldType.FieldAccessPolicies())
    original = source.choice
    with pytest.raises(TgiError) as error:
        api.setRegisterFieldFieldAccessPolicies(get_handle(source))
    assert error.value.fault_code == TgiFaultCode.INVALID_ID and source.choice is original


@pytest.mark.parametrize("model", BROADCASTS)
def test_broadcast_field_getters_preserve_source_indices_and_ownership(model):
    index = Index(value="2", id="index_id")
    reference = FieldRef(field_ref=" \tδ_target\n", indices=Indices(index=(index,)))
    broadcast = model(field_ref=reference)
    broadcast_id, ref_id = get_handle(broadcast), get_handle(reference)
    assert api.getBroadcastToFieldRefByName(broadcast_id) == "δ_target"
    assert api.getBroadcastToFieldRefID(broadcast_id) == ref_id
    assert reference.field_ref == " \tδ_target\n" and reference.indices.index == (index,)
    assert get_parent_info(ref_id).parent_handle == broadcast_id
    assert get_parent_info(get_handle(index)).parent_handle == get_handle(reference.indices)
    reference.field_ref = "bad Name"
    for operation in (api.getBroadcastToFieldRefByName, api.getBroadcastToFieldRefID):
        with pytest.raises(TgiError) as error:
            operation(broadcast_id)
        assert error.value.fault_code == TgiFaultCode.INVALID_ID
    broadcast.field_ref = None
    assert api.getBroadcastToFieldRefByName(broadcast_id) is None
    assert api.getBroadcastToFieldRefID(broadcast_id) is None
    broadcast.field_ref = AlternateRegisterRef(alternate_register_ref="wrong")
    with pytest.raises(TgiError) as error:
        api.getBroadcastToFieldRefID(broadcast_id)
    assert error.value.fault_code == TgiFaultCode.INVALID_ID


def test_alternate_reference_source_and_register_file_offset_model():
    alternate = AlternateRegisterRef(alternate_register_ref=" \tδ_alternate\n")
    assert api.getAlternateRegisterRefAlternateRegisterRefByName(get_handle(alternate)) == "δ_alternate"
    assert alternate.alternate_register_ref == " \tδ_alternate\n"
    alternate.alternate_register_ref = "bad Name"
    with pytest.raises(TgiError) as error:
        api.getAlternateRegisterRefAlternateRegisterRefByName(get_handle(alternate))
    assert error.value.fault_code == TgiFaultCode.INVALID_ID
    offset = UnsignedLongintExpression(value="OFFSET", minimum=0, maximum=1024)
    source = RegisterFile(name="file", address_offset=offset)
    offset_id = api.getRegisterFileAddressOffsetID(get_handle(source))
    assert resolve_handle(offset_id) is offset
    assert offset.value == "OFFSET" and offset.maximum == 1024
    assert get_parent_info(offset_id).parent_handle == get_handle(source)
    source.address_offset = None
    with pytest.raises(TgiError) as error:
        api.getRegisterFileAddressOffsetID(get_handle(source))
    assert error.value.fault_code == TgiFaultCode.INVALID_ID


def test_policy_holder_and_broadcast_round_trip_schema_validation():
    source = field()
    root = component(source)
    assert api.setRegisterFieldFieldAccessPolicies(get_handle(source))
    holder_id = api.getRegisterFieldFieldAccessPoliciesID(get_handle(source))
    policy_id = api.addFieldAccessPoliciesFieldAccessPolicy(holder_id)
    policy = resolve_handle(policy_id)
    policy.broadcasts = FieldType.FieldAccessPolicies.FieldAccessPolicy.Broadcasts(
        broadcast_to=[BROADCASTS[0](field_ref=FieldRef(field_ref="target"))]
    )
    assert api.setFieldAccessPolicyAccess(policy_id, "read-write")
    xml = XmlDocument.serializer().render(root)
    SCHEMA.assertValid(etree.fromstring(xml.encode()))
    parsed = XmlDocument.parser().from_string(xml, Component)
    parsed_field = parsed.memory_maps.memory_map[0].choice[0].choice[3].choice[1]
    parsed_holder_id = api.getRegisterFieldFieldAccessPoliciesID(get_handle(parsed_field))
    parsed_policy = resolve_handle(api.getFieldAccessPoliciesFieldAccessPolicyIDs(parsed_holder_id)[0])
    broadcast_id = get_handle(parsed_policy.broadcasts.broadcast_to[0])
    assert api.getBroadcastToFieldRefByName(broadcast_id) == "target"
    reference_id = api.getBroadcastToFieldRefID(broadcast_id)
    assert api.removeRegisterFieldFieldAccessPolicices(get_handle(parsed_field))
    assert resolve_handle(broadcast_id) is None and resolve_handle(reference_id) is None
    SCHEMA.assertValid(etree.fromstring(XmlDocument.serializer().render(parsed).encode()))

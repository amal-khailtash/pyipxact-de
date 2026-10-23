"""Access policy field-data choices serialize in schema order after arbitrary edits."""

import pytest
from lxml import etree

from amal.eda.accellera.ipxact.v1685_2022.tgi import access_policy as api
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import TgiError, get_handle, resolve_handle
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import (
    AddressBlock,
    BaseAddress,
    Component,
    FieldType,
    MemoryMaps,
    MemoryMapType,
    UnsignedIntExpression,
    UnsignedLongintExpression,
    UnsignedPositiveIntExpression,
    UnsignedPositiveLongintExpression,
)
from org.accellera.ipxact.v1685_2022.address_block_type import AddressBlockType


def _document():
    policy = FieldType.FieldAccessPolicies.FieldAccessPolicy()
    field = FieldType(
        name="data",
        bit_offset=UnsignedIntExpression(value="0"),
        choice=[UnsignedPositiveIntExpression(value="8"), FieldType.FieldAccessPolicies(field_access_policy=[policy])],
    )
    register = AddressBlockType.Register(
        name="reg",
        address_offset=UnsignedLongintExpression(value="0"),
        choice=[UnsignedPositiveIntExpression(value="8"), field],
    )
    block = AddressBlock(
        name="regs",
        base_address=BaseAddress(value="0"),
        choice=[UnsignedPositiveLongintExpression(value="1"), UnsignedPositiveIntExpression(value="8"), register],
    )
    root = Component(
        vendor="v",
        library="l",
        name="c",
        version="1",
        memory_maps=MemoryMaps(memory_map=[MemoryMapType(name="map", choice=[block])]),
    )
    return root, policy


def _valid(root):
    schema = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))
    xml = XmlDocument.serializer().render(root)
    assert schema.validate(etree.fromstring(xml.encode())), schema.error_log


def test_reverse_setter_order_and_write_constraint_branches():
    root, policy = _document()
    pid = get_handle(policy)
    api.setFieldAccessPolicyReadResponse(pid, "8'h12")
    api.setFieldAccessPolicyReadAction(pid, "clear")
    api.setFieldAccessPolicyWriteValueConstraintMinMax(pid, "0", "255")
    api.setFieldAccessPolicyModifiedWriteValue(pid, "oneToClear")
    api.setFieldAccessPolicyAccess(pid, "read-write")
    _valid(root)
    wid = api.getFieldAccessPolicyWriteValueConstraintID(pid)
    minimum = api.getWriteValueConstraintMinimumID(wid)
    api.setFieldAccessPolicyWriteValueConstraintUseEnumeratedValue(pid, True)
    assert api.getFieldAccessPolicyWriteValueConstraintID(pid) == wid
    assert resolve_handle(minimum) is None
    _valid(root)
    api.setFieldAccessPolicyWriteValueConstraintWriteAsRead(pid, True)
    _valid(root)
    api.setFieldAccessPolicyWriteValueConstraintMinMax(pid, "1", "254")
    _valid(root)


def test_invalid_update_keeps_handle_and_expression():
    root, policy = _document()
    pid = get_handle(policy)
    api.setFieldAccessPolicyReadResponse(pid, "8'h12")
    rid = api.getFieldAccessPolicyReadResponseID(pid)
    api.setFieldAccessPolicyReadResponse(pid, "8'h34")
    assert api.getFieldAccessPolicyReadResponseID(pid) == rid
    assert api.getFieldAccessPolicyReadResponse(pid) == 52
    with pytest.raises(TgiError):
        api.setFieldAccessPolicyReadResponse(pid, 3)
    assert api.getFieldAccessPolicyReadResponseExpression(pid) == "8'h34"
    _valid(root)


def test_direct_constraint_branch_setters_preserve_schema_and_reject_partial_range():
    root, policy = _document()
    pid = get_handle(policy)
    api.setFieldAccessPolicyWriteValueConstraintMinMax(pid, "0", "255")
    wid = api.getFieldAccessPolicyWriteValueConstraintID(pid)
    minimum = api.getWriteValueConstraintMinimumID(wid)
    maximum = api.getWriteValueConstraintMaximumID(wid)
    api.setWriteValueConstraintMaximum(wid, "127")
    api.setWriteValueConstraintMinimum(wid, "1")
    assert api.getWriteValueConstraintMinimumID(wid) == minimum
    assert api.getWriteValueConstraintMaximumID(wid) == maximum
    _valid(root)
    api.setWriteValueConstraintUseEnumeratedValues(wid, True)
    with pytest.raises(TgiError):
        api.setWriteValueConstraintMinimum(wid, "2")
    assert api.getWriteValueConstraintUseEnumeratedValues(wid) is True
    _valid(root)
    api.setWriteValueConstraintWriteAsRead(wid, True)
    _valid(root)


def test_equal_policy_from_other_container_is_not_removed():
    _, first = _document()
    _, second = _document()
    container = FieldType.FieldAccessPolicies(field_access_policy=[first])
    assert first == second
    assert api.removeFieldAccessPoliciesFieldAccessPolicy(get_handle(container), get_handle(second)) is False
    assert container.field_access_policy[0] is first
    assert api.removeFieldAccessPoliciesFieldAccessPolicy(get_handle(container)) is True
    assert resolve_handle(get_handle(second)) is second


def test_restriction_masks_source_expressions_and_owned_removal():
    _, policy = _document()
    pid = get_handle(policy)
    restriction = api.addFieldAccessPolicyAccessRestriction(pid)
    assert api.getFieldAccessPolicyAccessRestrictionIDs(pid) == [restriction]
    api.setAccessRestrictionReadAccessMask(restriction, "8'hF0")
    api.setAccessRestrictionWriteAccessMask(restriction, "(1 << 4) - 1")
    assert api.getAccessRestrictionReadAccessMask(restriction) == 240
    assert api.getAccessRestrictionReadAccessMaskExpression(restriction) == "8'hF0"
    assert api.getAccessRestrictionWriteAccessMask(restriction) == 15
    assert api.getAccessRestrictionWriteAccessMaskExpression(restriction) == "(1 << 4) - 1"
    read = api.getAccessRestrictionReadAccessMaskID(restriction)
    write = api.getAccessRestrictionWriteAccessMaskID(restriction)
    api.setAccessRestrictionReadAccessMask(restriction, "8'hFF")
    assert api.getAccessRestrictionReadAccessMaskID(restriction) == read
    assert api.removeAccessRestrictionReadAccessMask(restriction)
    assert resolve_handle(read) is None
    assert api.removeAccessRestrictionWriteAccessMask(restriction)
    assert resolve_handle(write) is None
    assert api.removeFieldAccessPolicyAccessRestriction(restriction)
    assert resolve_handle(restriction) is None


def test_field_inline_removers_invalidate_values_and_constraint_subtree():
    _, policy = _document()
    pid = get_handle(policy)
    api.setFieldAccessPolicyReadResponse(pid, "8'h12")
    api.setFieldAccessPolicyReadAction(pid, "clear")
    api.setFieldAccessPolicyAccess(pid, "read-write")
    response = api.getFieldAccessPolicyReadResponseID(pid)
    action = api.getFieldAccessPolicyReadActionID(pid)
    assert api.removeFieldAccessPolicyReadResponse(pid)
    assert api.removeFieldAccessPolicyReadAction(pid)
    assert api.removeFieldAccessPolicyAccess(pid)
    assert resolve_handle(response) is None
    assert resolve_handle(action) is None
    assert api.getFieldAccessPolicyAccess(pid) is None
    api.setFieldAccessPolicyWriteValueConstraintMinMax(pid, "0", "255")
    wid = api.getFieldAccessPolicyWriteValueConstraintID(pid)
    minimum = api.getWriteValueConstraintMinimumID(wid)
    maximum = api.getWriteValueConstraintMaximumID(wid)
    assert api.removeFieldAccessPolicyWriteValueConstraint(pid)
    assert resolve_handle(wid) is None
    assert resolve_handle(minimum) is None
    assert resolve_handle(maximum) is None


def test_constraint_numeric_and_source_getters():
    _, policy = _document()
    pid = get_handle(policy)
    api.setFieldAccessPolicyReadAction(pid, "clear")
    assert api.getFieldAccessPolicyReadAction(pid) == "clear"
    api.setFieldAccessPolicyWriteValueConstraintMinMax(pid, "4'h1", "(1 << 8) - 1")
    wid = api.getFieldAccessPolicyWriteValueConstraintID(pid)
    assert api.getWriteValueConstraintMinimum(wid) == 1
    assert api.getWriteValueConstraintMinimumExpression(wid) == "4'h1"
    assert api.getWriteValueConstraintMaximum(wid) == 255
    assert api.getWriteValueConstraintMaximumExpression(wid) == "(1 << 8) - 1"
    api.setWriteValueConstraintWriteAsRead(wid, False)
    assert api.getWriteValueConstraintWriteAsRead(wid) is False


def test_optional_reserved_testable_and_broadcast_lifetimes():
    _, policy = _document()
    pid = get_handle(policy)
    api.setFieldAccessPolicyReserved(pid, "1'b0")
    assert api.getFieldAccessPolicyReserved(pid) is False
    assert api.getFieldAccessPolicyReservedExpression(pid) == "1'b0"
    reserved = api.getFieldAccessPolicyReservedID(pid)
    api.setFieldAccessPolicyReserved(pid, "1'b1")
    assert api.getFieldAccessPolicyReservedID(pid) == reserved
    api.setFieldAccessPolicyTestable(pid, False)
    assert api.getFieldAccessPolicyTestable(pid) is False
    testable = api.getFieldAccessPolicyTestableID(pid)
    api.setFieldAccessPolicyTestable(pid, True)
    assert api.getFieldAccessPolicyTestableID(pid) == testable
    broadcast = api.addFieldAccessPolicyBroadcastTo(pid, "map", "regs", "reg", "data")
    assert api.getFieldAccesspolicyBroadcastToIDs(pid) == [broadcast]
    assert api.removeFieldAccessPolicyBroadcastTo(broadcast)
    assert resolve_handle(broadcast) is None
    assert api.removeFieldAccessPolicyReserved(pid)
    assert api.removeFieldAccessPolicyTestable(pid)
    assert resolve_handle(reserved) is None
    assert resolve_handle(testable) is None


def test_policy_container_insertions_follow_owner_schema_order():
    root, _ = _document()
    block = root.memory_maps.memory_map[0].choice[0]
    register = block.choice[-1]
    api.addAddressBlockAccessPolicy(get_handle(block))
    api.addRegisterAccessPolicy(get_handle(register))
    _valid(root)

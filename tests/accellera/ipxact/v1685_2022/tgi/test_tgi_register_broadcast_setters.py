"""Broadcast named setters and the Annex field-handle setter contract."""

import inspect

import pytest

from amal.eda.accellera.ipxact.v1685_2022 import tgi as api
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import TgiError, TgiFaultCode, get_handle, resolve_handle
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import (
    AddressBlockRef,
    AlternateRegisterRef,
    FieldDefinitions,
    FieldRef,
    FieldType,
    Index,
    Indices,
    MemoryRemapRef,
    RegisterRef,
    UnsignedIntExpression,
    UnsignedPositiveIntExpression,
)

OWNERS = [
    FieldType.FieldAccessPolicies.FieldAccessPolicy.Broadcasts.BroadcastTo,
    FieldDefinitions.FieldDefinition.FieldAccessPolicies.FieldAccessPolicy.Broadcasts.BroadcastTo,
]
DIRECT = [
    ("AddressBlock", "address_block_ref", AddressBlockRef, "addressBlockRef"),
    ("AlternateRegister", "alternate_register_ref", AlternateRegisterRef, "alternateRegisterRef"),
    ("Register", "register_ref", RegisterRef, "registerRef"),
]


@pytest.mark.parametrize("owner_type", OWNERS)
@pytest.mark.parametrize("kind,attribute,model,parameter", DIRECT)
def test_direct_setters_create_then_preserve_wrapper_indices_and_metadata(
    owner_type, kind, attribute, model, parameter
):
    owner = owner_type(field_ref=FieldRef(field_ref="field"))
    operation = getattr(api, f"setBroadcastTo{kind}Ref")
    assert list(inspect.signature(operation).parameters) == ["broadcastToID", parameter]
    assert operation(**{"broadcastToID": get_handle(owner), parameter: "first"}) is True
    child = getattr(owner, attribute)
    assert type(child) is model
    if model in (AddressBlockRef, RegisterRef):
        child.indices = Indices(index=[Index(value="2")])
    handle = get_handle(child)
    indices = getattr(child, "indices", None)
    assert operation(get_handle(owner), "  next  ") is True
    assert getattr(owner, attribute) is child
    assert getattr(child, attribute) == "next"
    assert resolve_handle(handle) is child
    assert getattr(child, "indices", None) is indices
    parsed = XmlDocument.parser().from_string(XmlDocument.serializer().render(owner), owner_type)
    assert getattr(getattr(parsed, attribute), attribute) == "next"
    for invalid in (None, [], {}, "", "bad name", "1bad"):
        with pytest.raises(TgiError) as error:
            operation(get_handle(owner), invalid)
        assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
        assert getattr(child, attribute) == "next"
    setattr(owner, attribute, FieldRef(field_ref="wrong"))
    with pytest.raises(TgiError) as error:
        operation(get_handle(owner), "valid")
    assert error.value.fault_code == TgiFaultCode.INVALID_ID


@pytest.mark.parametrize("owner_type", OWNERS)
def test_memory_map_choice_preserves_map_remap_and_invalidates_address_space(owner_type):
    address = owner_type.AddressSpaceRef(address_space_ref="space")
    owner = owner_type(field_ref=FieldRef(field_ref="field"))
    original = (address,)
    owner.address_space_ref_or_memory_map_ref_or_memory_remap_ref = original
    address_id = get_handle(address)
    with pytest.raises(TgiError):
        api.setBroadcastToMemoryMapRef(get_handle(owner), "bad name")
    assert owner.address_space_ref_or_memory_map_ref_or_memory_remap_ref is original
    assert resolve_handle(address_id) is address
    assert api.setBroadcastToMemoryMapRef(get_handle(owner), "map") is True
    assert resolve_handle(address_id) is None
    memory_map = owner.address_space_ref_or_memory_map_ref_or_memory_remap_ref[0]
    remap = MemoryRemapRef(memory_remap_ref="remap")
    owner.address_space_ref_or_memory_map_ref_or_memory_remap_ref = (memory_map, remap)
    map_id, remap_id = get_handle(memory_map), get_handle(remap)
    assert api.setBroadcastToMemoryMapRef(get_handle(owner), "next") is True
    assert owner.address_space_ref_or_memory_map_ref_or_memory_remap_ref == [memory_map, remap]
    assert memory_map.memory_map_ref == "next"
    assert resolve_handle(map_id) is memory_map and resolve_handle(remap_id) is remap
    malformed = (remap, memory_map)
    owner.address_space_ref_or_memory_map_ref_or_memory_remap_ref = malformed
    with pytest.raises(TgiError) as error:
        api.setBroadcastToMemoryMapRef(get_handle(owner), "valid")
    assert error.value.fault_code == TgiFaultCode.INVALID_ID
    assert owner.address_space_ref_or_memory_map_ref_or_memory_remap_ref is malformed
    assert memory_map.memory_map_ref == "next"


@pytest.mark.parametrize("owner_type", OWNERS)
@pytest.mark.parametrize("field_type", [FieldType, FieldDefinitions.FieldDefinition])
def test_field_setter_consumes_target_handle_and_preserves_reference_indices(owner_type, field_type):
    reference = FieldRef(field_ref="old", indices=Indices(index=[Index(value="3")]))
    owner = owner_type(field_ref=reference)
    target = (
        field_type(name="  target  ", bit_offset=UnsignedIntExpression(value="0"))
        if field_type is FieldType
        else field_type(name="  target  ", bit_width=UnsignedPositiveIntExpression(value="8"))
    )
    ref_id, index_id = get_handle(reference), get_handle(reference.indices.index[0])
    assert list(inspect.signature(api.setBroadcastToFieldRef).parameters) == ["broadcastToID", "fieldRef"]
    assert api.setBroadcastToFieldRef(get_handle(owner), get_handle(target)) is True
    assert owner.field_ref is reference and reference.field_ref == "target"
    assert target.name == "  target  "
    assert resolve_handle(ref_id) is reference and resolve_handle(index_id) is reference.indices.index[0]
    for invalid in (None, [], {}, "target", "missing", get_handle(FieldRef(field_ref="wrong"))):
        with pytest.raises(TgiError) as error:
            api.setBroadcastToFieldRef(get_handle(owner), invalid)
        assert error.value.fault_code == TgiFaultCode.INVALID_ID
        assert reference.field_ref == "target"
    target.name = "bad name"
    with pytest.raises(TgiError) as error:
        api.setBroadcastToFieldRef(get_handle(owner), get_handle(target))
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert reference.field_ref == "target"
    target.name = "created"
    owner.field_ref = None
    assert api.setBroadcastToFieldRef(get_handle(owner), get_handle(target)) is True
    assert type(owner.field_ref) is FieldRef and owner.field_ref.field_ref == "created"


def test_all_setters_reject_wrong_owner_handles():
    for kind in ("AddressBlock", "AlternateRegister", "Field", "MemoryMap", "Register"):
        operation = getattr(api, f"setBroadcastTo{kind}Ref")
        for invalid in (
            None,
            [],
            {},
            "missing",
            get_handle(FieldType(name="wrong", bit_offset=UnsignedIntExpression(value="0"))),
        ):
            with pytest.raises(TgiError) as error:
                operation(invalid, "target")
            assert error.value.fault_code == TgiFaultCode.INVALID_ID

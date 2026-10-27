"""Broadcast optional/path removal, descendant invalidation and ownership."""

import inspect

import pytest

from amal.eda.accellera.ipxact.v1685_2022 import tgi as api
from amal.eda.accellera.ipxact.v1685_2022.tgi.component import _register_graph
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import TgiError, TgiFaultCode, get_handle, resolve_handle
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import (
    AddressBlockRef,
    AlternateRegisterRef,
    BankRef,
    FieldDefinitions,
    FieldRef,
    FieldType,
    Index,
    Indices,
    MemoryRemapRef,
    RegisterFileRef,
    RegisterRef,
)

OWNERS = [
    FieldType.FieldAccessPolicies.FieldAccessPolicy.Broadcasts.BroadcastTo,
    FieldDefinitions.FieldDefinition.FieldAccessPolicies.FieldAccessPolicy.Broadcasts.BroadcastTo,
]
DIRECT = [
    ("AddressBlock", "address_block_ref", AddressBlockRef),
    ("AlternateRegister", "alternate_register_ref", AlternateRegisterRef),
    ("Register", "register_ref", RegisterRef),
]
PATHS = [
    ("Bank", "bank_ref", BankRef, "bankRefID"),
    ("RegisterFile", "register_file_ref", RegisterFileRef, "registerRefID"),
]


@pytest.mark.parametrize("owner_type", OWNERS)
@pytest.mark.parametrize("kind,attribute,model", DIRECT)
def test_direct_removal_preserves_siblings_and_invalidates_descendants(owner_type, kind, attribute, model):
    child = model(**{attribute: "missingTarget"})
    if model in (AddressBlockRef, RegisterRef):
        child.indices = Indices(index=[Index(value="2")])
    owner = owner_type(field_ref=FieldRef(field_ref="target"), **{attribute: child})
    child_id = get_handle(child)
    indices = (
        [get_handle(child.indices), get_handle(child.indices.index[0])]
        if model in (AddressBlockRef, RegisterRef)
        else []
    )
    operation = getattr(api, f"removeBroadcastTo{kind}Ref")
    assert list(inspect.signature(operation).parameters) == ["broadcastToID"]
    field_ref = owner.field_ref
    assert operation(get_handle(owner)) is True
    assert getattr(owner, attribute) is None
    assert all(resolve_handle(handle) is None for handle in [child_id, *indices])
    assert owner.field_ref is field_ref
    assert operation(get_handle(owner)) is False


@pytest.mark.parametrize("owner_type", OWNERS)
def test_memory_map_removal_prunes_remap_and_preserves_other_references(owner_type):
    memory_map = owner_type.MemoryMapRef(memory_map_ref="map")
    remap = MemoryRemapRef(memory_remap_ref="remap")
    owner = owner_type(
        field_ref=FieldRef(field_ref="target"),
        address_space_ref_or_memory_map_ref_or_memory_remap_ref=(memory_map, remap),
        register_ref=RegisterRef(register_ref="register"),
    )
    map_id, remap_id = get_handle(memory_map), get_handle(remap)
    register = owner.register_ref
    assert api.removeBroadcastToMemoryMapRef(get_handle(owner)) is True
    assert owner.address_space_ref_or_memory_map_ref_or_memory_remap_ref == []
    assert resolve_handle(map_id) is None and resolve_handle(remap_id) is None
    assert owner.register_ref is register
    assert api.removeBroadcastToMemoryMapRef(get_handle(owner)) is False
    address = owner_type.AddressSpaceRef(address_space_ref="space")
    original = (address,)
    owner.address_space_ref_or_memory_map_ref_or_memory_remap_ref = original
    assert api.removeBroadcastToMemoryMapRef(get_handle(owner)) is False
    assert owner.address_space_ref_or_memory_map_ref_or_memory_remap_ref is original
    owner.address_space_ref_or_memory_map_ref_or_memory_remap_ref = (remap,)
    with pytest.raises(TgiError) as error:
        api.removeBroadcastToMemoryMapRef(get_handle(owner))
    assert error.value.fault_code == TgiFaultCode.INVALID_ID


@pytest.mark.parametrize("owner_type", OWNERS)
@pytest.mark.parametrize("kind,attribute,model,parameter", PATHS)
def test_path_removal_matches_owner_family_preserves_order_and_parsed_indices(
    owner_type, kind, attribute, model, parameter
):
    first, second = model(**{attribute: "first"}), model(**{attribute: "second"})
    if model is RegisterFileRef:
        first.indices = Indices(index=[Index(value="1")])
    owner = owner_type(field_ref=FieldRef(field_ref="target"), **{attribute: (first, second)})
    parsed = XmlDocument.parser().from_string(XmlDocument.serializer().render(owner), owner_type)
    _register_graph(parsed)
    first, second = getattr(parsed, attribute)
    first_id = get_handle(first)
    descendant = get_handle(first.indices.index[0]) if model is RegisterFileRef else None
    operation = getattr(api, f"removeBroadcastTo{kind}Ref")
    assert list(inspect.signature(operation).parameters) == [parameter]
    assert operation(**{parameter: first_id}) is True
    assert getattr(parsed, attribute) == [second]
    assert resolve_handle(first_id) is None
    if descendant is not None:
        assert resolve_handle(descendant) is None
    with pytest.raises(TgiError) as error:
        operation(first_id)
    assert error.value.fault_code == TgiFaultCode.INVALID_ID
    other = FieldType.AliasOf(field_ref=FieldRef(field_ref="target"), **{attribute: [model(**{attribute: "foreign"})]})
    _register_graph(other)
    with pytest.raises(TgiError) as error:
        operation(get_handle(getattr(other, attribute)[0]))
    assert error.value.fault_code == TgiFaultCode.INVALID_ID
    assert len(getattr(other, attribute)) == 1


def test_all_removers_reject_invalid_handles_and_wrong_models():
    for kind in ("AddressBlock", "AlternateRegister", "Bank", "MemoryMap", "RegisterFile", "Register"):
        operation = getattr(api, f"removeBroadcastTo{kind}Ref")
        for invalid in (None, [], {}, "missing", get_handle(FieldRef(field_ref="wrong"))):
            with pytest.raises(TgiError) as error:
                operation(invalid)
            assert error.value.fault_code == TgiFaultCode.INVALID_ID
    owner = OWNERS[0](field_ref=FieldRef(field_ref="target"), register_ref=BankRef(bank_ref="wrong"))
    with pytest.raises(TgiError) as error:
        api.removeBroadcastToRegisterRef(get_handle(owner))
    assert error.value.fault_code == TgiFaultCode.INVALID_ID

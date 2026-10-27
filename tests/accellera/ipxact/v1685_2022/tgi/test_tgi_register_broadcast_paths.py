"""Ordered Broadcast bank/register-file paths and RegisterRef inspection."""

import inspect

import pytest

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
    BankRef,
    FieldDefinitions,
    FieldRef,
    FieldType,
    Index,
    Indices,
    RegisterFileRef,
    RegisterRef,
)

OWNERS = [
    FieldType.FieldAccessPolicies.FieldAccessPolicy.Broadcasts.BroadcastTo,
    FieldDefinitions.FieldDefinition.FieldAccessPolicies.FieldAccessPolicy.Broadcasts.BroadcastTo,
]
PATHS = [
    ("Bank", BankRef, "bank_ref", "bankRef"),
    ("RegisterFile", RegisterFileRef, "register_file_ref", "registerFileRef"),
]


@pytest.mark.parametrize("kind,model,attribute,parameter", PATHS)
@pytest.mark.parametrize("owner_type", OWNERS)
def test_paths_sources_order_tuple_and_owned_addition(kind, model, attribute, parameter, owner_type):
    index = Index(value="1")
    first = model(
        **{
            attribute: " \tfirst\n",
            **({"indices": Indices(index=[index])} if model is RegisterFileRef else {"id": "first_id"}),
        }
    )
    second = model(**{attribute: "second"})
    owner = owner_type(field_ref=FieldRef(field_ref="target"), **{attribute: (first, second)})
    owner_id = get_handle(owner)
    getter = getattr(api, f"getBroadcastTo{kind}RefByNames")
    ids = getattr(api, f"getBroadcastTo{kind}RefIDs")
    add = getattr(api, f"addBroadcastTo{kind}Ref")
    assert list(inspect.signature(add).parameters) == ["broadcastToID", parameter]
    assert all(fn.__name__ in register.__all__ for fn in (getter, ids, add))
    original = getattr(owner, attribute)
    assert getter(owner_id) == ["first", "second"]
    assert ids(owner_id) == [get_handle(first), get_handle(second)]
    assert getattr(owner, attribute) is original and getattr(first, attribute) == " \tfirst\n"
    assert get_parent_info(get_handle(first)).parent_handle == owner_id
    if model is RegisterFileRef:
        assert get_parent_info(get_handle(index)).parent_handle == get_handle(first.indices)
    for invalid in ("bad Name", "", False, 3):
        with pytest.raises(TgiError) as error:
            add(owner_id, invalid)
        assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
        assert getattr(owner, attribute) is original
    new_id = add(**{"broadcastToID": owner_id, parameter: "second"})
    assert isinstance(resolve_handle(new_id), model)
    assert getter(owner_id) == ["first", "second", "second"]
    assert ids(owner_id) == [get_handle(first), get_handle(second), new_id]
    if model is RegisterFileRef:
        assert first.indices.index[0] is index
    else:
        assert first.id == "first_id"
    parsed = XmlDocument.parser().from_string(XmlDocument.serializer().render(owner), owner_type)
    assert getattr(api, f"getBroadcastTo{kind}RefByNames")(get_handle(parsed)) == ["first", "second", "second"]


@pytest.mark.parametrize("kind,model,attribute,parameter", PATHS)
def test_invalid_path_model_and_source_are_atomic(kind, model, attribute, parameter):
    owner = OWNERS[0](field_ref=FieldRef(field_ref="target"))
    for bad in ("bad", [FieldRef(field_ref="wrong")], [model(**{attribute: "bad Name"})]):
        setattr(owner, attribute, bad)
        for operation in (
            lambda: getattr(api, f"getBroadcastTo{kind}RefIDs")(get_handle(owner)),
            lambda: getattr(api, f"addBroadcastTo{kind}Ref")(get_handle(owner), "target"),
        ):
            with pytest.raises(TgiError) as error:
                operation()
            assert error.value.fault_code == TgiFaultCode.INVALID_ID
            assert getattr(owner, attribute) is bad


@pytest.mark.parametrize("owner_type", OWNERS)
def test_register_reference_source_and_index_identity(owner_type):
    reference = RegisterRef(register_ref=" \tregister\n", indices=Indices(index=[Index(value="2")]))
    owner = owner_type(field_ref=FieldRef(field_ref="target"), register_ref=reference)
    owner_id, ref_id = get_handle(owner), get_handle(reference)
    assert api.getBroadcastToRegisterRefByName(owner_id) == "register"
    assert api.getBroadcastToRegisterRefID(owner_id) == ref_id
    assert get_parent_info(ref_id).parent_handle == owner_id
    assert reference.register_ref == " \tregister\n" and reference.indices.index[0].value == "2"
    reference.register_ref = "bad Name"
    with pytest.raises(TgiError) as error:
        api.getBroadcastToRegisterRefID(owner_id)
    assert error.value.fault_code == TgiFaultCode.INVALID_ID
    owner.register_ref = None
    assert api.getBroadcastToRegisterRefID(owner_id) is None
    assert api.getBroadcastToRegisterRefByName(owner_id) is None


def test_public_operations_reject_invalid_owners():
    names = [f"getBroadcastTo{kind}Ref{suffix}" for kind in ("Bank", "RegisterFile") for suffix in ("ByNames", "IDs")]
    names += [
        "getBroadcastToRegisterRefByName",
        "getBroadcastToRegisterRefID",
        "addBroadcastToBankRef",
        "addBroadcastToRegisterFileRef",
    ]
    for name in names:
        operation = getattr(api, name)
        for invalid in (None, [], "missing", get_handle(FieldRef(field_ref="wrong"))):
            with pytest.raises(TgiError) as error:
                operation(*([invalid, "target"] if name.startswith("add") else [invalid]))
            assert error.value.fault_code == TgiFaultCode.INVALID_ID

"""Register alias source, typed ownership and choice contracts."""

import inspect

import pytest

from amal.eda.accellera.ipxact.v1685_2022 import tgi as api
from amal.eda.accellera.ipxact.v1685_2022.tgi import register
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import (
    TgiError,
    TgiFaultCode,
    detach_child_by_handle,
    get_handle,
    get_parent_info,
    resolve_handle,
)
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022.alternate_register_ref import AlternateRegisterRef
from org.accellera.ipxact.v1685_2022.enumerated_values import EnumeratedValues
from org.accellera.ipxact.v1685_2022.field_ref import FieldRef
from org.accellera.ipxact.v1685_2022.field_type import FieldType
from org.accellera.ipxact.v1685_2022.indices import Indices
from org.accellera.ipxact.v1685_2022.register_ref import RegisterRef
from org.accellera.ipxact.v1685_2022.unsigned_int_expression import UnsignedIntExpression
from org.accellera.ipxact.v1685_2022.unsigned_positive_int_expression import UnsignedPositiveIntExpression

CASES = [
    ("AlternateRegister", "alternate_register_ref", "alternateRegisterRef", AlternateRegisterRef),
    ("Field", "field_ref", "fieldRef", FieldRef),
    ("Register", "register_ref", "registerRef", RegisterRef),
]


def alias() -> FieldType.AliasOf:
    return FieldType.AliasOf(
        field_ref=FieldRef(field_ref="targetField", indices=Indices(index=[UnsignedIntExpression(value="2")])),
        register_ref=RegisterRef(
            register_ref="targetRegister", indices=Indices(index=[UnsignedIntExpression(value="3")])
        ),
        alternate_register_ref=AlternateRegisterRef(alternate_register_ref="targetAlternate"),
    )


@pytest.mark.parametrize("kind,attribute,parameter,model", CASES)
def test_signatures_and_source_edits_preserve_wrappers_indices_and_siblings(kind, attribute, parameter, model):
    owner = alias()
    owner_id = get_handle(owner)
    child = getattr(owner, attribute)
    child_id = get_handle(child)
    siblings = (owner.field_ref, owner.register_ref, owner.alternate_register_ref)
    indices = getattr(child, "indices", None)
    indices_id = get_handle(indices) if indices is not None else None
    getter = getattr(api, f"getAliasOf{kind}RefByName")
    ids = getattr(api, f"getAliasOf{kind}RefID")
    setter = getattr(api, f"setAliasOf{kind}Ref")
    assert list(inspect.signature(setter).parameters) == ["aliasOfID", parameter]
    for operation in (getter, ids):
        assert list(inspect.signature(operation).parameters) == ["aliasOfID"]
    assert all(operation.__name__ in register.__all__ for operation in (getter, ids, setter))
    assert getter(owner_id) == getattr(child, attribute)
    assert ids(owner_id) == child_id
    assert setter(**{"aliasOfID": owner_id, parameter: "new:Name"}) is True
    assert getter(owner_id) == "new:Name"
    assert ids(owner_id) == child_id
    assert getattr(owner, attribute) is child
    assert (owner.field_ref, owner.register_ref, owner.alternate_register_ref) == siblings
    if indices_id is not None:
        assert child.indices is indices and resolve_handle(indices_id) is indices
    assert get_parent_info(child_id).parent_handle == owner_id


@pytest.mark.parametrize("kind,attribute,parameter,model", CASES)
def test_absent_reference_creation_and_owned_descendant_invalidation(kind, attribute, parameter, model):
    owner = alias()
    setattr(owner, attribute, None)
    owner_id = get_handle(owner)
    assert getattr(api, f"getAliasOf{kind}RefID")(owner_id) is None
    assert getattr(api, f"getAliasOf{kind}RefByName")(owner_id) is None
    assert getattr(api, f"setAliasOf{kind}Ref")(owner_id, "deferredTarget") is True
    child = getattr(owner, attribute)
    assert isinstance(child, model)
    child_id = getattr(api, f"getAliasOf{kind}RefID")(owner_id)
    assert resolve_handle(child_id) is child
    assert detach_child_by_handle(child_id)
    assert resolve_handle(child_id) is None
    assert getattr(owner, attribute) is None


@pytest.mark.parametrize("kind,attribute,parameter,model", CASES)
@pytest.mark.parametrize("invalid", ["bad Name", "", 2, False])
def test_invalid_names_are_atomic(kind, attribute, parameter, model, invalid):
    owner = alias()
    child = getattr(owner, attribute)
    original = getattr(child, attribute)
    with pytest.raises(TgiError) as error:
        getattr(api, f"setAliasOf{kind}Ref")(get_handle(owner), invalid)
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert getattr(owner, attribute) is child and getattr(child, attribute) == original


@pytest.mark.parametrize("kind,attribute,parameter,model", CASES)
def test_malformed_stored_names_and_wrong_models_fault(kind, attribute, parameter, model):
    owner = alias()
    child = getattr(owner, attribute)
    setattr(child, attribute, "bad Name")
    for suffix in ("ByName", "ID"):
        with pytest.raises(TgiError) as error:
            getattr(api, f"getAliasOf{kind}Ref{suffix}")(get_handle(owner))
        assert error.value.fault_code == TgiFaultCode.INVALID_ID
    # A valid setter can repair the stored source without changing its wrapper.
    assert getattr(api, f"setAliasOf{kind}Ref")(get_handle(owner), "fixedName")
    setattr(
        owner, attribute, FieldRef(field_ref="wrong") if model is not FieldRef else RegisterRef(register_ref="wrong")
    )
    with pytest.raises(TgiError) as error:
        getattr(api, f"setAliasOf{kind}Ref")(get_handle(owner), "fixedName")
    assert error.value.fault_code == TgiFaultCode.INVALID_ID


@pytest.mark.parametrize("invalid", [None, [], {}, 1, "unknown", get_handle(FieldRef(field_ref="other"))])
def test_wrong_alias_handles_fault_for_all_operations(invalid):
    for kind, _, _, _ in CASES:
        for suffix in ("ByName", "ID"):
            with pytest.raises(TgiError) as error:
                getattr(api, f"getAliasOf{kind}Ref{suffix}")(invalid)
            assert error.value.fault_code == TgiFaultCode.INVALID_ID
        with pytest.raises(TgiError) as error:
            getattr(api, f"setAliasOf{kind}Ref")(invalid, "target")
        assert error.value.fault_code == TgiFaultCode.INVALID_ID


def test_field_alias_choice_companions_parsed_ownership_and_xml_round_trip():
    owner = alias()
    field = FieldType(
        name="aliasField", bit_offset=UnsignedIntExpression(value="0"), choice=("AliasType", owner, EnumeratedValues())
    )
    field_id = get_handle(field)
    alias_id = api.getRegisterFieldAliasOfID(field_id)
    assert alias_id == get_handle(owner)
    assert get_parent_info(alias_id).parent_handle == field_id
    assert isinstance(field.choice, tuple)
    xml = XmlDocument.serializer().render(field)
    parsed = XmlDocument.parser().from_string(xml, FieldType)
    parsed_id = api.getRegisterFieldAliasOfID(get_handle(parsed))
    assert api.getAliasOfFieldRefByName(parsed_id) == "targetField"
    assert api.getAliasOfRegisterRefByName(parsed_id) == "targetRegister"
    assert api.setAliasOfFieldRef(parsed_id, "editedField")
    reparsed = XmlDocument.parser().from_string(XmlDocument.serializer().render(parsed), FieldType)
    assert reparsed.choice[1].field_ref.field_ref == "editedField"
    index_id = get_handle(parsed.choice[1].field_ref.indices.index[0])
    assert detach_child_by_handle(parsed_id)
    assert resolve_handle(index_id) is None


@pytest.mark.parametrize(
    "extra",
    [
        False,
        FieldType.Resets(),
        UnsignedPositiveIntExpression(value="8"),
        FieldType.FieldDefinitionRef(value="definition", type_definitions="library"),
        alias(),
    ],
)
def test_field_alias_rejects_incompatible_or_duplicate_branches(extra):
    field = FieldType(name="field", bit_offset=UnsignedIntExpression(value="0"), choice=(alias(), extra))
    original = field.choice
    with pytest.raises(TgiError) as error:
        api.getRegisterFieldAliasOfID(get_handle(field))
    assert error.value.fault_code == TgiFaultCode.INVALID_ID
    assert field.choice is original


def test_field_alias_optional_and_invalid_handle_contract():
    field = FieldType(
        name="inline", bit_offset=UnsignedIntExpression(value="0"), choice=[UnsignedPositiveIntExpression(value="8")]
    )
    assert api.getRegisterFieldAliasOfID(get_handle(field)) is None
    field.choice = [FieldType.FieldDefinitionRef(value="definition", type_definitions="library")]
    assert api.getRegisterFieldAliasOfID(get_handle(field)) is None
    for invalid in (None, [], "missing", get_handle(alias())):
        with pytest.raises(TgiError) as error:
            api.getRegisterFieldAliasOfID(invalid)
        assert error.value.fault_code == TgiFaultCode.INVALID_ID

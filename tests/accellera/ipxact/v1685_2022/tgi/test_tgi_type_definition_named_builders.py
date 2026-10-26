"""Generated named Type definitions collection lifecycle contracts."""

from collections.abc import Iterator
from inspect import signature

import pytest

from amal.eda.accellera.ipxact.v1685_2022 import tgi
from amal.eda.accellera.ipxact.v1685_2022.tgi import type_definitions as api
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import TgiError, TgiFaultCode, get_handle, registry, resolve_handle
from org.accellera.ipxact.v1685_2022 import (
    BankDefinitions,
    FieldAccessPolicyDefinitions,
    MemoryMapDefinitions,
    MemoryRemapDefinitions,
    TypeDefinitions,
)

_FAMILIES = (
    ("BankDefinition", "bank_definitions", "bank_definition", BankDefinitions, BankDefinitions.BankDefinition, 8),
    (
        "FieldAccessPolicyDefinition",
        "field_access_policy_definitions",
        "field_access_policy_definition",
        FieldAccessPolicyDefinitions,
        FieldAccessPolicyDefinitions.FieldAccessPolicyDefinition,
        12,
    ),
    (
        "MemoryMapDefinition",
        "memory_map_definitions",
        "memory_map_definition",
        MemoryMapDefinitions,
        MemoryMapDefinitions.MemoryMapDefinition,
        14,
    ),
    (
        "MemoryRemapDefinition",
        "memory_remap_definitions",
        "memory_remap_definition",
        MemoryRemapDefinitions,
        MemoryRemapDefinitions.MemoryRemapDefinition,
        15,
    ),
    ("Mode", "modes", "mode", TypeDefinitions.Modes, TypeDefinitions.Modes.Mode, 16),
    ("ResetType", "reset_types", "reset_type", TypeDefinitions.ResetTypes, TypeDefinitions.ResetTypes.ResetType, 19),
    ("View", "views", "view", TypeDefinitions.Views, TypeDefinitions.Views.View, 20),
)


@pytest.fixture(autouse=True)
def clear_registry() -> Iterator[None]:
    registry.clear()
    yield
    registry.clear()


def _root() -> TypeDefinitions:
    return TypeDefinitions(vendor="example.org", library="types", name="definitions", version="1.0")


@pytest.mark.parametrize("family", _FAMILIES, ids=[row[0] for row in _FAMILIES])
def test_typed_creation_unique_names_and_tuple_preservation(family: tuple[str, str, str, type, type, int]) -> None:
    label, attribute, member, holder_type, model, section = family
    operation = getattr(api, "addTypeDefinitions" + label)
    contract = signature(operation)
    assert tuple(contract.parameters) == ("typeDefinitionsID", "name")
    assert all(parameter.annotation is str for parameter in contract.parameters.values())
    assert contract.return_annotation is str
    assert f"F.7.82.{section}" in operation.__doc__
    assert getattr(tgi, operation.__name__) is operation
    root = _root()
    root_id = get_handle(root)
    first_id = operation(root_id, "  α:first  ")
    first = resolve_handle(first_id)
    assert isinstance(first, model)
    assert first.name == "α:first"
    holder = getattr(root, attribute)
    assert isinstance(holder, holder_type)
    values = (first,)
    setattr(holder, member, values)
    with pytest.raises(TgiError) as error:
        operation(root_id, "α:first")
    assert error.value.fault_code == TgiFaultCode.ALREADY_EXISTS
    assert getattr(holder, member) is values
    second_id = operation(root_id, "second")
    assert getattr(holder, member) == [first, resolve_handle(second_id)]
    assert getattr(root, attribute) is holder
    assert resolve_handle(first_id) is first


@pytest.mark.parametrize("family", _FAMILIES, ids=[row[0] for row in _FAMILIES])
def test_wrong_owners_names_and_malformed_holders_reject_atomically(
    family: tuple[str, str, str, type, type, int],
) -> None:
    label, attribute, member, holder_type, model, _ = family
    operation = getattr(api, "addTypeDefinitions" + label)
    for handle in ("stale", get_handle(model(name="wrong"))):
        with pytest.raises(TgiError) as error:
            operation(handle, "new")
        assert error.value.fault_code == TgiFaultCode.INVALID_ID
    root = _root()
    for name in ("", "two names", None, 3):
        with pytest.raises(TgiError) as error:
            operation(get_handle(root), name)
        assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
        assert getattr(root, attribute) is None
    setattr(root, attribute, model(name="wrong_holder"))
    original = getattr(root, attribute)
    with pytest.raises(TgiError) as error:
        operation(get_handle(root), "new")
    assert error.value.fault_code == TgiFaultCode.INVALID_ID
    assert getattr(root, attribute) is original
    holder = holder_type()
    values = (model(name="bad name"),)
    setattr(holder, member, values)
    setattr(root, attribute, holder)
    with pytest.raises(TgiError) as error:
        operation(get_handle(root), "new")
    assert error.value.fault_code == TgiFaultCode.INVALID_ID
    assert getattr(holder, member) is values


def test_field_policy_removal_membership_and_empty_holder_pruning() -> None:
    root = _root()
    first_id = api.addTypeDefinitionsFieldAccessPolicyDefinition(get_handle(root), "first")
    second_id = api.addTypeDefinitionsFieldAccessPolicyDefinition(get_handle(root), "second")
    holder = root.field_access_policy_definitions
    holder_id = get_handle(holder)
    assert api.removeTypeDefinitionsFieldAccessPolicyDefinition(first_id)
    assert resolve_handle(first_id) is None
    assert resolve_handle(second_id) is holder.field_access_policy_definition[0]
    assert api.removeTypeDefinitionsFieldAccessPolicyDefinition(second_id)
    assert root.field_access_policy_definitions is None
    assert resolve_handle(holder_id) is None
    for handle in (second_id, get_handle(FieldAccessPolicyDefinitions.FieldAccessPolicyDefinition(name="orphan"))):
        with pytest.raises(TgiError) as error:
            api.removeTypeDefinitionsFieldAccessPolicyDefinition(handle)
        assert error.value.fault_code == TgiFaultCode.INVALID_ID


def test_parsed_field_policy_removal_discovers_root_ownership() -> None:
    from amal.eda.ipxact_de.xml_document import XmlDocument

    root = _root()
    root.field_access_policy_definitions = FieldAccessPolicyDefinitions(
        field_access_policy_definition=[FieldAccessPolicyDefinitions.FieldAccessPolicyDefinition(name="policy")]
    )
    parsed = XmlDocument.parser().from_string(XmlDocument.serializer().render(root), TypeDefinitions)
    registry.register(parsed, (parsed.vendor, parsed.library, parsed.name, parsed.version))
    holder = parsed.field_access_policy_definitions
    child = holder.field_access_policy_definition[0]
    holder_id = get_handle(holder)
    child_id = get_handle(child)
    assert api.removeTypeDefinitionsFieldAccessPolicyDefinition(child_id)
    assert parsed.field_access_policy_definitions is None
    assert resolve_handle(holder_id) is None
    assert resolve_handle(child_id) is None

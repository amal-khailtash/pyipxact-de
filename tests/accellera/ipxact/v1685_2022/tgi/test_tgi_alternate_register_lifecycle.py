"""Alternate-register field and modeRef lifecycle operations."""

from collections.abc import Iterator
from dataclasses import fields, is_dataclass
from inspect import signature
from pathlib import Path
from typing import Any

import pytest
from lxml import etree

import amal.eda.accellera.ipxact.v1685_2022.tgi as tgi
from amal.eda.accellera.ipxact.v1685_2022.tgi import register as api
from amal.eda.accellera.ipxact.v1685_2022.tgi.component import _register_graph
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import (
    TgiError,
    TgiFaultCode,
    get_handle,
    get_parent_info,
    registry,
    resolve_handle,
)
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import Component
from org.accellera.ipxact.v1685_2022.access_restriction_type import AccessRestrictionType
from org.accellera.ipxact.v1685_2022.alternate_registers import AlternateRegisters
from org.accellera.ipxact.v1685_2022.field_type import FieldType
from org.accellera.ipxact.v1685_2022.mode_ref import ModeRef
from org.accellera.ipxact.v1685_2022.unsigned_int_expression import UnsignedIntExpression
from org.accellera.ipxact.v1685_2022.unsigned_positive_int_expression import UnsignedPositiveIntExpression

_SAMPLE = Path("tests/xml/ipxact/v1685_2022/accellera.org/Sample/SampleComponent/1.0/xml/SampleComponent.xml")
_SCHEMA = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))
_OPERATIONS = (
    ("getAlternateRegisterFieldIDs", ("alternateRegisterID",), "F.7.73.7"),
    ("getAlternateRegisterModeRefIDs", ("alternateRegisterID",), "F.7.73.8"),
    ("addAlternateRegisterField", ("alternateRegisterID", "name", "offset", "width"), "F.7.74.1"),
    ("addAlternaterRegisterModeRef", ("alternateRegisterID", "modeRef", "priority"), "F.7.74.2"),
    ("removeAlternateRegisterField", ("regFieldID",), "F.7.74.13"),
    ("removeAlternaterRegisterModeRef", ("modeRefID",), "F.7.74.16"),
    ("setModeRefPriority", ("modeRefID", "priority"), "F.7.74.55"),
)


@pytest.fixture(autouse=True)
def clean_registry() -> Iterator[None]:
    registry.clear()
    yield
    registry.clear()


def _field(name: str = "flag") -> FieldType:
    return FieldType(
        name=name,
        bit_offset=UnsignedIntExpression(value="0"),
        choice=[UnsignedPositiveIntExpression(value="1")],
    )


def _alternate(
    *,
    name: str = "alternate",
    fields_: list[FieldType] | tuple[FieldType, ...] = (),
    mode_refs: list[ModeRef] | tuple[ModeRef, ...] | None = None,
) -> AlternateRegisters.AlternateRegister:
    if mode_refs is None:
        mode_refs = [ModeRef(value="ModeA", priority=1)]
    return AlternateRegisters.AlternateRegister(name=name, field_value=fields_, mode_ref=mode_refs)


def _find[T](root: Any, expected: type[T]) -> T:
    pending = [root]
    seen: set[int] = set()
    while pending:
        current = pending.pop()
        if isinstance(current, expected):
            return current
        if id(current) in seen:
            continue
        seen.add(id(current))
        if is_dataclass(current) and not isinstance(current, type):
            pending.extend(getattr(current, item.name) for item in fields(current))
        elif isinstance(current, (list, tuple)):
            pending.extend(current)
    raise AssertionError(f"No {expected.__name__} in model")


def _load_sample() -> Component:
    component = XmlDocument.parser().from_string(_SAMPLE.read_text(), Component)
    _register_graph(component)
    return component


@pytest.mark.parametrize(("name", "parameters", "section"), _OPERATIONS)
def test_alternate_register_lifecycle_signatures_and_docs(name: str, parameters: tuple[str, ...], section: str) -> None:
    function = getattr(api, name)
    assert tuple(signature(function).parameters) == parameters
    assert name in api.__all__
    assert getattr(tgi, name) is function
    assert "Args:" in function.__doc__
    assert "Returns:" in function.__doc__
    assert f"Section: {section}." in function.__doc__


def test_alternate_register_getters_use_direct_typed_collections() -> None:
    field = _field()
    mode_ref = ModeRef(value="ModeA", priority=1)
    alternate_register = _alternate(fields_=[field], mode_refs=[mode_ref])
    alternate_id = get_handle(alternate_register)

    assert api.getAlternateRegisterFieldIDs(alternate_id) == [get_handle(field)]
    assert api.getAlternateRegisterModeRefIDs(alternate_id) == [get_handle(mode_ref)]
    assert get_parent_info(get_handle(field)).path == ("field_value",)
    assert get_parent_info(get_handle(mode_ref)).path == ("mode_ref",)


@pytest.mark.parametrize("getter", (api.getAlternateRegisterFieldIDs, api.getAlternateRegisterModeRefIDs))
def test_alternate_register_getters_reject_wrong_handle(getter: Any) -> None:
    with pytest.raises(TgiError) as error:
        getter("hdeadbeef")
    assert error.value.fault_code == TgiFaultCode.INVALID_ID


def test_add_alternate_field_builds_typed_nodes_and_normalizes_tuple_after_validation() -> None:
    alternate_register = _alternate(fields_=(_field("existing"),))
    alternate_id = get_handle(alternate_register)

    field_id = api.addAlternateRegisterField(alternate_id, "added", "1 + 1", "1 << 2")
    field = resolve_handle(field_id)
    assert isinstance(field, FieldType)
    assert field.name == "added"
    assert isinstance(field.bit_offset, UnsignedIntExpression)
    assert field.bit_offset.value == "1 + 1"
    assert isinstance(field.choice[0], UnsignedPositiveIntExpression)
    assert field.choice[0].value == "1 << 2"
    assert get_parent_info(field_id).parent_handle == alternate_id
    assert get_parent_info(field_id).path == ("field_value",)
    assert isinstance(alternate_register.field_value, list)


@pytest.mark.parametrize("bad_name", ("", "bad name", "a/name", 5, None))
def test_add_alternate_field_rejects_invalid_names_atomically(bad_name: object) -> None:
    original_fields = (_field("existing"),)
    alternate_register = _alternate(fields_=original_fields)
    alternate_id = get_handle(alternate_register)
    before = alternate_register.field_value

    with pytest.raises(TgiError) as error:
        api.addAlternateRegisterField(alternate_id, bad_name, "0", "1")

    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert alternate_register.field_value is before is original_fields


@pytest.mark.parametrize(("offset", "width"), (("-1", "1"), (str(1 << 32), "1"), ("0", "0"), ("0", str(1 << 32))))
def test_add_alternate_field_rejects_invalid_expressions_atomically(offset: str, width: str) -> None:
    alternate_register = _alternate(fields_=(_field("existing"),))
    alternate_id = get_handle(alternate_register)
    before = alternate_register.field_value

    with pytest.raises(TgiError) as error:
        api.addAlternateRegisterField(alternate_id, "added", offset, width)

    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert alternate_register.field_value is before


def test_add_alternate_field_accepts_deferred_expressions_and_rejects_duplicate_names() -> None:
    original_fields = (_field("flag"),)
    alternate_register = _alternate(fields_=original_fields)
    alternate_id = get_handle(alternate_register)
    field_id = api.addAlternateRegisterField(alternate_id, "deferred", "offsetParam", "widthParam")
    assert resolve_handle(field_id).bit_offset.value == "offsetParam"
    assert resolve_handle(field_id).choice[0].value == "widthParam"

    current_fields = alternate_register.field_value
    with pytest.raises(TgiError) as error:
        api.addAlternateRegisterField(alternate_id, "flag", "0", "1")
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert alternate_register.field_value is current_fields
    assert len(original_fields) == 1


def test_add_alternate_field_checks_known_containing_register_size() -> None:
    component = _load_sample()
    alternate_register = _find(component, AlternateRegisters.AlternateRegister)
    alternate_id = get_handle(alternate_register)
    before = alternate_register.field_value

    with pytest.raises(TgiError) as error:
        api.addAlternateRegisterField(alternate_id, "outside", "31", "2")

    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert alternate_register.field_value is before


def test_remove_alternate_field_is_owner_scoped_and_invalidates_descendants() -> None:
    field = _field()
    alternate_register = _alternate(fields_=[field])
    _register_graph(alternate_register)
    alternate_id = get_handle(alternate_register)
    field_id = get_handle(field)
    offset_id = get_handle(field.bit_offset)

    assert api.removeAlternateRegisterField(field_id) is True
    assert alternate_register.field_value == []
    assert resolve_handle(field_id) is None
    assert resolve_handle(offset_id) is None
    assert api.getAlternateRegisterFieldIDs(alternate_id) == []
    with pytest.raises(TgiError):
        api.removeAlternateRegisterField(field_id)


def test_remove_alternate_field_rejects_field_owned_by_register() -> None:
    component = _load_sample()
    fields_ = [item for item in _find(component, AlternateRegisters.AlternateRegister).field_value]
    # The sample register has a sibling field outside the alternate-register owner.
    normal_field = _find(component, FieldType)
    assert all(normal_field is not field for field in fields_)

    with pytest.raises(TgiError) as error:
        api.removeAlternateRegisterField(get_handle(normal_field))
    assert error.value.fault_code == TgiFaultCode.INVALID_ID


def test_add_alternate_mode_ref_validates_name_priority_and_schema_scopes() -> None:
    alternate_register = _alternate()
    alternate_id = get_handle(alternate_register)
    mode_ref_id = api.addAlternaterRegisterModeRef(alternate_id, "ModeB", 1 << 40)
    mode_ref = resolve_handle(mode_ref_id)
    assert isinstance(mode_ref, ModeRef)
    assert (mode_ref.value, mode_ref.priority) == ("ModeB", 1 << 40)
    assert api.getAlternateRegisterModeRefIDs(alternate_id) == [get_handle(alternate_register.mode_ref[0]), mode_ref_id]

    holder = AlternateRegisters(alternate_register=[alternate_register, _alternate(name="other")])
    _register_graph(holder)
    with pytest.raises(TgiError) as error:
        api.addAlternaterRegisterModeRef(get_handle(holder.alternate_register[1]), "ModeA", 7)
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert len(holder.alternate_register[1].mode_ref) == 1


@pytest.mark.parametrize(
    ("mode_name", "priority"), (("bad name", 2), ("ModeB", -1), ("ModeB", True), ("ModeA", 2), ("ModeB", 1))
)
def test_add_alternate_mode_ref_rejects_bad_or_duplicate_identity_atomically(mode_name: str, priority: int) -> None:
    alternate_register = _alternate(mode_refs=(ModeRef(value="ModeA", priority=1),))
    alternate_id = get_handle(alternate_register)
    before = alternate_register.mode_ref

    with pytest.raises(TgiError) as error:
        api.addAlternaterRegisterModeRef(alternate_id, mode_name, priority)

    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert alternate_register.mode_ref is before


def test_remove_alternate_mode_ref_invalidates_handle_and_normalizes_tuple() -> None:
    mode_ref = ModeRef(value="ModeA", priority=1)
    alternate_register = _alternate(mode_refs=(mode_ref,))
    _register_graph(alternate_register)
    alternate_id = get_handle(alternate_register)
    mode_ref_id = get_handle(mode_ref)

    assert api.removeAlternaterRegisterModeRef(mode_ref_id) is True
    assert alternate_register.mode_ref == []
    assert isinstance(alternate_register.mode_ref, list)
    assert resolve_handle(mode_ref_id) is None
    assert api.getAlternateRegisterModeRefIDs(alternate_id) == []


def test_remove_mode_ref_accepts_other_typed_mode_ref_owners() -> None:
    mode_ref = ModeRef(value="ModeA", priority=1)
    owner = AccessRestrictionType(mode_ref=(mode_ref,))
    _register_graph(owner)
    mode_ref_id = get_handle(mode_ref)

    assert api.removeAlternaterRegisterModeRef(mode_ref_id) is True
    assert owner.mode_ref == []
    assert resolve_handle(mode_ref_id) is None


def test_remove_mode_ref_rejects_wrong_or_unowned_handles() -> None:
    with pytest.raises(TgiError) as error:
        api.removeAlternaterRegisterModeRef(get_handle(_field()))
    assert error.value.fault_code == TgiFaultCode.INVALID_ID

    mode_ref_id = get_handle(ModeRef(value="ModeA", priority=1))
    with pytest.raises(TgiError) as error:
        api.removeAlternaterRegisterModeRef(mode_ref_id)
    assert error.value.fault_code == TgiFaultCode.INVALID_ID


@pytest.mark.parametrize("priority", (-1, True, 1.0, "2"))
def test_set_mode_ref_priority_rejects_non_nonnegative_integers(priority: object) -> None:
    mode_ref = ModeRef(value="ModeA", priority=1)
    mode_ref_id = get_handle(mode_ref)

    with pytest.raises(TgiError) as error:
        api.setModeRefPriority(mode_ref_id, priority)
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert mode_ref.priority == 1


def test_set_mode_ref_priority_accepts_detached_and_other_owner_handles() -> None:
    detached = ModeRef(value="Detached", priority=1, id="mode-id")
    detached_id = get_handle(detached)
    assert api.setModeRefPriority(detached_id, 1 << 80) is True
    assert detached.priority == 1 << 80
    assert detached.id == "mode-id"

    first = ModeRef(value="ModeA", priority=1, id="preserve-me")
    second = ModeRef(value="ModeB", priority=2)
    owner = AccessRestrictionType(mode_ref=[first, second])
    _register_graph(owner)
    first_id = get_handle(first)
    assert api.setModeRefPriority(first_id, 4) is True
    assert first.priority == 4
    assert first.id == "preserve-me"
    assert get_handle(first) == first_id


def test_set_mode_ref_priority_rejects_sibling_collision_without_mutation() -> None:
    first = ModeRef(value="ModeA", priority=1)
    second = ModeRef(value="ModeB", priority=2)
    owner = AccessRestrictionType(mode_ref=[first, second])
    _register_graph(owner)

    with pytest.raises(TgiError) as error:
        api.setModeRefPriority(get_handle(first), 2)
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert first.priority == 1


def test_parsed_alternate_register_ownership_recovers_and_round_trips_after_edits() -> None:
    component = _load_sample()
    alternate_register = _find(component, AlternateRegisters.AlternateRegister)
    original_field = alternate_register.field_value[0]
    original_field_id = get_handle(original_field)
    alternate_id = get_handle(alternate_register)
    mode_ref = alternate_register.mode_ref[0]
    mode_ref.id = "modeRefId"
    mode_ref_id = get_handle(mode_ref)

    assert api.getAlternateRegisterFieldIDs(alternate_id) == [original_field_id]
    assert api.getAlternateRegisterModeRefIDs(alternate_id) == [mode_ref_id]
    assert get_parent_info(original_field_id).parent_handle == alternate_id
    added_id = api.addAlternateRegisterField(alternate_id, "AddedField", "0", "1")
    assert api.removeAlternateRegisterField(original_field_id) is True
    assert api.setModeRefPriority(mode_ref_id, 2) is True
    assert resolve_handle(original_field_id) is None
    assert resolve_handle(added_id) is not None
    xml = XmlDocument.serializer().render(component)
    _SCHEMA.assertValid(etree.fromstring(xml.encode()))
    reloaded = XmlDocument.parser().from_string(xml, Component)
    loaded_alternate = _find(reloaded, AlternateRegisters.AlternateRegister)
    assert [field.name for field in loaded_alternate.field_value] == ["AddedField"]
    assert loaded_alternate.mode_ref[0].priority == 2
    assert loaded_alternate.mode_ref[0].id == "modeRefId"

"""Register field and alternate-register collection lifecycle contracts."""

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
from org.accellera.ipxact.v1685_2022.address_block_type import AddressBlockType
from org.accellera.ipxact.v1685_2022.alternate_registers import AlternateRegisters
from org.accellera.ipxact.v1685_2022.banked_block_type import BankedBlockType
from org.accellera.ipxact.v1685_2022.field_type import FieldType
from org.accellera.ipxact.v1685_2022.mode_ref import ModeRef
from org.accellera.ipxact.v1685_2022.register_file import RegisterFile
from org.accellera.ipxact.v1685_2022.register_file_definitions import RegisterFileDefinitions
from org.accellera.ipxact.v1685_2022.unsigned_int_expression import UnsignedIntExpression
from org.accellera.ipxact.v1685_2022.unsigned_longint_expression import UnsignedLongintExpression
from org.accellera.ipxact.v1685_2022.unsigned_positive_int_expression import UnsignedPositiveIntExpression

_SAMPLE = Path("tests/xml/ipxact/v1685_2022/accellera.org/Sample/SampleComponent/1.0/xml/SampleComponent.xml")
_SCHEMA = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))
_REGISTER_TYPES = (
    AddressBlockType.Register,
    BankedBlockType.Register,
    RegisterFile.Register,
    RegisterFileDefinitions.RegisterFileDefinition.Register,
)
_OPERATIONS = (
    ("getRegisterAlternateRegisterIDs", ("registerID",), "F.7.73.48"),
    ("getRegisterFieldIDs", ("registerID",), "F.7.73.61"),
    (
        "addRegisterAlternateRegister",
        ("registerID", "name", "modeRef", "priority", "fieldName", "fieldOffset", "fieldWidth"),
        "F.7.74.7",
    ),
    ("addRegisterField", ("registerID", "name", "offset", "width"), "F.7.74.8"),
    ("removeRegisterAlternateRegister", ("alternateRegisterID",), "F.7.74.25"),
    ("removeRegisterField", ("registerFieldID",), "F.7.74.26"),
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


def _register(register_type: type, *, choice: list[Any] | tuple[Any, ...] | None = None, name: str = "control") -> Any:
    if choice is None:
        choice = [UnsignedPositiveIntExpression(value="32"), _field()]
    return register_type(
        name=name,
        address_offset=UnsignedLongintExpression(value="0"),
        choice=choice,
    )


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
def test_register_child_lifecycle_signatures_exports_and_docs(
    name: str, parameters: tuple[str, ...], section: str
) -> None:
    function = getattr(api, name)
    assert tuple(signature(function).parameters) == parameters
    assert name in api.__all__
    assert getattr(tgi, name) is function
    assert "Args:" in function.__doc__
    assert "Returns:" in function.__doc__
    assert f"Section: {section}." in function.__doc__


@pytest.mark.parametrize("register_type", _REGISTER_TYPES)
def test_register_child_getters_use_ordered_typed_collections(register_type: type) -> None:
    first = _field("first")
    second = _field("second")
    alternate_a = AlternateRegisters.AlternateRegister(
        name="alternateA", mode_ref=[ModeRef(value="ModeA", priority=0)], field_value=[_field("altFlag")]
    )
    alternate_b = AlternateRegisters.AlternateRegister(
        name="alternateB", mode_ref=[ModeRef(value="ModeB", priority=0)], field_value=[_field("altOther")]
    )
    register = _register(
        register_type,
        choice=[UnsignedPositiveIntExpression(value="32"), first, second],
    )
    register.alternate_registers = AlternateRegisters(alternate_register=[alternate_a, alternate_b])
    _register_graph(register)

    assert api.getRegisterFieldIDs(get_handle(register)) == [get_handle(first), get_handle(second)]
    assert api.getRegisterAlternateRegisterIDs(get_handle(register)) == [
        get_handle(alternate_a),
        get_handle(alternate_b),
    ]
    assert get_parent_info(get_handle(first)).path == ("choice",)
    assert get_parent_info(get_handle(alternate_a)).path == ("alternate_register",)


def test_register_child_getters_return_empty_for_absent_children_and_reference_fields() -> None:
    register = _register(
        RegisterFile.Register,
        choice=[RegisterFile.Register.RegisterDefinitionRef(value="shared", type_definitions="types")],
    )
    _register_graph(register)
    assert api.getRegisterFieldIDs(get_handle(register)) == []
    assert api.getRegisterAlternateRegisterIDs(get_handle(register)) == []


@pytest.mark.parametrize("getter", (api.getRegisterFieldIDs, api.getRegisterAlternateRegisterIDs))
def test_register_child_getters_reject_wrong_or_unknown_handles(getter: Any) -> None:
    with pytest.raises(TgiError) as error:
        getter("hdeadbeef")
    assert error.value.fault_code == TgiFaultCode.INVALID_ID
    with pytest.raises(TgiError) as error:
        getter(get_handle(_field()))
    assert error.value.fault_code == TgiFaultCode.INVALID_ID


def test_add_register_field_builds_typed_choice_children_and_preserves_expression_sources() -> None:
    register = _register(AddressBlockType.Register)
    register_id = get_handle(register)
    field_id = api.addRegisterField(register_id, "newField", "base + 1", "1 << 2")
    field = resolve_handle(field_id)

    assert isinstance(field, FieldType)
    assert field.name == "newField"
    assert field.bit_offset.value == "base + 1"
    assert isinstance(field.bit_offset, UnsignedIntExpression)
    assert isinstance(field.choice[0], UnsignedPositiveIntExpression)
    assert field.choice[0].value == "1 << 2"
    assert api.getRegisterFieldIDs(register_id)[-1] == field_id
    assert get_parent_info(field_id).parent_handle == register_id
    assert get_parent_info(field_id).path == ("choice",)


@pytest.mark.parametrize(
    ("name", "offset", "width"),
    (
        ("bad name", "0", "1"),
        ("valid", "-1", "1"),
        ("valid", "0", "0"),
        ("valid", str(1 << 32), "1"),
        ("valid", "0", str(1 << 32)),
    ),
)
def test_add_register_field_rejects_bad_name_or_range_atomically(name: str, offset: str, width: str) -> None:
    register = _register(AddressBlockType.Register, choice=(UnsignedPositiveIntExpression(value="32"), _field()))
    register_id = get_handle(register)
    original = register.choice

    with pytest.raises(TgiError) as error:
        api.addRegisterField(register_id, name, offset, width)

    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert register.choice is original
    assert len(original) == 2


def test_add_register_field_rejects_duplicate_names_containment_and_reference_branch() -> None:
    register = _register(AddressBlockType.Register, choice=(UnsignedPositiveIntExpression(value="32"), _field("used")))
    register_id = get_handle(register)
    original = register.choice
    for name, offset, width in (("used", "0", "1"), ("outside", "31", "2")):
        with pytest.raises(TgiError) as error:
            api.addRegisterField(register_id, name, offset, width)
        assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
        assert register.choice is original

    reference = _register(
        RegisterFile.Register,
        choice=[RegisterFile.Register.RegisterDefinitionRef(value="shared", type_definitions="types")],
    )
    reference_id = get_handle(reference)
    with pytest.raises(TgiError) as error:
        api.addRegisterField(reference_id, "newField", "0", "1")
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert len(reference.choice) == 1


def test_add_register_field_accepts_deferred_size_and_field_expressions() -> None:
    register = _register(AddressBlockType.Register, choice=[UnsignedPositiveIntExpression(value="sizeParam")])
    register_id = get_handle(register)
    field_id = api.addRegisterField(register_id, "symbolic", "offsetParam", "widthParam")
    field = resolve_handle(field_id)
    assert field.bit_offset.value == "offsetParam"
    assert field.choice[0].value == "widthParam"


def test_add_alternate_register_builds_schema_models_and_allows_register_definition_reference() -> None:
    register = _register(
        RegisterFile.Register,
        choice=[RegisterFile.Register.RegisterDefinitionRef(value="shared", type_definitions="types")],
    )
    register_id = get_handle(register)
    alternate_id = api.addRegisterAlternateRegister(
        register_id, "alt", "ModeA", 1 << 48, "status", "offsetExpr", "widthExpr"
    )
    alternate = resolve_handle(alternate_id)

    assert isinstance(alternate, AlternateRegisters.AlternateRegister)
    assert isinstance(register.alternate_registers, AlternateRegisters)
    assert alternate.mode_ref == [ModeRef(value="ModeA", priority=1 << 48)]
    assert alternate.field_value[0].bit_offset.value == "offsetExpr"
    assert alternate.field_value[0].choice[0].value == "widthExpr"
    assert get_parent_info(alternate_id).parent_handle == get_handle(register.alternate_registers)
    assert api.getRegisterAlternateRegisterIDs(register_id) == [alternate_id]


@pytest.mark.parametrize(
    ("name", "mode", "priority", "field_name", "offset", "width"),
    (
        ("bad name", "Mode", 0, "field", "0", "1"),
        ("alt", "bad mode", 0, "field", "0", "1"),
        ("alt", "Mode", -1, "field", "0", "1"),
        ("alt", "Mode", True, "field", "0", "1"),
        ("alt", "Mode", 0, "bad field", "0", "1"),
        ("alt", "Mode", 0, "field", "-1", "1"),
        ("alt", "Mode", 0, "field", "31", "2"),
        ("alt", "Mode", 0, "field", "0", "0"),
    ),
)
def test_add_alternate_register_rejects_bad_arguments_without_attaching_holder(
    name: str, mode: str, priority: int, field_name: str, offset: str, width: str
) -> None:
    register = _register(AddressBlockType.Register)
    original = register.alternate_registers

    with pytest.raises(TgiError) as error:
        api.addRegisterAlternateRegister(get_handle(register), name, mode, priority, field_name, offset, width)

    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert register.alternate_registers is original is None


def test_add_alternate_register_enforces_register_data_names_and_holder_mode_names() -> None:
    existing_alternate = AlternateRegisters.AlternateRegister(
        name="existingAlt", mode_ref=[ModeRef(value="TakenMode", priority=0)], field_value=[_field("altField")]
    )
    register = _register(RegisterFile.Register, name="parent", choice=[UnsignedPositiveIntExpression(value="32")])
    register.alternate_registers = AlternateRegisters(alternate_register=[existing_alternate])
    sibling_register = _register(
        RegisterFile.Register, name="sibling", choice=[UnsignedPositiveIntExpression(value="32")]
    )
    sibling_register.alternate_registers = AlternateRegisters(
        alternate_register=[
            AlternateRegisters.AlternateRegister(
                name="peerAlt", mode_ref=[ModeRef(value="PeerMode", priority=0)], field_value=[_field("peerField")]
            )
        ]
    )
    owner = RegisterFile(
        name="rf",
        address_offset=UnsignedLongintExpression(value="0"),
        choice=[
            register,
            sibling_register,
            RegisterFile(name="reserved", address_offset=UnsignedLongintExpression(value="0")),
        ],
    )
    _register_graph(owner)
    register_id = get_handle(register)

    for alternate_name, mode_name in (
        ("parent", "NewMode"),
        ("sibling", "NewMode"),
        ("peerAlt", "NewMode"),
        ("newAlt", "TakenMode"),
        ("reserved", "NewMode"),
    ):
        original = register.alternate_registers.alternate_register
        with pytest.raises(TgiError) as error:
            api.addRegisterAlternateRegister(register_id, alternate_name, mode_name, 0, "newField", "0", "1")
        assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
        assert register.alternate_registers.alternate_register is original

    accepted = api.addRegisterAlternateRegister(register_id, "newAlt", "NewMode", 0, "newField", "0", "1")
    assert resolve_handle(accepted).name == "newAlt"


def test_add_alternate_register_normalizes_tuple_only_after_all_validation_and_preserves_siblings() -> None:
    first = AlternateRegisters.AlternateRegister(
        name="first", mode_ref=[ModeRef(value="ModeA", priority=0)], field_value=[_field("firstField")]
    )
    original = (first,)
    register = _register(AddressBlockType.Register, choice=[UnsignedPositiveIntExpression(value="32")])
    register.alternate_registers = AlternateRegisters(alternate_register=original)
    register_id = get_handle(register)
    with pytest.raises(TgiError):
        api.addRegisterAlternateRegister(register_id, "bad name", "ModeB", 0, "field", "0", "1")
    assert register.alternate_registers.alternate_register is original

    added = api.addRegisterAlternateRegister(register_id, "second", "ModeB", 0, "secondField", "0", "1")
    assert isinstance(register.alternate_registers.alternate_register, list)
    assert register.alternate_registers.alternate_register[0] is first
    assert api.getRegisterAlternateRegisterIDs(register_id) == [get_handle(first), added]


def test_remove_register_field_invalidates_descendants_and_preserves_sibling_choice_items() -> None:
    first = _field("first")
    second = _field("second")
    register = _register(AddressBlockType.Register, choice=(UnsignedPositiveIntExpression(value="32"), first, second))
    _register_graph(register)
    register_id = get_handle(register)
    field_id = get_handle(first)
    offset_id = get_handle(first.bit_offset)
    width_id = get_handle(first.choice[0])

    assert api.removeRegisterField(field_id) is True
    assert isinstance(register.choice, list)
    assert register.choice == [register.choice[0], second]
    assert resolve_handle(field_id) is None
    assert resolve_handle(offset_id) is None
    assert resolve_handle(width_id) is None
    assert api.getRegisterFieldIDs(register_id) == [get_handle(second)]


def test_remove_register_field_rejects_alternate_field_wrong_type_and_unowned_field() -> None:
    alternate = AlternateRegisters.AlternateRegister(
        name="alt", mode_ref=[ModeRef(value="Mode", priority=0)], field_value=[_field("alternateField")]
    )
    register = _register(AddressBlockType.Register)
    register.alternate_registers = AlternateRegisters(alternate_register=[alternate])
    _register_graph(register)
    for invalid in (get_handle(alternate.field_value[0]), get_handle(UnsignedPositiveIntExpression(value="1"))):
        with pytest.raises(TgiError) as error:
            api.removeRegisterField(invalid)
        assert error.value.fault_code == TgiFaultCode.INVALID_ID

    with pytest.raises(TgiError) as error:
        api.removeRegisterField(get_handle(_field("detached")))
    assert error.value.fault_code == TgiFaultCode.INVALID_ID


def test_remove_alternate_register_preserves_siblings_then_prunes_holder_and_invalidates_descendants() -> None:
    first_field = _field("firstField")
    second_field = _field("secondField")
    first_mode = ModeRef(value="ModeA", priority=0)
    second_mode = ModeRef(value="ModeB", priority=0)
    first = AlternateRegisters.AlternateRegister(name="first", mode_ref=[first_mode], field_value=[first_field])
    second = AlternateRegisters.AlternateRegister(name="second", mode_ref=[second_mode], field_value=[second_field])
    holder = AlternateRegisters(alternate_register=(first, second))
    register = _register(AddressBlockType.Register)
    register.alternate_registers = holder
    _register_graph(register)
    register_id = get_handle(register)
    first_id = get_handle(first)
    first_child_id = get_handle(first_field)
    first_mode_id = get_handle(first_mode)
    holder_id = get_handle(holder)

    assert api.removeRegisterAlternateRegister(first_id) is True
    assert register.alternate_registers is holder
    assert isinstance(holder.alternate_register, list)
    assert holder.alternate_register == [second]
    assert resolve_handle(first_child_id) is None
    assert resolve_handle(first_mode_id) is None
    assert api.getRegisterAlternateRegisterIDs(register_id) == [get_handle(second)]

    second_id = get_handle(second)
    second_child_id = get_handle(second_field)
    assert api.removeRegisterAlternateRegister(second_id) is True
    assert register.alternate_registers is None
    assert resolve_handle(holder_id) is None
    assert resolve_handle(second_id) is None
    assert resolve_handle(second_child_id) is None
    assert api.getRegisterAlternateRegisterIDs(register_id) == []


def test_remove_register_alternate_rejects_detached_or_wrong_handle() -> None:
    for invalid in ("hdeadbeef", get_handle(_field())):
        with pytest.raises(TgiError) as error:
            api.removeRegisterAlternateRegister(invalid)
        assert error.value.fault_code == TgiFaultCode.INVALID_ID


def test_schema_valid_round_trip_recovers_parsed_register_child_ownership() -> None:
    component = _load_sample()
    registers = []
    pending = [component]
    seen: set[int] = set()
    while pending:
        current = pending.pop()
        if id(current) in seen:
            continue
        seen.add(id(current))
        if isinstance(current, _REGISTER_TYPES) and any(
            isinstance(item, UnsignedPositiveIntExpression) for item in current.choice
        ):
            registers.append(current)
        if is_dataclass(current) and not isinstance(current, type):
            pending.extend(getattr(current, item.name) for item in fields(current))
        elif isinstance(current, (list, tuple)):
            pending.extend(current)
    register = registers[0]
    register_id = get_handle(register)
    field_id = api.addRegisterField(register_id, "codexAddedField", "0", "1")
    alternate_id = api.addRegisterAlternateRegister(
        register_id, "codexAddedAlternate", "Boot", 1 << 36, "codexAlternateField", "0", "1"
    )

    xml = XmlDocument.serializer().render(component)
    _SCHEMA.assertValid(etree.fromstring(xml.encode()))
    parsed = XmlDocument.parser().from_string(xml, Component)
    _register_graph(parsed)
    parsed_register = None
    parsed_pending = [parsed]
    while parsed_pending:
        current = parsed_pending.pop()
        if isinstance(current, _REGISTER_TYPES) and current.name == register.name:
            parsed_register = current
            break
        if is_dataclass(current) and not isinstance(current, type):
            parsed_pending.extend(getattr(current, item.name) for item in fields(current))
        elif isinstance(current, (list, tuple)):
            parsed_pending.extend(current)
    assert parsed_register is not None
    parsed_field = next(
        field for field in parsed_register.choice if isinstance(field, FieldType) and field.name == "codexAddedField"
    )
    parsed_alternate = next(
        item for item in parsed_register.alternate_registers.alternate_register if item.name == "codexAddedAlternate"
    )
    parsed_field_id = get_handle(parsed_field)
    parsed_alternate_id = get_handle(parsed_alternate)
    assert field_id != parsed_field_id
    assert alternate_id != parsed_alternate_id
    assert parsed_field_id in api.getRegisterFieldIDs(get_handle(parsed_register))
    assert parsed_alternate_id in api.getRegisterAlternateRegisterIDs(get_handle(parsed_register))
    assert get_parent_info(parsed_field_id).parent_handle == get_handle(parsed_register)
    assert get_parent_info(parsed_alternate_id).parent_handle == get_handle(parsed_register.alternate_registers)
    assert api.removeRegisterField(parsed_field_id) is True
    assert api.removeRegisterAlternateRegister(parsed_alternate_id) is True
    final_xml = XmlDocument.serializer().render(parsed)
    _SCHEMA.assertValid(etree.fromstring(final_xml.encode()))

"""Register typeIdentifier and volatility TGI operations."""

from collections.abc import Iterator

import pytest
from lxml import etree

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
from org.accellera.ipxact.v1685_2022.address_block import AddressBlock
from org.accellera.ipxact.v1685_2022.address_block_type import AddressBlockType
from org.accellera.ipxact.v1685_2022.address_unit_bits import AddressUnitBits
from org.accellera.ipxact.v1685_2022.bank import Bank
from org.accellera.ipxact.v1685_2022.bank_alignment_type import BankAlignmentType
from org.accellera.ipxact.v1685_2022.banked_block_type import BankedBlockType
from org.accellera.ipxact.v1685_2022.base_address import BaseAddress
from org.accellera.ipxact.v1685_2022.component import Component
from org.accellera.ipxact.v1685_2022.field_type import FieldType
from org.accellera.ipxact.v1685_2022.memory_map_type import MemoryMapType
from org.accellera.ipxact.v1685_2022.memory_maps import MemoryMaps
from org.accellera.ipxact.v1685_2022.register_file import RegisterFile
from org.accellera.ipxact.v1685_2022.register_file_definitions import RegisterFileDefinitions
from org.accellera.ipxact.v1685_2022.unsigned_int_expression import UnsignedIntExpression
from org.accellera.ipxact.v1685_2022.unsigned_longint_expression import UnsignedLongintExpression
from org.accellera.ipxact.v1685_2022.unsigned_positive_int_expression import UnsignedPositiveIntExpression
from org.accellera.ipxact.v1685_2022.unsigned_positive_longint_expression import UnsignedPositiveLongintExpression
from org.accellera.ipxact.v1685_2022.usage_type import UsageType
from org.accellera.ipxact.v1685_2022.volatile import Volatile

_SCHEMA = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))

type _RegisterType = (
    type[AddressBlockType.Register]
    | type[BankedBlockType.Register]
    | type[RegisterFile.Register]
    | type[RegisterFileDefinitions.RegisterFileDefinition.Register]
)
type _Register = (
    AddressBlockType.Register
    | BankedBlockType.Register
    | RegisterFile.Register
    | RegisterFileDefinitions.RegisterFileDefinition.Register
)


@pytest.fixture(autouse=True)
def clean_registry() -> Iterator[None]:
    registry.clear()
    yield
    registry.clear()


def _register(
    register_type: _RegisterType,
    *,
    choice: tuple[object, ...] = (),
    volatile: Volatile | None = None,
) -> _Register:
    size = UnsignedPositiveIntExpression(value="32")
    fields = [
        FieldType(
            name="data",
            bit_offset=UnsignedIntExpression(value="0"),
            choice=[UnsignedPositiveIntExpression(value="32")],
        )
    ]
    choices = [*choice, size]
    if choice and isinstance(choice[0], str):
        choices = [choice[0], size, *choice[1:]]
    if volatile is not None:
        choices.append(volatile)
    choices.extend(fields)
    return register_type(
        name="control",
        address_offset=UnsignedLongintExpression(value="0"),
        choice=choices,
    )


_REGISTER_TYPES: tuple[_RegisterType, ...] = (
    AddressBlockType.Register,
    BankedBlockType.Register,
    RegisterFile.Register,
    RegisterFileDefinitions.RegisterFileDefinition.Register,
)


@pytest.mark.parametrize("register_type", _REGISTER_TYPES)
def test_register_type_identifier_and_volatility_mutators_preserve_typed_children(register_type: _RegisterType) -> None:
    register = _register(register_type)
    register_id = get_handle(register)

    assert api.getRegisterTypeIdentifier(register_id) is None
    assert api.getRegisterVolatility(register_id) is None
    assert api.setRegisterTypeIdentifier(register_id, "Control_Type") is True
    assert api.getRegisterTypeIdentifier(register_id) == "Control_Type"
    assert register.choice[0] == "Control_Type"

    assert api.setRegisterVolatility(register_id, False) is True
    volatile = next(child for child in register.choice if isinstance(child, Volatile))
    volatile_id = get_handle(volatile)
    assert get_parent_info(volatile_id).parent_handle == register_id
    assert get_parent_info(volatile_id).path == ("choice",)
    assert get_parent_info(volatile_id).container == "list"
    assert api.getRegisterVolatility(register_id) is False

    assert api.setRegisterVolatility(register_id, True) is True
    assert next(child for child in register.choice if isinstance(child, Volatile)) is volatile
    assert get_handle(volatile) == volatile_id
    assert api.getRegisterVolatility(register_id) is True

    assert api.setRegisterTypeIdentifier(register_id, "Updated_Type") is True
    assert api.getRegisterTypeIdentifier(register_id) == "Updated_Type"
    assert api.removeRegisterTypeIdentifier(register_id) is True
    assert api.getRegisterTypeIdentifier(register_id) is None
    assert api.removeRegisterTypeIdentifier(register_id) is False
    assert api.removeRegisterVolatility(register_id) is True
    assert not any(isinstance(child, Volatile) for child in register.choice)
    assert resolve_handle(volatile_id) is None
    assert api.getRegisterVolatility(register_id) is None
    assert api.removeRegisterVolatility(register_id) is False


@pytest.mark.parametrize("register_type", _REGISTER_TYPES)
def test_register_volatile_wrapper_edits_preserve_identity_and_explicit_false(register_type: _RegisterType) -> None:
    volatile = Volatile(value=False)
    register = _register(register_type, choice=("Initial_Type",), volatile=volatile)
    register_id = get_handle(register)
    volatile_id = get_handle(volatile)
    size = next(child for child in register.choice if isinstance(child, UnsignedPositiveIntExpression))

    assert api.getRegisterVolatility(register_id) is False
    assert api.getRegisterTypeIdentifier(register_id) == "Initial_Type"
    assert api.setRegisterVolatility(register_id, True) is True
    assert next(child for child in register.choice if isinstance(child, Volatile)) is volatile
    assert get_handle(next(child for child in register.choice if isinstance(child, Volatile))) == volatile_id
    assert api.setRegisterTypeIdentifier(register_id, "Renamed_Type") is True
    assert next(child for child in register.choice if isinstance(child, UnsignedPositiveIntExpression)) is size
    assert api.getRegisterTypeIdentifier(register_id) == "Renamed_Type"


@pytest.mark.parametrize("register_type", _REGISTER_TYPES)
def test_register_definition_reference_branch_is_read_only_for_type_and_volatility(
    register_type: _RegisterType,
) -> None:
    reference = register_type.RegisterDefinitionRef(value="sharedRegister", type_definitions="sharedTypes")
    register = register_type(
        name="control",
        address_offset=UnsignedLongintExpression(value="0"),
        choice=[reference],
    )
    register_id = get_handle(register)
    reference_id = get_handle(reference)

    assert api.getRegisterTypeIdentifier(register_id) is None
    assert api.getRegisterVolatility(register_id) is None
    assert api.removeRegisterTypeIdentifier(register_id) is False
    assert api.removeRegisterVolatility(register_id) is False
    for operation, args in (
        (api.setRegisterTypeIdentifier, (register_id, "Local_Type")),
        (api.setRegisterVolatility, (register_id, True)),
    ):
        with pytest.raises(TgiError) as error:
            operation(*args)
        assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
        assert register.choice == [reference]
        assert resolve_handle(reference_id) is reference


def test_register_type_and_volatility_reject_invalid_inputs_without_mutation() -> None:
    volatile = Volatile(value=False)
    register = _register(AddressBlockType.Register, choice=("Good_Type",), volatile=volatile)
    register_id = get_handle(register)
    volatile_id = get_handle(volatile)
    choice = register.choice
    size = next(child for child in register.choice if isinstance(child, UnsignedPositiveIntExpression))

    for invalid_name in ("", "not a Name", "a/name", 12):
        with pytest.raises(TgiError) as error:
            api.setRegisterTypeIdentifier(register_id, invalid_name)
        assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
        assert register.choice is choice
        assert register.choice[0] == "Good_Type"
        assert next(child for child in register.choice if isinstance(child, UnsignedPositiveIntExpression)) is size
        assert api.getRegisterTypeIdentifier(register_id) == "Good_Type"

    for invalid_boolean in (0, 1, "true", None):
        with pytest.raises(TgiError) as error:
            api.setRegisterVolatility(register_id, invalid_boolean)
        assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
        assert next(child for child in register.choice if isinstance(child, Volatile)) is volatile
        assert volatile.value is False
        assert get_handle(volatile) == volatile_id


def test_register_type_and_volatility_operations_require_typed_handles() -> None:
    register_id = get_handle(_register(AddressBlockType.Register))
    field_id = get_handle(FieldType(name="data", bit_offset=UnsignedIntExpression(value="0")))
    operations = (
        (api.getRegisterTypeIdentifier, ()),
        (api.getRegisterVolatility, ()),
        (api.removeRegisterTypeIdentifier, ()),
        (api.removeRegisterVolatility, ()),
        (api.setRegisterTypeIdentifier, ("Valid_Type",)),
        (api.setRegisterVolatility, (True,)),
    )

    for operation, tail in operations:
        for invalid_id in (field_id, "hdeadbeef"):
            with pytest.raises(TgiError) as error:
                operation(invalid_id, *tail)
            assert error.value.fault_code == TgiFaultCode.INVALID_ID
    assert api.getRegisterTypeIdentifier(register_id) is None


def test_register_type_and_volatile_duplicate_choices_are_rejected() -> None:
    duplicate_type = _register(AddressBlockType.Register, choice=("First_Type", "Second_Type"))
    with pytest.raises(TgiError) as error:
        api.getRegisterTypeIdentifier(get_handle(duplicate_type))
    assert error.value.fault_code == TgiFaultCode.INVALID_ID

    duplicate_volatility = _register(AddressBlockType.Register)
    duplicate_volatility.choice.extend((Volatile(value=False), Volatile(value=True)))
    register_id = get_handle(duplicate_volatility)
    for operation, args in (
        (api.getRegisterVolatility, (register_id,)),
        (api.setRegisterVolatility, (register_id, False)),
        (api.removeRegisterVolatility, (register_id,)),
    ):
        with pytest.raises(TgiError) as error:
            operation(*args)
        assert error.value.fault_code == TgiFaultCode.INVALID_ID


def test_register_type_and_volatility_setters_require_inline_size_atomically() -> None:
    register = _register(AddressBlockType.Register)
    register.choice = tuple(child for child in register.choice if not isinstance(child, UnsignedPositiveIntExpression))
    register_id = get_handle(register)
    original_choice = register.choice

    for operation, args in (
        (api.setRegisterTypeIdentifier, (register_id, "Local_Type")),
        (api.setRegisterVolatility, (register_id, True)),
    ):
        with pytest.raises(TgiError) as error:
            operation(*args)
        assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
        assert register.choice is original_choice
        assert register.choice == original_choice


def test_register_type_and_volatility_setters_normalize_tuple_choice_storage() -> None:
    register = _register(AddressBlockType.Register)
    register.choice = tuple(register.choice)
    register_id = get_handle(register)

    assert api.setRegisterTypeIdentifier(register_id, "Local_Type") is True
    assert api.setRegisterVolatility(register_id, False) is True
    assert isinstance(register.choice, list)
    assert register.choice[0] == "Local_Type"
    assert isinstance(register.choice[1], UnsignedPositiveIntExpression)
    assert isinstance(register.choice[2], Volatile)


def _schema_round_trip[T](document: T, document_type: type[T]) -> T:
    xml = XmlDocument.serializer().render(document)
    _SCHEMA.assertValid(etree.fromstring(xml.encode()))
    parsed = XmlDocument.parser().from_string(xml, document_type)
    _register_graph(parsed)
    reparsed_xml = XmlDocument.serializer().render(parsed)
    _SCHEMA.assertValid(etree.fromstring(reparsed_xml.encode()))
    return parsed


def test_register_type_and_volatility_round_trip_for_four_register_variants() -> None:
    address_register = _register(AddressBlockType.Register)
    file_register = _register(RegisterFile.Register)
    banked_register = _register(BankedBlockType.Register)
    block = AddressBlock(
        name="registers",
        base_address=BaseAddress(value="0"),
        choice=[
            UnsignedPositiveLongintExpression(value="256"),
            UnsignedPositiveIntExpression(value="32"),
            UsageType.REGISTER,
            address_register,
            RegisterFile(
                name="nested",
                address_offset=UnsignedLongintExpression(value="64"),
                choice=[UnsignedPositiveLongintExpression(value="64"), file_register],
            ),
        ],
    )
    banked_block = BankedBlockType(
        name="bankedRegisters",
        range=UnsignedPositiveLongintExpression(value="64"),
        width=UnsignedPositiveIntExpression(value="32"),
        usage=UsageType.REGISTER,
        register_or_register_file=[banked_register],
    )
    bank = Bank(
        name="registerBank",
        base_address=BaseAddress(value="256"),
        choice=[banked_block],
        bank_alignment=BankAlignmentType.SERIAL,
    )
    root = Component(
        vendor="test",
        library="library",
        name="registerTypeVolatility",
        version="1",
        memory_maps=MemoryMaps(
            memory_map=[
                MemoryMapType(
                    name="peripheral",
                    choice=[block, bank, AddressUnitBits(value="8")],
                )
            ]
        ),
    )

    for register in (address_register, file_register, banked_register):
        register_id = get_handle(register)
        assert api.setRegisterTypeIdentifier(register_id, f"{register.name}_Type") is True
        assert api.setRegisterVolatility(register_id, False) is True

    parsed = _schema_round_trip(root, Component)
    parsed_block = parsed.memory_maps.memory_map[0].choice[0]
    parsed_address = parsed_block.choice[3]
    parsed_file = parsed_block.choice[4].choice[1]
    parsed_banked = parsed.memory_maps.memory_map[0].choice[1].choice[0].register_or_register_file[0]
    for register in (parsed_address, parsed_file, parsed_banked):
        register_id = get_handle(register)
        assert api.getRegisterTypeIdentifier(register_id) == "control_Type"
        assert api.getRegisterVolatility(register_id) is False

    definition_register = _register(RegisterFileDefinitions.RegisterFileDefinition.Register)
    definition = RegisterFileDefinitions.RegisterFileDefinition(
        name="sharedFile",
        range=UnsignedPositiveLongintExpression(value="64"),
        register_or_register_file=[definition_register],
    )
    definitions = RegisterFileDefinitions(register_file_definition=[definition])
    register_id = get_handle(definition_register)
    assert api.setRegisterTypeIdentifier(register_id, "Defined_Type") is True
    assert api.setRegisterVolatility(register_id, True) is True

    parsed_definitions = _schema_round_trip(definitions, RegisterFileDefinitions)
    parsed_definition_register = parsed_definitions.register_file_definition[0].register_or_register_file[0]
    parsed_id = get_handle(parsed_definition_register)
    assert api.getRegisterTypeIdentifier(parsed_id) == "Defined_Type"
    assert api.getRegisterVolatility(parsed_id) is True

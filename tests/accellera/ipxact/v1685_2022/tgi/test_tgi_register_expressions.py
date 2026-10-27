"""Register address and size TGI expression contracts."""

from collections.abc import Iterator

import pytest
from lxml import etree

from amal.eda.accellera.ipxact.v1685_2022.tgi import register as api
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

_SCHEMA = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))

type _Register = (
    AddressBlockType.Register
    | BankedBlockType.Register
    | RegisterFile.Register
    | RegisterFileDefinitions.RegisterFileDefinition.Register
)
type _RegisterType = (
    type[AddressBlockType.Register]
    | type[BankedBlockType.Register]
    | type[RegisterFile.Register]
    | type[RegisterFileDefinitions.RegisterFileDefinition.Register]
)


@pytest.fixture(autouse=True)
def clean_registry() -> Iterator[None]:
    registry.clear()
    yield
    registry.clear()


def _register(
    register_type: _RegisterType,
    *,
    offset: str = "16",
    size: str | None = "32",
    choices: tuple[object, ...] = (),
) -> _Register:
    choice: list[object] = list(choices)
    if size is not None:
        choice.insert(0, UnsignedPositiveIntExpression(value=size))
    return register_type(
        name="control",
        address_offset=UnsignedLongintExpression(value=offset),
        choice=choice,
    )


@pytest.mark.parametrize(
    "register_type",
    [
        AddressBlockType.Register,
        BankedBlockType.Register,
        RegisterFile.Register,
        RegisterFileDefinitions.RegisterFileDefinition.Register,
    ],
)
def test_register_expression_getters_and_setters_preserve_typed_children(register_type: _RegisterType) -> None:
    offset = UnsignedLongintExpression(
        value="4 * 4",
        minimum=0,
        maximum=255,
        other_attributes={"{urn:test}offset": "keep"},
    )
    size = UnsignedPositiveIntExpression(
        value="8 * 4",
        minimum=1,
        maximum=128,
        other_attributes={"{urn:test}size": "keep"},
    )
    register = register_type(name="control", address_offset=offset, choice=[size])
    register_id = get_handle(register)
    offset_id = api.getRegisterAddressOffsetID(register_id)
    size_id = api.getRegisterSizeID(register_id)

    assert api.getRegisterAddressOffset(register_id) == 16
    assert api.getRegisterAddressOffsetExpression(register_id) == "4 * 4"
    assert api.getRegisterSize(register_id) == 32
    assert api.getRegisterSizeExpression(register_id) == "8 * 4"
    assert offset_id == get_handle(offset)
    assert size_id == get_handle(size)
    assert get_parent_info(offset_id).parent_handle == register_id
    assert get_parent_info(offset_id).path == ("address_offset",)
    assert get_parent_info(offset_id).container == "single"
    assert get_parent_info(size_id).parent_handle == register_id
    assert get_parent_info(size_id).path == ("choice",)
    assert get_parent_info(size_id).container == "list"

    assert api.setRegisterAddressOffset(register_id, "1 << 7") is True
    assert api.setRegisterSize(register_id, "2 ** 6") is True
    assert api.getRegisterAddressOffsetID(register_id) == offset_id
    assert api.getRegisterSizeID(register_id) == size_id
    assert api.getRegisterAddressOffset(register_id) == 128
    assert api.getRegisterSize(register_id) == 64
    assert offset.other_attributes == {"{urn:test}offset": "keep"}
    assert (offset.minimum, offset.maximum) == (0, 255)
    assert size.other_attributes == {"{urn:test}size": "keep"}
    assert (size.minimum, size.maximum) == (1, 128)


@pytest.mark.parametrize(
    "register_type",
    [
        AddressBlockType.Register,
        BankedBlockType.Register,
        RegisterFile.Register,
        RegisterFileDefinitions.RegisterFileDefinition.Register,
    ],
)
def test_register_expression_functions_reject_wrong_handles(register_type: _RegisterType) -> None:
    register_id = get_handle(_register(register_type))
    field_id = get_handle(FieldType(name="data", bit_offset=UnsignedIntExpression(value="0")))

    for operation in (
        api.getRegisterAddressOffset,
        api.getRegisterAddressOffsetExpression,
        api.getRegisterAddressOffsetID,
        api.getRegisterSize,
        api.getRegisterSizeExpression,
        api.getRegisterSizeID,
        api.setRegisterAddressOffset,
        api.setRegisterSize,
    ):
        for invalid_id in (field_id, "hdeadbeef"):
            arguments = (
                (invalid_id, "1") if operation in (api.setRegisterAddressOffset, api.setRegisterSize) else (invalid_id,)
            )
            with pytest.raises(TgiError) as error:
                operation(*arguments)
            assert error.value.fault_code == TgiFaultCode.INVALID_ID

    assert api.getRegisterAddressOffset(register_id) == 16


def test_register_expression_bounds_and_parse_failures_are_atomic() -> None:
    register = _register(
        AddressBlockType.Register,
        offset="16",
        size="32",
    )
    register_id = get_handle(register)
    offset = register.address_offset
    size = register.choice[0]

    invalid_updates = (
        (api.setRegisterAddressOffset, "-1", TgiFaultCode.INVALID_ARGUMENT),
        (api.setRegisterAddressOffset, str(1 << 64), TgiFaultCode.INVALID_ARGUMENT),
        (api.setRegisterAddressOffset, "1 +", TgiFaultCode.INVALID_ARGUMENT),
        (api.setRegisterSize, "0", TgiFaultCode.INVALID_ARGUMENT),
        (api.setRegisterSize, str(1 << 32), TgiFaultCode.INVALID_ARGUMENT),
        (api.setRegisterSize, "1 +", TgiFaultCode.INVALID_ARGUMENT),
    )
    for operation, source, fault in invalid_updates:
        with pytest.raises(TgiError) as error:
            operation(register_id, source)
        assert error.value.fault_code == fault
        assert register.address_offset is offset
        assert offset.value == "16"
        assert register.choice == [size]
        assert size.value == "32"

    assert api.setRegisterAddressOffset(register_id, "unresolved_offset") is True
    assert api.getRegisterAddressOffsetExpression(register_id) == "unresolved_offset"
    with pytest.raises(TgiError) as error:
        api.getRegisterAddressOffset(register_id)
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert offset.value == "unresolved_offset"


@pytest.mark.parametrize(
    "register_type",
    [
        AddressBlockType.Register,
        BankedBlockType.Register,
        RegisterFile.Register,
        RegisterFileDefinitions.RegisterFileDefinition.Register,
    ],
)
def test_register_size_getters_are_inline_choice_aware_and_setter_replaces_reference_branch(
    register_type: _RegisterType,
) -> None:
    register = register_type(
        name="control",
        address_offset=UnsignedLongintExpression(value="0"),
        choice=[register_type.RegisterDefinitionRef(value="shared", type_definitions="types")],
    )
    register_id = get_handle(register)
    reference_id = get_handle(register.choice[0])

    assert api.getRegisterSize(register_id) is None
    assert api.getRegisterSizeExpression(register_id) is None
    assert api.getRegisterSizeID(register_id) is None
    with pytest.raises(TgiError) as error:
        api.setRegisterSize(register_id, "0")
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert register.choice[0].value == "shared"
    assert resolve_handle(reference_id) is register.choice[0]

    assert api.setRegisterSize(register_id, "64") is True
    assert len(register.choice) == 1
    assert isinstance(register.choice[0], UnsignedPositiveIntExpression)
    assert api.getRegisterSize(register_id) == 64
    assert resolve_handle(reference_id) is None


def test_register_size_cannot_exclude_inline_field_and_failed_resize_is_atomic() -> None:
    field = FieldType(
        name="upper",
        bit_offset=UnsignedIntExpression(value="28"),
        choice=[UnsignedPositiveIntExpression(value="8")],
    )
    register = _register(AddressBlockType.Register, size="40", choices=[field])
    register_id = get_handle(register)
    size = register.choice[0]

    with pytest.raises(TgiError) as error:
        api.setRegisterSize(register_id, "32")
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert register.choice[0] is size
    assert size.value == "40"

    assert api.setRegisterSize(register_id, "36") is True
    assert api.getRegisterSize(register_id) == 36


def test_register_size_insertion_preserves_choice_order_and_converts_tuple_storage() -> None:
    field = FieldType(name="data", bit_offset=UnsignedIntExpression(value="0"), choice=[])
    register = AddressBlockType.Register(
        name="control",
        address_offset=UnsignedLongintExpression(value="0"),
        choice=("registerType", field),
    )
    register_id = get_handle(register)

    assert api.setRegisterSize(register_id, "32") is True
    assert isinstance(register.choice, list)
    assert register.choice[0] == "registerType"
    assert isinstance(register.choice[1], UnsignedPositiveIntExpression)
    assert register.choice[2] is field
    size_id = api.getRegisterSizeID(register_id)
    assert get_parent_info(size_id).parent_handle == register_id
    assert get_parent_info(size_id).path == ("choice",)


def test_register_expression_setters_respect_declared_bounds_without_mutation() -> None:
    offset = UnsignedLongintExpression(value="16", maximum=31)
    size = UnsignedPositiveIntExpression(value="32", minimum=8, maximum=48)
    register = AddressBlockType.Register(name="control", address_offset=offset, choice=[size])
    register_id = get_handle(register)

    for operation, source, node, original in (
        (api.setRegisterAddressOffset, "32", offset, "16"),
        (api.setRegisterSize, "64", size, "32"),
    ):
        with pytest.raises(TgiError) as error:
            operation(register_id, source)
        assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
        assert node.value == original


def test_register_size_getters_fault_on_duplicate_or_mixed_size_choices() -> None:
    duplicate = _register(
        AddressBlockType.Register,
        size=None,
        choices=(UnsignedPositiveIntExpression(value="16"), UnsignedPositiveIntExpression(value="32")),
    )
    mixed = AddressBlockType.Register(
        name="mixed",
        address_offset=UnsignedLongintExpression(value="0"),
        choice=[
            UnsignedPositiveIntExpression(value="16"),
            AddressBlockType.Register.RegisterDefinitionRef(value="shared", type_definitions="types"),
        ],
    )

    for register in (duplicate, mixed):
        with pytest.raises(TgiError) as error:
            api.getRegisterSize(get_handle(register))
        assert error.value.fault_code == TgiFaultCode.INVALID_ID


def test_register_expression_edits_survive_ipxact_xml_round_trip() -> None:
    register = AddressBlock.Register(
        name="control",
        address_offset=UnsignedLongintExpression(value="0"),
        choice=[
            UnsignedPositiveIntExpression(value="32"),
            FieldType(
                name="data",
                bit_offset=UnsignedIntExpression(value="0"),
                choice=[UnsignedPositiveIntExpression(value="1")],
            ),
        ],
    )
    block = AddressBlock(
        name="registers",
        base_address=BaseAddress(value="0"),
        choice=[
            UnsignedPositiveLongintExpression(value="256"),
            UnsignedPositiveIntExpression(value="32"),
            UsageType.REGISTER,
            register,
        ],
    )
    root = Component(
        vendor="test",
        library="library",
        name="registerExpressions",
        version="1",
        memory_maps=MemoryMaps(
            memory_map=[MemoryMapType(name="peripheral", choice=[block, AddressUnitBits(value="8")])]
        ),
    )
    register_id = get_handle(register)
    api.setRegisterAddressOffset(register_id, "4 * 4")
    api.setRegisterSize(register_id, "2 ** 5")

    xml = XmlDocument.serializer().render(root)
    _SCHEMA.assertValid(etree.fromstring(xml.encode()))
    parsed = XmlDocument.parser().from_string(xml, Component)
    parsed_register = parsed.memory_maps.memory_map[0].choice[0].choice[3]
    parsed_id = get_handle(parsed_register)

    assert api.getRegisterAddressOffsetExpression(parsed_id) == "4 * 4"
    assert api.getRegisterAddressOffset(parsed_id) == 16
    assert api.getRegisterSizeExpression(parsed_id) == "2 ** 5"
    assert api.getRegisterSize(parsed_id) == 32

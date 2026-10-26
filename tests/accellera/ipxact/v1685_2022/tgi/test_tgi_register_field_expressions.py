"""Register field bit offset and width TGI contracts."""

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
from org.accellera.ipxact.v1685_2022.alternate_registers import AlternateRegisters
from org.accellera.ipxact.v1685_2022.banked_block_type import BankedBlockType
from org.accellera.ipxact.v1685_2022.base_address import BaseAddress
from org.accellera.ipxact.v1685_2022.component import Component
from org.accellera.ipxact.v1685_2022.component_type import ComponentType
from org.accellera.ipxact.v1685_2022.configurable_library_ref_type import ConfigurableLibraryRefType
from org.accellera.ipxact.v1685_2022.external_type_definitions import ExternalTypeDefinitions
from org.accellera.ipxact.v1685_2022.field_ref import FieldRef
from org.accellera.ipxact.v1685_2022.field_type import FieldType
from org.accellera.ipxact.v1685_2022.memory_map_type import MemoryMapType
from org.accellera.ipxact.v1685_2022.memory_maps import MemoryMaps
from org.accellera.ipxact.v1685_2022.mode_ref import ModeRef
from org.accellera.ipxact.v1685_2022.register_definitions import RegisterDefinitions
from org.accellera.ipxact.v1685_2022.register_file import RegisterFile
from org.accellera.ipxact.v1685_2022.register_file_definitions import RegisterFileDefinitions
from org.accellera.ipxact.v1685_2022.unsigned_int_expression import UnsignedIntExpression
from org.accellera.ipxact.v1685_2022.unsigned_longint_expression import UnsignedLongintExpression
from org.accellera.ipxact.v1685_2022.unsigned_positive_int_expression import UnsignedPositiveIntExpression
from org.accellera.ipxact.v1685_2022.unsigned_positive_longint_expression import UnsignedPositiveLongintExpression
from org.accellera.ipxact.v1685_2022.usage_type import UsageType

_SCHEMA = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))
type _RegisterType = (
    type[AddressBlockType.Register]
    | type[RegisterFile.Register]
    | type[RegisterFileDefinitions.RegisterFileDefinition.Register]
)


@pytest.fixture(autouse=True)
def clean_registry() -> Iterator[None]:
    registry.clear()
    yield
    registry.clear()


def _load_component(field: FieldType, *, size: str = "32") -> tuple[Component, AddressBlockType.Register, FieldType]:
    register = AddressBlock.Register(
        name="control",
        address_offset=UnsignedLongintExpression(value="0"),
        choice=[UnsignedPositiveIntExpression(value=size), field],
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
    component = Component(
        vendor="test",
        library="library",
        name="registerFieldExpressions",
        version="1",
        type_definitions=ComponentType.TypeDefinitions(
            external_type_definitions=[
                ExternalTypeDefinitions(
                    name="types",
                    type_definitions_ref=ConfigurableLibraryRefType(
                        vendor="test",
                        library="types",
                        name="sharedTypes",
                        version="1",
                    ),
                )
            ]
        ),
        memory_maps=MemoryMaps(
            memory_map=[MemoryMapType(name="peripheral", choice=[block, AddressUnitBits(value="8")])]
        ),
    )
    xml = XmlDocument.serializer().render(component)
    _SCHEMA.assertValid(etree.fromstring(xml.encode()))
    loaded = XmlDocument.parser().from_string(xml, Component)
    _register_graph(loaded)
    loaded_register = loaded.memory_maps.memory_map[0].choice[0].choice[3]
    loaded_field = next(child for child in loaded_register.choice if isinstance(child, FieldType))
    return loaded, loaded_register, loaded_field


def test_register_field_getters_read_typed_children_from_loaded_xml() -> None:
    offset = UnsignedIntExpression(value="2 * 2", minimum=0, maximum=31)
    width = UnsignedPositiveIntExpression(value="1 << 3", minimum=1, maximum=32)
    _, register, field = _load_component(FieldType(name="status", bit_offset=offset, choice=[width]))
    offset = field.bit_offset
    width = next(child for child in field.choice if isinstance(child, UnsignedPositiveIntExpression))
    register_id = get_handle(register)
    field_id = get_handle(field)

    assert api.getFieldBitOffsetID(field_id) == get_handle(offset)
    assert api.getRegisterFieldBitOffset(field_id) == 4
    assert api.getRegisterFieldBitOffsetExpression(field_id) == "2 * 2"
    assert api.getRegisterFieldBitOffsetID(field_id) == get_handle(offset)
    assert api.getRegisterFieldBitWidth(field_id) == 8
    assert api.getRegisterFieldBitWidthExpression(field_id) == "1 << 3"
    assert api.getRegisterFieldBitWidthID(field_id) == get_handle(width)
    assert get_parent_info(field_id).parent_handle == register_id
    assert get_parent_info(field_id).path == ("choice",)
    assert get_parent_info(get_handle(offset)).parent_handle == field_id
    assert get_parent_info(get_handle(width)).parent_handle == field_id


def test_register_field_getters_validate_numeric_ranges_and_unresolved_sources() -> None:
    _, _, field = _load_component(
        FieldType(
            name="status",
            bit_offset=UnsignedIntExpression(value="offset_param"),
            choice=[UnsignedPositiveIntExpression(value="1")],
        )
    )
    field_id = get_handle(field)
    assert api.getRegisterFieldBitOffsetExpression(field_id) == "offset_param"
    with pytest.raises(TgiError) as error:
        api.getRegisterFieldBitOffset(field_id)
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT

    field.bit_offset.value = str(1 << 32)
    with pytest.raises(TgiError) as error:
        api.getRegisterFieldBitOffset(field_id)
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT


def test_register_field_width_getter_rejects_nonpositive_and_out_of_range_values() -> None:
    width = UnsignedPositiveIntExpression(value="1")
    _, _, field = _load_component(FieldType(name="status", bit_offset=UnsignedIntExpression(value="0"), choice=[width]))
    width = field.choice[0]
    field_id = get_handle(field)

    for source in ("0", str(1 << 32)):
        width.value = source
        with pytest.raises(TgiError) as error:
            api.getRegisterFieldBitWidth(field_id)
        assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT


@pytest.mark.parametrize(
    "register_type",
    [
        AddressBlockType.Register,
        BankedBlockType.Register,
        RegisterFile.Register,
        RegisterFileDefinitions.RegisterFileDefinition.Register,
    ],
)
def test_register_field_getters_support_all_register_model_variants(register_type: _RegisterType) -> None:
    width = UnsignedPositiveIntExpression(value="16")
    field = FieldType(name="data", bit_offset=UnsignedIntExpression(value="0"), choice=[width])
    register = register_type(
        name="control",
        address_offset=UnsignedLongintExpression(value="0"),
        choice=[UnsignedPositiveIntExpression(value="32"), field],
    )
    register_id = get_handle(register)
    _register_graph(register)
    field_id = get_handle(field)

    assert api.getRegisterFieldBitWidth(field_id) == 16
    assert api.getRegisterFieldBitWidthID(field_id) == get_handle(width)
    assert get_parent_info(field_id).parent_handle == register_id


def test_register_field_getters_return_none_for_reference_width_and_reject_malformed_choices() -> None:
    reference = FieldType.FieldDefinitionRef(value="shared", type_definitions="types")
    _, _, field = _load_component(
        FieldType(name="status", bit_offset=UnsignedIntExpression(value="0"), choice=[reference])
    )
    field_id = get_handle(field)
    assert api.getRegisterFieldBitWidth(field_id) is None
    assert api.getRegisterFieldBitWidthExpression(field_id) is None
    assert api.getRegisterFieldBitWidthID(field_id) is None

    field.choice.append(UnsignedPositiveIntExpression(value="8"))
    for operation in (
        api.getRegisterFieldBitWidth,
        api.getRegisterFieldBitWidthExpression,
        api.getRegisterFieldBitWidthID,
    ):
        with pytest.raises(TgiError) as error:
            operation(field_id)
        assert error.value.fault_code == TgiFaultCode.INVALID_ID


def test_register_field_getters_reject_wrong_handles_and_accept_detached_fields() -> None:
    _, _, field = _load_component(
        FieldType(
            name="data",
            bit_offset=UnsignedIntExpression(value="0"),
            choice=[UnsignedPositiveIntExpression(value="1")],
        )
    )
    field_id = get_handle(field)
    width_id = get_handle(UnsignedPositiveIntExpression(value="8"))

    for invalid_id in ("hdeadbeef", width_id):
        for operation in (
            api.getRegisterFieldBitOffset,
            api.getRegisterFieldBitOffsetExpression,
            api.getRegisterFieldBitOffsetID,
            api.getRegisterFieldBitWidth,
            api.getRegisterFieldBitWidthExpression,
            api.getRegisterFieldBitWidthID,
        ):
            with pytest.raises(TgiError) as error:
                operation(invalid_id)
            assert error.value.fault_code == TgiFaultCode.INVALID_ID

    detached = FieldType(
        name="detached",
        bit_offset=UnsignedIntExpression(value="3"),
        choice=[UnsignedPositiveIntExpression(value="1")],
    )
    assert api.getRegisterFieldBitOffset(get_handle(detached)) == 3
    assert api.getFieldBitOffsetID(field_id)


def test_register_field_operations_accept_fields_inside_alternate_registers() -> None:
    field = FieldType(
        name="alternateData",
        bit_offset=UnsignedIntExpression(value="4"),
        choice=[UnsignedPositiveIntExpression(value="8")],
    )
    alternate = AlternateRegisters.AlternateRegister(
        name="alternate",
        mode_ref=[ModeRef(value="secure", priority=0)],
        field_value=[field],
    )
    register = AddressBlockType.Register(
        name="control",
        address_offset=UnsignedLongintExpression(value="0"),
        choice=[UnsignedPositiveIntExpression(value="32")],
        alternate_registers=AlternateRegisters(alternate_register=[alternate]),
    )
    _register_graph(register)
    field_id = get_handle(field)

    assert api.getRegisterFieldBitOffset(field_id) == 4
    assert api.getRegisterFieldBitWidth(field_id) == 8
    assert api.setRegisterFieldBitWidth(field_id, "12") is True
    assert api.getRegisterFieldBitWidth(field_id) == 12


def test_register_field_operations_accept_register_definition_fields() -> None:
    field = FieldType(
        name="definedData",
        bit_offset=UnsignedIntExpression(value="0"),
        choice=[UnsignedPositiveIntExpression(value="8")],
    )
    definition = RegisterDefinitions.RegisterDefinition(
        name="sharedRegister",
        size=UnsignedPositiveIntExpression(value="32"),
        field_value=[field],
    )
    _register_graph(definition)
    field_id = get_handle(field)

    assert api.getRegisterFieldBitWidth(field_id) == 8
    assert api.setRegisterFieldBitWidth(field_id, "16") is True
    assert api.getRegisterFieldBitWidth(field_id) == 16


def test_set_register_field_bit_width_preserves_existing_wrapper_and_rolls_back_invalid_updates() -> None:
    width = UnsignedPositiveIntExpression(
        value="8",
        minimum=1,
        maximum=16,
        other_attributes={"{urn:test}preserve": "yes"},
    )
    _, _, field = _load_component(FieldType(name="status", bit_offset=UnsignedIntExpression(value="0"), choice=[width]))
    width = field.choice[0]
    field_id = get_handle(field)
    width_id = api.getRegisterFieldBitWidthID(field_id)

    assert api.setRegisterFieldBitWidth(field_id, "2 ** 3") is True
    assert api.getRegisterFieldBitWidth(field_id) == 8
    assert api.getRegisterFieldBitWidthExpression(field_id) == "2 ** 3"
    assert api.getRegisterFieldBitWidthID(field_id) == width_id
    assert width.value == "2 ** 3"
    assert width.minimum == 1 and width.maximum == 16
    assert width.other_attributes == {"{urn:test}preserve": "yes"}

    for source in ("0", str(1 << 32), "8 +"):
        with pytest.raises(TgiError) as error:
            api.setRegisterFieldBitWidth(field_id, source)
        assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
        assert width.value == "2 ** 3"
        assert field.choice == [width]

    assert api.setRegisterFieldBitWidth(field_id, "width_parameter") is True
    assert api.getRegisterFieldBitWidthExpression(field_id) == "width_parameter"
    with pytest.raises(TgiError) as error:
        api.getRegisterFieldBitWidth(field_id)
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT


def test_set_register_field_bit_width_normalizes_tuple_choice_without_replacing_wrapper() -> None:
    width = UnsignedPositiveIntExpression(value="8", minimum=1, maximum=32)
    field = FieldType(name="data", bit_offset=UnsignedIntExpression(value="0"), choice=(width, False))
    register = AddressBlockType.Register(
        name="control",
        address_offset=UnsignedLongintExpression(value="0"),
        choice=(UnsignedPositiveIntExpression(value="32"), field),
    )
    _register_graph(register)
    field_id = get_handle(field)
    width_id = api.getRegisterFieldBitWidthID(field_id)

    assert api.setRegisterFieldBitWidth(field_id, "16") is True
    assert isinstance(field.choice, list)
    assert field.choice == [width, False]
    assert api.getRegisterFieldBitWidthID(field_id) == width_id
    assert get_parent_info(width_id).parent_handle == field_id


def test_set_register_field_bit_width_checks_scalar_containment_atomically() -> None:
    field = FieldType(
        name="upper",
        bit_offset=UnsignedIntExpression(value="28"),
        choice=[UnsignedPositiveIntExpression(value="4")],
    )
    _, _, loaded_field = _load_component(field, size="32")
    field_id = get_handle(loaded_field)
    width_id = api.getRegisterFieldBitWidthID(field_id)
    width = resolve_handle(width_id)

    with pytest.raises(TgiError) as error:
        api.setRegisterFieldBitWidth(field_id, "8")
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert loaded_field.choice[0] is width
    assert width.value == "4"

    assert api.setRegisterFieldBitWidth(field_id, "2") is True
    assert api.getRegisterFieldBitWidth(field_id) == 2


def test_set_register_field_bit_width_replaces_definition_reference_and_invalidates_old_handle() -> None:
    reference = FieldType.FieldDefinitionRef(value="shared", type_definitions="types")
    field = FieldType(name="status", bit_offset=UnsignedIntExpression(value="0"), choice=[reference])
    loaded, _, loaded_field = _load_component(field)
    field_id = get_handle(loaded_field)
    reference_id = get_handle(loaded_field.choice[0])

    assert api.setRegisterFieldBitWidth(field_id, "16") is True
    assert isinstance(loaded_field.choice[0], UnsignedPositiveIntExpression)
    assert api.getRegisterFieldBitWidth(field_id) == 16
    assert resolve_handle(reference_id) is None
    assert get_parent_info(api.getRegisterFieldBitWidthID(field_id)).parent_handle == field_id

    xml = XmlDocument.serializer().render(loaded)
    _SCHEMA.assertValid(etree.fromstring(xml.encode()))


def test_set_register_field_bit_width_replaces_alias_branch_with_schema_valid_order() -> None:
    alias = FieldType.AliasOf(field_ref=FieldRef(field_ref="original"))
    field = FieldType(
        name="alias",
        bit_offset=UnsignedIntExpression(value="0"),
        choice=["fieldType", alias],
    )
    loaded, _, loaded_field = _load_component(field)
    field_id = get_handle(loaded_field)
    alias_id = get_handle(loaded_field.choice[1])
    field_ref_id = get_handle(loaded_field.choice[1].field_ref)

    assert api.setRegisterFieldBitWidth(field_id, "8") is True
    assert loaded_field.choice[0] == "fieldType"
    assert isinstance(loaded_field.choice[1], UnsignedPositiveIntExpression)
    assert resolve_handle(alias_id) is None
    assert resolve_handle(field_ref_id) is None
    xml = XmlDocument.serializer().render(loaded)
    _SCHEMA.assertValid(etree.fromstring(xml.encode()))

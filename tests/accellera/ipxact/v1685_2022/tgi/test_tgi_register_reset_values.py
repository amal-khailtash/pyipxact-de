"""Register reset value and mask TGI contracts."""

import inspect
from collections.abc import Iterator

import pytest
from lxml import etree

from amal.eda.accellera.ipxact.v1685_2022 import tgi
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
from org.accellera.ipxact.v1685_2022.base_address import BaseAddress
from org.accellera.ipxact.v1685_2022.component import Component
from org.accellera.ipxact.v1685_2022.field_definitions import FieldDefinitions
from org.accellera.ipxact.v1685_2022.field_type import FieldType
from org.accellera.ipxact.v1685_2022.memory_map_type import MemoryMapType
from org.accellera.ipxact.v1685_2022.memory_maps import MemoryMaps
from org.accellera.ipxact.v1685_2022.reset import Reset
from org.accellera.ipxact.v1685_2022.unsigned_bit_vector_expression import UnsignedBitVectorExpression
from org.accellera.ipxact.v1685_2022.unsigned_int_expression import UnsignedIntExpression
from org.accellera.ipxact.v1685_2022.unsigned_longint_expression import UnsignedLongintExpression
from org.accellera.ipxact.v1685_2022.unsigned_positive_int_expression import UnsignedPositiveIntExpression
from org.accellera.ipxact.v1685_2022.unsigned_positive_longint_expression import UnsignedPositiveLongintExpression
from org.accellera.ipxact.v1685_2022.usage_type import UsageType

_SCHEMA = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))
_BASE = [
    ("getResetMask", "resetID", "F.7.73.78"),
    ("getResetMaskExpression", "resetID", "F.7.73.79"),
    ("getResetMaskID", "resetID", "F.7.73.80"),
    ("getResetValue", "resetID", "F.7.73.81"),
    ("getResetValueExpression", "resetID", "F.7.73.82"),
    ("getResetValueID", "resetID", "F.7.73.83"),
]
_EXTENDED = [
    ("removeResetMask", "resetID", "F.7.74.37"),
    ("setResetMask", "resetID,mask", "F.7.74.68"),
    ("setResetValue", "resetID,value", "F.7.74.69"),
]


@pytest.fixture(autouse=True)
def clean_registry() -> Iterator[None]:
    registry.clear()
    yield
    registry.clear()


def _reset(source: str = "0", mask: str | None = None, *, reset_type_ref: str | None = None) -> Reset:
    return Reset(
        value=UnsignedBitVectorExpression(value=source),
        mask=UnsignedBitVectorExpression(value=mask) if mask is not None else None,
        reset_type_ref=reset_type_ref,
        id="warm-reset",
    )


def _owned_reset(source: str = "0", mask: str | None = None, width: str = "8") -> tuple[FieldType, Reset, str]:
    reset = _reset(source, mask, reset_type_ref="WARM")
    resets = FieldType.Resets(reset=[reset])
    field = FieldType(
        name="status",
        bit_offset=UnsignedIntExpression(value="0"),
        choice=[UnsignedPositiveIntExpression(value=width), resets],
    )
    _register_graph(field)
    return field, reset, get_handle(reset)


@pytest.mark.parametrize(
    "name,args,section",
    [(*operation,) for operation in _BASE + _EXTENDED],
)
def test_reset_value_and_mask_contract_exports_and_documentation(name: str, args: str, section: str) -> None:
    function = getattr(api, name)
    assert list(inspect.signature(function).parameters) == args.split(",")
    assert name in api.__all__
    assert getattr(tgi, name) is function
    assert "Args:" in function.__doc__ and "Returns:" in function.__doc__
    assert f"Section: {section}." in function.__doc__


def test_getters_read_expression_source_handles_and_optional_stored_mask() -> None:
    reset = _reset("4'b1010", "4'b1110")
    reset_id = get_handle(reset)

    assert api.getResetValueExpression(reset_id) == "4'b1010"
    assert api.getResetMaskExpression(reset_id) == "4'b1110"
    value_id = api.getResetValueID(reset_id)
    mask_id = api.getResetMaskID(reset_id)
    assert value_id == get_handle(reset.value)
    assert mask_id == get_handle(reset.mask)
    assert get_parent_info(value_id).parent_handle == reset_id
    assert get_parent_info(mask_id).parent_handle == reset_id

    absent = _reset("0")
    absent_id = get_handle(absent)
    assert api.getResetMask(absent_id) is None
    assert api.getResetMaskExpression(absent_id) is None
    assert api.getResetMaskID(absent_id) is None
    assert absent.mask is None


@pytest.mark.parametrize(
    "source,expected",
    [
        ("16'h1234", 0x34),
        ("-1", 0xFF),
        ("1024", 0),
        ("8'b10x1_zz01", 0x91),
        ("8'hf0 + 8'h20", 0x10),
    ],
)
def test_numeric_getters_apply_containing_field_width_and_bit_cast(source: str, expected: int) -> None:
    _, reset, reset_id = _owned_reset(source, "16'h1234")
    assert api.getResetValue(reset_id) == expected
    assert api.getResetMask(reset_id) == 0x34
    assert reset.value.value == source


def test_numeric_getters_keep_inferred_width_and_unbounded_integer_domain() -> None:
    reset = _reset("128'h1 << 100", "128'h1 << 96")
    reset_id = get_handle(reset)
    assert api.getResetValue(reset_id) == 1 << 100
    assert api.getResetMask(reset_id) == 1 << 96


def test_alternate_and_field_definition_owners_supply_contextual_width() -> None:
    from org.accellera.ipxact.v1685_2022.alternate_registers import AlternateRegisters

    alternate_reset = _reset("16'h1234")
    alternate_field = FieldType(
        name="status",
        bit_offset=UnsignedIntExpression(value="0"),
        choice=[UnsignedPositiveIntExpression(value="4"), FieldType.Resets(reset=[alternate_reset])],
    )
    alternate = AlternateRegisters.AlternateRegister(name="alternate", field_value=[alternate_field])
    _register_graph(alternate)
    assert api.getResetValue(get_handle(alternate_reset)) == 4

    definition_reset = _reset("16'h1234")
    definition = FieldDefinitions.FieldDefinition(
        name="status",
        bit_width=UnsignedPositiveIntExpression(value="4"),
        resets=FieldDefinitions.FieldDefinition.Resets(reset=[definition_reset]),
    )
    _register_graph(definition)
    assert api.getResetValue(get_handle(definition_reset)) == 4


def test_unresolved_containing_width_is_deferred_by_setters_and_faults_getters() -> None:
    reset = _reset("8'h12")
    field = FieldType(
        name="status",
        bit_offset=UnsignedIntExpression(value="0"),
        choice=[UnsignedPositiveIntExpression(value="FIELD_WIDTH"), FieldType.Resets(reset=[reset])],
    )
    _register_graph(field)
    reset_id = get_handle(reset)
    assert api.setResetValue(reset_id, "16'h1234") is True
    assert reset.value.value == "16'h1234"
    with pytest.raises(TgiError) as error:
        api.getResetValue(reset_id)
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT


def test_expression_setters_defer_symbols_but_numeric_getters_require_resolution() -> None:
    _, reset, reset_id = _owned_reset("0")
    assert api.setResetValue(reset_id, "RESET_VALUE + 1") is True
    assert api.setResetMask(reset_id, "RESET_MASK") is True
    assert api.getResetValueExpression(reset_id) == "RESET_VALUE + 1"
    assert api.getResetMaskExpression(reset_id) == "RESET_MASK"
    for operation in (api.getResetValue, api.getResetMask):
        with pytest.raises(TgiError) as error:
            operation(reset_id)
        assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT


@pytest.mark.parametrize("operation", [api.setResetValue, api.setResetMask])
@pytest.mark.parametrize("bad_source", [None, 1, True, "1 +", "bad\x00text"])
def test_invalid_bit_vector_sources_roll_back(operation, bad_source) -> None:
    _, reset, reset_id = _owned_reset("8'h12", "8'hff")
    old_value, old_mask = reset.value, reset.mask
    with pytest.raises(TgiError) as error:
        operation(reset_id, bad_source)
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert reset.value is old_value and reset.mask is old_mask
    assert reset.value.value == "8'h12" and reset.mask.value == "8'hff"


def test_existing_wrappers_and_reset_metadata_survive_setters() -> None:
    _, reset, reset_id = _owned_reset("8'h12", "8'hff")
    value, mask = reset.value, reset.mask
    value.other_attributes = {"{urn:test}marker": "value"}
    mask.other_attributes = {"{urn:test}marker": "mask"}
    value_id, mask_id = get_handle(value), get_handle(mask)

    assert api.setResetValue(reset_id, "-2") is True
    assert api.setResetMask(reset_id, "4'b1x01") is True
    assert reset.value is value and reset.mask is mask
    assert value.value == "-2" and mask.value == "4'b1x01"
    assert value.other_attributes == {"{urn:test}marker": "value"}
    assert mask.other_attributes == {"{urn:test}marker": "mask"}
    assert api.getResetValueID(reset_id) == value_id
    assert api.getResetMaskID(reset_id) == mask_id
    assert reset.id == "warm-reset" and reset.reset_type_ref == "WARM"


def test_mask_creation_removal_is_repeatable_and_invalidates_owned_handle() -> None:
    _, reset, reset_id = _owned_reset("8'h42")
    value, reset_type_ref, xml_id = reset.value, reset.reset_type_ref, reset.id

    assert api.removeResetMask(reset_id) is False
    assert api.getResetMaskID(reset_id) is None
    assert api.setResetMask(reset_id, "8'hf0") is True
    mask = reset.mask
    mask_id = api.getResetMaskID(reset_id)
    assert mask_id == get_handle(mask)
    assert api.removeResetMask(reset_id) is True
    assert reset.mask is None
    assert resolve_handle(mask_id) is None
    assert api.removeResetMask(reset_id) is False
    assert api.getResetMaskExpression(reset_id) is None
    assert reset.value is value and reset.reset_type_ref == reset_type_ref and reset.id == xml_id


def test_known_field_width_bounds_are_checked_before_value_or_mask_mutation() -> None:
    width = UnsignedPositiveIntExpression(value="8", maximum=7)
    reset = _reset("8'h12", "8'hff")
    field = FieldType(
        name="status",
        bit_offset=UnsignedIntExpression(value="0"),
        choice=[width, FieldType.Resets(reset=[reset])],
    )
    _register_graph(field)
    reset_id = get_handle(reset)
    value, mask = reset.value, reset.mask

    with pytest.raises(TgiError) as error:
        api.setResetValue(reset_id, "8'h33")
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    with pytest.raises(TgiError) as error:
        api.setResetMask(reset_id, "8'h00")
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert reset.value is value and reset.mask is mask
    assert value.value == "8'h12" and mask.value == "8'hff"


def test_required_value_and_wrong_reset_handles_fault_cleanly() -> None:
    missing_value = Reset(value=None)  # type: ignore[arg-type]
    missing_id = get_handle(missing_value)
    for operation in (api.getResetValue, api.getResetValueExpression, api.getResetValueID, api.setResetValue):
        with pytest.raises(TgiError) as error:
            operation(missing_id, "1") if operation is api.setResetValue else operation(missing_id)
        assert error.value.fault_code == TgiFaultCode.INVALID_ID

    wrong_id = get_handle(UnsignedPositiveIntExpression(value="8"))
    for operation, tail in (
        *((getattr(api, name), ()) for name in ("getResetMask", "getResetMaskExpression", "getResetMaskID")),
        *((getattr(api, name), ()) for name in ("getResetValue", "getResetValueExpression", "getResetValueID")),
        (api.removeResetMask, ()),
        (api.setResetMask, ("8'h0",)),
        (api.setResetValue, ("8'h0",)),
    ):
        with pytest.raises(TgiError) as error:
            operation(wrong_id, *tail)
        assert error.value.fault_code == TgiFaultCode.INVALID_ID
    for operation, tail in (
        (api.getResetValue, ()),
        (api.getResetMask, ()),
        (api.removeResetMask, ()),
        (api.setResetValue, ("1",)),
        (api.setResetMask, ("1",)),
    ):
        with pytest.raises(TgiError) as error:
            operation("hdeadbeef", *tail)
        assert error.value.fault_code == TgiFaultCode.INVALID_ID


def test_schema_valid_round_trip_preserves_reset_parentage_and_updated_sources() -> None:
    reset = _reset("4'b1010", "4'b1111")
    field = FieldType(
        name="status",
        bit_offset=UnsignedIntExpression(value="0"),
        choice=[UnsignedPositiveIntExpression(value="4"), FieldType.Resets(reset=[reset])],
    )
    register = AddressBlock.Register(
        name="control",
        address_offset=UnsignedLongintExpression(value="0"),
        choice=[UnsignedPositiveIntExpression(value="32"), field],
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
        name="registerResetValues",
        version="1",
        memory_maps=MemoryMaps(
            memory_map=[MemoryMapType(name="peripheral", choice=[block, AddressUnitBits(value="8")])]
        ),
    )
    xml = XmlDocument.serializer().render(component)
    _SCHEMA.assertValid(etree.fromstring(xml.encode()))
    parsed = XmlDocument.parser().from_string(xml, Component)
    _register_graph(parsed)
    block_choice = parsed.memory_maps.memory_map[0].choice[0].choice
    parsed_register = next(child for child in block_choice if isinstance(child, AddressBlockType.Register))
    parsed_field = next(child for child in parsed_register.choice if isinstance(child, FieldType))
    parsed_resets = next(child for child in parsed_field.choice if isinstance(child, FieldType.Resets))
    parsed_reset = parsed_resets.reset[0]
    reset_id = get_handle(parsed_reset)

    assert api.getResetValue(reset_id) == 0b1010
    assert api.getResetMask(reset_id) == 0b1111
    assert api.setResetValue(reset_id, "16'h1234") is True
    assert api.setResetMask(reset_id, "16'h12ff") is True
    updated_xml = XmlDocument.serializer().render(parsed)
    _SCHEMA.assertValid(etree.fromstring(updated_xml.encode()))

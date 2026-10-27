"""Register field reset lifecycle contracts."""

import inspect
from collections.abc import Iterator

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
from org.accellera.ipxact.v1685_2022.access import Access
from org.accellera.ipxact.v1685_2022.access_type import AccessType
from org.accellera.ipxact.v1685_2022.address_block import AddressBlock
from org.accellera.ipxact.v1685_2022.address_block_type import AddressBlockType
from org.accellera.ipxact.v1685_2022.address_unit_bits import AddressUnitBits
from org.accellera.ipxact.v1685_2022.base_address import BaseAddress
from org.accellera.ipxact.v1685_2022.component import Component
from org.accellera.ipxact.v1685_2022.component_type import ComponentType
from org.accellera.ipxact.v1685_2022.enumerated_value_type import EnumeratedValueType
from org.accellera.ipxact.v1685_2022.enumerated_values import EnumeratedValues
from org.accellera.ipxact.v1685_2022.field_definitions import FieldDefinitions
from org.accellera.ipxact.v1685_2022.field_ref import FieldRef
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
_OPERATIONS = (
    ("getRegisterFieldResetIDs", ("registerFieldID",), "F.7.73.62"),
    ("addRegisterFieldReset", ("registerFieldID", "value"), "F.7.74.9"),
    ("removeRegisterFieldReset", ("resetID",), "F.7.74.31"),
)


@pytest.fixture(autouse=True)
def clean_registry() -> Iterator[None]:
    registry.clear()
    yield
    registry.clear()


def _field(
    *,
    width: str = "8",
    choice: list[object] | tuple[object, ...] | None = None,
    name: str = "status",
) -> FieldType:
    if choice is None:
        choice = [UnsignedPositiveIntExpression(value=width)]
    return FieldType(name=name, bit_offset=UnsignedIntExpression(value="0"), choice=choice)


def _component(field: FieldType) -> Component:
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
    return Component(
        vendor="test",
        library="library",
        name="registerResetLifecycle",
        version="1",
        memory_maps=MemoryMaps(
            memory_map=[MemoryMapType(name="peripheral", choice=[block, AddressUnitBits(value="8")])]
        ),
    )


@pytest.mark.parametrize(("name", "parameters", "section"), _OPERATIONS)
def test_reset_lifecycle_exports_signatures_and_sections(name: str, parameters: tuple[str, ...], section: str) -> None:
    function = getattr(api, name)
    assert tuple(inspect.signature(function).parameters) == parameters
    assert name in api.__all__
    assert getattr(tgi, name) is function
    assert "Args:" in function.__doc__
    assert "Returns:" in function.__doc__
    assert f"Section: {section}." in function.__doc__


def test_getter_handles_tuple_choices_and_reset_collections_in_schema_order() -> None:
    resets = FieldType.Resets(
        reset=(
            Reset(value=UnsignedBitVectorExpression(value="8'h01"), reset_type_ref="WARM"),
            Reset(value=UnsignedBitVectorExpression(value="8'h02")),
        )
    )
    field = _field(choice=(UnsignedPositiveIntExpression(value="8"), resets))
    _register_graph(field)

    reset_ids = api.getRegisterFieldResetIDs(get_handle(field))
    assert reset_ids == [get_handle(reset) for reset in resets.reset]
    assert all(get_parent_info(reset_id).parent_handle == get_handle(resets) for reset_id in reset_ids)


def test_add_preserves_expression_source_and_registers_detached_field_ownership() -> None:
    field = _field(width="4", choice=(UnsignedPositiveIntExpression(value="4"), False))
    _register_graph(field)

    reset_id = api.addRegisterFieldReset(get_handle(field), "FIELD_RESET")
    reset = resolve_handle(reset_id)
    assert isinstance(reset, Reset)
    assert reset.value.value == "FIELD_RESET"
    assert reset.reset_type_ref is None
    assert api.getRegisterFieldResetIDs(get_handle(field)) == [reset_id]
    holder = field.choice[-1]
    assert isinstance(holder, FieldType.Resets)
    assert get_parent_info(get_handle(holder)).parent_handle == get_handle(field)
    assert get_parent_info(reset_id).parent_handle == get_handle(holder)


def test_add_default_hard_reset_rejects_duplicate_identity_without_mutation() -> None:
    field = _field(width="8")
    _register_graph(field)
    field_id = get_handle(field)
    first_id = api.addRegisterFieldReset(field_id, "8'h11")
    holder = field.choice[-1]
    choice_before = tuple(field.choice)
    resets_before = tuple(holder.reset)

    with pytest.raises(TgiError) as error:
        api.addRegisterFieldReset(field_id, "8'h22")

    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert tuple(field.choice) == choice_before
    assert tuple(holder.reset) == resets_before
    assert api.getRegisterFieldResetIDs(field_id) == [first_id]


def test_default_hard_and_explicit_hard_are_the_same_reset_identity() -> None:
    field = _field(
        choice=[
            UnsignedPositiveIntExpression(value="8"),
            FieldType.Resets(
                reset=[
                    Reset(value=UnsignedBitVectorExpression(value="0")),
                    Reset(value=UnsignedBitVectorExpression(value="1"), reset_type_ref="HARD"),
                ]
            ),
        ]
    )
    _register_graph(field)

    with pytest.raises(TgiError) as error:
        api.getRegisterFieldResetIDs(get_handle(field))
    assert error.value.fault_code == TgiFaultCode.INVALID_ID


@pytest.mark.parametrize("bad_value", [None, 1, True, "8'h1 +", "bad\x00value"])
def test_invalid_add_value_rolls_back_field_choice(bad_value: object) -> None:
    field = _field(width="8")
    _register_graph(field)
    field_id = get_handle(field)
    before = tuple(field.choice)

    with pytest.raises(TgiError) as error:
        api.addRegisterFieldReset(field_id, bad_value)  # type: ignore[arg-type]

    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert tuple(field.choice) == before
    assert api.getRegisterFieldResetIDs(field_id) == []


def test_alias_and_field_definition_reference_cannot_gain_an_inline_reset_width() -> None:
    alias = _field(choice=[FieldType.AliasOf(field_ref=FieldRef(field_ref="shared"))])
    reference = _field(choice=[FieldType.FieldDefinitionRef(value="shared", type_definitions="types")])
    _register_graph(alias)
    _register_graph(reference)

    for field in (alias, reference):
        with pytest.raises(TgiError) as error:
            api.addRegisterFieldReset(get_handle(field), "0")
        assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
        assert api.getRegisterFieldResetIDs(get_handle(field)) == []
        assert len(field.choice) == 1


def test_wrong_handles_and_field_definition_resets_are_rejected() -> None:
    field = _field()
    _register_graph(field)
    wrong_id = get_handle(UnsignedIntExpression(value="0"))
    definition_reset = Reset(value=UnsignedBitVectorExpression(value="0"))
    definition = FieldDefinitions.FieldDefinition(
        name="shared",
        bit_width=UnsignedPositiveIntExpression(value="8"),
        resets=FieldDefinitions.FieldDefinition.Resets(reset=[definition_reset]),
    )
    _register_graph(definition)

    for operation, args in (
        (api.getRegisterFieldResetIDs, (wrong_id,)),
        (api.addRegisterFieldReset, (wrong_id, "0")),
        (api.removeRegisterFieldReset, (wrong_id,)),
        (api.removeRegisterFieldReset, (get_handle(definition_reset),)),
        (api.getRegisterFieldResetIDs, ("missing",)),
    ):
        with pytest.raises(TgiError) as error:
            operation(*args)
        assert error.value.fault_code == TgiFaultCode.INVALID_ID

    assert api.getRegisterFieldResetIDs(get_handle(field)) == []


def test_remove_invalidates_reset_descendants_and_prunes_empty_group() -> None:
    reset = Reset(
        value=UnsignedBitVectorExpression(value="8'h12"),
        mask=UnsignedBitVectorExpression(value="8'hff"),
        reset_type_ref="WARM",
        id="reset-id",
    )
    holder = FieldType.Resets(reset=[reset])
    field = _field(choice=[UnsignedPositiveIntExpression(value="8"), holder])
    _register_graph(field)
    reset_id = get_handle(reset)
    value_id = get_handle(reset.value)
    mask_id = get_handle(reset.mask)
    holder_id = get_handle(holder)

    assert api.removeRegisterFieldReset(reset_id) is True
    assert holder not in field.choice
    assert resolve_handle(reset_id) is None
    assert resolve_handle(value_id) is None
    assert resolve_handle(mask_id) is None
    assert resolve_handle(holder_id) is None
    assert api.getRegisterFieldResetIDs(get_handle(field)) == []


def test_remove_parsed_reset_round_trips_and_preserves_sibling_source() -> None:
    warm = Reset(
        value=UnsignedBitVectorExpression(value="8'h44"),
        mask=UnsignedBitVectorExpression(value="8'hff"),
        reset_type_ref="WARM",
    )
    cold = Reset(value=UnsignedBitVectorExpression(value="8'h00"))
    field = _field(choice=[UnsignedPositiveIntExpression(value="8"), FieldType.Resets(reset=[warm, cold])])
    component = _component(field)
    component.reset_types = ComponentType.ResetTypes(reset_type=[ComponentType.ResetTypes.ResetType(name="WARM")])
    xml = XmlDocument.serializer().render(component)
    _SCHEMA.assertValid(etree.fromstring(xml.encode()))
    parsed = XmlDocument.parser().from_string(xml, Component)
    _register_graph(parsed)
    parsed_block = parsed.memory_maps.memory_map[0].choice[0]
    parsed_register = next(child for child in parsed_block.choice if isinstance(child, AddressBlockType.Register))
    parsed_field = next(child for child in parsed_register.choice if isinstance(child, FieldType))
    parsed_holder = next(child for child in parsed_field.choice if isinstance(child, FieldType.Resets))
    parsed_warm, parsed_cold = parsed_holder.reset
    warm_id = get_handle(parsed_warm)
    cold_id = get_handle(parsed_cold)
    value_id = get_handle(parsed_warm.value)

    assert api.getRegisterFieldResetIDs(get_handle(parsed_field)) == [warm_id, cold_id]
    assert api.removeRegisterFieldReset(warm_id) is True
    assert resolve_handle(warm_id) is None
    assert resolve_handle(value_id) is None
    assert api.getRegisterFieldResetIDs(get_handle(parsed_field)) == [cold_id]
    updated_xml = XmlDocument.serializer().render(parsed)
    _SCHEMA.assertValid(etree.fromstring(updated_xml.encode()))
    assert "8'h00" in updated_xml
    assert "8'h44" not in updated_xml


def test_add_inserts_resets_before_field_data_and_round_trips_schema_valid() -> None:
    policy = FieldType.FieldAccessPolicies(
        field_access_policy=[
            FieldType.FieldAccessPolicies.FieldAccessPolicy(choice=[Access(value=AccessType.READ_WRITE)])
        ]
    )
    enumerated = EnumeratedValues(
        enumeration_definition_ref_or_enumerated_value=[
            EnumeratedValueType(name="IDLE", value=UnsignedBitVectorExpression(value="0"))
        ]
    )
    field = _field(choice=[UnsignedPositiveIntExpression(value="8"), True, policy, enumerated])
    component = _component(field)
    _register_graph(component)
    field_id = get_handle(field)

    api.addRegisterFieldReset(field_id, "8'h00")

    assert isinstance(field.choice[0], UnsignedPositiveIntExpression)
    assert field.choice[1] is True
    assert isinstance(field.choice[2], FieldType.Resets)
    assert field.choice[3] is policy
    assert field.choice[4] is enumerated
    xml = XmlDocument.serializer().render(component)
    _SCHEMA.assertValid(etree.fromstring(xml.encode()))
    parsed = XmlDocument.parser().from_string(xml, Component)
    _register_graph(parsed)
    parsed_block = parsed.memory_maps.memory_map[0].choice[0]
    parsed_register = next(child for child in parsed_block.choice if isinstance(child, AddressBlockType.Register))
    parsed_field = next(child for child in parsed_register.choice if isinstance(child, FieldType))
    assert [type(child) for child in parsed_field.choice] == [
        UnsignedPositiveIntExpression,
        bool,
        FieldType.Resets,
        FieldType.FieldAccessPolicies,
        EnumeratedValues,
    ]

"""IEEE 1685-2022 F.7.81 address-unit getters on reusable definitions."""

from collections.abc import Callable, Iterator
from inspect import signature

import pytest
from lxml import etree

from amal.eda.accellera.ipxact.v1685_2022 import tgi as root_api
from amal.eda.accellera.ipxact.v1685_2022.tgi import type_definitions as api
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import (
    TgiError,
    TgiFaultCode,
    get_handle,
    get_parent_info,
    registry,
    resolve_handle,
)
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import (
    AddressBlock,
    AddressBlockDefinitions,
    AddressUnitBits,
    BankDefinitions,
    BankedBlockType,
    BaseAddress,
    MemoryRemapDefinitions,
    TypeDefinitions,
    UnsignedPositiveIntExpression,
    UnsignedPositiveLongintExpression,
)

_SCHEMA = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))
_NS = "http://www.accellera.org/XMLSchema/IPXACT/1685-2022"

_Getter = Callable[[str], int | str | None]
type _DefinitionOwner = (
    AddressBlockDefinitions.AddressBlockDefinition
    | BankDefinitions.BankDefinition
    | MemoryRemapDefinitions.MemoryRemapDefinition
)


@pytest.fixture(autouse=True)
def clear_registry() -> Iterator[None]:
    registry.clear()
    yield
    registry.clear()


def _definitions(
    address_block_bits: str | None = "2**3",
    bank_bits: str | None = "64'h10",
    remap_bits: str | None = "8",
) -> TypeDefinitions:
    address_block = AddressBlockDefinitions.AddressBlockDefinition(
        name="memory_block",
        range=UnsignedPositiveLongintExpression(value="256"),
        width=UnsignedPositiveIntExpression(value="32"),
        address_unit_bits=AddressUnitBits(value=address_block_bits) if address_block_bits is not None else None,
    )
    bank = BankDefinitions.BankDefinition(
        name="memory_bank",
        address_block_or_bank=[
            BankedBlockType(
                name="bank_block",
                range=UnsignedPositiveLongintExpression(value="256"),
                width=UnsignedPositiveIntExpression(value="32"),
            )
        ],
        address_unit_bits=AddressUnitBits(value=bank_bits) if bank_bits is not None else None,
    )
    remap = MemoryRemapDefinitions.MemoryRemapDefinition(
        name="memory_remap",
        address_block_or_bank=[
            AddressBlock(
                name="remap_block",
                base_address=BaseAddress(value="0"),
                choice=[
                    UnsignedPositiveLongintExpression(value="256"),
                    UnsignedPositiveIntExpression(value="32"),
                ],
            )
        ],
        address_unit_bits=AddressUnitBits(value=remap_bits) if remap_bits is not None else None,
    )
    return TypeDefinitions(
        vendor="example.org",
        library="types",
        name="memory_types",
        version="1.0",
        address_block_definitions=AddressBlockDefinitions(address_block_definition=[address_block]),
        bank_definitions=BankDefinitions(bank_definition=[bank]),
        memory_remap_definitions=MemoryRemapDefinitions(memory_remap_definition=[remap]),
    )


def _owner_cases(root: TypeDefinitions) -> list[tuple[str, _DefinitionOwner, _Getter, _Getter, _Getter]]:
    assert root.address_block_definitions is not None
    assert root.bank_definitions is not None
    assert root.memory_remap_definitions is not None
    return [
        (
            "address block definition",
            root.address_block_definitions.address_block_definition[0],
            api.getAddressBlockDefinitionAddressUnitBits,
            api.getAddressBlockDefinitionAddressUnitBitsExpression,
            api.getAddressBlockDefinitionAddressUnitBitsID,
        ),
        (
            "bank definition",
            root.bank_definitions.bank_definition[0],
            api.getBankDefinitionAddressUnitBits,
            api.getBankDefinitionAddressUnitBitsExpression,
            api.getBankDefinitionAddressUnitBitsID,
        ),
        (
            "memory remap definition",
            root.memory_remap_definitions.memory_remap_definition[0],
            api.getMemoryRemapDefinitionAddressUnitBits,
            api.getMemoryRemapDefinitionAddressUnitBitsExpression,
            api.getMemoryRemapDefinitionAddressUnitBitsID,
        ),
    ]


def _register(root: TypeDefinitions) -> None:
    registry.register(root, ("example.org", "types", "memory_types", "1.0"))


def _assert_fault(action: Callable[[], object], fault_code: str) -> None:
    with pytest.raises(TgiError) as error:
        action()
    assert error.value.fault_code == fault_code


def test_address_unit_getters_resolve_expression_source_and_owned_child_handles() -> None:
    root = _definitions()
    _register(root)

    expected = {
        "address block definition": (8, "2**3"),
        "bank definition": (16, "64'h10"),
        "memory remap definition": (8, "8"),
    }
    for name, owner, value_getter, expression_getter, id_getter in _owner_cases(root):
        owner_id = get_handle(owner)
        child = owner.address_unit_bits
        assert child is not None
        child.other_attributes = {"{urn:test}marker": name}
        child_id = id_getter(owner_id)
        assert child_id is not None
        assert resolve_handle(child_id) is child
        assert value_getter(owner_id) == expected[name][0]
        assert expression_getter(owner_id) == expected[name][1]
        assert owner.address_unit_bits is child
        assert child.other_attributes["{urn:test}marker"] == name
        parent_info = get_parent_info(child_id)
        assert parent_info is not None
        assert parent_info.parent_handle == owner_id
        assert parent_info.path == ("address_unit_bits",)


def test_address_unit_getters_accept_xsd_valid_parsed_type_definitions_round_trip() -> None:
    root = _definitions()
    xml = XmlDocument.serializer().render(root)
    _SCHEMA.assertValid(etree.fromstring(xml.encode()))
    parsed = XmlDocument.parser().from_string(xml, TypeDefinitions)
    assert parsed == root
    _register(parsed)

    for _name, owner, value_getter, expression_getter, id_getter in _owner_cases(parsed):
        owner_id = get_handle(owner)
        assert id_getter(owner_id) == get_handle(owner.address_unit_bits)
        assert expression_getter(owner_id) == owner.address_unit_bits.value
        assert value_getter(owner_id) is not None


@pytest.mark.parametrize(
    ("name", "owner_index", "expression", "expected"),
    [
        ("decimal", 0, "12", 12),
        ("based literal", 1, "64'h7FFF_FFFF_FFFF_FFFF", (1 << 63) - 1),
        ("arithmetic", 2, "2**4 + 3", 19),
    ],
)
def test_resolved_values_use_sv_integer_evaluation_without_changing_source(
    name: str, owner_index: int, expression: str, expected: int
) -> None:
    root = _definitions()
    _register(root)
    owner = _owner_cases(root)[owner_index][1]
    owner.address_unit_bits.value = expression
    owner_id = get_handle(owner)
    value_getter = _owner_cases(root)[owner_index][2]
    expression_getter = _owner_cases(root)[owner_index][3]

    assert value_getter(owner_id) == expected, name
    assert expression_getter(owner_id) == expression
    assert owner.address_unit_bits.value == expression


@pytest.mark.parametrize(
    "expression",
    [
        "0",
        "-1",
        "1.5",
        "1 +",
        "MISSING_PARAMETER",
        "64'hx",
        "64'h1_0000_0000_0000_0000",
        "64'h8000_0000_0000_0000",
    ],
)
@pytest.mark.parametrize("owner_index", [0, 1, 2])
def test_invalid_address_unit_values_raise_invalid_argument(expression: str, owner_index: int) -> None:
    root = _definitions()
    _register(root)
    owner = _owner_cases(root)[owner_index][1]
    owner.address_unit_bits.value = expression
    value_getter = _owner_cases(root)[owner_index][2]

    _assert_fault(lambda: value_getter(get_handle(owner)), TgiFaultCode.INVALID_ARGUMENT)


@pytest.mark.parametrize("owner_index", [0, 1, 2])
@pytest.mark.parametrize(("expression", "valid"), [("4", True), ("8", True), ("3", False), ("9", False)])
def test_declared_minimum_and_maximum_are_enforced(owner_index: int, expression: str, valid: bool) -> None:
    root = _definitions()
    _register(root)
    owner = _owner_cases(root)[owner_index][1]
    owner.address_unit_bits = AddressUnitBits(value=expression, minimum=4, maximum=8)
    value_getter = _owner_cases(root)[owner_index][2]

    if valid:
        assert value_getter(get_handle(owner)) == int(expression)
    else:
        _assert_fault(lambda: value_getter(get_handle(owner)), TgiFaultCode.INVALID_ARGUMENT)


@pytest.mark.parametrize("owner_index", [0, 1, 2])
def test_absent_address_unit_has_no_synthesized_default(owner_index: int) -> None:
    root = _definitions(None, None, None)
    _register(root)
    owner = _owner_cases(root)[owner_index][1]
    value_getter, expression_getter, id_getter = _owner_cases(root)[owner_index][2:]
    owner_id = get_handle(owner)

    assert owner.address_unit_bits is None
    assert value_getter(owner_id) is None
    assert expression_getter(owner_id) is None
    assert id_getter(owner_id) is None


@pytest.mark.parametrize("owner_index", [0, 1, 2])
def test_wrong_owner_unknown_handle_and_wrong_child_type_raise_invalid_id(owner_index: int) -> None:
    root = _definitions()
    _register(root)
    cases = _owner_cases(root)
    name, owner, value_getter, expression_getter, id_getter = cases[owner_index]
    other_owner = cases[(owner_index + 1) % len(cases)][1]

    for getter in (value_getter, expression_getter, id_getter):
        _assert_fault(lambda getter=getter: getter(get_handle(other_owner)), TgiFaultCode.INVALID_ID)
        _assert_fault(lambda getter=getter: getter("unknown-handle"), TgiFaultCode.INVALID_ID)

    object.__setattr__(owner, "address_unit_bits", UnsignedPositiveLongintExpression(value="8"))
    for getter in (value_getter, expression_getter, id_getter):
        _assert_fault(lambda getter=getter: getter(get_handle(owner)), TgiFaultCode.INVALID_ID)


@pytest.mark.parametrize("owner_index", [0, 1, 2])
def test_non_string_value_faults_as_invalid_id_but_child_handle_allows_repair(owner_index: int) -> None:
    root = _definitions()
    _register(root)
    owner = _owner_cases(root)[owner_index][1]
    value_getter, expression_getter, id_getter = _owner_cases(root)[owner_index][2:]
    child = owner.address_unit_bits
    object.__setattr__(child, "value", 8)
    owner_id = get_handle(owner)

    child_id = id_getter(owner_id)
    assert child_id == get_handle(child)
    _assert_fault(lambda: expression_getter(owner_id), TgiFaultCode.INVALID_ID)
    _assert_fault(lambda: value_getter(owner_id), TgiFaultCode.INVALID_ID)

    child.value = "8"
    assert expression_getter(owner_id) == "8"
    assert value_getter(owner_id) == 8


@pytest.mark.parametrize("owner_index", [0, 1, 2])
def test_getting_child_id_registers_standalone_definition_parent(owner_index: int) -> None:
    root = _definitions()
    owner = _owner_cases(root)[owner_index][1]
    owner_id = get_handle(owner)
    id_getter = _owner_cases(root)[owner_index][4]

    child_id = id_getter(owner_id)
    assert child_id is not None
    parent_info = get_parent_info(child_id)
    assert parent_info is not None
    assert parent_info.parent_handle == owner_id
    assert parent_info.path == ("address_unit_bits",)


def test_f781_getters_keep_the_documented_names_parameters_and_exports() -> None:
    functions: tuple[tuple[str, str, object, str], ...] = (
        ("getAddressBlockDefinitionAddressUnitBits", "addressBlockDefinitionID", int | None, "F.7.81.1"),
        ("getAddressBlockDefinitionAddressUnitBitsExpression", "addressBlockDefinitionID", str | None, "F.7.81.2"),
        ("getAddressBlockDefinitionAddressUnitBitsID", "addressBlockDefinitionID", str | None, "F.7.81.3"),
        ("getBankDefinitionAddressUnitBits", "bankDefinitionID", int | None, "F.7.81.4"),
        ("getBankDefinitionAddressUnitBitsExpression", "bankDefinitionID", str | None, "F.7.81.5"),
        ("getBankDefinitionAddressUnitBitsID", "bankDefinitionID", str | None, "F.7.81.6"),
        ("getMemoryRemapDefinitionAddressUnitBits", "memoryRemapDefinitionID", int | None, "F.7.81.16"),
        (
            "getMemoryRemapDefinitionAddressUnitBitsExpression",
            "memoryRemapDefinitionID",
            str | None,
            "F.7.81.17",
        ),
        ("getMemoryRemapDefinitionAddressUnitBitsID", "memoryRemapDefinitionID", str | None, "F.7.81.18"),
    )
    for name, parameter, return_type, section in functions:
        function = getattr(api, name)
        assert name in api.__all__
        assert name in root_api.__all__
        assert getattr(root_api, name) is function
        function_signature = signature(function)
        assert tuple(function_signature.parameters) == (parameter,)
        assert function_signature.parameters[parameter].annotation is str
        assert function_signature.return_annotation == return_type
        assert function_signature.parameters[parameter].default is function_signature.empty
        assert function.__doc__ is not None
        assert "Args:" in function.__doc__
        assert "Returns:" in function.__doc__
        assert f"Section: {section}." in function.__doc__

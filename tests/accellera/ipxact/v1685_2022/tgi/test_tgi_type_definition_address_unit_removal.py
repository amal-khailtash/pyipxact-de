"""IEEE 1685-2022 reusable-definition address-unit getters and removers."""

from collections.abc import Callable, Iterator
from inspect import Signature, signature

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
    RegisterFileDefinitions,
    TypeDefinitions,
    UnsignedPositiveIntExpression,
    UnsignedPositiveLongintExpression,
)

_SCHEMA = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))
_NS = "http://www.accellera.org/XMLSchema/IPXACT/1685-2022"

type _DefinitionOwner = (
    AddressBlockDefinitions.AddressBlockDefinition
    | BankDefinitions.BankDefinition
    | MemoryRemapDefinitions.MemoryRemapDefinition
    | RegisterFileDefinitions.RegisterFileDefinition
)
type _ValueGetter = Callable[[str], int | None]
type _ExpressionGetter = Callable[[str], str | None]
type _IdGetter = Callable[[str], str | None]
type _Remover = Callable[[str], bool]
type _DefinitionCase = tuple[
    str,
    _DefinitionOwner,
    _ValueGetter,
    _ExpressionGetter,
    _IdGetter,
    _Remover,
    str,
    str,
]


@pytest.fixture(autouse=True)
def clear_registry() -> Iterator[None]:
    registry.clear()
    yield
    registry.clear()


def _definitions(
    address_block_bits: str | None = "2**3",
    bank_bits: str | None = "64'h10",
    remap_bits: str | None = "8",
    register_file_bits: str | None = "32'h20",
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
    register_file = RegisterFileDefinitions.RegisterFileDefinition(
        name="register_file",
        range=UnsignedPositiveLongintExpression(value="256"),
        register_or_register_file=[],
        address_unit_bits=AddressUnitBits(value=register_file_bits) if register_file_bits is not None else None,
    )
    return TypeDefinitions(
        vendor="example.org",
        library="types",
        name="memory_types",
        version="1.0",
        address_block_definitions=AddressBlockDefinitions(address_block_definition=[address_block]),
        bank_definitions=BankDefinitions(bank_definition=[bank]),
        memory_remap_definitions=MemoryRemapDefinitions(memory_remap_definition=[remap]),
        register_file_definitions=RegisterFileDefinitions(register_file_definition=[register_file]),
    )


def _definition_cases(root: TypeDefinitions) -> list[_DefinitionCase]:
    assert root.address_block_definitions is not None
    assert root.bank_definitions is not None
    assert root.memory_remap_definitions is not None
    assert root.register_file_definitions is not None
    return [
        (
            "address block definition",
            root.address_block_definitions.address_block_definition[0],
            api.getAddressBlockDefinitionAddressUnitBits,
            api.getAddressBlockDefinitionAddressUnitBitsExpression,
            api.getAddressBlockDefinitionAddressUnitBitsID,
            api.removeAddressBlockDefinitionAddressUnitBits,
            "addressBlockDefinitionID",
            "F.7.82.21",
        ),
        (
            "bank definition",
            root.bank_definitions.bank_definition[0],
            api.getBankDefinitionAddressUnitBits,
            api.getBankDefinitionAddressUnitBitsExpression,
            api.getBankDefinitionAddressUnitBitsID,
            api.removeBankDefinitionAddressUnitBits,
            "bankDefinitionID",
            "F.7.82.22",
        ),
        (
            "memory remap definition",
            root.memory_remap_definitions.memory_remap_definition[0],
            api.getMemoryRemapDefinitionAddressUnitBits,
            api.getMemoryRemapDefinitionAddressUnitBitsExpression,
            api.getMemoryRemapDefinitionAddressUnitBitsID,
            api.removeMemoryRemapDefinitionAddressUnitBits,
            "memoryRemapDefinitionID",
            "F.7.82.30",
        ),
        (
            "register file definition",
            root.register_file_definitions.register_file_definition[0],
            api.getRegisterFileDefinitionAddressUnitBits,
            api.getRegisterFileDefinitionAddressUnitBitsExpression,
            api.getRegisterFileDefinitionAddressUnitBitsID,
            api.removeRegisterFileDefinitionAddressUnitBits,
            "registerFileDefinitionID",
            "F.7.82.31",
        ),
    ]


def _register(root: TypeDefinitions) -> None:
    registry.register(root, ("example.org", "types", "memory_types", "1.0"))


def _assert_fault(action: Callable[[], object], fault_code: str) -> None:
    with pytest.raises(TgiError) as error:
        action()
    assert error.value.fault_code == fault_code


def _assert_schema_valid(root: TypeDefinitions) -> str:
    xml = XmlDocument.serializer().render(root)
    _SCHEMA.assertValid(etree.fromstring(xml.encode()))
    return xml


def test_register_file_getters_resolve_source_and_register_owned_child() -> None:
    root = _definitions()
    _register(root)
    name, owner, value_getter, expression_getter, id_getter, _remover, _parameter, _section = _definition_cases(root)[3]
    child = owner.address_unit_bits
    assert child is not None
    child.other_attributes = {"{urn:test}marker": "register file"}
    owner_id = get_handle(owner)

    child_id = id_getter(owner_id)
    assert child_id == get_handle(child)
    assert resolve_handle(child_id) is child
    assert value_getter(owner_id) == 32
    assert expression_getter(owner_id) == "32'h20"
    assert child.value == "32'h20"
    assert child.other_attributes["{urn:test}marker"] == "register file"
    parent_info = get_parent_info(child_id)
    assert parent_info is not None
    assert parent_info.parent_handle == owner_id
    assert parent_info.path == ("address_unit_bits",)
    assert name == "register file definition"


def test_register_file_getters_accept_schema_valid_parsed_type_definitions() -> None:
    root = _definitions()
    xml = _assert_schema_valid(root)
    parsed = XmlDocument.parser().from_string(xml, TypeDefinitions)
    assert XmlDocument.serializer().render(parsed) == xml
    _register(parsed)
    owner = _definition_cases(parsed)[3][1]
    owner_id = get_handle(owner)

    assert api.getRegisterFileDefinitionAddressUnitBitsID(owner_id) == get_handle(owner.address_unit_bits)
    assert api.getRegisterFileDefinitionAddressUnitBitsExpression(owner_id) == owner.address_unit_bits.value
    assert api.getRegisterFileDefinitionAddressUnitBits(owner_id) == 32


@pytest.mark.parametrize(
    ("expression", "expected"),
    [("20", 20), ("64'h7FFF_FFFF_FFFF_FFFF", (1 << 63) - 1), ("2**4 + 3", 19)],
)
def test_register_file_resolved_values_preserve_expression_source(expression: str, expected: int) -> None:
    root = _definitions()
    _register(root)
    owner = _definition_cases(root)[3][1]
    assert owner.address_unit_bits is not None
    owner.address_unit_bits.value = expression
    owner_id = get_handle(owner)

    assert api.getRegisterFileDefinitionAddressUnitBits(owner_id) == expected
    assert api.getRegisterFileDefinitionAddressUnitBitsExpression(owner_id) == expression
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
def test_register_file_invalid_address_unit_values_raise_invalid_argument(expression: str) -> None:
    root = _definitions()
    _register(root)
    owner = _definition_cases(root)[3][1]
    assert owner.address_unit_bits is not None
    owner.address_unit_bits.value = expression

    _assert_fault(
        lambda: api.getRegisterFileDefinitionAddressUnitBits(get_handle(owner)), TgiFaultCode.INVALID_ARGUMENT
    )


@pytest.mark.parametrize("expression, valid", [("4", True), ("8", True), ("3", False), ("9", False)])
def test_register_file_declared_address_unit_bounds_are_enforced(expression: str, valid: bool) -> None:
    root = _definitions()
    _register(root)
    owner = _definition_cases(root)[3][1]
    owner.address_unit_bits = AddressUnitBits(value=expression, minimum=4, maximum=8)

    if valid:
        assert api.getRegisterFileDefinitionAddressUnitBits(get_handle(owner)) == int(expression)
    else:
        _assert_fault(
            lambda: api.getRegisterFileDefinitionAddressUnitBits(get_handle(owner)), TgiFaultCode.INVALID_ARGUMENT
        )


def test_register_file_absent_address_unit_has_no_default() -> None:
    root = _definitions(register_file_bits=None)
    _register(root)
    owner = _definition_cases(root)[3][1]
    owner_id = get_handle(owner)

    assert api.getRegisterFileDefinitionAddressUnitBits(owner_id) is None
    assert api.getRegisterFileDefinitionAddressUnitBitsExpression(owner_id) is None
    assert api.getRegisterFileDefinitionAddressUnitBitsID(owner_id) is None


def test_register_file_typed_bad_source_id_remains_available_for_repair() -> None:
    root = _definitions()
    _register(root)
    owner = _definition_cases(root)[3][1]
    child = owner.address_unit_bits
    assert child is not None
    object.__setattr__(child, "value", 8)
    owner_id = get_handle(owner)

    child_id = api.getRegisterFileDefinitionAddressUnitBitsID(owner_id)
    assert child_id == get_handle(child)
    _assert_fault(lambda: api.getRegisterFileDefinitionAddressUnitBitsExpression(owner_id), TgiFaultCode.INVALID_ID)
    _assert_fault(lambda: api.getRegisterFileDefinitionAddressUnitBits(owner_id), TgiFaultCode.INVALID_ID)

    child.value = "8"
    assert api.getRegisterFileDefinitionAddressUnitBitsExpression(owner_id) == "8"
    assert api.getRegisterFileDefinitionAddressUnitBits(owner_id) == 8


def test_register_file_getters_reject_wrong_unknown_and_wrong_child_handles() -> None:
    root = _definitions()
    _register(root)
    cases = _definition_cases(root)
    owner = cases[3][1]
    other_owner = cases[0][1]
    getters = cases[3][2:5]
    for getter in getters:
        _assert_fault(lambda getter=getter: getter(get_handle(other_owner)), TgiFaultCode.INVALID_ID)
        _assert_fault(lambda getter=getter: getter("unknown-handle"), TgiFaultCode.INVALID_ID)

    object.__setattr__(owner, "address_unit_bits", UnsignedPositiveLongintExpression(value="8"))
    for getter in getters:
        _assert_fault(lambda getter=getter: getter(get_handle(owner)), TgiFaultCode.INVALID_ID)


def test_register_file_child_id_registers_standalone_owner_parent() -> None:
    owner = _definition_cases(_definitions())[3][1]
    owner_id = get_handle(owner)
    child_id = api.getRegisterFileDefinitionAddressUnitBitsID(owner_id)

    assert child_id is not None
    parent_info = get_parent_info(child_id)
    assert parent_info is not None
    assert parent_info.parent_handle == owner_id
    assert parent_info.path == ("address_unit_bits",)


def test_getters_and_removers_keep_documented_signatures_exports_and_sections() -> None:
    functions: tuple[tuple[str, str, object, str], ...] = (
        ("getRegisterFileDefinitionAddressUnitBits", "registerFileDefinitionID", int | None, "F.7.81.23"),
        (
            "getRegisterFileDefinitionAddressUnitBitsExpression",
            "registerFileDefinitionID",
            str | None,
            "F.7.81.24",
        ),
        ("getRegisterFileDefinitionAddressUnitBitsID", "registerFileDefinitionID", str | None, "F.7.81.25"),
        (
            "removeAddressBlockDefinitionAddressUnitBits",
            "addressBlockDefinitionID",
            bool,
            "F.7.82.21",
        ),
        ("removeBankDefinitionAddressUnitBits", "bankDefinitionID", bool, "F.7.82.22"),
        (
            "removeMemoryRemapDefinitionAddressUnitBits",
            "memoryRemapDefinitionID",
            bool,
            "F.7.82.30",
        ),
        (
            "removeRegisterFileDefinitionAddressUnitBits",
            "registerFileDefinitionID",
            bool,
            "F.7.82.31",
        ),
    )
    for name, parameter_name, return_type, section in functions:
        function = getattr(api, name)
        assert name in api.__all__
        assert name in root_api.__all__
        assert getattr(root_api, name) is function
        function_signature = signature(function)
        assert tuple(function_signature.parameters) == (parameter_name,)
        parameter = function_signature.parameters[parameter_name]
        assert parameter.annotation is str
        assert not isinstance(parameter.annotation, str)
        assert parameter.default is Signature.empty
        assert function_signature.return_annotation == return_type
        assert function.__doc__ is not None
        assert "Args:" in function.__doc__
        assert "Returns:" in function.__doc__
        assert f"Section: {section}." in function.__doc__


@pytest.mark.parametrize("case_index", [0, 1, 2, 3])
def test_removers_return_false_when_absent_and_reject_unknown_or_wrong_owner(case_index: int) -> None:
    root = _definitions(None, None, None, None)
    _register(root)
    cases = _definition_cases(root)
    _name, owner, _value, _expression, _id, remover, _parameter, _section = cases[case_index]
    other_owner = cases[(case_index + 1) % len(cases)][1]

    assert remover(get_handle(owner)) is False
    _assert_fault(lambda: remover("unknown-handle"), TgiFaultCode.INVALID_ID)
    _assert_fault(lambda: remover(get_handle(other_owner)), TgiFaultCode.INVALID_ID)
    assert owner.address_unit_bits is None


@pytest.mark.parametrize("case_index", [0, 1, 2, 3])
def test_removers_invalidate_only_the_address_unit_handle_and_preserve_siblings(case_index: int) -> None:
    root = _definitions()
    _register(root)
    cases = _definition_cases(root)
    _name, owner, _value, _expression, id_getter, remover, _parameter, _section = cases[case_index]
    owner_id = get_handle(owner)
    child = owner.address_unit_bits
    assert child is not None
    child.other_attributes = {"{urn:test}preserved": "source"}
    child_id = id_getter(owner_id)
    assert child_id is not None
    peer_records = tuple(
        (get_handle(peer_owner), peer_owner, get_handle(peer_owner.address_unit_bits))
        for index, (_peer_name, peer_owner, _vg, _eg, _ig, _rm, _arg, _section) in enumerate(cases)
        if index != case_index and peer_owner.address_unit_bits is not None
    )
    source = child.value

    assert remover(owner_id) is True
    assert owner.address_unit_bits is None
    assert child.value == source
    assert child.other_attributes["{urn:test}preserved"] == "source"
    assert resolve_handle(child_id) is None
    assert remover(owner_id) is False
    for peer_id, peer_owner, peer_child_id in peer_records:
        assert resolve_handle(peer_id) is peer_owner
        assert get_handle(peer_owner.address_unit_bits) == peer_child_id
    _assert_fault(lambda: remover(child_id), TgiFaultCode.INVALID_ID)


@pytest.mark.parametrize("case_index", [0, 1, 2, 3])
def test_remover_can_remove_parsed_child_without_prior_child_getter(case_index: int) -> None:
    root = _definitions()
    xml = _assert_schema_valid(root)
    parsed = XmlDocument.parser().from_string(xml, TypeDefinitions)
    owner = _definition_cases(parsed)[case_index][1]
    child = owner.address_unit_bits
    assert child is not None
    owner_id = get_handle(owner)
    child_id = get_handle(child)
    remover = _definition_cases(parsed)[case_index][5]

    assert remover(owner_id) is True
    assert owner.address_unit_bits is None
    assert resolve_handle(child_id) is None
    assert remover(owner_id) is False
    _assert_schema_valid(parsed)


@pytest.mark.parametrize("case_index", [0, 1, 2, 3])
def test_removers_reject_wrong_child_type_without_mutating_owner(case_index: int) -> None:
    root = _definitions()
    _register(root)
    cases = _definition_cases(root)
    owner = cases[case_index][1]
    remover = cases[case_index][5]
    wrong_child = UnsignedPositiveLongintExpression(value="8")
    object.__setattr__(owner, "address_unit_bits", wrong_child)
    owner_id = get_handle(owner)

    _assert_fault(lambda: remover(owner_id), TgiFaultCode.INVALID_ID)
    assert owner.address_unit_bits is wrong_child


@pytest.mark.parametrize("case_index", [0, 1, 2, 3])
def test_removers_allow_malformed_raw_source_to_be_removed_for_repair(case_index: int) -> None:
    root = _definitions()
    _register(root)
    owner = _definition_cases(root)[case_index][1]
    child = owner.address_unit_bits
    assert child is not None
    object.__setattr__(child, "value", 8)
    owner_id = get_handle(owner)
    remover = _definition_cases(root)[case_index][5]

    assert remover(owner_id) is True
    assert owner.address_unit_bits is None


def test_all_four_removers_preserve_xsd_valid_type_definition_round_trips() -> None:
    root = _definitions()
    xml = _assert_schema_valid(root)
    parsed = XmlDocument.parser().from_string(xml, TypeDefinitions)
    assert XmlDocument.serializer().render(parsed) == xml
    _register(parsed)

    for _name, owner, _value, _expression, id_getter, remover, _parameter, _section in _definition_cases(parsed):
        owner_id = get_handle(owner)
        original_child = owner.address_unit_bits
        assert original_child is not None
        child_id = id_getter(owner_id)
        assert child_id == get_handle(original_child)
        before = _assert_schema_valid(parsed)
        assert remover(owner_id) is True
        assert owner.address_unit_bits is None
        assert resolve_handle(child_id) is None
        after = _assert_schema_valid(parsed)
        reparsed = XmlDocument.parser().from_string(after, TypeDefinitions)
        assert XmlDocument.serializer().render(reparsed) == after
        assert before != after
    assert _NS in xml

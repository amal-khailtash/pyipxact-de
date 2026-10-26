"""IEEE 1685-2022 type-definition value setters and enumeration-width getters."""

from collections.abc import Callable, Iterator
from inspect import Parameter, getdoc, signature
from typing import cast, get_type_hints

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
    EnumeratedValueType,
    EnumerationDefinitions,
    MemoryRemapDefinitions,
    RegisterFileDefinitions,
    TypeDefinitions,
    UnsignedBitVectorExpression,
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
type _Setter = Callable[[str, str], bool]
type _ResolvedGetter = Callable[[str], int | None]
type _SourceGetter = Callable[[str], str | None]
type _IdGetter = Callable[[str], str | None]
type _DefinitionCase = tuple[
    str,
    _DefinitionOwner,
    _Setter,
    _ResolvedGetter,
    _SourceGetter,
    _IdGetter,
    str,
    str,
]


@pytest.fixture(autouse=True)
def clear_registry() -> Iterator[None]:
    registry.clear()
    yield
    registry.clear()


def _definitions(
    address_block_bits: str | None = "8",
    bank_bits: str | None = "16",
    remap_bits: str | None = "32",
    register_file_bits: str | None = "64",
    enumeration_width: str = "8",
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
    enumeration = EnumerationDefinitions.EnumerationDefinition(
        name="status",
        width=UnsignedPositiveIntExpression(value=enumeration_width),
        enumerated_value=[EnumeratedValueType(name="ready", value=UnsignedBitVectorExpression(value="1"))],
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
        enumeration_definitions=EnumerationDefinitions(enumeration_definition=[enumeration]),
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
            api.setAddressBlockDefinitionAddressUnitBits,
            api.getAddressBlockDefinitionAddressUnitBits,
            api.getAddressBlockDefinitionAddressUnitBitsExpression,
            api.getAddressBlockDefinitionAddressUnitBitsID,
            "addressBlockDefinitionID",
            "F.7.82.46",
        ),
        (
            "bank definition",
            root.bank_definitions.bank_definition[0],
            api.setBankDefinitionAddressUnitBits,
            api.getBankDefinitionAddressUnitBits,
            api.getBankDefinitionAddressUnitBitsExpression,
            api.getBankDefinitionAddressUnitBitsID,
            "bankDefinitionID",
            "F.7.82.47",
        ),
        (
            "memory remap definition",
            root.memory_remap_definitions.memory_remap_definition[0],
            api.setMemoryRemapDefinitionAddressUnitBits,
            api.getMemoryRemapDefinitionAddressUnitBits,
            api.getMemoryRemapDefinitionAddressUnitBitsExpression,
            api.getMemoryRemapDefinitionAddressUnitBitsID,
            "memoryRemapDefinitionID",
            "F.7.82.50",
        ),
        (
            "register file definition",
            root.register_file_definitions.register_file_definition[0],
            api.setRegisterFileDefinitionAddressUnitBits,
            api.getRegisterFileDefinitionAddressUnitBits,
            api.getRegisterFileDefinitionAddressUnitBitsExpression,
            api.getRegisterFileDefinitionAddressUnitBitsID,
            "registerFileDefinitionID",
            "F.7.82.53",
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


def test_definition_setters_create_and_register_generated_address_unit_children() -> None:
    root = _definitions(None, None, None, None)
    _register(root)

    for _name, owner, setter, value_getter, expression_getter, id_getter, _parameter, _section in _definition_cases(
        root
    ):
        assert owner.address_unit_bits is None
        owner_id = get_handle(owner)

        assert setter(owner_id, "2**3")

        child = owner.address_unit_bits
        assert isinstance(child, AddressUnitBits)
        child_id = id_getter(owner_id)
        assert child_id == get_handle(child)
        assert resolve_handle(child_id) is child
        assert expression_getter(owner_id) == "2**3"
        assert value_getter(owner_id) == 8
        parent_info = get_parent_info(child_id)
        assert parent_info is not None
        assert parent_info.parent_handle == owner_id
        assert parent_info.path == ("address_unit_bits",)


def test_definition_setters_update_source_without_replacing_wrapper_metadata() -> None:
    root = _definitions()
    _register(root)

    for _name, owner, setter, value_getter, expression_getter, id_getter, _parameter, _section in _definition_cases(
        root
    ):
        child = owner.address_unit_bits
        assert child is not None
        child.minimum = 4
        child.maximum = 32
        child.other_attributes = {"{urn:test}tag": "preserve"}
        owner_id = get_handle(owner)
        child_id = get_handle(child)

        assert setter(owner_id, "64'h10")

        assert owner.address_unit_bits is child
        assert id_getter(owner_id) == child_id
        assert child.value == "64'h10"
        assert child.minimum == 4
        assert child.maximum == 32
        assert child.other_attributes == {"{urn:test}tag": "preserve"}
        assert expression_getter(owner_id) == "64'h10"
        assert value_getter(owner_id) == 16


@pytest.mark.parametrize(
    ("source", "expected"),
    [("12", 12), ("64'h10", 16), ("2**4 + 3", 19)],
)
def test_definition_setters_accept_decimal_based_and_arithmetic_sources(source: str, expected: int) -> None:
    root = _definitions(None, None, None, None)
    _register(root)

    for _name, owner, setter, value_getter, expression_getter, _id_getter, _parameter, _section in _definition_cases(
        root
    ):
        owner_id = get_handle(owner)
        assert setter(owner_id, source)
        assert expression_getter(owner_id) == source
        assert value_getter(owner_id) == expected


@pytest.mark.parametrize("owner_index", [0, 1, 2, 3])
def test_definition_setters_defer_unresolved_identifier_sources(owner_index: int) -> None:
    root = _definitions(None, None, None, None)
    _register(root)
    _name, owner, setter, value_getter, expression_getter, _id_getter, _parameter, _section = _definition_cases(root)[
        owner_index
    ]
    owner_id = get_handle(owner)

    assert setter(owner_id, "BUS_WIDTH")
    assert expression_getter(owner_id) == "BUS_WIDTH"
    _assert_fault(lambda: value_getter(owner_id), TgiFaultCode.INVALID_ARGUMENT)


@pytest.mark.parametrize(
    "source",
    [
        "0",
        "-1",
        "1.5",
        "1 +",
        "64'hx",
        "64'h1_0000_0000_0000_0000",
        "<addressUnitBits>8</addressUnitBits>",
        "",
        "nul\x00source",
    ],
)
@pytest.mark.parametrize("owner_index", [0, 1, 2, 3])
@pytest.mark.parametrize("present", [False, True])
def test_invalid_definition_setter_sources_are_rejected_without_model_mutation(
    source: str, owner_index: int, present: bool
) -> None:
    root = _definitions() if present else _definitions(None, None, None, None)
    _register(root)
    _name, owner, setter, _value_getter, _expression_getter, _id_getter, _parameter, _section = _definition_cases(root)[
        owner_index
    ]
    owner_id = get_handle(owner)
    child = owner.address_unit_bits
    original_source = child.value if child is not None else None

    _assert_fault(lambda: setter(owner_id, source), TgiFaultCode.INVALID_ARGUMENT)
    assert owner.address_unit_bits is child
    if child is not None:
        assert child.value == original_source


@pytest.mark.parametrize("owner_index", [0, 1, 2, 3])
def test_definition_setters_reject_non_string_runtime_arguments(owner_index: int) -> None:
    root = _definitions(None, None, None, None)
    _register(root)
    _name, owner, setter, _value_getter, _expression_getter, _id_getter, _parameter, _section = _definition_cases(root)[
        owner_index
    ]
    owner_id = get_handle(owner)

    for value in (8, object()):
        _assert_fault(lambda value=value: setter(owner_id, cast(str, value)), TgiFaultCode.INVALID_ARGUMENT)
        assert owner.address_unit_bits is None


@pytest.mark.parametrize("owner_index", [0, 1, 2, 3])
@pytest.mark.parametrize(("source", "valid"), [("3", False), ("4", True), ("8", True), ("9", False)])
def test_definition_setters_enforce_existing_declared_bounds(owner_index: int, source: str, valid: bool) -> None:
    root = _definitions()
    _register(root)
    _name, owner, setter, value_getter, _expression_getter, _id_getter, _parameter, _section = _definition_cases(root)[
        owner_index
    ]
    assert owner.address_unit_bits is not None
    owner.address_unit_bits.minimum = 4
    owner.address_unit_bits.maximum = 8
    owner_id = get_handle(owner)
    original = owner.address_unit_bits.value

    if valid:
        assert setter(owner_id, source)
        assert owner.address_unit_bits.value == source
        assert value_getter(owner_id) == int(source)
    else:
        _assert_fault(lambda: setter(owner_id, source), TgiFaultCode.INVALID_ARGUMENT)
        assert owner.address_unit_bits.value == original


@pytest.mark.parametrize("owner_index", [0, 1, 2, 3])
def test_definition_setters_accept_unsigned_64_sources_above_tgi_long_getter_range(owner_index: int) -> None:
    root = _definitions(None, None, None, None)
    _register(root)
    _name, owner, setter, value_getter, expression_getter, _id_getter, _parameter, _section = _definition_cases(root)[
        owner_index
    ]
    owner_id = get_handle(owner)
    source = "64'hFFFF_FFFF_FFFF_FFFF"

    assert setter(owner_id, source)
    assert expression_getter(owner_id) == source
    _assert_fault(lambda: value_getter(owner_id), TgiFaultCode.INVALID_ARGUMENT)


@pytest.mark.parametrize("owner_index", [0, 1, 2, 3])
def test_definition_setters_can_repair_existing_malformed_raw_source(owner_index: int) -> None:
    root = _definitions()
    _register(root)
    _name, owner, setter, value_getter, expression_getter, _id_getter, _parameter, _section = _definition_cases(root)[
        owner_index
    ]
    child = owner.address_unit_bits
    assert child is not None
    child.value = "1 +"
    owner_id = get_handle(owner)
    child_id = get_handle(child)

    assert setter(owner_id, "24")

    assert owner.address_unit_bits is child
    assert get_handle(owner.address_unit_bits) == child_id
    assert expression_getter(owner_id) == "24"
    assert value_getter(owner_id) == 24


@pytest.mark.parametrize("owner_index", [0, 1, 2, 3])
def test_definition_setters_require_matching_owner_and_address_unit_child_types(owner_index: int) -> None:
    root = _definitions()
    _register(root)
    _name, owner, setter, _value_getter, _expression_getter, _id_getter, _parameter, _section = _definition_cases(root)[
        owner_index
    ]
    owner_id = get_handle(owner)
    original = owner.address_unit_bits
    assert root.enumeration_definitions is not None
    wrong_owner = get_handle(root.enumeration_definitions.enumeration_definition[0])

    _assert_fault(lambda: setter("unknown-id", "8"), TgiFaultCode.INVALID_ID)
    _assert_fault(lambda: setter(wrong_owner, "8"), TgiFaultCode.INVALID_ID)
    assert owner.address_unit_bits is original

    wrong_child = cast(AddressUnitBits, UnsignedPositiveLongintExpression(value="8"))
    owner.address_unit_bits = wrong_child
    _assert_fault(lambda: setter(owner_id, "16"), TgiFaultCode.INVALID_ID)
    assert owner.address_unit_bits is wrong_child


def test_enumeration_width_getters_resolve_source_and_register_mandatory_child() -> None:
    root = _definitions(enumeration_width="2**4")
    _register(root)
    assert root.enumeration_definitions is not None
    enumeration = root.enumeration_definitions.enumeration_definition[0]
    owner_id = get_handle(enumeration)

    width_id = api.getEnumerationDefinitionWidthID(owner_id)
    assert width_id == get_handle(enumeration.width)
    assert resolve_handle(width_id) is enumeration.width
    assert api.getEnumerationDefinitionWidth(owner_id) == 16
    assert api.getEnumerationDefinitionWidthExpression(owner_id) == "2**4"
    parent_info = get_parent_info(width_id)
    assert parent_info is not None
    assert parent_info.parent_handle == owner_id
    assert parent_info.path == ("width",)
    _assert_fault(lambda: api.getEnumerationDefinitionWidth(width_id), TgiFaultCode.INVALID_ID)


def test_enumeration_width_getters_accept_schema_valid_parsed_type_definitions() -> None:
    root = _definitions(enumeration_width="2**4")
    xml = _assert_schema_valid(root)
    parsed = XmlDocument.parser().from_string(xml, TypeDefinitions)
    assert XmlDocument.serializer().render(parsed) == xml
    _register(parsed)
    assert parsed.enumeration_definitions is not None
    enumeration = parsed.enumeration_definitions.enumeration_definition[0]
    owner_id = get_handle(enumeration)

    assert api.getEnumerationDefinitionWidthID(owner_id) == get_handle(enumeration.width)
    assert api.getEnumerationDefinitionWidthExpression(owner_id) == "2**4"
    assert api.getEnumerationDefinitionWidth(owner_id) == 16


@pytest.mark.parametrize(
    ("source", "expected"),
    [("12", 12), ("32'h10", 16), ("2**4 + 3", 19), ("4294967295", (1 << 32) - 1)],
)
def test_enumeration_width_values_use_sv_evaluation_and_preserve_source(source: str, expected: int) -> None:
    root = _definitions(enumeration_width=source)
    _register(root)
    assert root.enumeration_definitions is not None
    enumeration = root.enumeration_definitions.enumeration_definition[0]
    owner_id = get_handle(enumeration)

    assert api.getEnumerationDefinitionWidth(owner_id) == expected
    assert api.getEnumerationDefinitionWidthExpression(owner_id) == source
    assert enumeration.width.value == source


@pytest.mark.parametrize("source", ["0", "-1", "1.5", "1 +", "MISSING_WIDTH", "64'h1_0000_0000"])
def test_invalid_enumeration_width_expression_faults_as_invalid_argument(source: str) -> None:
    root = _definitions(enumeration_width=source)
    _register(root)
    assert root.enumeration_definitions is not None
    enumeration = root.enumeration_definitions.enumeration_definition[0]
    owner_id = get_handle(enumeration)

    _assert_fault(lambda: api.getEnumerationDefinitionWidth(owner_id), TgiFaultCode.INVALID_ARGUMENT)
    assert api.getEnumerationDefinitionWidthExpression(owner_id) == source
    assert api.getEnumerationDefinitionWidthID(owner_id) == get_handle(enumeration.width)


def test_enumeration_width_declared_bounds_and_malformed_raw_source_contracts() -> None:
    root = _definitions()
    _register(root)
    assert root.enumeration_definitions is not None
    enumeration = root.enumeration_definitions.enumeration_definition[0]
    enumeration.width.minimum = 4
    enumeration.width.maximum = 8
    owner_id = get_handle(enumeration)

    enumeration.width.value = "4"
    assert api.getEnumerationDefinitionWidth(owner_id) == 4
    for source in ("3", "9"):
        enumeration.width.value = source
        _assert_fault(lambda: api.getEnumerationDefinitionWidth(owner_id), TgiFaultCode.INVALID_ARGUMENT)
    enumeration.width.value = cast(str, 8)
    _assert_fault(lambda: api.getEnumerationDefinitionWidth(owner_id), TgiFaultCode.INVALID_ID)
    _assert_fault(lambda: api.getEnumerationDefinitionWidthExpression(owner_id), TgiFaultCode.INVALID_ID)
    assert api.getEnumerationDefinitionWidthID(owner_id) == get_handle(enumeration.width)


def test_enumeration_width_getters_require_typed_owner_and_mandatory_child() -> None:
    root = _definitions()
    _register(root)
    assert root.enumeration_definitions is not None
    enumeration = root.enumeration_definitions.enumeration_definition[0]
    owner_id = get_handle(enumeration)
    assert root.address_block_definitions is not None
    address_block_id = get_handle(root.address_block_definitions.address_block_definition[0])

    for getter in (
        api.getEnumerationDefinitionWidth,
        api.getEnumerationDefinitionWidthExpression,
        api.getEnumerationDefinitionWidthID,
    ):
        _assert_fault(lambda getter=getter: getter("unknown-id"), TgiFaultCode.INVALID_ID)
        _assert_fault(lambda getter=getter: getter(address_block_id), TgiFaultCode.INVALID_ID)

    enumeration.width = cast(UnsignedPositiveIntExpression, AddressUnitBits(value="8"))
    _assert_fault(lambda: api.getEnumerationDefinitionWidth(owner_id), TgiFaultCode.INVALID_ID)
    _assert_fault(lambda: api.getEnumerationDefinitionWidthExpression(owner_id), TgiFaultCode.INVALID_ID)
    _assert_fault(lambda: api.getEnumerationDefinitionWidthID(owner_id), TgiFaultCode.INVALID_ID)


def test_enumeration_width_getters_reject_missing_mandatory_child() -> None:
    root = _definitions()
    _register(root)
    assert root.enumeration_definitions is not None
    enumeration = root.enumeration_definitions.enumeration_definition[0]
    owner_id = get_handle(enumeration)
    enumeration.width = cast(UnsignedPositiveIntExpression, None)

    _assert_fault(lambda: api.getEnumerationDefinitionWidth(owner_id), TgiFaultCode.INVALID_ID)
    _assert_fault(lambda: api.getEnumerationDefinitionWidthExpression(owner_id), TgiFaultCode.INVALID_ID)
    _assert_fault(lambda: api.getEnumerationDefinitionWidthID(owner_id), TgiFaultCode.INVALID_ID)


def test_type_definition_operation_signatures_exports_and_documentation() -> None:
    contracts: dict[str, tuple[list[str], str, object]] = {
        "getEnumerationDefinitionWidth": (
            ["enumerationDefinitionID"],
            "F.7.81.8",
            int,
        ),
        "getEnumerationDefinitionWidthExpression": (
            ["enumerationDefinitionID"],
            "F.7.81.9",
            str,
        ),
        "getEnumerationDefinitionWidthID": (
            ["enumerationDefinitionID"],
            "F.7.81.10",
            str,
        ),
        "setAddressBlockDefinitionAddressUnitBits": (
            ["addressBlockDefinitionID", "addressUnitBits"],
            "F.7.82.46",
            bool,
        ),
        "setBankDefinitionAddressUnitBits": (
            ["bankDefinitionID", "addressUnitBits"],
            "F.7.82.47",
            bool,
        ),
        "setMemoryRemapDefinitionAddressUnitBits": (
            ["memoryRemapDefinitionID", "addressUnitBits"],
            "F.7.82.50",
            bool,
        ),
        "setRegisterFileDefinitionAddressUnitBits": (
            ["registerFileDefinitionID", "addressUnitBits"],
            "F.7.82.53",
            bool,
        ),
    }

    for name, (parameters, section, return_type) in contracts.items():
        function = getattr(api, name)
        assert name in api.__all__
        assert name in root_api.__all__
        assert getattr(root_api, name) is function
        function_signature = signature(function)
        assert list(function_signature.parameters) == parameters
        assert all(parameter.default is Parameter.empty for parameter in function_signature.parameters.values())
        hints = get_type_hints(function)
        assert set(hints) == {*parameters, "return"}
        assert hints["return"] == return_type
        assert all(hints[parameter] is str for parameter in parameters)
        doc = getdoc(function)
        assert doc is not None
        assert f"Section: {section}." in doc
        assert "Args:" in doc and "Returns:" in doc
        assert all(f"{parameter}:" in doc for parameter in parameters)


@pytest.mark.parametrize("owner_index", [0, 1, 2, 3])
def test_definition_setters_preserve_decimal_unsigned_longint_maximum(owner_index: int) -> None:
    root = _definitions(None, None, None, None)
    _register(root)
    _name, owner, setter, value_getter, source_getter, id_getter, _parameter, _section = _definition_cases(root)[
        owner_index
    ]
    owner_id = get_handle(owner)
    source = str((1 << 64) - 1)

    assert setter(owner_id, source)
    assert source_getter(owner_id) == source
    assert id_getter(owner_id) == get_handle(owner.address_unit_bits)
    _assert_fault(lambda: value_getter(owner_id), TgiFaultCode.INVALID_ARGUMENT)
    _assert_schema_valid(root)

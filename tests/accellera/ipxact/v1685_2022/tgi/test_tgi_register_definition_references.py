"""RegisterDefinition reference Annex contracts and scoped resolution."""

from collections.abc import Iterator
from inspect import signature

import pytest
from lxml import etree

from amal.eda.accellera.ipxact.v1685_2022 import tgi as root_api
from amal.eda.accellera.ipxact.v1685_2022.tgi import register as api
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import TgiError, TgiFaultCode, get_handle, registry, resolve_handle
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import (
    AddressBlock,
    AddressUnitBits,
    Array,
    Bank,
    BankAlignmentType,
    BaseAddress,
    Component,
    ComponentType,
    ConfigurableLibraryRefType,
    Dim,
    ExternalTypeDefinitions,
    FieldType,
    MemoryMaps,
    MemoryMapType,
    RegisterDefinitions,
    RegisterFile,
    RegisterFileDefinitions,
    TypeDefinitions,
    UnsignedIntExpression,
    UnsignedLongintExpression,
    UnsignedPositiveIntExpression,
    UnsignedPositiveLongintExpression,
    UsageType,
)
from org.accellera.ipxact.v1685_2022.address_block_type import AddressBlockType
from org.accellera.ipxact.v1685_2022.alternate_registers import AlternateRegisters
from org.accellera.ipxact.v1685_2022.banked_block_type import BankedBlockType
from org.accellera.ipxact.v1685_2022.parameters import Parameters
from org.accellera.ipxact.v1685_2022.vendor_extensions import VendorExtensions
from org.accellera.ipxact.v1685_2022.volatile import Volatile

_SCHEMA = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))
_OWNER_VLNV = ("example.org", "components", "owner", "1.0")
_FILE_OWNER_VLNV = ("example.org", "types", "fileOwner", "1.0")
_TARGET_VLNV = ("example.org", "types", "shared", "1.0")
_REGISTER_CLASSES = (
    AddressBlockType.Register,
    BankedBlockType.Register,
    RegisterFile.Register,
    RegisterFileDefinitions.RegisterFileDefinition.Register,
)
_OPERATIONS = {
    "getRegisterRegisterDefinitionRefByExternalTypeDefID": (
        "F.7.73.69",
        ("registerID",),
        str | None,
    ),
    "getRegisterRegisterDefinitionRefByID": ("F.7.73.70", ("registerID",), str | None),
    "getRegisterRegisterDefinitionRefByName": ("F.7.73.71", ("registerID",), str | None),
    "getRegisterRegisterDefinitionRefID": ("F.7.73.72", ("registerID",), str | None),
    "setRegisterRegisterDefinitionRef": (
        "F.7.74.64",
        ("registerID", "value", "typeDefinitions"),
        bool,
    ),
}


@pytest.fixture(autouse=True)
def clear_registry() -> Iterator[None]:
    registry.clear()
    yield
    registry.clear()


def _field(name: str = "flag") -> FieldType:
    return FieldType(
        name=name,
        bit_offset=UnsignedIntExpression(value="0"),
        choice=[UnsignedPositiveIntExpression(value="1")],
    )


def _external(name: str = "sharedTypes", target: tuple[str, str, str, str] = _TARGET_VLNV) -> ExternalTypeDefinitions:
    return ExternalTypeDefinitions(
        name=name,
        type_definitions_ref=ConfigurableLibraryRefType(
            vendor=target[0], library=target[1], name=target[2], version=target[3]
        ),
    )


def _register(register_type: type, name: str) -> object:
    return register_type(
        name=name,
        address_offset=UnsignedLongintExpression(value="0"),
        choice=[UnsignedPositiveIntExpression(value="32"), _field()],
    )


def _component() -> tuple[Component, tuple[object, object, object]]:
    address_register = _register(AddressBlockType.Register, "addressControl")
    file_register = _register(RegisterFile.Register, "fileControl")
    bank_register = _register(BankedBlockType.Register, "bankControl")
    nested_file = RegisterFile(
        name="nested",
        address_offset=UnsignedLongintExpression(value="64"),
        choice=[UnsignedPositiveLongintExpression(value="64"), file_register],
    )
    block = AddressBlock(
        name="registers",
        base_address=BaseAddress(value="0"),
        choice=[
            UnsignedPositiveLongintExpression(value="256"),
            UnsignedPositiveIntExpression(value="32"),
            UsageType.REGISTER,
            address_register,
            nested_file,
        ],
    )
    banked_block = BankedBlockType(
        name="bankedRegisters",
        range=UnsignedPositiveLongintExpression(value="64"),
        width=UnsignedPositiveIntExpression(value="32"),
        usage=UsageType.REGISTER,
        register_or_register_file=[bank_register],
    )
    bank = Bank(
        name="registerBank",
        base_address=BaseAddress(value="256"),
        choice=[banked_block],
        bank_alignment=BankAlignmentType.SERIAL,
    )
    component = Component(
        vendor=_OWNER_VLNV[0],
        library=_OWNER_VLNV[1],
        name=_OWNER_VLNV[2],
        version=_OWNER_VLNV[3],
        type_definitions=ComponentType.TypeDefinitions(external_type_definitions=[_external()]),
        memory_maps=MemoryMaps(
            memory_map=[MemoryMapType(name="peripheral", choice=[block, bank, AddressUnitBits(value="8")])]
        ),
    )
    return component, (address_register, file_register, bank_register)


def _file_owner() -> tuple[TypeDefinitions, object]:
    register = _register(RegisterFileDefinitions.RegisterFileDefinition.Register, "fileDefinitionControl")
    file_definition = RegisterFileDefinitions.RegisterFileDefinition(
        name="sharedFile",
        range=UnsignedPositiveLongintExpression(value="64"),
        register_or_register_file=[register],
    )
    owner = TypeDefinitions(
        vendor=_FILE_OWNER_VLNV[0],
        library=_FILE_OWNER_VLNV[1],
        name=_FILE_OWNER_VLNV[2],
        version=_FILE_OWNER_VLNV[3],
        external_type_definitions=[_external()],
        register_file_definitions=RegisterFileDefinitions(register_file_definition=[file_definition]),
    )
    return owner, register


def _target(vlnv: tuple[str, str, str, str] = _TARGET_VLNV, names: tuple[str, ...] = ("control",)) -> TypeDefinitions:
    definitions = RegisterDefinitions(
        register_definition=[
            RegisterDefinitions.RegisterDefinition(
                name=name, size=UnsignedPositiveIntExpression(value="32"), field_value=[_field()]
            )
            for name in names
        ]
    )
    return TypeDefinitions(
        vendor=vlnv[0],
        library=vlnv[1],
        name=vlnv[2],
        version=vlnv[3],
        register_definitions=definitions,
    )


def _assert_schema_round_trip(document: object, root_type: type) -> object:
    xml = XmlDocument.serializer().render(document)
    _SCHEMA.assertValid(etree.fromstring(xml.encode()))
    parsed = XmlDocument.parser().from_string(xml, root_type)
    parsed_xml = XmlDocument.serializer().render(parsed)
    assert parsed_xml == xml
    return parsed


@pytest.mark.parametrize(("name", "contract"), _OPERATIONS.items())
def test_exact_annex_signatures_exports_and_documentation(name: str, contract: tuple) -> None:
    section, parameters, return_type = contract
    function = getattr(api, name)
    assert tuple(signature(function).parameters) == parameters
    assert name in api.__all__ and getattr(root_api, name) is function
    assert signature(function).return_annotation == return_type
    assert f"Section: {section}." in function.__doc__
    assert "Args:" in function.__doc__ and "Returns:" in function.__doc__


def test_all_four_register_variants_resolve_scoped_import_and_round_trip() -> None:
    component, component_registers = _component()
    file_owner, file_register = _file_owner()
    target = _target()
    registry.register(component, _OWNER_VLNV)
    registry.register(file_owner, _FILE_OWNER_VLNV)
    registry.register(target, _TARGET_VLNV)
    definition = target.register_definitions.register_definition[0]

    for register in (*component_registers, file_register):
        register_id = get_handle(register)
        assert api.getRegisterRegisterDefinitionRefByName(register_id) is None
        assert api.getRegisterRegisterDefinitionRefByExternalTypeDefID(register_id) is None
        assert api.getRegisterRegisterDefinitionRefByID(register_id) is None
        assert api.getRegisterRegisterDefinitionRefID(register_id) is None
        assert api.setRegisterRegisterDefinitionRef(register_id, "control", "sharedTypes") is True
        reference_id = api.getRegisterRegisterDefinitionRefID(register_id)
        assert reference_id is not None
        assert api.getRegisterRegisterDefinitionRefByName(register_id) == "control"
        assert api.getRegisterRegisterDefinitionRefByExternalTypeDefID(register_id) == get_handle(
            component.type_definitions.external_type_definitions[0]
            if register is not file_register
            else file_owner.external_type_definitions[0]
        )
        assert api.getRegisterRegisterDefinitionRefByID(register_id) == get_handle(definition)
        assert api.setRegisterRegisterDefinitionRef(register_id, "otherControl", "sharedTypes") is True
        assert api.getRegisterRegisterDefinitionRefID(register_id) == reference_id
        assert api.setRegisterRegisterDefinitionRef(register_id, "control", "sharedTypes") is True

    parsed_component = _assert_schema_round_trip(component, Component)
    parsed_file_owner = _assert_schema_round_trip(file_owner, TypeDefinitions)
    parsed_registers = (
        parsed_component.memory_maps.memory_map[0].choice[0].choice[3],
        parsed_component.memory_maps.memory_map[0].choice[0].choice[4].choice[1],
        parsed_component.memory_maps.memory_map[0].choice[1].choice[0].register_or_register_file[0],
    )
    parsed_file_register = parsed_file_owner.register_file_definitions.register_file_definition[
        0
    ].register_or_register_file[0]
    registry.clear()
    registry.register(target, _TARGET_VLNV)
    registry.register(parsed_component, _OWNER_VLNV)
    registry.register(parsed_file_owner, _FILE_OWNER_VLNV)
    for register in (*parsed_registers, parsed_file_register):
        assert isinstance(register.choice[0], type(register).RegisterDefinitionRef)
        assert register.choice[0].value == "control"
        assert register.choice[0].type_definitions == "sharedTypes"
        assert api.getRegisterRegisterDefinitionRefByName(get_handle(register)) == "control"
        assert api.getRegisterRegisterDefinitionRefByID(get_handle(register)) == get_handle(definition)


def test_local_declaration_scope_does_not_use_same_name_declaration_elsewhere() -> None:
    component, (register, _, _) = _component()
    other_vlnv = ("example.org", "components", "decoy", "1.0")
    decoy = Component(
        vendor=other_vlnv[0],
        library=other_vlnv[1],
        name=other_vlnv[2],
        version=other_vlnv[3],
        type_definitions=ComponentType.TypeDefinitions(
            external_type_definitions=[_external("sharedTypes", ("example.org", "types", "decoy", "1.0"))]
        ),
    )
    registry.register(component, _OWNER_VLNV)
    registry.register(decoy, other_vlnv)
    expected_external = component.type_definitions.external_type_definitions[0]
    api.setRegisterRegisterDefinitionRef(get_handle(register), "control", "sharedTypes")
    assert api.getRegisterRegisterDefinitionRefByExternalTypeDefID(get_handle(register)) == get_handle(
        expected_external
    )


@pytest.mark.parametrize("failure", ["missing_external", "duplicate_external", "missing_target", "duplicate_target"])
def test_reference_resolution_reports_missing_or_ambiguous_declarations(failure: str) -> None:
    component, (register, _, _) = _component()
    if failure == "missing_external":
        component.type_definitions.external_type_definitions = []
    elif failure == "duplicate_external":
        component.type_definitions.external_type_definitions.append(_external())
    registry.register(component, _OWNER_VLNV)
    if failure == "duplicate_target":
        registry.register(_target(names=("control", "control")), _TARGET_VLNV)
    elif failure != "missing_target":
        registry.register(_target(), _TARGET_VLNV)
    register_id = get_handle(register)
    api.setRegisterRegisterDefinitionRef(register_id, "control", "sharedTypes")

    with pytest.raises(TgiError) as error:
        api.getRegisterRegisterDefinitionRefByExternalTypeDefID(register_id)
        if failure in {"missing_target", "duplicate_target"}:
            api.getRegisterRegisterDefinitionRefByID(register_id)
    assert error.value.fault_code == (
        TgiFaultCode.INVALID_ARGUMENT
        if failure in {"duplicate_external", "duplicate_target"}
        else TgiFaultCode.NOT_FOUND
    )


def test_setter_validates_before_mutation_and_invalidates_only_removed_branch() -> None:
    address_offset = UnsignedLongintExpression(value="16")
    array = Array(dim=[Dim(value="4")])
    alternates = AlternateRegisters(alternate_register=[AlternateRegisters.AlternateRegister(name="alias")])
    parameters = Parameters()
    vendor_extensions = VendorExtensions()
    field = _field()
    size = UnsignedPositiveIntExpression(value="32")
    volatile = Volatile(value=True)
    register = AddressBlockType.Register(
        name="control",
        address_offset=address_offset,
        array=array,
        alternate_registers=alternates,
        parameters=parameters,
        vendor_extensions=vendor_extensions,
        choice=("registerType", size, volatile, field),
    )
    register_id = get_handle(register)
    field_id = get_handle(field)
    field_offset_id = get_handle(field.bit_offset)
    width_id = get_handle(field.choice[0])
    size_id = get_handle(size)
    volatile_id = get_handle(volatile)
    scalar_handle = get_handle("registerType")
    original_choice = register.choice

    with pytest.raises(TgiError) as error:
        api.setRegisterRegisterDefinitionRef(register_id, "invalid name", "sharedTypes")
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert register.choice is original_choice
    assert resolve_handle(field_id) is field
    assert resolve_handle(width_id) is field.choice[0]
    with pytest.raises(TgiError) as error:
        api.setRegisterRegisterDefinitionRef(register_id, "control", "invalid name")
    assert error.value.fault_code == TgiFaultCode.INVALID_ARGUMENT
    assert register.choice is original_choice
    assert resolve_handle(field_id) is field

    assert api.setRegisterRegisterDefinitionRef(register_id, "control", "sharedTypes") is True
    assert len(register.choice) == 1
    assert isinstance(register.choice[0], AddressBlockType.Register.RegisterDefinitionRef)
    assert all(resolve_handle(handle) is None for handle in (field_id, field_offset_id, width_id, size_id, volatile_id))
    assert resolve_handle(scalar_handle) == "registerType"
    assert register.name == "control"
    assert register.address_offset is address_offset
    assert register.array is array
    assert register.alternate_registers is alternates
    assert register.parameters is parameters
    assert register.vendor_extensions is vendor_extensions


@pytest.mark.parametrize(
    ("value", "type_definitions"),
    [("invalid name", "sharedTypes"), ("control", "invalid name")],
)
def test_getters_reject_malformed_stored_reference_names(value: str, type_definitions: str) -> None:
    register = AddressBlockType.Register(
        name="control",
        address_offset=UnsignedLongintExpression(value="0"),
        choice=[AddressBlockType.Register.RegisterDefinitionRef(value=value, type_definitions=type_definitions)],
    )
    register_id = get_handle(register)
    for getter in (
        api.getRegisterRegisterDefinitionRefByExternalTypeDefID,
        api.getRegisterRegisterDefinitionRefByID,
        api.getRegisterRegisterDefinitionRefByName,
        api.getRegisterRegisterDefinitionRefID,
    ):
        with pytest.raises(TgiError) as error:
            getter(register_id)
        assert error.value.fault_code == TgiFaultCode.INVALID_ID


@pytest.mark.parametrize("register_type", _REGISTER_CLASSES)
def test_getters_reject_wrong_or_nonstring_register_handles(register_type: type) -> None:
    register = _register(register_type, "control")
    register_id = get_handle(register)
    for getter in (
        api.getRegisterRegisterDefinitionRefByExternalTypeDefID,
        api.getRegisterRegisterDefinitionRefByID,
        api.getRegisterRegisterDefinitionRefByName,
        api.getRegisterRegisterDefinitionRefID,
    ):
        with pytest.raises(TgiError) as error:
            getter(None)
        assert error.value.fault_code == TgiFaultCode.INVALID_ID
        with pytest.raises(TgiError) as error:
            getter(get_handle(object()))
        assert error.value.fault_code == TgiFaultCode.INVALID_ID
        assert getter(register_id) is None

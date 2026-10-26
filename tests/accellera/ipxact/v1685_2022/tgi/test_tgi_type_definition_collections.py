"""Typed collection getters for reusable IP-XACT type definitions."""

from collections.abc import Callable, Iterator
from dataclasses import fields, is_dataclass
from inspect import getdoc, signature
from typing import Any

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
    AddressBlockDefinitions,
    BankDefinitions,
    Choices,
    ConfigurableLibraryRefType,
    ExternalTypeDefinitions,
    FieldDefinitions,
    MemoryMapDefinitions,
    MemoryRemapDefinitions,
    RegisterDefinitions,
    RegisterFileDefinitions,
    TypeDefinitions,
    UnsignedPositiveIntExpression,
    UnsignedPositiveLongintExpression,
)

_SCHEMA = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))

type _Getter = Callable[[str], list[str]]
type _CaseFactory = Callable[[], tuple[TypeDefinitions, object, tuple[object, ...]]]


@pytest.fixture(autouse=True)
def clear_registry() -> Iterator[None]:
    registry.clear()
    yield
    registry.clear()


def _external(name: str) -> ExternalTypeDefinitions:
    return ExternalTypeDefinitions(
        name=name,
        type_definitions_ref=ConfigurableLibraryRefType(
            vendor="example.org",
            library="types",
            name=f"{name}_types",
            version="1.0",
        ),
    )


def _root(**attributes: Any) -> TypeDefinitions:
    return TypeDefinitions(vendor="example.org", library="types", name="device_types", version="1.0", **attributes)


def _cases() -> list[tuple[str, _Getter, str, str | None, type[Any], type[Any], _CaseFactory]]:
    address_blocks = (
        AddressBlockDefinitions.AddressBlockDefinition(
            name="memory_a",
            range=UnsignedPositiveLongintExpression(value="256"),
            width=UnsignedPositiveIntExpression(value="32"),
        ),
        AddressBlockDefinitions.AddressBlockDefinition(
            name="memory_b",
            range=UnsignedPositiveLongintExpression(value="512"),
            width=UnsignedPositiveIntExpression(value="64"),
        ),
    )
    banks = (BankDefinitions.BankDefinition(name="bank_a"), BankDefinitions.BankDefinition(name="bank_b"))
    choices = (
        Choices.Choice(name="access_a", enumeration=(Choices.Choice.Enumeration(value="read"),)),
        Choices.Choice(name="access_b", enumeration=(Choices.Choice.Enumeration(value="write"),)),
    )
    external_types = (_external("external_a"), _external("external_b"))
    fields = (
        FieldDefinitions.FieldDefinition(name="field_a", bit_width=UnsignedPositiveIntExpression(value="1")),
        FieldDefinitions.FieldDefinition(name="field_b", bit_width=UnsignedPositiveIntExpression(value="2")),
    )
    memory_maps = (
        MemoryMapDefinitions.MemoryMapDefinition(name="map_a"),
        MemoryMapDefinitions.MemoryMapDefinition(name="map_b"),
    )
    memory_remaps = (
        MemoryRemapDefinitions.MemoryRemapDefinition(name="remap_a"),
        MemoryRemapDefinitions.MemoryRemapDefinition(name="remap_b"),
    )
    registers = (
        RegisterDefinitions.RegisterDefinition(name="register_a", size=UnsignedPositiveIntExpression(value="8")),
        RegisterDefinitions.RegisterDefinition(name="register_b", size=UnsignedPositiveIntExpression(value="16")),
    )
    register_files = (
        RegisterFileDefinitions.RegisterFileDefinition(
            name="register_file_a", range=UnsignedPositiveLongintExpression(value="16")
        ),
        RegisterFileDefinitions.RegisterFileDefinition(
            name="register_file_b", range=UnsignedPositiveLongintExpression(value="32")
        ),
    )

    def holder_case(
        root_attr: str,
        holder_type: type[Any],
        member_attr: str,
        member_type: type[Any],
        members: tuple[object, ...],
    ) -> _CaseFactory:
        def build() -> tuple[TypeDefinitions, object, tuple[object, ...]]:
            holder = holder_type(**{member_attr: members})
            return _root(**{root_attr: holder}), holder, members

        return build

    def external_case() -> tuple[TypeDefinitions, object, tuple[object, ...]]:
        return _root(external_type_definitions=external_types), None, external_types

    return [
        (
            "address block definitions",
            api.getTypeDefinitionsAddressBlockDefinitionIDs,
            "address_block_definitions",
            "address_block_definition",
            AddressBlockDefinitions,
            AddressBlockDefinitions.AddressBlockDefinition,
            holder_case(
                "address_block_definitions",
                AddressBlockDefinitions,
                "address_block_definition",
                AddressBlockDefinitions.AddressBlockDefinition,
                address_blocks,
            ),
        ),
        (
            "bank definitions",
            api.getTypeDefinitionsBankDefinitionIDs,
            "bank_definitions",
            "bank_definition",
            BankDefinitions,
            BankDefinitions.BankDefinition,
            holder_case("bank_definitions", BankDefinitions, "bank_definition", BankDefinitions.BankDefinition, banks),
        ),
        (
            "choices",
            api.getTypeDefinitionsChoiceIDs,
            "choices",
            "choice",
            Choices,
            Choices.Choice,
            holder_case("choices", Choices, "choice", Choices.Choice, choices),
        ),
        (
            "external type definitions",
            api.getTypeDefinitionsExternalTypeDefinitionsIDs,
            "external_type_definitions",
            None,
            list,
            ExternalTypeDefinitions,
            external_case,
        ),
        (
            "field definitions",
            api.getTypeDefinitionsFieldDefinitionIDs,
            "field_definitions",
            "field_definition",
            FieldDefinitions,
            FieldDefinitions.FieldDefinition,
            holder_case(
                "field_definitions", FieldDefinitions, "field_definition", FieldDefinitions.FieldDefinition, fields
            ),
        ),
        (
            "memory map definitions",
            api.getTypeDefinitionsMemoryMapDefinitionIDs,
            "memory_map_definitions",
            "memory_map_definition",
            MemoryMapDefinitions,
            MemoryMapDefinitions.MemoryMapDefinition,
            holder_case(
                "memory_map_definitions",
                MemoryMapDefinitions,
                "memory_map_definition",
                MemoryMapDefinitions.MemoryMapDefinition,
                memory_maps,
            ),
        ),
        (
            "memory remap definitions",
            api.getTypeDefinitionsMemoryRemapDefinitionIDs,
            "memory_remap_definitions",
            "memory_remap_definition",
            MemoryRemapDefinitions,
            MemoryRemapDefinitions.MemoryRemapDefinition,
            holder_case(
                "memory_remap_definitions",
                MemoryRemapDefinitions,
                "memory_remap_definition",
                MemoryRemapDefinitions.MemoryRemapDefinition,
                memory_remaps,
            ),
        ),
        (
            "register definitions",
            api.getTypeDefinitionsRegisterDefinitionIDs,
            "register_definitions",
            "register_definition",
            RegisterDefinitions,
            RegisterDefinitions.RegisterDefinition,
            holder_case(
                "register_definitions",
                RegisterDefinitions,
                "register_definition",
                RegisterDefinitions.RegisterDefinition,
                registers,
            ),
        ),
        (
            "register file definitions",
            api.getTypeDefinitionsRegisterFileDefinitionIDs,
            "register_file_definitions",
            "register_file_definition",
            RegisterFileDefinitions,
            RegisterFileDefinitions.RegisterFileDefinition,
            holder_case(
                "register_file_definitions",
                RegisterFileDefinitions,
                "register_file_definition",
                RegisterFileDefinitions.RegisterFileDefinition,
                register_files,
            ),
        ),
    ]


def _assert_descendant_ownership(root: object) -> None:
    pending = [root]
    seen: set[int] = set()
    while pending:
        parent = pending.pop()
        if id(parent) in seen or not is_dataclass(parent) or isinstance(parent, type):
            continue
        seen.add(id(parent))
        for model_field in fields(parent):
            value = getattr(parent, model_field.name)
            if is_dataclass(value) and not isinstance(value, type):
                info = get_parent_info(get_handle(value))
                assert info is not None
                assert info.parent_handle == get_handle(parent)
                assert info.path == (model_field.name,)
                assert info.container == "single"
                pending.append(value)
            elif isinstance(value, (list, tuple)):
                for child in value:
                    if not is_dataclass(child) or isinstance(child, type):
                        continue
                    info = get_parent_info(get_handle(child))
                    assert info is not None
                    assert info.parent_handle == get_handle(parent)
                    assert info.path == (model_field.name,)
                    assert info.container == "list"
                    pending.append(child)


def test_type_definition_collection_getters_have_native_public_signatures() -> None:
    for label, getter, *_ in _cases():
        operation = getattr(api, getter.__name__)
        assert getattr(root_api, getter.__name__) is operation, label
        assert getter.__name__ in api.__all__, label
        assert getter.__name__ in root_api.__all__, label
        operation_signature = signature(operation)
        assert tuple(operation_signature.parameters) == ("typeDefinitionsID",), label
        assert tuple(parameter.annotation for parameter in operation_signature.parameters.values()) == (str,), label
        assert operation_signature.return_annotation == list[str], label
        assert all(parameter.default is parameter.empty for parameter in operation_signature.parameters.values()), label
        docstring = getdoc(operation)
        assert docstring is not None and "Section: F.7.81." in docstring, label
        assert "Args:" in docstring and "Returns:" in docstring, label


@pytest.mark.parametrize(
    ("label", "getter", "root_attr", "member_attr", "holder_type", "member_type", "factory"), _cases()
)
def test_collection_getters_return_ordered_handles_and_restore_ownership(
    label: str,
    getter: _Getter,
    root_attr: str,
    member_attr: str | None,
    holder_type: type[Any],
    member_type: type[Any],
    factory: _CaseFactory,
) -> None:
    root, holder, members = factory()
    assert all(isinstance(member, member_type) for member in members)
    if member_attr is None:
        assert isinstance(root.external_type_definitions, tuple)
        owner = root
    else:
        assert isinstance(holder, holder_type)
        assert getattr(holder, member_attr) is members
        owner = holder

    root_id = get_handle(root)
    ids = getter(root_id)
    assert ids == [get_handle(member) for member in members], label
    assert [resolve_handle(handle) for handle in ids] == list(members), label
    stored_members = root.external_type_definitions if member_attr is None else getattr(holder, member_attr)
    assert stored_members is members, label
    for handle in ids:
        info = get_parent_info(handle)
        assert info is not None, label
        assert info.parent_handle == get_handle(owner), label
        expected_path = (root_attr,) if member_attr is None else (member_attr,)
        assert info.path == expected_path, label
        assert info.container == "list", label
        _assert_descendant_ownership(resolve_handle(handle))

    if member_attr is not None:
        holder_info = get_parent_info(get_handle(holder))
        assert holder_info is not None and holder_info.parent_handle == root_id, label
        assert holder_info.path == (root_attr,), label


@pytest.mark.parametrize(
    ("label", "getter", "root_attr", "member_attr", "holder_type", "member_type", "factory"), _cases()
)
def test_collection_getters_reject_invalid_roots_holders_and_members(
    label: str,
    getter: _Getter,
    root_attr: str,
    member_attr: str | None,
    holder_type: type[Any],
    member_type: type[Any],
    factory: _CaseFactory,
) -> None:
    del holder_type, member_type
    for invalid_root_id in ("stale-handle", get_handle(object())):
        with pytest.raises(TgiError) as error:
            getter(invalid_root_id)
        assert error.value.fault_code == TgiFaultCode.INVALID_ID, label

    root, holder, _members = factory()
    root_id = get_handle(root)
    if member_attr is None:
        root.external_type_definitions = object()  # type: ignore[assignment]
    else:
        setattr(root, root_attr, object())
    with pytest.raises(TgiError) as error:
        getter(root_id)
    assert error.value.fault_code == TgiFaultCode.INVALID_ID, f"{label}: wrong holder"

    root, holder, _members = factory()
    root_id = get_handle(root)
    collection = root if member_attr is None else holder
    attribute = root_attr if member_attr is None else member_attr
    setattr(collection, attribute, object())
    with pytest.raises(TgiError) as error:
        getter(root_id)
    assert error.value.fault_code == TgiFaultCode.INVALID_ID, f"{label}: wrong collection"

    root, holder, _members = factory()
    root_id = get_handle(root)
    collection = root if member_attr is None else holder
    attribute = root_attr if member_attr is None else member_attr
    setattr(collection, attribute, (object(),))
    with pytest.raises(TgiError) as error:
        getter(root_id)
    assert error.value.fault_code == TgiFaultCode.INVALID_ID, f"{label}: wrong member"


@pytest.mark.parametrize(
    ("label", "getter", "root_attr", "member_attr", "holder_type", "member_type", "factory"), _cases()
)
def test_absent_optional_definition_collections_return_empty_lists(
    label: str,
    getter: _Getter,
    root_attr: str,
    member_attr: str | None,
    holder_type: type[Any],
    member_type: type[Any],
    factory: _CaseFactory,
) -> None:
    del label, root_attr, member_attr, holder_type, member_type, factory
    assert getter(get_handle(_root())) == []


def test_parsed_choice_collection_restores_immediate_and_descendant_ownership() -> None:
    nested_value = Choices.Choice.Enumeration(value="idle", text="Idle mode")
    choice = Choices.Choice(name="mode", enumeration=(nested_value,))
    root = _root(choices=Choices(choice=(choice,)))
    xml = XmlDocument.serializer().render(root)
    _SCHEMA.assertValid(etree.fromstring(xml.encode()))
    parsed = XmlDocument.parser().from_string(xml, TypeDefinitions)
    parsed_choice = parsed.choices.choice[0]
    parsed_value = parsed_choice.enumeration[0]

    choice_ids = api.getTypeDefinitionsChoiceIDs(get_handle(parsed))
    assert choice_ids == [get_handle(parsed_choice)]
    value_id = get_handle(parsed_value)
    choice_info = get_parent_info(choice_ids[0])
    value_info = get_parent_info(value_id)
    assert choice_info is not None
    assert choice_info.parent_handle == get_handle(parsed.choices)
    assert choice_info.path == ("choice",)
    assert choice_info.container == "list"
    assert value_info is not None
    assert value_info.parent_handle == choice_ids[0]
    assert value_info.path == ("enumeration",)
    assert value_info.container == "list"

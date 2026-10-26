"""Removal contracts for the nine TypeDefinitions collection families."""

from collections.abc import Callable, Iterator
from dataclasses import fields, is_dataclass
from inspect import signature
from pathlib import Path
from typing import Any

import pytest
from lxml import etree

from amal.eda.accellera.ipxact.v1685_2022 import tgi as root_api
from amal.eda.accellera.ipxact.v1685_2022.tgi import type_definitions as api
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import (
    TgiError,
    TgiFaultCode,
    get_handle,
    register_parent,
    registry,
    resolve_handle,
)
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import (
    AddressBlockDefinitions,
    AddressUnitBits,
    BankDefinitions,
    BankedBlockType,
    Choices,
    ConfigurableLibraryRefType,
    EnumeratedValues,
    EnumeratedValueType,
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
_SAMPLE = Path(
    "tests/xml/ipxact/v1685_2022/accellera.org/Sample/SampleTypeDefinitions/1.0/xml/SampleTypeDefinitions.xml"
)

type _Factory = Callable[[str], Any]
type _Getter = Callable[[str], list[str]]
type _Remover = Callable[[str], bool]


class _Family:
    def __init__(
        self,
        name: str,
        code: str,
        root_attribute: str,
        member_attribute: str | None,
        member_type: type[Any],
        member_factory: _Factory,
        getter: _Getter,
        remover: _Remover,
    ) -> None:
        self.name = name
        self.code = code
        self.root_attribute = root_attribute
        self.member_attribute = member_attribute
        self.member_type = member_type
        self.member_factory = member_factory
        self.getter = getter
        self.remover = remover


def _external(name: str) -> ExternalTypeDefinitions:
    return ExternalTypeDefinitions(
        name=name,
        type_definitions_ref=ConfigurableLibraryRefType(
            vendor="example.org", library="types", name=f"{name}_ref", version="1.0"
        ),
    )


FAMILIES = (
    _Family(
        "address block definition",
        "F.7.82.32",
        "address_block_definitions",
        "address_block_definition",
        AddressBlockDefinitions.AddressBlockDefinition,
        lambda name: AddressBlockDefinitions.AddressBlockDefinition(
            name=name,
            range=UnsignedPositiveLongintExpression(value="256"),
            width=UnsignedPositiveIntExpression(value="32"),
        ),
        api.getTypeDefinitionsAddressBlockDefinitionIDs,
        api.removeTypeDefinitionsAddressBlockDefinition,
    ),
    _Family(
        "bank definition",
        "F.7.82.33",
        "bank_definitions",
        "bank_definition",
        BankDefinitions.BankDefinition,
        lambda name: BankDefinitions.BankDefinition(
            name=name,
            address_block_or_bank=(
                BankedBlockType(
                    name=f"{name}_block",
                    range=UnsignedPositiveLongintExpression(value="128"),
                    width=UnsignedPositiveIntExpression(value="16"),
                ),
            ),
            address_unit_bits=AddressUnitBits(value="8"),
        ),
        api.getTypeDefinitionsBankDefinitionIDs,
        api.removeTypeDefinitionsBankDefinition,
    ),
    _Family(
        "choice",
        "F.7.82.34",
        "choices",
        "choice",
        Choices.Choice,
        lambda name: Choices.Choice(name=name, enumeration=(Choices.Choice.Enumeration(value="read"),)),
        api.getTypeDefinitionsChoiceIDs,
        api.removeTypeDefinitionsChoice,
    ),
    _Family(
        "external type definitions",
        "F.7.82.36",
        "external_type_definitions",
        None,
        ExternalTypeDefinitions,
        _external,
        api.getTypeDefinitionsExternalTypeDefinitionsIDs,
        api.removeTypeDefinitionsExternalTypeDefinitions,
    ),
    _Family(
        "field definition",
        "F.7.82.38",
        "field_definitions",
        "field_definition",
        FieldDefinitions.FieldDefinition,
        lambda name: FieldDefinitions.FieldDefinition(
            name=name,
            bit_width=UnsignedPositiveIntExpression(value="4"),
            enumerated_values=EnumeratedValues(
                enumeration_definition_ref_or_enumerated_value=(
                    EnumeratedValueType(name=f"{name}_enabled", value=UnsignedPositiveIntExpression(value="1")),
                )
            ),
        ),
        api.getTypeDefinitionsFieldDefinitionIDs,
        api.removeTypeDefinitionsFieldDefinition,
    ),
    _Family(
        "memory map definition",
        "F.7.82.39",
        "memory_map_definitions",
        "memory_map_definition",
        MemoryMapDefinitions.MemoryMapDefinition,
        lambda name: MemoryMapDefinitions.MemoryMapDefinition(
            name=name,
            address_unit_bits=AddressUnitBits(value="8"),
        ),
        api.getTypeDefinitionsMemoryMapDefinitionIDs,
        api.removeTypeDefinitionsMemoryMapDefinition,
    ),
    _Family(
        "memory remap definition",
        "F.7.82.40",
        "memory_remap_definitions",
        "memory_remap_definition",
        MemoryRemapDefinitions.MemoryRemapDefinition,
        lambda name: MemoryRemapDefinitions.MemoryRemapDefinition(
            name=name,
            address_unit_bits=AddressUnitBits(value="16"),
        ),
        api.getTypeDefinitionsMemoryRemapDefinitionIDs,
        api.removeTypeDefinitionsMemoryRemapDefinition,
    ),
    _Family(
        "register definition",
        "F.7.82.42",
        "register_definitions",
        "register_definition",
        RegisterDefinitions.RegisterDefinition,
        lambda name: RegisterDefinitions.RegisterDefinition(
            name=name,
            size=UnsignedPositiveIntExpression(value="32"),
        ),
        api.getTypeDefinitionsRegisterDefinitionIDs,
        api.removeTypeDefinitionsRegisterDefinition,
    ),
    _Family(
        "register file definition",
        "F.7.82.43",
        "register_file_definitions",
        "register_file_definition",
        RegisterFileDefinitions.RegisterFileDefinition,
        lambda name: RegisterFileDefinitions.RegisterFileDefinition(
            name=name,
            range=UnsignedPositiveLongintExpression(value="256"),
            address_unit_bits=AddressUnitBits(value="32"),
        ),
        api.getTypeDefinitionsRegisterFileDefinitionIDs,
        api.removeTypeDefinitionsRegisterFileDefinition,
    ),
)


@pytest.fixture(autouse=True)
def clear_registry() -> Iterator[None]:
    registry.clear()
    yield
    registry.clear()


def _root_for(family: _Family, members: tuple[Any, ...], suffix: str = "primary") -> TypeDefinitions:
    attributes: dict[str, Any] = {
        "vendor": "example.org",
        "library": "types",
        "name": f"{family.root_attribute}_{suffix}",
        "version": "1.0",
        "display_name": "Preserve this document metadata",
    }
    if family.member_attribute is None:
        attributes[family.root_attribute] = members
        attributes["choices"] = Choices(choice=(Choices.Choice(name="unrelated", enumeration=()),))
    else:
        holder_type = {
            "address_block_definitions": AddressBlockDefinitions,
            "bank_definitions": BankDefinitions,
            "choices": Choices,
            "field_definitions": FieldDefinitions,
            "memory_map_definitions": MemoryMapDefinitions,
            "memory_remap_definitions": MemoryRemapDefinitions,
            "register_definitions": RegisterDefinitions,
            "register_file_definitions": RegisterFileDefinitions,
        }[family.root_attribute]
        attributes[family.root_attribute] = holder_type(**{family.member_attribute: members})
        attributes["external_type_definitions"] = (_external("unrelated_external"),)
    return TypeDefinitions(**attributes)


def _make(family: _Family, count: int = 2, suffix: str = "primary") -> tuple[TypeDefinitions, tuple[Any, ...]]:
    members = tuple(family.member_factory(f"{family.root_attribute}_{index}") for index in range(count))
    return _root_for(family, members, suffix), members


def _register(root: TypeDefinitions) -> None:
    registry.register(root, (root.vendor, root.library, root.name, root.version))


def _members(root: TypeDefinitions, family: _Family) -> Any:
    if family.member_attribute is None:
        return root.external_type_definitions
    holder = getattr(root, family.root_attribute)
    assert holder is not None
    return getattr(holder, family.member_attribute)


def _descendant_handles(root: Any) -> list[str]:
    result: list[str] = []
    pending = [root]
    seen: set[int] = set()
    while pending:
        node = pending.pop()
        if id(node) in seen or not is_dataclass(node) or isinstance(node, type):
            continue
        seen.add(id(node))
        for model_field in fields(node):
            value = getattr(node, model_field.name)
            children = value if isinstance(value, (list, tuple)) else (value,)
            for child in children:
                if is_dataclass(child) and not isinstance(child, type):
                    result.append(get_handle(child))
                    pending.append(child)
    return result


@pytest.mark.parametrize("family", FAMILIES, ids=lambda family: family.name)
def test_removers_have_native_signatures_exports_and_section_docs(family: _Family) -> None:
    operation = family.remover
    assert getattr(root_api, operation.__name__) is operation
    assert operation.__name__ in api.__all__
    assert operation.__name__ in root_api.__all__
    operation_signature = signature(operation)
    parameter_names = {
        "address block definition": "addressBlockDefinitionID",
        "bank definition": "bankDefinitionID",
        "choice": "choiceID",
        "external type definitions": "externalTypeDefinitionsID",
        "field definition": "fieldDefinitionID",
        "memory map definition": "memoryMapDefinitionID",
        "memory remap definition": "memoryRemapDefinitionID",
        "register definition": "registerDefinitionID",
        "register file definition": "registerFileDefinitionID",
    }
    assert tuple(operation_signature.parameters) == (parameter_names[family.name],)
    assert tuple(parameter.annotation for parameter in operation_signature.parameters.values()) == (str,)
    assert operation_signature.return_annotation is bool
    assert all(parameter.default is parameter.empty for parameter in operation_signature.parameters.values())
    docstring = operation.__doc__
    assert docstring is not None and f"Section: {family.code}." in docstring
    assert "Args:" in docstring and "Returns:" in docstring


@pytest.mark.parametrize("family", FAMILIES, ids=lambda family: family.name)
def test_remover_discovers_parsed_registered_root_before_getter_use(family: _Family) -> None:
    root, _members_before_parse = _make(family)
    parsed = XmlDocument.parser().from_string(XmlDocument.serializer().render(root), TypeDefinitions)
    parsed_members = tuple(_members(parsed, family))
    selected, peer = parsed_members
    subtree = [get_handle(selected), *_descendant_handles(selected)]
    _register(parsed)

    # Deliberately obtain the selected ID from the parsed object without first calling
    # the public getter, so the remover has to discover root ownership itself.
    assert family.remover(get_handle(selected))

    remaining = _members(parsed, family)
    assert list(remaining) == [peer]
    assert all(resolve_handle(handle) is None for handle in subtree)
    assert family.getter(get_handle(parsed)) == [get_handle(peer)]
    reparsed = XmlDocument.parser().from_string(XmlDocument.serializer().render(parsed), TypeDefinitions)
    assert reparsed == parsed


@pytest.mark.parametrize("family", FAMILIES, ids=lambda family: family.name)
def test_remover_normalizes_only_its_tuple_and_preserves_peer_metadata(family: _Family) -> None:
    root, members = _make(family)
    original_tuple = _members(root, family)
    assert isinstance(original_tuple, tuple)
    _register(root)
    subtree = [get_handle(members[0]), *_descendant_handles(members[0])]
    unrelated_external = root.external_type_definitions if family.member_attribute is not None else None
    unrelated_choices = root.choices if family.member_attribute is None else None

    assert family.remover(get_handle(members[0]))

    current = _members(root, family)
    assert isinstance(current, list)
    assert current == [members[1]] and current[0] is members[1]
    assert original_tuple == members
    assert root.display_name == "Preserve this document metadata"
    assert family.getter(get_handle(root)) == [get_handle(members[1])]
    assert resolve_handle(get_handle(members[1])) is members[1]
    assert all(resolve_handle(handle) is None for handle in subtree)
    if unrelated_choices is None:
        assert root.external_type_definitions is unrelated_external
    else:
        assert root.choices is unrelated_choices


@pytest.mark.parametrize("family", FAMILIES, ids=lambda family: family.name)
def test_remover_prunes_last_optional_holder_but_keeps_external_list(family: _Family) -> None:
    root, members = _make(family, count=1)
    _register(root)
    member_handle = get_handle(members[0])

    assert family.remover(get_handle(members[0]))

    if family.member_attribute is None:
        assert root.external_type_definitions == []
    else:
        assert getattr(root, family.root_attribute) is None
    assert family.getter(get_handle(root)) == []
    assert resolve_handle(member_handle) is None


@pytest.mark.parametrize("family", FAMILIES, ids=lambda family: family.name)
def test_remover_can_remove_malformed_member_content(family: _Family) -> None:
    root, members = _make(family, count=1)
    members[0].name = None
    _register(root)

    assert family.remover(get_handle(members[0]))
    assert family.getter(get_handle(root)) == []


@pytest.mark.parametrize("family", FAMILIES, ids=lambda family: family.name)
def test_remover_rejects_wrong_and_orphan_handles_atomically(family: _Family) -> None:
    root, members = _make(family)
    _register(root)
    peer_snapshot = tuple(_members(root, family))

    for invalid_handle in ("stale-handle", get_handle(object())):
        with pytest.raises(TgiError) as error:
            family.remover(invalid_handle)
        assert error.value.fault_code == TgiFaultCode.INVALID_ID
        assert tuple(_members(root, family)) == peer_snapshot

    other_family = next(candidate for candidate in FAMILIES if candidate is not family)
    wrong_family_member = other_family.member_factory("wrong_family")
    with pytest.raises(TgiError) as error:
        family.remover(get_handle(wrong_family_member))
    assert error.value.fault_code == TgiFaultCode.INVALID_ID
    assert tuple(_members(root, family)) == peer_snapshot

    orphan = family.member_factory("orphan")
    with pytest.raises(TgiError) as error:
        family.remover(get_handle(orphan))
    assert error.value.fault_code == TgiFaultCode.INVALID_ID
    assert tuple(_members(root, family)) == peer_snapshot
    assert resolve_handle(get_handle(members[0])) is members[0]


@pytest.mark.parametrize("family", FAMILIES, ids=lambda family: family.name)
@pytest.mark.parametrize("forgery", ("foreign_holder", "foreign_root"))
def test_remover_rejects_misleading_same_type_parent_links_atomically(family: _Family, forgery: str) -> None:
    root, members = _make(family, suffix="source")
    foreign_root, foreign_members = _make(family, suffix="foreign")
    _register(root)
    _register(foreign_root)
    selected = members[0]
    selected_handle = get_handle(selected)

    if family.member_attribute is None:
        foreign_owner: Any = foreign_root
        foreign_attribute = family.root_attribute
    elif forgery == "foreign_holder":
        foreign_owner = getattr(foreign_root, family.root_attribute)
        foreign_attribute = family.member_attribute
    else:
        foreign_owner = foreign_root
        foreign_attribute = family.root_attribute

    if forgery == "foreign_root" and family.member_attribute is not None:
        # The real holder remains in root, while its recorded same-type parent points
        # at a foreign root whose matching slot contains a different holder.
        register_parent(getattr(root, family.root_attribute), foreign_owner, (foreign_attribute,), "single")
    else:
        register_parent(selected, foreign_owner, (foreign_attribute,), "list")

    with pytest.raises(TgiError) as error:
        family.remover(selected_handle)

    assert error.value.fault_code == TgiFaultCode.INVALID_ID
    assert selected in _members(root, family)
    assert foreign_members[0] in _members(foreign_root, family)
    assert resolve_handle(selected_handle) is selected


@pytest.mark.parametrize("family", FAMILIES, ids=lambda family: family.name)
def test_parsed_partial_models_roundtrip_after_each_family_removal(family: _Family) -> None:
    root, _members_before_parse = _make(family)
    parsed = XmlDocument.parser().from_string(XmlDocument.serializer().render(root), TypeDefinitions)
    selected, peer = tuple(_members(parsed, family))
    _register(parsed)

    assert family.remover(get_handle(selected))
    assert list(_members(parsed, family)) == [peer]
    roundtrip = XmlDocument.parser().from_string(XmlDocument.serializer().render(parsed), TypeDefinitions)
    assert roundtrip == parsed


@pytest.mark.parametrize(
    ("root_attribute", "member_attribute", "member_name", "remover"),
    (
        ("field_definitions", "field_definition", "status", api.removeTypeDefinitionsFieldDefinition),
        ("register_definitions", "register_definition", "reg", api.removeTypeDefinitionsRegisterDefinition),
    ),
    ids=("field", "register"),
)
def test_schema_valid_sample_families_remove_and_roundtrip(
    root_attribute: str, member_attribute: str | None, member_name: str, remover: _Remover
) -> None:
    parsed = XmlDocument.parser().from_string(_SAMPLE.read_text(), TypeDefinitions)
    initial_xml = XmlDocument.serializer().render(parsed)
    _SCHEMA.assertValid(etree.fromstring(initial_xml.encode()))
    _register(parsed)

    if member_attribute is None:
        selected = next(item for item in parsed.external_type_definitions if item.name == member_name)
    else:
        holder = getattr(parsed, root_attribute)
        selected = next(item for item in getattr(holder, member_attribute) if item.name == member_name)
    assert remover(get_handle(selected))

    output_xml = XmlDocument.serializer().render(parsed)
    _SCHEMA.assertValid(etree.fromstring(output_xml.encode()))
    roundtrip = XmlDocument.parser().from_string(output_xml, TypeDefinitions)
    assert roundtrip == parsed

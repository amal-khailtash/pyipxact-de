"""Register-file TGI operations preserve IP-XACT 2022 schema choices."""

import pytest
from lxml import etree

from amal.eda.accellera.ipxact.v1685_2022.tgi import register_file as api
from amal.eda.accellera.ipxact.v1685_2022.tgi.component import _register_graph
from amal.eda.accellera.ipxact.v1685_2022.tgi.core import TgiError, get_handle, registry, resolve_handle
from amal.eda.ipxact_de.xml_document import XmlDocument
from org.accellera.ipxact.v1685_2022 import (
    AccessPolicies,
    AccessType,
    AddressBlock,
    AddressUnitBits,
    Array,
    BaseAddress,
    Component,
    ConfigurableLibraryRefType,
    Dim,
    ExternalTypeDefinitions,
    FieldRef,
    FieldType,
    Index,
    Indices,
    MemoryMaps,
    MemoryMapType,
    PathSegmentType,
    RegisterFile,
    RegisterFileDefinitions,
    RegisterFileRef,
    SimpleAccessHandle,
    UnsignedIntExpression,
    UnsignedLongintExpression,
    UnsignedPositiveIntExpression,
    UnsignedPositiveLongintExpression,
    UsageType,
)

_SCHEMA = etree.XMLSchema(etree.parse("submodules/accellera-schemas/IPXACT/1685-2022/index.xsd"))
_NS = {"i": "http://www.accellera.org/XMLSchema/IPXACT/1685-2022"}


@pytest.fixture(autouse=True)
def clean_registry():
    registry.clear()
    yield
    registry.clear()


def _schema_round_trip(document, document_type):
    xml = XmlDocument.serializer().render(document)
    _SCHEMA.assertValid(etree.fromstring(xml.encode()))
    parsed = XmlDocument.parser().from_string(xml, document_type)
    _register_graph(parsed)
    reparsed_xml = XmlDocument.serializer().render(parsed)
    _SCHEMA.assertValid(etree.fromstring(reparsed_xml.encode()))
    return parsed


def _register_file(name, offset, range_value, *, children=()):
    return RegisterFile(
        name=name,
        address_offset=UnsignedLongintExpression(value=offset),
        choice=[UnsignedPositiveLongintExpression(value=range_value), *children],
    )


def _component():
    first_ref = RegisterFileRef(
        register_file_ref="sharedFile",
        indices=Indices(index=[Index(value="1"), Index(value="3")]),
        id="shared-ref",
    )
    second_ref = RegisterFileRef(register_file_ref="otherFile", id="other-ref")
    alias = FieldType.AliasOf(register_file_ref=[first_ref, second_ref], field_ref=FieldRef(field_ref="data"))
    field = FieldType(
        name="data",
        bit_offset=UnsignedIntExpression(value="0"),
        choice=[alias],
    )
    register = RegisterFile.Register(
        name="control",
        address_offset=UnsignedLongintExpression(value="0"),
        choice=[UnsignedPositiveIntExpression(value="32"), field],
    )
    policy = AccessPolicies(access_policy=[AccessPolicies.AccessPolicy(access=AccessType.READ_WRITE, id="rf-policy")])
    access_handle = SimpleAccessHandle(
        path_segments=SimpleAccessHandle.PathSegments(path_segment=[PathSegmentType(value="regs")]),
        id="rf-access",
    )
    array = Array(dim=[Dim(value="4", index_var="i", id="rf-dim")])
    range_value = UnsignedPositiveLongintExpression(value="64", other_attributes={"{urn:test}marker": "range"})
    nested = _register_file("nested", "8", "16")
    inline = RegisterFile(
        name="inlineFile",
        id="rf-inline",
        access_handles=RegisterFile.AccessHandles(access_handle=[access_handle]),
        array=array,
        address_offset=UnsignedLongintExpression(value="16", other_attributes={"{urn:test}marker": "offset"}),
        choice=["registerFileType", range_value, policy, register, nested],
    )
    reference = RegisterFile(
        name="referencedFile",
        id="rf-reference",
        address_offset=UnsignedLongintExpression(value="128"),
        choice=[RegisterFile.RegisterFileDefinitionRef(value="sharedFile", type_definitions="sharedTypes")],
    )
    block = AddressBlock(
        name="registers",
        base_address=BaseAddress(value="0"),
        choice=[
            UnsignedPositiveLongintExpression(value="4096"),
            UnsignedPositiveIntExpression(value="32"),
            UsageType.REGISTER,
            inline,
            reference,
        ],
    )
    memory_map = MemoryMapType(name="peripheral", choice=[block, AddressUnitBits(value="8")])
    root = Component(
        vendor="v",
        library="l",
        name="registerFileContracts",
        version="1",
        memory_maps=MemoryMaps(memory_map=[memory_map]),
        type_definitions=Component.TypeDefinitions(
            external_type_definitions=[
                ExternalTypeDefinitions(
                    name="sharedTypes",
                    type_definitions_ref=ConfigurableLibraryRefType(vendor="v", library="l", name="types", version="1"),
                )
            ]
        ),
    )
    return root


def _register_files(root):
    block = root.memory_maps.memory_map[0].choice[0]
    inline, reference = block.choice[3:]
    return inline, reference


def test_register_file_base_getters_follow_inline_and_reference_schema_choices():
    root = _schema_round_trip(_component(), Component)
    inline, reference = _register_files(root)
    inline_id = get_handle(inline)

    assert api.getRegisterFileAddressOffset(inline_id) == 16
    assert api.getRegisterFileAddressOffsetExpression(inline_id) == "16"
    assert api.getRegisterFileArrayID(inline_id) == get_handle(inline.array)
    assert api.getRegisterFileRange(inline_id) == 64
    assert api.getRegisterFileRangeExpression(inline_id) == "64"
    assert api.getRegisterFileRangeID(inline_id) == get_handle(inline.choice[1])
    assert api.getRegisterFileTypeIdentifier(inline_id) == "registerFileType"
    assert api.getRegisterFileAccessHandleIDs(inline_id) == [get_handle(inline.access_handles.access_handle[0])]
    assert api.getRegisterFileAccessPolicyIDs(inline_id) == [get_handle(inline.choice[2].access_policy[0])]
    assert api.getRegisterFileRegisterIDs(inline_id) == [get_handle(inline.choice[3])]
    assert api.getRegisterFileRegisterFileIDs(inline_id) == [get_handle(inline.choice[4])]

    reference_id = get_handle(reference)
    definition_ref = reference.choice[0]
    assert api.getRegisterFileRegisterFileDefinitionRefByName(reference_id) == "sharedFile"
    assert api.getRegisterFileRegisterFileDefinitionRefID(reference_id) == get_handle(definition_ref)
    external_type_definitions = root.type_definitions.external_type_definitions[0]
    assert api.getRegisterFileRegisterFileDefinitionRefByExternalTypeDefID(reference_id) == get_handle(
        external_type_definitions
    )
    assert api.getRegisterFileRegisterFileDefinitionRefByID(reference_id) is None
    assert api.getRegisterFileRange(reference_id) is None
    assert api.getRegisterFileRegisterIDs(reference_id) == []
    assert api.getRegisterFileRegisterFileIDs(reference_id) == []


def test_register_file_alias_refs_and_indices_round_trip_and_invalidate_on_removal():
    root = _schema_round_trip(_component(), Component)
    inline, _reference = _register_files(root)
    register = inline.choice[3]
    alias = register.choice[1].choice[0]
    alias_id = get_handle(alias)

    assert api.getAliasOfRegisterFileRefByNames(alias_id) == ["sharedFile", "otherFile"]
    ref_ids = api.getAliasOfRegisterFileRefIDs(alias_id)
    assert ref_ids == [get_handle(ref) for ref in alias.register_file_ref]
    assert api.getRegisterFileRefIndexIDs(ref_ids[0]) == [
        get_handle(index) for index in alias.register_file_ref[0].indices.index
    ]

    new_ref_id = api.addAliasOfRegisterFileRef(alias_id, "generatedFile")
    new_index_id = api.addRegisterFileRefIndex(new_ref_id, "5")
    assert api.getAliasOfRegisterFileRefByNames(alias_id) == ["sharedFile", "otherFile", "generatedFile"]
    assert api.getRegisterFileRefIndexIDs(new_ref_id) == [new_index_id]
    _schema_round_trip(root, Component)

    assert api.removeRegisterFileRefIndex(new_index_id)
    assert resolve_handle(new_index_id) is None
    assert api.getRegisterFileRefIndexIDs(new_ref_id) == []
    assert api.removeAliasOfRegisterFileRef(new_ref_id)
    assert resolve_handle(new_ref_id) is None
    assert api.getAliasOfRegisterFileRefByNames(alias_id) == ["sharedFile", "otherFile"]
    _schema_round_trip(root, Component)


def test_register_file_definition_addition_uses_definition_model_and_is_schema_valid():
    definition = RegisterFileDefinitions.RegisterFileDefinition(
        name="sharedFile",
        range=UnsignedPositiveLongintExpression(value="64"),
    )
    definitions = RegisterFileDefinitions(register_file_definition=[definition])
    parsed = _schema_round_trip(definitions, RegisterFileDefinitions)
    parsed_definition = parsed.register_file_definition[0]

    new_id = api.addRegisterFileDefinitionRegisterFile(get_handle(parsed_definition), "childFile", "8", "16")
    child = resolve_handle(new_id)
    assert isinstance(child, RegisterFile)
    assert child.name == "childFile"
    assert child.address_offset.value == "8"
    assert child.choice[0].value == "16"
    assert parsed_definition.register_or_register_file == [child]
    reparsed = _schema_round_trip(parsed, RegisterFileDefinitions)
    assert reparsed.register_file_definition[0].register_or_register_file[0].name == "childFile"


def test_register_file_expression_edits_preserve_schema_wrapper_and_definition_choice_transitions():
    root = _schema_round_trip(_component(), Component)
    inline, reference = _register_files(root)
    inline_id = get_handle(inline)
    offset_wrapper = inline.address_offset
    range_wrapper = inline.choice[1]
    offset_id = get_handle(offset_wrapper)
    range_id = api.getRegisterFileRangeID(inline_id)

    api.setRegisterFileAddressOffset(inline_id, "BASE_OFFSET + 16")
    api.setRegisterFileRange(inline_id, "WINDOW_RANGE")
    assert inline.address_offset is offset_wrapper
    assert inline.choice[1] is range_wrapper
    assert get_handle(offset_wrapper) == offset_id
    assert api.getRegisterFileRangeID(inline_id) == range_id
    assert offset_wrapper.other_attributes == {"{urn:test}marker": "offset"}
    assert range_wrapper.other_attributes == {"{urn:test}marker": "range"}
    assert api.getRegisterFileAddressOffsetExpression(inline_id) == "BASE_OFFSET + 16"
    assert api.getRegisterFileRangeExpression(inline_id) == "WINDOW_RANGE"
    with pytest.raises(TgiError):
        api.getRegisterFileAddressOffset(inline_id)
    with pytest.raises(TgiError):
        api.getRegisterFileRange(inline_id)

    api.setRegisterFileTypeIdentifier(inline_id, "updatedType")
    assert api.getRegisterFileTypeIdentifier(inline_id) == "updatedType"
    access_handle_id = api.getRegisterFileAccessHandleIDs(inline_id)[0]
    assert api.removeRegisterFileAccessHandle(access_handle_id)
    assert resolve_handle(access_handle_id) is None
    assert api.getRegisterFileAccessHandleIDs(inline_id) == []
    assert api.removeRegisterFileTypeIdentifier(inline_id)
    assert api.getRegisterFileTypeIdentifier(inline_id) is None
    _schema_round_trip(root, Component)

    reference_id = get_handle(reference)
    ref_node_id = api.getRegisterFileRegisterFileDefinitionRefID(reference_id)
    api.setRegisterFileRange(reference_id, "32")
    assert resolve_handle(ref_node_id) is None
    assert api.getRegisterFileRegisterFileDefinitionRefID(reference_id) is None
    assert api.getRegisterFileRange(reference_id) == 32
    assert api.getRegisterFileRegisterIDs(reference_id) == []

    added_register_id = api.addRegisterFileRegister(reference_id, "status", "0", "32", "ready", "0", "1")
    added_register = resolve_handle(added_register_id)
    assert isinstance(added_register, RegisterFile.Register)
    assert api.getRegisterFileRegisterIDs(reference_id) == [added_register_id]
    _schema_round_trip(root, Component)

    api.setRegisterFileRegisterFileDefinitionRef(reference_id, "sharedFile", "sharedTypes")
    assert api.getRegisterFileRegisterFileDefinitionRefByName(reference_id) == "sharedFile"
    assert resolve_handle(added_register_id) is None
    assert api.getRegisterFileRegisterIDs(reference_id) == []
    assert api.getRegisterFileRange(reference_id) is None
    _schema_round_trip(root, Component)


def test_nested_register_file_removal_invalidates_owned_register_field_and_range_handles():
    root = _schema_round_trip(_component(), Component)
    inline, _reference = _register_files(root)
    inline_id = get_handle(inline)
    nested_id = api.getRegisterFileRegisterFileIDs(inline_id)[0]
    nested = resolve_handle(nested_id)
    nested_range_id = get_handle(nested.choice[0])
    assert api.removeRegisterFileRegisterFile(nested_id)
    assert resolve_handle(nested_id) is None
    assert resolve_handle(nested_range_id) is None
    assert api.getRegisterFileRegisterFileIDs(inline_id) == []
    _schema_round_trip(root, Component)

    register_id = api.getRegisterFileRegisterIDs(inline_id)[0]
    register = resolve_handle(register_id)
    field_id = get_handle(register.choice[1])
    assert api.removeRegisterFileRegister(register_id)
    assert resolve_handle(register_id) is None
    assert resolve_handle(field_id) is None
    assert api.getRegisterFileRegisterIDs(inline_id) == []
    _schema_round_trip(root, Component)
